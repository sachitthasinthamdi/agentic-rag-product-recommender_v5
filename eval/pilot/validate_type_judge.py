"""ตรวจสอบความน่าเชื่อถือของ LLM judge เทียบ label จากคนจริง (Amazon ESCI)

ผลลัพธ์คือค่า Cohen's κ ที่ **ต้องอ้างคู่กับตัวเลข product-type precision ทุกครั้ง**
ถ้า κ ต่ำ แปลว่าตัวเลข precision ที่วัดด้วย judge ตัวนี้เชื่อถือไม่ได้ ไม่ว่าจะดูสวยแค่ไหน

เทียบได้กับ mark4 ที่ใช้ ESCI ตรวจ judge แบบให้คะแนน relevance แล้วได้ κ = 0.267 (fair)
งานนี้ถามคำถามที่แคบกว่า (binary "ประเภทเดียวกันไหม") จึงควรได้สูงกว่า — แต่ต้องวัด ไม่ใช่เดา

รัน:  python -m eval.pilot.validate_type_judge [--limit N]
"""

from __future__ import annotations

import argparse
import json
import time

from config import settings
from mark5.common.logger import get_logger

from .agreement import confusion, interpret, summarise
from .build_esci_gold import GOLD_FILE
from .type_judge import ProductTypeJudge, TwoStepProductTypeJudge

log = get_logger(__name__)

REPORT_FILE = settings.ROOT / "eval" / "results" / "type_judge_validation.md"
RAW_FILE = settings.ROOT / "eval" / "results" / "type_judge_validation.json"


def load_split(split: str) -> list[dict]:
    """แบ่ง gold เป็น dev/test แบบตายตัว — **ปรับ prompt ด้วย dev เท่านั้น**

    ถ้าปรับ prompt โดยดูผลบนชุดเดียวกับที่ใช้รายงาน ค่า kappa จะสวยเกินจริง
    เพราะเท่ากับปรับให้เข้ากับคำตอบที่รู้อยู่แล้ว (train on test set)
    ชุด gold ถูกสับไพ่ด้วย seed คงที่ตอนสร้าง การแบ่งตามเลขคู่/คี่จึงกระจาย label สมดุลเอง
    """
    if not GOLD_FILE.exists():
        raise SystemExit(f"ไม่พบ {GOLD_FILE} — รัน `python -m eval.pilot.build_esci_gold` ก่อน")
    gold = json.loads(GOLD_FILE.read_text(encoding="utf-8"))
    if split == "all":
        return gold
    keep = 0 if split == "dev" else 1
    return [row for i, row in enumerate(gold) if i % 2 == keep]


def run(limit: int | None = None, split: str = "test", two_step: bool = False) -> dict:
    gold = load_split(split)
    if limit:
        gold = gold[:limit]
    log.info("ชุด gold '%s' %d คู่ | judge = %s", split, len(gold),
             "สองคำถาม" if two_step else "คำถามเดียว")

    judged = []
    started = time.perf_counter()
    judge_class = TwoStepProductTypeJudge if two_step else ProductTypeJudge
    with judge_class() as judge:
        for i, item in enumerate(gold, 1):
            verdict, reason = judge.judge(item["query"], item["product_title"])
            judged.append({**item, "judge_same_type": verdict, "judge_reason": reason})
            if i % 25 == 0:
                elapsed = time.perf_counter() - started
                log.info("ตัดสินไป %d/%d | เหลือประมาณ %.0f นาที",
                         i, len(gold), (len(gold) - i) * elapsed / i / 60)

    # เอาเฉพาะคู่ที่ gold ไม่กำกวม (ตัด Substitute) และ judge ตอบในรูปแบบที่อ่านได้
    usable = [x for x in judged if x["gold_same_type"] is not None
              and x["judge_same_type"] is not None]
    unparsed = sum(1 for x in judged if x["judge_same_type"] is None)
    ambiguous = [x for x in judged if x["gold_same_type"] is None]

    stats = summarise([x["gold_same_type"] for x in usable],
                      [x["judge_same_type"] for x in usable])
    stats["n_unparsed"] = unparsed
    stats["n_ambiguous_excluded"] = len(ambiguous)

    # judge ตอบว่าอย่างไรกับกลุ่มกำกวม (Substitute) — รายงานแยก ไม่เอามาคิด kappa
    if ambiguous:
        answered = [x for x in ambiguous if x["judge_same_type"] is not None]
        stats["substitute_yes_rate"] = (
            sum(1 for x in answered if x["judge_same_type"]) / len(answered) if answered else 0.0
        )

    # แยกดูทีละ label เพื่อรู้ว่าพลาดกับ label ไหนเป็นหลัก
    per_label = {}
    for label in ("Exact", "Complement", "Irrelevant"):
        rows = [x for x in usable if x["esci_label"] == label]
        if rows:
            correct = sum(1 for x in rows if x["judge_same_type"] == x["gold_same_type"])
            per_label[label] = {"n": len(rows), "accuracy": correct / len(rows)}
    stats["per_label"] = per_label

    return {"stats": stats, "judged": judged, "usable": usable}


