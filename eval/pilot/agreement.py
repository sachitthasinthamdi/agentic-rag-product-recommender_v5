"""วัดความสอดคล้องระหว่างผู้ตัดสินสองฝ่าย — Cohen's kappa แบบเขียนเอง

**ทำไมเขียนเอง:** `sklearn.metrics.cohen_kappa_score` ใช้ไม่ได้บนเครื่องนี้
(Windows Application Control บล็อก DLL ของ sklearn/scipy) สูตรไม่ซับซ้อน
และการเขียนเองทำให้ unit test ได้ด้วย

Cohen, J. (1960). *A Coefficient of Agreement for Nominal Scales*
เกณฑ์ตีความใช้ของ Landis, J. R. & Koch, G. G. (1977) *Biometrics* 33(1)
"""

from __future__ import annotations

# Landis & Koch (1977) — เกณฑ์ตีความค่า kappa ที่ใช้อ้างอิงกันทั่วไป
_LANDIS_KOCH = [
    (0.00, "poor (แย่)"),
    (0.20, "slight (เล็กน้อย)"),
    (0.40, "fair (พอใช้)"),
    (0.60, "moderate (ปานกลาง)"),
    (0.80, "substantial (ดี)"),
    (1.01, "almost perfect (เกือบสมบูรณ์)"),
]


def interpret(kappa: float) -> str:
    """แปลค่า kappa เป็นระดับตามเกณฑ์ Landis & Koch (1977)"""
    for upper, label in _LANDIS_KOCH:
        if kappa < upper:
            return label
    return _LANDIS_KOCH[-1][1]


def cohen_kappa(a: list, b: list) -> float:
    """κ = (Po - Pe) / (1 - Pe)

    Po = สัดส่วนที่ตรงกันจริง, Pe = สัดส่วนที่คาดว่าจะตรงกันโดยบังเอิญ
    คืน 1.0 เมื่อทั้งคู่ตัดสินเหมือนกันหมดและไม่มีความหลากหลาย (Pe = 1)
    ซึ่งเป็นกรณีที่ kappa นิยามไม่ได้ตามสูตร แต่ตีความว่าสอดคล้องสมบูรณ์
    """
    if len(a) != len(b):
        raise ValueError(f"จำนวนไม่เท่ากัน: {len(a)} กับ {len(b)}")
    if not a:
        raise ValueError("ไม่มีข้อมูลให้คำนวณ")

    n = len(a)
    labels = sorted(set(a) | set(b), key=str)

    observed = sum(1 for x, y in zip(a, b, strict=True) if x == y) / n
    expected = sum((a.count(label) / n) * (b.count(label) / n) for label in labels)

    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return (observed - expected) / (1 - expected)


def confusion(a: list, b: list) -> dict[tuple, int]:
    """ตารางความสับสน {(ค่าของ a, ค่าของ b): จำนวน} — ดูว่าพลาดไปทางไหน"""
    table: dict[tuple, int] = {}
    for x, y in zip(a, b, strict=True):
        table[(x, y)] = table.get((x, y), 0) + 1
    return table


def summarise(gold: list, predicted: list) -> dict:
    """สรุปความสอดคล้องพร้อมตัวเลขที่ต้องรายงานคู่กันเสมอ

    รายงาน accuracy เดี่ยว ๆ ไม่พอ เพราะถ้า label เอียงไปทางเดียว (เช่น YES 80%)
    ผู้ตัดสินที่ตอบ YES ทุกครั้งก็ได้ accuracy 80% ทั้งที่ไม่มีประโยชน์เลย
    — kappa หักส่วนที่ตรงกันโดยบังเอิญออกไปแล้ว
    """
    n = len(gold)
    kappa = cohen_kappa(gold, predicted)
    tp = sum(1 for g, p in zip(gold, predicted, strict=True) if g and p)
    tn = sum(1 for g, p in zip(gold, predicted, strict=True) if not g and not p)
    fp = sum(1 for g, p in zip(gold, predicted, strict=True) if not g and p)
    fn = sum(1 for g, p in zip(gold, predicted, strict=True) if g and not p)
    return {
        "n": n,
        "kappa": kappa,
        "kappa_label": interpret(kappa),
        "accuracy": (tp + tn) / n,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "true_positive": tp, "true_negative": tn,
        "false_positive": fp, "false_negative": fn,
        "gold_yes_rate": sum(1 for g in gold if g) / n,
        "pred_yes_rate": sum(1 for p in predicted if p) / n,
    }
