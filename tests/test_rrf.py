"""unit test ของ Reciprocal Rank Fusion และการทำความสะอาดคำแปล"""

import pytest

from mark5.retrieval.query_translator import QueryTranslator
from mark5.retrieval.rrf import fuse

# --------------------------------------------------------------------------- RRF


def test_single_ranking_preserves_order():
    assert [doc for doc, _ in fuse([["a", "b", "c"]])] == ["a", "b", "c"]


def test_document_in_both_rankings_beats_document_in_one():
    """หัวใจของ RRF: ของที่ทั้งสองรายการเห็นตรงกันควรขึ้นมาก่อน"""
    ranked = [doc for doc, _ in fuse([["a", "b"], ["b", "c"]])]
    assert ranked[0] == "b"


def test_score_matches_formula():
    """อันดับ 1 ของทั้งสองรายการ = 2 × 1/(60+1)"""
    scores = dict(fuse([["x"], ["x"]], k=60))
    assert scores["x"] == pytest.approx(2 / 61)


def test_k_controls_how_much_top_ranks_dominate():
    """k เล็กทำให้อันดับต้น ๆ ได้เปรียบมากขึ้น (ระยะห่างของคะแนนถ่างออก)"""
    gap_small_k = dict(fuse([["a", "b"]], k=1))
    gap_large_k = dict(fuse([["a", "b"]], k=1000))
    assert gap_small_k["a"] - gap_small_k["b"] > gap_large_k["a"] - gap_large_k["b"]


def test_weights_shift_the_winner():
    """ถ่วงน้ำหนักรายการที่สองให้มากพอ ต้องพลิกผลได้"""
    equal = [doc for doc, _ in fuse([["a", "b"], ["b", "a"]])]
    weighted = [doc for doc, _ in fuse([["a", "b"], ["b", "a"]], weights=[1.0, 5.0])]
    assert equal[0] == "a"       # เสมอกัน -> ตัดสินด้วย id เพื่อให้ผลคงที่
    assert weighted[0] == "b"


def test_tie_breaks_deterministically_by_id():
    """คะแนนเท่ากันต้องได้ลำดับเดิมทุกครั้ง ไม่งั้น eval ทำซ้ำไม่ได้"""
    for _ in range(5):
        assert [doc for doc, _ in fuse([["z", "a"], ["a", "z"]])] == ["a", "z"]


def test_rejects_mismatched_weights():
    with pytest.raises(ValueError):
        fuse([["a"], ["b"]], weights=[1.0])


def test_empty_input():
    assert fuse([]) == []
    assert fuse([[]]) == []


# --------------------------------------------------------------------------- คำแปล


@pytest.mark.parametrize("raw,expected", [
    ("yoga mat", "yoga mat"),
    ("อังกฤษ: yoga mat", "yoga mat"),
    ("English: yoga mat", "yoga mat"),
    ('"yoga mat"', "yoga mat"),
    ("yoga mat\nอธิบายเพิ่มเติม...", "yoga mat"),
    ("   ", ""),
])
def test_translation_cleanup(raw, expected):
    """โมเดลชอบแถมคำนำหน้า เครื่องหมายคำพูด และคำอธิบายบรรทัดถัดไป — ต้องตัดออกให้หมด"""
    assert QueryTranslator._clean(raw) == expected
