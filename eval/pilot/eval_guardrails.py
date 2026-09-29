"""ประเมินชั้น guardrails โดย **ไม่ใช้ LLM judge เลย**

เหตุผลที่ต้องเลี่ยง judge: ตรวจสอบแล้วว่าเชื่อถือไม่ได้ (κ = 0.246 ดู `docs/02_judge_reliability.md`)
และ guardrail กับ judge จะใช้เกณฑ์เดียวกัน ถ้าวัดด้วยกันเองจะได้ผลลวง (circular)

**สิ่งที่วัดได้โดยไม่ต้องมีใครตัดสิน:**
  1. **Correct rejection** — คำค้นนอกขอบเขต (ตั๋วเครื่องบิน, ประกันรถยนต์, บริการต่าง ๆ)
     ถูกปฏิเสธไหม · ground truth ชัด 100% เพราะเป็นไปไม่ได้ที่จะมีในแคตตาล็อกสินค้า
  2. **False rejection** — คำค้นจริง 25 คำถูกปฏิเสธผิดไหม (ควรเป็น 0)
  3. **อัตราการตัดทิ้ง** — ตัวกรองหมวดตัดของไปกี่ชิ้น เหลือพอเสนอไหม

**การแบ่งชุด:** ตั้งเกณฑ์ (calibrate) ด้วยครึ่งหนึ่ง แล้วรายงานผลจากอีกครึ่งที่ไม่เคยใช้ตั้งเกณฑ์
ถ้าตั้งเกณฑ์แล้วรายงานบนชุดเดียวกัน ตัวเลขจะสวยเกินจริงโดยอัตโนมัติ

รัน:  python -m eval.pilot.eval_guardrails
"""

from __future__ import annotations

import argparse
import json

from config import settings
from mark5 import guardrails
from mark5.common.logger import get_logger
from mark5.guardrails import category_guard
from mark5.retrieval.retriever import Retriever

from .queries_out_of_domain import OUT_OF_DOMAIN_QUERIES
from .queries_th_en import QUERY_PAIRS

log = get_logger(__name__)

POOL = 30
SHOW = 5
REPORT_FILE = settings.ROOT / "eval" / "results" / "guardrails_eval.md"
RAW_FILE = settings.ROOT / "eval" / "results" / "guardrails_eval.json"

# ช่วงที่กวาดหาเกณฑ์ — ครอบช่วงที่สองกลุ่มซ้อนกัน (คำค้นจริงต่ำสุด 0.529, นอกขอบเขตสูงสุด 0.580)
TOP1_GRID = [0.50, 0.52, 0.54, 0.55, 0.56, 0.58, 0.60]
MEAN5_GRID = [0.48, 0.50, 0.51, 0.52, 0.53, 0.54, 0.56]


def collect_scores() -> dict:
    """ค้นทุกคำค้นครั้งเดียว เก็บคะแนนกับหมวดไว้ เพื่อกวาดหาเกณฑ์ได้โดยไม่ต้องค้นซ้ำ"""
    data: dict[str, list] = {"in_domain": [], "out_of_domain": []}
    with Retriever() as retriever:
        for group, queries in (("in_domain", QUERY_PAIRS),
                               ("out_of_domain", OUT_OF_DOMAIN_QUERIES)):
            for q in queries:
                hits = retriever.search(q["th"], n=POOL, strategy="translate")
                data[group].append({
                    "id": q["id"], "th": q["th"],
                    "scores": [round(h.score, 5) for h in hits],
                    "categories": [h.category for h in hits],
                    "titles": [h.title[:80] for h in hits[:SHOW]],
                })
                log.info("[%s] %s top1=%.3f", group, q["th"][:30], hits[0].score)
    return data


class _Hit:
    """ตัวแทนผลการค้นตอนเล่นย้อนหลังจากคะแนนที่เก็บไว้"""
    __slots__ = ("score", "category", "title")

    def __init__(self, score, category, title=""):
        self.score, self.category, self.title = score, category, title


def _replay(entry: dict) -> list[_Hit]:
    titles = entry["titles"] + [""] * (len(entry["scores"]) - len(entry["titles"]))
    return [_Hit(s, c, t) for s, c, t in
            zip(entry["scores"], entry["categories"], titles, strict=True)]


