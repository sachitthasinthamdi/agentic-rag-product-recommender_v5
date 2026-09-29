"""unit test ของการแปลงในชั้น clean (src/mark5/data/clean.py)"""

import numpy as np
import pandas as pd

from mark5.data.clean import category_from_filename, parse_details, resolve_category

# --------------------------------------------------------------------------- parse_details


def test_parse_details_reads_python_repr_not_json():
    """ต้นทางเป็น repr ของ dict ใน Python (single quote) ไม่ใช่ JSON — json.loads ใช้ไม่ได้"""
    assert parse_details("{'Brand': 'Acme', 'Color': 'Black'}") == {"Brand": "Acme", "Color": "Black"}


def test_parse_details_tolerates_garbage():
    for bad in ["", "   ", None, 123, "not a dict", "['a', 'b']", "{'unclosed':"]:
        assert parse_details(bad) == {}


# --------------------------------------------------------------------------- category


def test_category_from_filename():
    assert category_from_filename("meta_Digital_Music") == "Digital Music"
    assert category_from_filename("meta_Grocery_and_Gourmet_Food") == "Grocery and Gourmet Food"
    assert category_from_filename("") is None
    assert category_from_filename(None) is None


def _frame(main, cats, filename):
    return pd.DataFrame({"main_category": main, "categories": cats, "filename": filename})


def test_resolve_category_prefers_main_category():
    cat, src = resolve_category(_frame(["Tools"], [["Hardware"]], ["meta_Tools"]))
    assert cat.iloc[0] == "Tools"
    assert src.iloc[0] == "main_category"


def test_resolve_category_falls_back_to_first_subcategory():
    cat, src = resolve_category(_frame([None], [["Hardware", "Drills"]], ["meta_Tools"]))
    assert cat.iloc[0] == "Hardware"
    assert src.iloc[0] == "categories"


def test_resolve_category_last_resort_is_filename():
    """ชั้นสุดท้ายนี้คือเหตุผลที่ category ครบ 100% ซึ่ง guardrail "ตรงประเภท" ต้องพึ่ง"""
    cat, src = resolve_category(_frame([None], [[]], ["meta_Digital_Music"]))
    assert cat.iloc[0] == "Digital Music"
    assert src.iloc[0] == "filename"


def test_resolve_category_treats_blank_as_missing():
    cat, src = resolve_category(_frame(["   "], [[]], ["meta_Tools"]))
    assert cat.iloc[0] == "Tools"
    assert src.iloc[0] == "filename"


def test_resolve_category_handles_numpy_array_categories():
    """categories อ่านจาก parquet มาเป็น numpy array ไม่ใช่ list"""
    cat, src = resolve_category(_frame([None], [np.array(["Hardware"])], ["meta_Tools"]))
    assert cat.iloc[0] == "Hardware"
    assert src.iloc[0] == "categories"
