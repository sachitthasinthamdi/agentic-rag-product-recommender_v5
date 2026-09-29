"""การทดลองรอบสอง: เทียบ 3 กลยุทธ์ CLIR บนคลังเต็ม 117,243 รายการ

แก้ข้อจำกัดของรอบแรก (`crosslingual_pilot.py`) ไป 2 ข้อ:
  1. รอบแรกใช้ตัวอย่างแค่ 5,018 รายการ — บางคำค้นอาจไม่มีของตรงอยู่เลย
     รอบนี้ค้นบนดัชนีเต็มที่สร้างด้วย `mark5.index.build_index`
  2. รอบแรกวัดได้แค่ "ความสอดคล้อง" ไม่ใช่ "ความถูกต้อง"
     รอบนี้เพิ่ม **product-type precision@5** ตัดสินด้วย LLM judge (ตรงกับตัวชี้วัดกลุ่ม B
     ใน `docs/01_objectives.md`)

กลยุทธ์ที่เทียบ (ตัวเลือกใน ADR-0005):
  - `thai`      ค้นด้วยคำค้นไทยตรง ๆ
  - `translate` แปลเป็นอังกฤษด้วย Typhoon2 แล้วค้น
  - `fused`     ค้นทั้งสองภาษา รวมอันดับด้วย RRF
  - `en_oracle` ค้นด้วยคำค้นอังกฤษที่คนเขียนเอง — **เพดานบน** ไม่ใช่กลยุทธ์ที่ใช้จริง
                (ผู้ใช้จริงพิมพ์ไทย) แต่บอกว่า "ดีที่สุดเท่าที่ระบบนี้ทำได้" อยู่ตรงไหน

รัน:  python -m eval.pilot.crosslingual_compare [--top-k 5]
"""

from __future__ import annotations

import argparse
import json
import time

from config import settings
from mark5.common.llm import OllamaChat
from mark5.common.logger import get_logger
from mark5.retrieval.retriever import Retriever

from .queries_th_en import QUERY_PAIRS
from .type_judge import ProductTypeJudge

log = get_logger(__name__)

RESULTS_DIR = settings.ROOT / "eval" / "results"
REPORT_FILE = RESULTS_DIR / "crosslingual_compare.md"
RAW_FILE = RESULTS_DIR / "crosslingual_compare.json"

# ชื่อกลยุทธ์ -> (โหมดของ Retriever, น้ำหนัก RRF (ไทย, อังกฤษ))
# `fused_w3` / `fused_w5` เพิ่มหลังพบว่า RRF น้ำหนักเท่ากันแพ้การแปลอย่างเดียว
# สมมติฐาน: ถ่วงให้ฝั่งอังกฤษมากกว่า จะได้ความแม่นของฝั่งแปล + เก็บกลไกพยุงตอนแปลผิดไว้
STRATEGY_SPECS: dict[str, tuple[str, tuple[float, float]]] = {
    "thai": ("thai", (1.0, 1.0)),
    "translate": ("translate", (1.0, 1.0)),
    "fused": ("fused", (1.0, 1.0)),
    "fused_w3": ("fused", (1.0, 3.0)),
    "fused_w5": ("fused", (1.0, 5.0)),
    "en_oracle": ("raw", (1.0, 1.0)),
}
STRATEGIES = list(STRATEGY_SPECS)


def retrieve_all(k: int) -> tuple[dict, dict]:
    """ค้นทุกกลยุทธ์ทุกคำค้น — คืน (ผลการค้น, คำแปลที่ได้)"""
    results: dict[str, dict[str, list]] = {s: {} for s in STRATEGIES}
    translations: dict[str, str] = {}

    with Retriever() as retriever:
        for i, pair in enumerate(QUERY_PAIRS, 1):
            thai, english = pair["th"], pair["en"]
            translations[pair["id"]] = retriever.translator.translate(thai)

            for strategy, (mode, weights) in STRATEGY_SPECS.items():
                text = english if strategy == "en_oracle" else thai
                hits = retriever.search(text, n=k, strategy=mode, fuse_weights=weights)
                results[strategy][pair["id"]] = [
                    {"id": h.id, "title": h.title, "category": h.category,
                     "score": round(h.score, 4)} for h in hits
                ]
            log.info("[%d/%d] %s | แปลได้: %s", i, len(QUERY_PAIRS), thai, translations[pair["id"]])

    return results, translations


