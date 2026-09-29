"""unit test ของ src/mark5/data/features.py

เน้นทดสอบ **เคสที่เคยพังจริง** ไม่ใช่แค่ happy path — เคสเหล่านี้มาจากบั๊กที่เจอใน mark4
"""

import pytest

from mark5.data.features import (
    details_to_text,
    extract_best_sellers_rank,
    extract_brand,
    extract_color,
    extract_material,
    extract_weight_g,
    popularity,
    value_score,
)

# --------------------------------------------------------------------------- color


def test_color_normalizes_to_vocabulary():
    assert extract_color({"Color": "Black"}) == "black"
    assert extract_color({"Colour": "RED"}) == "red"


def test_color_grey_maps_to_gray():
    assert extract_color({"Color": "Grey"}) == "gray"


def test_color_picks_word_appearing_first_in_text_not_first_in_vocab():
    """บั๊กเดิม: "Space Gray, Rose Gold" คืน "gold" เพราะ gold ประกาศก่อน gray ใน vocab"""
    assert extract_color({"Color": "Space Gray, Rose Gold"}) == "gray"


def test_color_unknown_value_returns_raw_not_truncated_mid_word():
    """ค่ายาวที่ไม่อยู่ใน vocab ต้องไม่ถูกตัดขาดกลางคำ (เดิมตัดที่ 20 ตัวอักษร)"""
    assert extract_color({"Color": "Ethylene Vinyl Acetate"}) == "ethylene vinyl acetate"


def test_color_missing_returns_none():
    assert extract_color({}) is None
    assert extract_color({"Color": ""}) is None
    assert extract_color({"Color": None}) is None


def test_color_is_not_guessed_from_title():
    """ต้องไม่เดาสีจาก field อื่น — เชื่อเฉพาะ details['Color']"""
    assert extract_color({"Title": "Black Running Shoes"}) is None


# --------------------------------------------------------------------------- material


def test_material_normalizes_and_falls_back():
    assert extract_material({"Material": "100% Cotton"}) == "cotton"
    assert extract_material({"Material": "Bamboo Fiber, Recycled"}) == "bamboo fiber"
    assert extract_material({}) is None


# --------------------------------------------------------------------------- weight


def test_weight_unit_conversion():
    assert extract_weight_g({"Item Weight": "2 kg"}) == 2000.0
    assert extract_weight_g({"Item Weight": "500 grams"}) == 500.0
    assert extract_weight_g({"Item Weight": "1 pound"}) == 453.6
    assert extract_weight_g({"Item Weight": "8 ounces"}) == 226.8


def test_weight_handles_thousands_separator():
    """บั๊กเดิม: regex ไม่รับ comma ทำให้ "1,200 grams" จับได้แค่ 200 — ผิด 6 เท่าแบบเงียบ ๆ"""
    assert extract_weight_g({"Item Weight": "1,200 grams"}) == 1200.0


def test_weight_zero_is_invalid():
    """ผู้ขายกรอก "0 ounces" ผิด — น้ำหนัก 0 เป็นไปไม่ได้จริง"""
    assert extract_weight_g({"Item Weight": "0 ounces"}) is None


def test_weight_unparseable_returns_none():
    assert extract_weight_g({"Item Weight": "see description"}) is None
    assert extract_weight_g({}) is None


# --------------------------------------------------------------------------- BSR


def test_bsr_accepts_dict_list_and_string():
    assert extract_best_sellers_rank({"Best Sellers Rank": {"Tools": "1,234", "Drills": "56"}}) == 56
    assert extract_best_sellers_rank({"Best Sellers Rank": ["#900", "#42"]}) == 42
    assert extract_best_sellers_rank({"Best Sellers Rank": "#1,234 in Tools"}) == 1234


def test_bsr_ignores_stray_commas():
    """บั๊กเดิม: r"#?([\\d,]+)" จับ ", " จาก str(list) ได้ แล้ว int("") พัง"""
    assert extract_best_sellers_rank({"Best Sellers Rank": ", , #77 in X"}) == 77


def test_bsr_missing_returns_none():
    assert extract_best_sellers_rank({}) is None
    assert extract_best_sellers_rank({"Best Sellers Rank": "no rank"}) is None


# --------------------------------------------------------------------------- brand


def test_brand_prefers_brand_over_manufacturer():
    assert extract_brand({"Brand": "Acme", "Manufacturer": "Other Co"}) == "acme"
    assert extract_brand({"Manufacturer": "Other Co"}) == "other co"
    assert extract_brand({}) is None


# --------------------------------------------------------------------------- popularity


def test_popularity_pulls_low_review_items_toward_mean():
    """สินค้า 5 ดาวจากรีวิวเดียว ต้องไม่ชนะสินค้า 4.5 ดาวจากรีวิวพันรายการ"""
    fluke = popularity(5.0, 1, mean_rating=4.0, m=50)
    established = popularity(4.5, 1000, mean_rating=4.0, m=50)
    assert fluke < established


def test_popularity_uses_mean_when_rating_missing():
    assert popularity(None, 0, mean_rating=4.2, m=50) == pytest.approx(4.2)


def test_popularity_survives_zero_denominator():
    assert popularity(None, 0, mean_rating=4.2, m=0) == pytest.approx(4.2)


def test_popularity_handles_nan_review_count():
    """NaN เป็น truthy ใน Python — `rating_count or 0` จึงปล่อย NaN ทะลุสูตรไปเงียบ ๆ

    ข้อมูลจริงมี 6 แถวที่ rating_number เป็น NaN และเคยทำให้ popularity ว่างทั้งคอลัมน์
    """
    nan = float("nan")
    assert popularity(4.5, nan, mean_rating=4.0, m=50) == pytest.approx(4.0)
    assert popularity(nan, 100, mean_rating=4.0, m=50) == pytest.approx(4.0)


# --------------------------------------------------------------------------- value_score


def test_value_score_basic_and_guards():
    assert value_score(4.0, 20.0) == pytest.approx(0.2)
    assert value_score(4.0, 0) is None
    assert value_score(4.0, None) is None
    assert value_score(None, 20.0) is None
    assert value_score(float("nan"), 20.0) is None


def test_value_score_keeps_signal_for_very_expensive_items():
    """ปัดที่ 4 ตำแหน่งทำให้สินค้าราคาหลักหมื่นได้ 0.0 เท่ากันหมด เสียสัญญาณจัดอันดับ"""
    cheaper = value_score(1.0, 30_000.0)
    pricier = value_score(1.0, 49_484.0)
    assert cheaper > 0
    assert pricier > 0
    assert cheaper > pricier


# --------------------------------------------------------------------------- details_to_text


def test_details_to_text_skips_useless_and_already_extracted_keys():
    text = details_to_text({
        "ASIN": "B01",                  # useless
        "Color": "Black",               # สกัดเป็นคอลัมน์แยกแล้ว
        "Best Sellers Rank": {"a": 1},  # dict ซ้อน
        "Connectivity": "Bluetooth",    # เก็บ
    })
    assert text == "Connectivity: Bluetooth"


def test_details_to_text_respects_max_pairs():
    many = {f"Key{i}": f"v{i}" for i in range(50)}
    assert len(details_to_text(many, max_pairs=3).split(" | ")) == 3


def test_details_to_text_drops_overly_long_values():
    assert details_to_text({"Note": "x" * 200}) == ""


def test_details_to_text_empty_details():
    assert details_to_text({}) == ""
