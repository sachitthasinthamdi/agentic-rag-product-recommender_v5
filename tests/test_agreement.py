"""unit test ของการคำนวณ Cohen's kappa (เขียนเองเพราะ sklearn ถูกบล็อกบนเครื่องนี้)"""

import pytest

from eval.pilot.agreement import cohen_kappa, confusion, interpret, summarise


def test_perfect_agreement():
    assert cohen_kappa([True, False, True, False], [True, False, True, False]) == pytest.approx(1.0)


def test_total_disagreement_is_negative():
    """ตรงข้ามกันทุกข้อ แย่กว่าการเดาสุ่ม จึงต้องติดลบ"""
    assert cohen_kappa([True, False, True, False], [False, True, False, True]) < 0


def test_all_same_label_both_sides():
    """ทั้งคู่ตอบเหมือนกันหมดและไม่มีความหลากหลาย — kappa นิยามไม่ได้ตามสูตร ตีความเป็น 1.0"""
    assert cohen_kappa([True] * 5, [True] * 5) == pytest.approx(1.0)


def test_constant_predictor_scores_zero_despite_high_accuracy():
    """หัวใจของ kappa: ผู้ตัดสินที่ตอบ 'ใช่' ทุกครั้งได้ accuracy 90% แต่ไม่มีประโยชน์เลย

    นี่คือเหตุผลที่ต้องรายงาน kappa ไม่ใช่ accuracy อย่างเดียว — mark4 เจอ judge
    ที่ตอบค่าเดิมเกือบทุกครั้งแล้วดูเหมือนแม่น
    """
    gold = [True] * 9 + [False]
    predicted = [True] * 10
    stats = summarise(gold, predicted)
    assert stats["accuracy"] == pytest.approx(0.9)
    assert stats["kappa"] == pytest.approx(0.0)


def test_known_value():
    """ตรวจกับค่าที่คำนวณด้วยมือทีละขั้น"""
    gold = [True, True, True, True, True, False, False, False, False, False]
    pred = [True, True, True, True, False, False, False, False, True, True]
    # ตรงกัน 7/10 (พลาดที่ตำแหน่ง 5, 9, 10) -> Po = 0.7
    # gold ตอบ "ใช่" 50%, pred ตอบ "ใช่" 60% -> Pe = 0.5*0.6 + 0.5*0.4 = 0.5
    # kappa = (0.7 - 0.5) / (1 - 0.5) = 0.4
    assert cohen_kappa(gold, pred) == pytest.approx(0.4)


def test_summarise_counts():
    stats = summarise([True, True, False, False], [True, False, True, False])
    assert (stats["true_positive"], stats["false_negative"]) == (1, 1)
    assert (stats["false_positive"], stats["true_negative"]) == (1, 1)
    assert stats["precision"] == pytest.approx(0.5)
    assert stats["recall"] == pytest.approx(0.5)


def test_confusion_table():
    table = confusion([True, True, False], [True, False, False])
    assert table == {(True, True): 1, (True, False): 1, (False, False): 1}


@pytest.mark.parametrize("kappa,expected", [
    (-0.1, "poor"), (0.1, "slight"), (0.3, "fair"),
    (0.5, "moderate"), (0.7, "substantial"), (0.9, "almost perfect"),
])
def test_landis_koch_bands(kappa, expected):
    assert interpret(kappa).startswith(expected)


def test_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        cohen_kappa([True], [True, False])


def test_rejects_empty():
    with pytest.raises(ValueError):
        cohen_kappa([], [])