def judge_all(results: dict, k: int, warm_cache: dict | None = None) -> dict:
    """ตัดสินทุกคู่ (คำค้น, สินค้า) ว่าตรงประเภทไหม

    `warm_cache` = คำตัดสินจากการรันครั้งก่อน ใช้ซ้ำได้เมื่อ **prompt ของ judge ไม่เปลี่ยน**
    นอกจากจะเร็วขึ้นแล้ว ยังทำให้คู่เดิมได้คำตัดสินเดิมเป๊ะ — กลยุทธ์ที่เพิ่มเข้ามาทีหลัง
    จึงถูกวัดด้วยไม้บรรทัดอันเดียวกับของเดิม ไม่ใช่ไม้บรรทัดที่สุ่มใหม่
    """
    verdicts: dict[str, dict] = dict(warm_cache or {})
    if verdicts:
        log.info("ใช้คำตัดสินเดิมซ้ำ %s คู่", f"{len(verdicts):,}")
    total = sum(len(results[s][q["id"]]) for s in STRATEGIES for q in QUERY_PAIRS)
    done = 0
    started = time.perf_counter()

    with OllamaChat() as chat:
        judge = ProductTypeJudge(chat)
        for pair in QUERY_PAIRS:
            # ตัดสินโดยอิงคำค้น **ภาษาอังกฤษที่คนเขียน** เป็นตัวแทนเจตนาของผู้ใช้เสมอ
            # เพื่อให้ทุกกลยุทธ์ถูกตัดสินด้วยไม้บรรทัดอันเดียวกัน
            wanted = pair["en"]
            for strategy in STRATEGIES:
                for hit in results[strategy][pair["id"]]:
                    key = f"{pair['id']}|{hit['id']}"
                    if key not in verdicts:
                        match, reason = judge.judge(wanted, hit["title"])
                        verdicts[key] = {"match": match, "reason": reason,
                                         "title": hit["title"], "wanted": wanted}
                    done += 1
                    if done % 20 == 0:
                        elapsed = time.perf_counter() - started
                        log.info("judge %d/%d (%.0f%%) | เหลือประมาณ %.0f นาที",
                                 done, total, done / total * 100,
                                 (total - done) * elapsed / done / 60)
    return verdicts


def summarise(results: dict, verdicts: dict, k: int) -> dict:
    summary = {}
    oracle_sets = {q["id"]: {h["id"] for h in results["en_oracle"][q["id"]]} for q in QUERY_PAIRS}

    for strategy in STRATEGIES:
        matched = unmatched = unparsed = 0
        per_query = {}
        overlaps = []
        for pair in QUERY_PAIRS:
            hits = results[strategy][pair["id"]]
            q_matched = 0
            for hit in hits:
                verdict = verdicts[f"{pair['id']}|{hit['id']}"]["match"]
                if verdict is True:
                    matched += 1
                    q_matched += 1
                elif verdict is False:
                    unmatched += 1
                else:
                    unparsed += 1
            per_query[pair["id"]] = q_matched / len(hits) if hits else 0.0
            overlaps.append(len({h["id"] for h in hits} & oracle_sets[pair["id"]]) / k)

        judged = matched + unmatched
        summary[strategy] = {
            "precision_at_k": matched / judged if judged else 0.0,
            "n_matched": matched, "n_judged": judged, "n_unparsed": unparsed,
            "queries_with_zero_match": sum(1 for v in per_query.values() if v == 0),
            "overlap_with_oracle": sum(overlaps) / len(overlaps),
            "per_query": per_query,
        }
    return summary


