"""การทดลองนำร่อง: BGE-M3 ค้นด้วยคำค้นภาษาไทยบนคลังสินค้าภาษาอังกฤษได้ดีแค่ไหน

**ทำไมต้องทดลองก่อน:** mark5 ตัดสินใจรับคำค้นภาษาไทยล้วน แต่ข้อมูลสินค้าเป็นอังกฤษทั้งหมด
จึงเป็นงาน cross-lingual retrieval (CLIR) ถ้า BGE-M3 ทำไม่ได้ ต้องเปลี่ยนสถาปัตยกรรม
(เช่น แปลคำค้นเป็นอังกฤษก่อนค้น) — ต้องรู้ **ก่อน** ลงทุน embed ทั้งชุด ~3.4 ชั่วโมง
ผลของสคริปต์นี้เป็นหลักฐานประกอบ ADR-0005

**วิธีวัด:** ใช้ตัวอย่างสินค้าแบบสุ่มตามสัดส่วนหมวด แล้วยิงคำค้นคู่ไทย-อังกฤษที่มีความหมาย
เดียวกัน 25 คู่ เทียบว่าได้ผลลัพธ์ชุดเดียวกันไหม

**ข้อจำกัดที่ต้องระบุเสมอ:** ตัวชี้วัดหลักคือ **ความสอดคล้อง (agreement)** ระหว่างผลไทยกับ
ผลอังกฤษ **ไม่ใช่ความถูกต้อง** ถ้าฝั่งอังกฤษค้นผิดอยู่แล้ว overlap สูงก็แปลว่าผิดเหมือนกันทั้งคู่
รายงานจึงพิมพ์ชื่อสินค้า top-3 ของทั้งสองภาษาออกมาให้ตรวจด้วยตาเสมอ

รัน:  python -m eval.pilot.crosslingual_pilot [--sample 5000] [--top-k 10]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from config import settings
from mark5.common.logger import get_logger
from mark5.index.embedder import OllamaEmbedder

from .queries_th_en import QUERY_PAIRS

log = get_logger(__name__)

RESULTS_DIR = settings.ROOT / "eval" / "results"
REPORT_FILE = RESULTS_DIR / "crosslingual_pilot.md"
RAW_FILE = RESULTS_DIR / "crosslingual_pilot.json"


def stratified_sample(df: pd.DataFrame, n: int, seed: int = 42) -> pd.DataFrame:
    """สุ่มตัวอย่างตามสัดส่วนหมวด โดยรับประกันว่าทุกหมวดมีอย่างน้อย 1 รายการ

    สุ่มตามสัดส่วนเพื่อให้ตัวอย่างสะท้อนคลังจริง (แฟชั่น 31% ก็ควรเป็น 31% ในตัวอย่าง)
    ถ้าปรับให้ทุกหมวดเท่ากันจะได้ผลที่สวยเกินจริง เพราะลดการแข่งขันจากหมวดใหญ่
    """
    per_category = (df["category"].value_counts(normalize=True) * n).round().astype(int).clip(lower=1)
    parts = [
        group.sample(min(len(group), per_category[name]), random_state=seed)
        for name, group in df.groupby("category", sort=False)
    ]
    return pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)


def top_k(query_vec: list[float], doc_vecs: list[list[float]], k: int) -> list[tuple[int, float]]:
    """คืน (ตำแหน่งเอกสาร, คะแนน cosine) k อันดับแรก — เวกเตอร์ normalize แล้ว cosine = dot"""
    scores = [(i, sum(q * d for q, d in zip(query_vec, vec, strict=True)))
              for i, vec in enumerate(doc_vecs)]
    scores.sort(key=lambda pair: -pair[1])
    return scores[:k]


def run(sample_size: int, k: int) -> dict:
    log.info("อ่านชั้น feature ...")
    df = pd.read_parquet(settings.FEATURE_FILE,
                         columns=["parent_asin", "title", "category", "embed_text"])
    sample = stratified_sample(df, sample_size)
    log.info("ตัวอย่าง %s รายการ จาก %s รายการ ครอบคลุม %d หมวด",
             f"{len(sample):,}", f"{len(df):,}", sample["category"].nunique())

    with OllamaEmbedder(batch_size=32) as embedder:
        embedder.health_check()

        log.info("เข้ารหัสเอกสารตัวอย่าง (ประมาณ %.0f นาที) ...", len(sample) * 0.104 / 60)
        started = time.perf_counter()
        doc_vecs = embedder.embed(sample["embed_text"].tolist(), show_progress=True)
        log.info("เข้ารหัสเอกสารเสร็จใน %.1f นาที", (time.perf_counter() - started) / 60)

        log.info("เข้ารหัสคำค้น %d คู่ ...", len(QUERY_PAIRS))
        th_vecs = embedder.embed([q["th"] for q in QUERY_PAIRS])
        en_vecs = embedder.embed([q["en"] for q in QUERY_PAIRS])

    rows = []
    for pair, th_vec, en_vec in zip(QUERY_PAIRS, th_vecs, en_vecs, strict=True):
        th_hits = top_k(th_vec, doc_vecs, k)
        en_hits = top_k(en_vec, doc_vecs, k)
        th_ids = [i for i, _ in th_hits]
        en_ids = [i for i, _ in en_hits]

        rows.append({
            "id": pair["id"], "th": pair["th"], "en": pair["en"],
            "overlap_at_5": len(set(th_ids[:5]) & set(en_ids[:5])) / 5,
            "overlap_at_k": len(set(th_ids) & set(en_ids)) / k,
            "en_top1_in_th_topk": en_ids[0] in th_ids,
            "th_top1_in_en_topk": th_ids[0] in en_ids,
            # คะแนน cosine เฉลี่ยของ top-5 — บอกว่าโมเดล "มั่นใจ" ต่างกันแค่ไหนระหว่างสองภาษา
            "th_mean_score_at_5": sum(s for _, s in th_hits[:5]) / 5,
            "en_mean_score_at_5": sum(s for _, s in en_hits[:5]) / 5,
            "query_pair_cosine": sum(a * b for a, b in zip(th_vec, en_vec, strict=True)),
            "th_top3": [{"title": sample.at[i, "title"][:90],
                         "category": sample.at[i, "category"]} for i in th_ids[:3]],
            "en_top3": [{"title": sample.at[i, "title"][:90],
                         "category": sample.at[i, "category"]} for i in en_ids[:3]],
        })

    summary = {
        "sample_size": len(sample),
        "top_k": k,
        "n_queries": len(rows),
        "mean_overlap_at_5": sum(r["overlap_at_5"] for r in rows) / len(rows),
        "mean_overlap_at_k": sum(r["overlap_at_k"] for r in rows) / len(rows),
        "rate_en_top1_in_th_topk": sum(r["en_top1_in_th_topk"] for r in rows) / len(rows),
        "rate_th_top1_in_en_topk": sum(r["th_top1_in_en_topk"] for r in rows) / len(rows),
        "mean_th_score_at_5": sum(r["th_mean_score_at_5"] for r in rows) / len(rows),
        "mean_en_score_at_5": sum(r["en_mean_score_at_5"] for r in rows) / len(rows),
        "mean_query_pair_cosine": sum(r["query_pair_cosine"] for r in rows) / len(rows),
    }
    return {"summary": summary, "queries": rows}


def write_report(result: dict) -> None:
    s, rows = result["summary"], result["queries"]
    worst = sorted(rows, key=lambda r: r["overlap_at_k"])[:5]

    lines = [
        "# การทดลองนำร่อง: Cross-lingual retrieval (คำค้นไทย → คลังสินค้าอังกฤษ)",
        "",
        f"BGE-M3 ผ่าน Ollama · ตัวอย่าง {s['sample_size']:,} รายการ (สุ่มตามสัดส่วนหมวด) · "
        f"คำค้น {s['n_queries']} คู่ · top-{s['top_k']}",
        "",
        "> **ตัวชี้วัดนี้วัด _ความสอดคล้อง_ ไม่ใช่ _ความถูกต้อง_** — ถ้าฝั่งอังกฤษค้นผิดอยู่แล้ว",
        "> overlap สูงก็แปลว่าผิดเหมือนกันทั้งสองภาษา ต้องอ่านตารางท้ายรายงานประกอบเสมอ",
        "",
        "## ผลรวม", "",
        "| ตัวชี้วัด | ค่า |", "|---|---|",
        f"| overlap@5 (ผลไทย ∩ ผลอังกฤษ) | **{s['mean_overlap_at_5']:.1%}** |",
        f"| overlap@{s['top_k']} | **{s['mean_overlap_at_k']:.1%}** |",
        f"| อันดับ 1 ของอังกฤษ ติด top-{s['top_k']} ของไทย | {s['rate_en_top1_in_th_topk']:.1%} |",
        f"| อันดับ 1 ของไทย ติด top-{s['top_k']} ของอังกฤษ | {s['rate_th_top1_in_en_topk']:.1%} |",
        f"| cosine เฉลี่ย top-5 (ไทย) | {s['mean_th_score_at_5']:.4f} |",
        f"| cosine เฉลี่ย top-5 (อังกฤษ) | {s['mean_en_score_at_5']:.4f} |",
        f"| cosine ระหว่างคำค้นไทยกับอังกฤษที่คู่กัน | {s['mean_query_pair_cosine']:.4f} |",
        "",
        "## รายคำค้น", "",
        f"| id | คำค้นไทย | overlap@5 | overlap@{s['top_k']} | cosine ไทย | cosine อังกฤษ |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['id']} | {r['th']} | {r['overlap_at_5']:.0%} | {r['overlap_at_k']:.0%} "
                     f"| {r['th_mean_score_at_5']:.3f} | {r['en_mean_score_at_5']:.3f} |")

    lines += ["", "## 5 คำค้นที่สอดคล้องกันน้อยที่สุด (ตรวจด้วยตา)", ""]
    for r in worst:
        lines += [f"### {r['id']} — ไทย: “{r['th']}” · อังกฤษ: “{r['en']}” "
                  f"(overlap@{s['top_k']} = {r['overlap_at_k']:.0%})", ""]
        for lang, key in (("ไทย", "th_top3"), ("อังกฤษ", "en_top3")):
            lines.append(f"**{lang}**")
            lines += [f"- {h['title']}  _[{h['category']}]_" for h in r[key]]
            lines.append("")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    RAW_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("เขียนรายงาน %s", REPORT_FILE.relative_to(settings.ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="ทดลอง cross-lingual retrieval บนตัวอย่างเล็ก")
    parser.add_argument("--sample", type=int, default=5000, help="จำนวนสินค้าในตัวอย่าง")
    parser.add_argument("--top-k", type=int, default=10, help="จำนวนผลลัพธ์ที่นำมาเทียบ")
    args = parser.parse_args()

    result = run(args.sample, args.top_k)
    write_report(result)

    s = result["summary"]
    log.info("=" * 60)
    log.info("overlap@5 = %.1f%% | overlap@%d = %.1f%% | cosine คำค้นคู่ = %.4f",
             s["mean_overlap_at_5"] * 100, s["top_k"], s["mean_overlap_at_k"] * 100,
             s["mean_query_pair_cosine"])


if __name__ == "__main__":
    main()