def write_report(result: dict) -> None:
    s, judged = result["stats"], result["judged"]
    table = confusion([x["gold_same_type"] for x in result["usable"]],
                      [x["judge_same_type"] for x in result["usable"]])

    lines = [
        "# ตรวจสอบความน่าเชื่อถือของ LLM judge (ประเภทสินค้า)",
        "",
        "เทียบคำตัดสินของ Typhoon2-8B กับ **label จากคนจริง** ใน Amazon Shopping Queries "
        "Dataset (ESCI, Reddy et al. 2022, arXiv:2206.06588)",
        "",
        f"**ชุดที่ใช้: `{s.get('split', '?')}`** — ปรับ prompt ด้วย `dev` เท่านั้น "
        "ตัวเลขที่รายงานเป็นทางการต้องมาจาก `test` ที่ไม่เคยใช้ปรับ",
        "",
        "การแมป label: `Exact` → ประเภทเดียวกัน | `Complement` และ `Irrelevant` → คนละประเภท | "
        "`Substitute` → **ตัดออก** เพราะกำกวมสำหรับคำถามนี้",
        "",
        "## ผลรวม", "",
        "| ตัวชี้วัด | ค่า |", "|---|---|",
        f"| จำนวนคู่ที่ใช้คิด | {s['n']} |",
        f"| **Cohen's κ** | **{s['kappa']:.3f}** ({s['kappa_label']}) |",
        f"| Accuracy | {s['accuracy']:.1%} |",
        f"| Precision (judge ว่าใช่ แล้วใช่จริง) | {s['precision']:.1%} |",
        f"| Recall (ของที่ใช่จริง judge จับได้) | {s['recall']:.1%} |",
        f"| สัดส่วน \"ใช่\" ใน gold | {s['gold_yes_rate']:.1%} |",
        f"| สัดส่วน \"ใช่\" ที่ judge ตอบ | {s['pred_yes_rate']:.1%} |",
        f"| คู่ที่ parse คำตอบไม่ได้ | {s['n_unparsed']} |",
        f"| คู่ที่ตัดออกเพราะกำกวม (Substitute) | {s['n_ambiguous_excluded']} |",
        "",
        "> **เกณฑ์ตีความ κ** ใช้ของ Landis & Koch (1977) — รายงาน accuracy เดี่ยว ๆ ไม่พอ",
        "> เพราะถ้า label เอียงไปทางเดียว ผู้ตัดสินที่ตอบเหมือนกันทุกครั้งก็ได้ accuracy สูงได้",
        "",
        "## ตารางความสับสน", "",
        "| gold \\ judge | ว่าใช่ | ว่าไม่ใช่ |", "|---|---|---|",
        f"| **ใช่** | {table.get((True, True), 0)} | {table.get((True, False), 0)} |",
        f"| **ไม่ใช่** | {table.get((False, True), 0)} | {table.get((False, False), 0)} |",
        "",
        "## ความถูกต้องแยกตาม label ของ ESCI", "",
        "| label | จำนวน | ถูก |", "|---|---|---|",
    ]
    for label, info in s["per_label"].items():
        lines.append(f"| {label} | {info['n']} | {info['accuracy']:.1%} |")

    if "substitute_yes_rate" in s:
        lines += ["", f"กลุ่มกำกวม `Substitute`: judge ตอบว่าเป็นประเภทเดียวกัน "
                      f"{s['substitute_yes_rate']:.1%} (ไม่นำมาคิด κ)"]

    # ตัวอย่างที่ไม่ตรงกัน — ส่วนที่ใช้ปรับ prompt ได้จริง
    wrong = [x for x in result["usable"] if x["judge_same_type"] != x["gold_same_type"]]
    lines += ["", f"## ตัวอย่างที่ judge ไม่ตรงกับคน ({len(wrong)} คู่)", ""]
    for x in wrong[:25]:
        direction = "คนว่าใช่ judge ว่าไม่ใช่" if x["gold_same_type"] else "คนว่าไม่ใช่ judge ว่าใช่"
        lines += [f"- **{direction}** · ESCI={x['esci_label']}",
                  f"  - ถามหา: {x['query']}",
                  f"  - ได้: {x['product_title'][:110]}",
                  f"  - เหตุผลของ judge: _{x['judge_reason'][:130]}_"]

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    RAW_FILE.write_text(json.dumps({"stats": s, "judged": judged},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("เขียนรายงาน %s", REPORT_FILE.relative_to(settings.ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="วัด Cohen's kappa ของ LLM judge เทียบ ESCI")
    parser.add_argument("--limit", type=int, help="จำกัดจำนวนคู่ (สำหรับทดสอบเร็ว)")
    parser.add_argument("--split", choices=["dev", "test", "all"], default="test",
                        help="dev = ใช้ตอนปรับ prompt, test = ตัวเลขที่รายงานจริง")
    parser.add_argument("--two-step", action="store_true",
                        help="ใช้ judge แบบแยกสองคำถามแล้วรวมผลด้วยโค้ด")
    args = parser.parse_args()
    result = run(args.limit, args.split, args.two_step)
    result["stats"]["split"] = args.split
    result["stats"]["judge"] = "two_step" if args.two_step else "single"
    write_report(result)

    s = result["stats"]
    log.info("=" * 60)
    log.info("Cohen's kappa = %.3f (%s) | accuracy = %.1f%% | n = %d",
             s["kappa"], interpret(s["kappa"]), s["accuracy"] * 100, s["n"])


if __name__ == "__main__":
    main()