def write_report(summary: dict, results: dict, translations: dict, verdicts: dict, k: int) -> None:
    names = {"thai": "ก. ไทยล้วน", "translate": "ข. แปลก่อนค้น",
             "fused": "ค. สองภาษา + RRF (1:1)", "fused_w3": "ง. สองภาษา + RRF (ไทย:อังกฤษ = 1:3)",
             "fused_w5": "จ. สองภาษา + RRF (1:5)",
             "en_oracle": "(เพดานบน) คำค้นอังกฤษที่คนเขียน"}
    short = {"thai": "ก.ไทย", "translate": "ข.แปล", "fused": "ค.1:1",
             "fused_w3": "ง.1:3", "fused_w5": "จ.1:5", "en_oracle": "เพดานบน"}

    lines = [
        "# เทียบกลยุทธ์ Cross-lingual Retrieval บนคลังเต็ม",
        "",
        f"ดัชนีเต็ม 117,243 รายการ · คำค้น {len(QUERY_PAIRS)} คู่ · top-{k} · "
        "ตัดสินประเภทสินค้าด้วย Typhoon2-8B (binary)",
        "",
        "> **ข้อจำกัด:** ความน่าเชื่อถือของ judge ยังไม่ได้ตรวจสอบกับ label ของคน",
        "> ตัวเลข precision จึงเป็นหลักฐานระดับ indicative — ใช้เปรียบเทียบกลยุทธ์กันเองได้",
        "> แต่ยังอ้างเป็นค่าสัมบูรณ์ในเล่มไม่ได้จนกว่าจะ validate judge",
        "",
        "## ผลรวม", "",
        f"| กลยุทธ์ | product-type precision@{k} | คำค้นที่ไม่ได้ของตรงเลย | overlap กับเพดานบน |",
        "|---|---|---|---|",
    ]
    for strategy in STRATEGIES:
        s = summary[strategy]
        lines.append(f"| {names[strategy]} | **{s['precision_at_k']:.1%}** "
                     f"({s['n_matched']}/{s['n_judged']}) | {s['queries_with_zero_match']}/{len(QUERY_PAIRS)} "
                     f"| {s['overlap_with_oracle']:.1%} |")

    unparsed = sum(summary[s]["n_unparsed"] for s in STRATEGIES)
    if unparsed:
        lines += ["", f"⚠ judge ตอบในรูปแบบที่ parse ไม่ได้ {unparsed} ครั้ง (ไม่นับรวมในตัวหาร)"]

    header = " | ".join(short[s] for s in STRATEGIES)
    lines += ["", "## รายคำค้น", "",
              f"| id | คำค้นไทย | คำแปลที่ Typhoon2 ได้ | {header} |",
              "|---|---|---|" + "---|" * len(STRATEGIES)]
    for pair in QUERY_PAIRS:
        row = " | ".join(f"{summary[s]['per_query'][pair['id']]:.0%}" for s in STRATEGIES)
        lines.append(f"| {pair['id']} | {pair['th']} | {translations[pair['id']]} | {row} |")

    # คำค้นที่กลยุทธ์ "ไทยล้วน" แย่กว่า "รวมสองภาษา" มากที่สุด — ตรวจด้วยตา
    gaps = sorted(QUERY_PAIRS,
                  key=lambda p: summary["fused"]["per_query"][p["id"]]
                  - summary["thai"]["per_query"][p["id"]], reverse=True)[:4]
    lines += ["", "## คำค้นที่การรวมสองภาษาช่วยได้มากที่สุด (ตรวจด้วยตา)", ""]
    for pair in gaps:
        lines += [f"### {pair['id']} — “{pair['th']}” → แปลเป็น “{translations[pair['id']]}”", ""]
        for strategy in ("thai", "fused"):
            lines.append(f"**{names[strategy]}** ({summary[strategy]['per_query'][pair['id']]:.0%})")
            for hit in results[strategy][pair["id"]][:3]:
                verdict = verdicts[f"{pair['id']}|{hit['id']}"]["match"]
                mark = {True: "✅", False: "❌"}.get(verdict, "❓")
                lines.append(f"- {mark} {hit['title'][:85]}  _[{hit['category']}]_")
            lines.append("")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    RAW_FILE.write_text(json.dumps(
        {"summary": summary, "results": results, "translations": translations,
         "verdicts": verdicts}, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("เขียนรายงาน %s", REPORT_FILE.relative_to(settings.ROOT))


def _audit_dump(verdicts: dict) -> str:
    """เทคำตัดสินทั้งหมดออกมาเป็นไฟล์เดียวให้คนไล่ตรวจได้

    จำเป็นเพราะรอบแรก judge ตัดสินผิดแบบเป็นระบบ (ปฏิเสธปลอกคอสุนัขเมื่อถามหาปลอกคอสุนัข)
    ถ้าไม่มีไฟล์แบบนี้ให้ไล่ดู จะไม่มีทางรู้เลยว่าตัวเลข precision ที่ได้มาเชื่อถือไม่ได้
    """
    by_query: dict[str, list] = {}
    for key, value in verdicts.items():
        by_query.setdefault(key.split("|")[0], []).append(value)

    lines = ["# คำตัดสินทั้งหมดของ LLM judge (สำหรับไล่ตรวจด้วยมือ)", "",
             f"รวม {len(verdicts)} คู่ (คำค้น × สินค้า) หลังตัดรายการซ้ำ", ""]
    for qid in sorted(by_query):
        items = by_query[qid]
        lines += [f"## {qid} — ผู้ใช้ต้องการ: {items[0]['wanted']}", ""]
        for item in items:
            mark = {True: "✅ YES", False: "❌ NO ", None: "❓ ??"}[item["match"]]
            lines.append(f"- {mark} | {item['title'][:88]}")
            lines.append(f"  - _{item['reason'][:150]}_")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="เทียบกลยุทธ์ CLIR 3 แบบบนคลังเต็ม")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--rejudge", action="store_true",
                        help="ใช้ผลการค้นเดิมจากไฟล์ JSON แล้วตัดสินใหม่อย่างเดียว "
                             "(สำหรับตอนแก้ prompt ของ judge — ไม่ต้องค้นซ้ำ)")
    args = parser.parse_args()
    k = args.top_k

    previous = json.loads(RAW_FILE.read_text(encoding="utf-8")) if RAW_FILE.exists() else {}

    if args.rejudge:
        if not previous:
            raise SystemExit(f"ไม่พบ {RAW_FILE} — ต้องรันเต็มอย่างน้อยหนึ่งครั้งก่อน")
        log.info("โหมด rejudge — ใช้ผลการค้นเดิมจาก %s", RAW_FILE.name)
        results, translations = previous["results"], previous["translations"]
        warm_cache = None    # แก้ prompt ของ judge อยู่ จึงต้องตัดสินใหม่หมด
    else:
        log.info("ขั้นที่ 1/3 — ค้นด้วย %d กลยุทธ์ × %d คำค้น", len(STRATEGIES), len(QUERY_PAIRS))
        results, translations = retrieve_all(k)
        warm_cache = previous.get("verdicts")

    log.info("ขั้นที่ 2/3 — ตัดสินประเภทสินค้าด้วย LLM judge")
    verdicts = judge_all(results, k, warm_cache=warm_cache)

    log.info("ขั้นที่ 3/3 — สรุปผล")
    summary = summarise(results, verdicts, k)
    write_report(summary, results, translations, verdicts, k)
    RESULTS_DIR.joinpath("judge_verdicts_for_audit.md").write_text(
        _audit_dump(verdicts), encoding="utf-8")

    log.info("=" * 62)
    for strategy in STRATEGIES:
        log.info("%-10s precision@%d = %.1f%%  | overlap กับเพดานบน = %.1f%%",
                 strategy, k, summary[strategy]["precision_at_k"] * 100,
                 summary[strategy]["overlap_with_oracle"] * 100)


if __name__ == "__main__":
    main()
