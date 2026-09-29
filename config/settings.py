"""ค่าตั้งของ mark5 — รวมทุกค่าคงที่ไว้ที่เดียว

หลักการ: ค่าที่ยังไม่ได้ตัดสินใน ADR จะ **ไม่ใส่ไว้ที่นี่** เพื่อกันการล็อกค่าโดยไม่ตั้งใจ
ดู `docs/roadmap.md` ว่าค่าไหนรอด่านไหน
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# ---- ด่าน 4: ชั้นข้อมูล (Medallion) ----
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
FEATURE_DIR = DATA_DIR / "feature"
EMBED_DIR = DATA_DIR / "embed"

# ใช้ Feather (= Arrow IPC file) ไม่ใช่ Parquet — Application Control บล็อก DLL `pyarrow._fs`
# ที่ `pyarrow.parquet` ต้องใช้ ดูเหตุผลเต็มใน src/mark5/common/tables.py (ADR ในหัวไฟล์)
RAW_FILE = RAW_DIR / "products_raw.feather"
CLEAN_FILE = CLEAN_DIR / "products_clean.feather"
FEATURE_FILE = FEATURE_DIR / "products_feature.feather"

SOURCE_DATASET = "milistu/AMAZON-Products-2023"

LOG_DIR = ROOT / "logs"

# ---- ด่าน 5: LLM (local ผ่าน Ollama) ----
# ⚠ ต้องสตาร์ต server เองทุกเซสชัน: ollama.exe serve
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
# ชื่อโมเดลตามที่ติดตั้งจริงบนเครื่องนี้ (ตรวจด้วย `ollama list` เมื่อ 2026-09-28)
OLLAMA_CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "scb10x/llama3.1-typhoon2-8b-instruct")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "bge-m3")

# ---- ด่าน 4: Vector store ----
# **Chroma local เท่านั้น** (ตัดสิน 2026-09-28 ดู ADR-0004) — ไม่ใช้ Chroma Cloud
# จึงไม่มี API key, ไม่มีค่าใช้จ่าย, ไม่ติดเพดาน 300 record/request ของฝั่ง cloud
CHROMA_DIR = EMBED_DIR / "chroma"
COLLECTION_NAME = "products"
CHROMA_MAX_BATCH = 5_000   # จำกัดเองเพื่อคุมการใช้หน่วยความจำตอน add ไม่ใช่ข้อจำกัดของ Chroma

# ---- ด่าน 13: Observability ----
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY")

# ---- ด่าน 4: Feature engineering (Phase 1) ----
MIN_DESC_LEN = 20                # ความยาวคำอธิบายขั้นต่ำที่ถือว่า embed ตรง ๆ ได้
POPULARITY_M_QUANTILE = 0.75     # เกณฑ์จำนวนรีวิว m ของสูตร Bayesian popularity
PRICE_TIER_LABELS = ["cheap", "mid", "premium"]
DETAILS_MAX_PAIRS = 12           # จำนวนคู่ key-value สูงสุดที่ยัดเข้า embed_text
DETAILS_MAX_VALUE_LEN = 60       # ค่ายาวเกินนี้ถือเป็นขยะ ไม่ใช่ attribute จริง
EMBED_MAX_CHARS = 2000           # ตัดความยาว embed_text (กันเอกสารยาวผิดปกติถ่วง encode)
EMBED_FEATURES_MAX = 8           # จำนวน bullet ใน `features` ที่ใส่ใน embed_text

# controlled vocabulary — normalize ค่าที่สกัดได้ ไม่เดาจากข้อความอิสระ
COLORS = ["black", "white", "red", "blue", "green", "pink", "purple", "gold",
          "silver", "gray", "grey", "yellow", "orange", "brown", "beige", "navy", "teal"]
MATERIALS = ["cotton", "leather", "plastic", "metal", "wood", "silicone", "stainless",
             "aluminum", "glass", "rubber", "ceramic", "polyester", "nylon", "wool"]

# key ใน details ที่ไม่มีความหมายเชิงค้นหา (ID/วันที่/ไม่มีความหลากหลาย) — ตัดทิ้ง
# "Is Discontinued By Manufacturer" 98% เป็นค่า "no" เหมือนกันหมด แยกแยะสินค้าไม่ได้
USELESS_DETAIL_KEYS = {
    "Date First Available", "Item model number", "Manufacturer Part Number",
    "Part Number", "ASIN", "UPC", "Global Trade Identification Number",
    "Is Discontinued By Manufacturer",
}

# ---- ยังไม่ตัดสิน (อย่าเดาค่าใส่ไว้ก่อน) ----
# - EMBED_MAX_CHARS / batch size     -> Phase 1 (หลังล็อก embed_text)
# - พารามิเตอร์ Reranker             -> Phase 2
# - เกณฑ์ guardrails                 -> Phase 2
# - ค่าตั้งของ agent (max turns ฯลฯ) -> Phase 3 หลัง ADR-0001
