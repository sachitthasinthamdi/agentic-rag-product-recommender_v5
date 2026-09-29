"""สร้างดัชนีเวกเตอร์: ชั้น feature -> BGE-M3 (Ollama) -> ChromaDB local

ออกแบบให้ **ขัดจังหวะแล้วรันต่อได้** เพราะงานเต็มใช้เวลา ~84 นาที — ถ้าไฟดับหรือ Ollama
ล่มกลางทาง การต้องเริ่มใหม่ตั้งแต่ต้นแพงเกินไป จึงเช็ค id ที่อยู่ใน collection แล้วข้าม

ทำทีละก้อน (embed -> add -> ทิ้ง) ไม่เก็บเวกเตอร์ทั้งหมดในหน่วยความจำก่อน
(117,243 × 1,024 มิติ = ~480 MB ถ้าเป็น float32 แต่ใน list ของ Python จะบานกว่านั้นหลายเท่า)

รัน:  python -m mark5.index.build_index [--limit N] [--reset] [--chunk 512]
"""

from __future__ import annotations

import argparse
import time

import pandas as pd

from config import settings
from mark5.common.logger import get_logger
from mark5.common.tables import read_table
from mark5.index.embedder import OllamaEmbedder
from mark5.index.vector_store import ChromaStore

log = get_logger(__name__)

# คอลัมน์ที่แนบไปกับเวกเตอร์เป็น metadata — ใช้ทั้งกรองตอนค้นและแสดงผลโดยไม่ต้องกลับไปอ่าน parquet
METADATA_COLUMNS = [
    "title", "category", "category_source", "brand", "brand_source",
    "price", "price_tier", "price_missing", "average_rating", "rating_number",
    "popularity", "value_score", "color", "material", "weight_g",
    "best_sellers_rank", "image",
]
# `parent_asin` เป็น id ของเวกเตอร์ (ตรวจแล้วไม่ซ้ำเลยใน 117,243 แถว) จึงไม่ต้องซ้ำใน metadata


def build(limit: int | None = None, chunk: int = 512, reset: bool = False,
          batch_size: int = 32) -> None:
    log.info("อ่านชั้น feature ...")
    columns = ["parent_asin", "embed_text", *METADATA_COLUMNS]
    df = read_table(settings.FEATURE_FILE, columns=columns)
    if limit:
        df = df.head(limit)
        log.info("โหมดทดสอบ: ใช้แค่ %s แถวแรก", f"{limit:,}")

    store = ChromaStore()
    if reset:
        store.reset()

    before = store.count()
    log.info("collection '%s' มีอยู่แล้ว %s รายการ", store.collection_name, f"{before:,}")

    done = store.existing_ids(df["parent_asin"].tolist()) if before else set()
    todo = df[~df["parent_asin"].isin(done)].reset_index(drop=True)
    if done:
        log.info("ข้าม %s รายการที่ index ไว้แล้ว — เหลือทำ %s รายการ",
                 f"{len(done):,}", f"{len(todo):,}")
    if todo.empty:
        log.info("ไม่มีอะไรต้องทำ — ดัชนีครบแล้ว (%s รายการ)", f"{store.count():,}")
        return

    with OllamaEmbedder(batch_size=batch_size) as embedder:
        embedder.health_check()
        log.info("เริ่ม index %s รายการ (ประมาณ %.0f นาที)", f"{len(todo):,}", len(todo) * 0.043 / 60)

        started = time.perf_counter()
        for start in range(0, len(todo), chunk):
            part = todo.iloc[start:start + chunk]
            vectors = embedder.embed(part["embed_text"].tolist())
            store.add(
                ids=part["parent_asin"].tolist(),
                embeddings=vectors,
                documents=part["embed_text"].tolist(),
                metadatas=part[METADATA_COLUMNS].to_dict(orient="records"),
            )
            finished = min(start + chunk, len(todo))
            elapsed = time.perf_counter() - started
            log.info("index %s/%s (%.1f%%) | %.1f ms/doc | เหลือประมาณ %.0f นาที",
                     f"{finished:,}", f"{len(todo):,}", finished / len(todo) * 100,
                     elapsed / finished * 1000, (len(todo) - finished) * elapsed / finished / 60)

    log.info("เสร็จใน %.1f นาที | collection มีทั้งหมด %s รายการ",
             (time.perf_counter() - started) / 60, f"{store.count():,}")


def main() -> None:
    parser = argparse.ArgumentParser(description="สร้างดัชนีเวกเตอร์ลง ChromaDB local")
    parser.add_argument("--limit", type=int, help="จำกัดจำนวนแถว (สำหรับทดสอบ)")
    parser.add_argument("--chunk", type=int, default=512, help="จำนวนแถวต่อรอบ embed+add")
    parser.add_argument("--batch-size", type=int, default=32, help="ขนาด batch ที่ส่งให้ Ollama")
    parser.add_argument("--reset", action="store_true", help="ลบ collection เดิมแล้วสร้างใหม่")
    args = parser.parse_args()
    build(limit=args.limit, chunk=args.chunk, reset=args.reset, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
