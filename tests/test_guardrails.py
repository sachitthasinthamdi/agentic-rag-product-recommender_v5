"""unit test ของชั้น guardrails (ตรรกะล้วน ไม่แตะ Chroma/Ollama)"""

from dataclasses import dataclass

import pytest

from mark5 import guardrails
from mark5.guardrails import category_guard, score_guard


@dataclass
class Hit:
    """ตัวแทนผลการค้นแบบย่อ — guardrails ใช้แค่ score กับ category"""
    id: str
    score: float
    category: str


def hits(*specs) -> list[Hit]:
    return [Hit(f"p{i}", score, category) for i, (score, category) in enumerate(specs)]


# --------------------------------------------------------------------------- score guard


def test_accepts_clearly_good_results():
    decision = score_guard.evaluate([0.72, 0.71, 0.70, 0.69, 0.68])
    assert not decision.rejected


def test_rejects_when_best_match_is_weak():
    """คำค้นนอกขอบเขตวัดได้สูงสุด 0.580 ส่วนคำค้นจริงต่ำสุด 0.529"""
    assert score_guard.evaluate([0.49, 0.48, 0.47, 0.47, 0.46]).rejected


def test_rejects_when_only_one_lucky_match():
    """อันดับ 1 ผ่าน แต่ที่เหลือไม่เกี่ยว — ไม่ควรเสนอ"""
    decision = score_guard.evaluate([0.60, 0.40, 0.39, 0.38, 0.37])
    assert decision.rejected
    assert "เฉลี่ย" in decision.reason


def test_rejects_empty_results():
    assert score_guard.evaluate([]).rejected


def test_threshold_is_adjustable():
    scores = [0.56] * 5
    assert not score_guard.evaluate(scores, min_top1=0.55, min_mean5=0.52).rejected
    assert score_guard.evaluate(scores, min_top1=0.60, min_mean5=0.52).rejected


# --------------------------------------------------------------------------- category guard


def test_consensus_ignores_unknown_category():
    """`Unknown` ไม่ใช่หมวดจริง ถ้านับโหวตจะไปเบียดหมวดที่ถูกต้อง"""
    category, share = category_guard.consensus(["Tools", "Tools", "Unknown", "Unknown"])
    assert category == "Tools"
    assert share == pytest.approx(1.0)


def test_consensus_none_when_all_unknown():
    assert category_guard.consensus(["Unknown", "Unknown"]) == (None, 0.0)


def test_drops_rare_outlier_category():
    pool = hits(*[(0.7, "Tools")] * 28) + hits((0.6, "AMAZON FASHION"))
    result = category_guard.apply(pool, pool=pool)
    assert result.applied
    assert [h.category for h in result.dropped] == ["AMAZON FASHION"]


def test_keeps_sibling_categories_that_are_well_represented():
    """บทเรียนจาก q01: `Electronics` กับ `All Electronics` คือหมวดพี่น้อง

    การบังคับ "หมวดเดียว" เคยทำให้คำค้นที่คะแนน 0.731 ถูกตัดทิ้งทั้งหมด
    """
    pool = (hits(*[(0.7, "All Electronics")] * 15)
            + hits(*[(0.7, "Electronics")] * 9)
            + hits(*[(0.7, "Cell Phones & Accessories")] * 6))
    shown = hits((0.7, "Electronics"), (0.7, "Cell Phones & Accessories"))
    result = category_guard.apply(shown, pool=pool)
    assert result.dropped == []
    assert len(result.kept) == 2


def test_keeps_unknown_category_items():
    """"ไม่รู้หมวด" ไม่เท่ากับ "หมวดผิด" — ไม่ลงโทษข้อมูลที่ขาด (541 แถวในคลังเป็นแบบนี้)"""
    pool = hits(*[(0.7, "Tools")] * 12) + hits((0.7, "Unknown"))
    result = category_guard.apply(pool, pool=pool)
    assert any(h.category == "Unknown" for h in result.kept)


def test_does_not_filter_when_pool_is_too_small():
    """กลุ่มผู้สมัครเล็กเกินไป สัดส่วนผันผวนจนเชื่อไม่ได้ -> ไม่กรอง"""
    pool = hits((0.7, "A"), (0.7, "B"), (0.7, "C"))
    result = category_guard.apply(pool, pool=pool)
    assert not result.applied
    assert len(result.kept) == len(pool)


def test_wide_pool_decides_shares_not_the_displayed_slice():
    """สัดส่วนต้องมาจากกลุ่มผู้สมัครที่กว้าง ไม่ใช่แค่ 2 ชิ้นที่จะแสดง"""
    shown = hits((0.7, "AMAZON FASHION"), (0.69, "Tools"))
    pool = shown + hits(*[(0.6, "Tools")] * 28)
    result = category_guard.apply(shown, pool=pool)
    assert result.consensus_category == "Tools"
    assert [h.category for h in result.kept] == ["Tools"]


# --------------------------------------------------------------------------- รวมทั้งชั้น


def test_rejection_short_circuits_category_filtering():
    pool = hits(*[(0.40, "Tools")] * 10)
    result = guardrails.apply(pool, n=5)
    assert result.rejected and result.hits == []
    assert not result.category_filter_applied


def test_normal_path_keeps_consensus_items():
    pool = hits(*[(0.70, "Tools")] * 8) + hits((0.69, "Pet Supplies"))
    result = guardrails.apply(pool, n=5)
    assert not result.rejected
    assert len(result.hits) == 5
    assert result.consensus_category == "Tools"


def test_falls_back_instead_of_rejecting_when_filter_empties_the_list():
    """ตัวกรองหมวดห้ามปฏิเสธทั้งคำค้น — การปฏิเสธเป็นหน้าที่ของคะแนนเท่านั้น

    บทเรียนจริง: q01 "หูฟังบลูทูธ" คะแนน 0.731 เคยถูกปฏิเสธทั้งคำค้น
    เพราะหมวดพี่น้องที่ชื่อต่างกัน (Electronics vs All Electronics)
    """
    shown = hits(*[(0.70, "AMAZON FASHION")] * 3)
    pool = shown + hits(*[(0.68, "Tools")] * 40)
    result = guardrails.apply(pool, n=3)
    assert not result.rejected
    assert len(result.hits) == 3
    assert not result.category_filter_applied


def test_result_records_its_own_evidence():
    """ต้องตรวจย้อนหลังได้ว่าทำไมถึงตัดสินแบบนั้น"""
    pool = hits(*[(0.70, "Tools")] * 10)
    result = guardrails.apply(pool, n=5)
    assert result.top1_score == pytest.approx(0.70)
    assert result.mean_top5_score == pytest.approx(0.70)
    assert result.consensus_share == pytest.approx(1.0)
    assert result.reason