def split(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    """แบ่งครึ่งแบบตายตัวตามลำดับคู่/คี่ — ครึ่งแรกใช้ตั้งเกณฑ์ ครึ่งหลังใช้รายงาน"""
    return entries[::2], entries[1::2]


def measure(in_domain: list[dict], out_domain: list[dict],
            min_top1: float, min_mean5: float) -> dict:
    false_reject, correct_reject = 0, 0
    kept_counts, dropped_counts = [], []

    for entry in in_domain:
        result = guardrails.apply(_replay(entry), n=SHOW,
                                  min_top1=min_top1, min_mean5=min_mean5)
        if result.rejected:
            false_reject += 1
        else:
            kept_counts.append(len(result.hits))
            dropped_counts.append(result.n_dropped)

    for entry in out_domain:
        if guardrails.apply(_replay(entry), n=SHOW,
                            min_top1=min_top1, min_mean5=min_mean5).rejected:
            correct_reject += 1

    return {
        "min_top1": min_top1, "min_mean5": min_mean5,
        "n_in_domain": len(in_domain), "n_out_domain": len(out_domain),
        "false_rejection": false_reject,
        "false_rejection_rate": false_reject / len(in_domain) if in_domain else 0.0,
        "correct_rejection": correct_reject,
        "correct_rejection_rate": correct_reject / len(out_domain) if out_domain else 0.0,
        "mean_kept": sum(kept_counts) / len(kept_counts) if kept_counts else 0.0,
        "mean_dropped": sum(dropped_counts) / len(dropped_counts) if dropped_counts else 0.0,
    }


def calibrate(in_domain: list[dict], out_domain: list[dict]) -> dict:
    """เลือกเกณฑ์ที่ปฏิเสธคำค้นนอกขอบเขตได้มากที่สุด **โดยไม่ปฏิเสธคำค้นจริงเลย**

    ลำดับความสำคัญนี้มาจาก `01_objectives.md`: การปฏิเสธคำค้นที่มีของจริง
    ทำให้ระบบใช้งานไม่ได้ ส่วนการเสนอของที่ไม่ค่อยตรงยังมีชั้นอื่นช่วยกรองต่อได้
    """
    results = [measure(in_domain, out_domain, t, m) for t in TOP1_GRID for m in MEAN5_GRID]
    safe = [r for r in results if r["false_rejection"] == 0]
    pool = safe or results          # ถ้าไม่มีเกณฑ์ไหนปลอดภัยเลย ค่อยยอมแลก
    best = max(pool, key=lambda r: (r["correct_rejection"], -r["false_rejection"]))
    log.info("เกณฑ์ที่เลือก: top1 >= %.2f, mean5 >= %.2f (จาก %d ชุดที่กวาด, ปลอดภัย %d ชุด)",
             best["min_top1"], best["min_mean5"], len(results), len(safe))
    return best


def category_stats(entries: list[dict]) -> dict:
    """ตัวกรองหมวดทำงานบ่อยแค่ไหน และตัดของไปเท่าไหร่"""
    applied = dropped_total = shown_total = 0
    for entry in entries:
        hits = _replay(entry)
        decision = category_guard.apply(hits[:SHOW], pool=hits)
        applied += int(decision.applied)
        dropped_total += len(decision.dropped)
        shown_total += SHOW
    return {"n_queries": len(entries), "filter_applied": applied,
            "dropped": dropped_total, "drop_rate": dropped_total / shown_total}


def main() -> None:
    parser = argparse.ArgumentParser(description="ประเมิน guardrails แบบไม่ใช้ LLM judge")
    parser.add_argument("--reuse", action="store_true", help="ใช้คะแนนที่เก็บไว้ ไม่ค้นใหม่")
    args = parser.parse_args()

    if args.reuse and RAW_FILE.exists():
        data = json.loads(RAW_FILE.read_text(encoding="utf-8"))["scores"]
        log.info("ใช้คะแนนเดิมจาก %s", RAW_FILE.name)
    else:
        data = collect_scores()

    cal_in, hold_in = split(data["in_domain"])
    cal_out, hold_out = split(data["out_of_domain"])
    log.info("ตั้งเกณฑ์ด้วย %d+%d คำค้น | รายงานจาก %d+%d คำค้นที่ไม่เคยใช้ตั้งเกณฑ์",
             len(cal_in), len(cal_out), len(hold_in), len(hold_out))

    chosen = calibrate(cal_in, cal_out)
    holdout = measure(hold_in, hold_out, chosen["min_top1"], chosen["min_mean5"])
    baseline = measure(hold_in, hold_out, 0.0, 0.0)   # ไม่มี guardrail = ไม่เคยปฏิเสธเลย

    report = {
        "chosen_thresholds": {"min_top1": chosen["min_top1"], "min_mean5": chosen["min_mean5"]},
        "calibration": chosen, "holdout": holdout, "baseline_no_guard": baseline,
        "category_in_domain": category_stats(data["in_domain"]),
    }
    write_report(report, data)

    log.info("=" * 64)
    log.info("ชุด holdout — ปฏิเสธคำค้นนอกขอบเขตถูก %d/%d (%.0f%%) | "
             "ปฏิเสธคำค้นจริงผิด %d/%d",
             holdout["correct_rejection"], holdout["n_out_domain"],
             holdout["correct_rejection_rate"] * 100,
             holdout["false_rejection"], holdout["n_in_domain"])


def write_report(report: dict, data: dict) -> None:
    h, b, c = report["holdout"], report["baseline_no_guard"], report["category_in_domain"]
    t = report["chosen_thresholds"]

    lines = [
        "# ประเมินชั้น Guardrails (ไม่ใช้ LLM judge)",
        "",
        "วัดด้วยสิ่งที่มี ground truth แน่นอนเท่านั้น — ไม่พึ่ง LLM judge ที่ตรวจสอบแล้วว่า",
        "เชื่อถือไม่ได้ (κ = 0.246 ดู `docs/02_judge_reliability.md`)",
        "",
        f"**เกณฑ์ที่ตั้งได้จากชุด calibration:** คะแนนอันดับ 1 ≥ {t['min_top1']} "
        f"และคะแนนเฉลี่ย 5 อันดับแรก ≥ {t['min_mean5']}",
        "",
        "## ผลบนชุด holdout (ไม่เคยใช้ตั้งเกณฑ์)", "",
        "| | ไม่มี guardrail | มี guardrail |", "|---|---|---|",
        f"| ปฏิเสธคำค้นนอกขอบเขตได้ถูก | {b['correct_rejection']}/{b['n_out_domain']} "
        f"({b['correct_rejection_rate']:.0%}) | **{h['correct_rejection']}/{h['n_out_domain']} "
        f"({h['correct_rejection_rate']:.0%})** |",
        f"| ปฏิเสธคำค้นจริงผิด (ยิ่งน้อยยิ่งดี) | {b['false_rejection']}/{b['n_in_domain']} | "
        f"**{h['false_rejection']}/{h['n_in_domain']}** |",
        f"| จำนวนสินค้าที่เหลือเสนอโดยเฉลี่ย | {b['mean_kept']:.1f} | {h['mean_kept']:.1f} |",
        "",
        "> mark4 ปฏิเสธคำค้นได้ **0 ครั้งจาก 25** คือเสนอของเสมอ — ตรงกับคอลัมน์ "
        "\"ไม่มี guardrail\"",
        "",
        "## ตัวกรองหมวด (คำค้นจริงทั้ง 25 คำ)", "",
        f"- ตัวกรองทำงานจริง {c['filter_applied']}/{c['n_queries']} คำค้น "
        "(ที่เหลือกลุ่มผู้สมัครเล็กเกินกว่าจะประเมินสัดส่วนได้ จึงไม่กรอง)",
        f"- ตัดสินค้าออก {c['dropped']} ชิ้นจาก {c['n_queries'] * SHOW} ชิ้น "
        f"(**{c['drop_rate']:.1%}**)",
        "",
        "## ข้อจำกัดที่ต้องระบุ", "",
        "1. ชุดทดสอบเล็กมาก — คำค้นจริง 25 คำ นอกขอบเขต 15 คำ แบ่งครึ่งเหลือชุดละไม่ถึง 15",
        "   ตัวเลขจึงหยาบ ห้ามอ้างทศนิยม",
        "2. คำค้นนอกขอบเขตเลือกเป็น **บริการ/ตั๋ว/ของสด** ซึ่งต่างจากสินค้าชัดเจนมาก",
        "   ของจริงที่ยากกว่าคือ \"สินค้าที่คลังไม่มีแต่เป็นสินค้า\" ซึ่งยังไม่ได้ทดสอบ",
        "3. ชั้นนี้**ยังไม่ได้วัดว่าแก้ปัญหาสินค้าผิดประเภทได้แค่ไหน** — ตัวชี้วัดนั้น",
        "   ต้องใช้คนตรวจ (จากการวิเคราะห์ ของที่ผิดประเภท 67% อยู่หมวดเดียวกับของที่ถูก",
        "   ซึ่งตัวกรองหมวดแตะไม่ได้เลย)",
        "",
        "## คำค้นนอกขอบเขตที่ยังหลุดผ่าน (ชุด holdout)", "",
    ]

    hold_out_entries = split(data["out_of_domain"])[1]
    for entry in hold_out_entries:
        result = guardrails.apply(_replay(entry), n=SHOW,
                                  min_top1=t["min_top1"], min_mean5=t["min_mean5"])
        if not result.rejected:
            lines.append(f"- **{entry['th']}** (top1 = {result.top1_score:.3f}) "
                         f"→ เสนอ: {entry['titles'][0][:70]}")
    if all(guardrails.apply(_replay(e), n=SHOW, min_top1=t["min_top1"],
                            min_mean5=t["min_mean5"]).rejected for e in hold_out_entries):
        lines.append("- ไม่มี — ปฏิเสธได้ครบทุกคำค้นในชุด holdout")

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    RAW_FILE.write_text(json.dumps({"report": report, "scores": data},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("เขียนรายงาน %s", REPORT_FILE.relative_to(settings.ROOT))


if __name__ == "__main__":
    main()
