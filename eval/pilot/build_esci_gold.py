"""สร้างชุด gold สำหรับตรวจสอบ LLM judge จาก Amazon ESCI (label จากคนจริง)

**ทำไมต้องมี:** ตัวเลข product-type precision ทั้งหมดของเราอิง LLM judge ถ้า judge ผิด
ตัวเลขก็ผิดตาม และเราเจอมาแล้ว 2 รอบว่า judge ผิดแบบเป็นระบบ (รอบแรกปฏิเสธปลอกคอสุนัข
เมื่อถามหาปลอกคอสุนัข, รอบสองปฏิเสธ "adidas Men's Lightweight Running Shoe" เมื่อถามหา
รองเท้าวิ่งผู้ชาย) — ต้องมี ground truth จากคนมาวัดว่า judge เชื่อถือได้แค่ไหน

**แหล่ง ground truth:** Amazon Shopping Queries Dataset (ESCI)
Reddy et al. (2022), arXiv:2206.06588 — label โดยคนจริงของ Amazon
mark4 เคยใช้ชุดนี้ตรวจ judge มาแล้ว จึงเทียบข้ามรุ่นได้

**การแมป label:** คำถามของเราคือ "สินค้าชิ้นนี้เป็นประเภทเดียวกับที่ถามหาไหม"
    Exact       -> YES  (ตรงกับที่ถามหา)
    Complement  -> NO   (ของใช้คู่กัน เช่น สายชาร์จของกล้อง — คนละประเภท)
    Irrelevant  -> NO   (ไม่เกี่ยวเลย)
    Substitute  -> **ตัดออกจากชุดหลัก** เพราะกำกวมสำหรับคำถามนี้: ESCI นิยามว่า
                   "ใช้แทนกันได้แต่ไม่ตรงทั้งหมด" ซึ่งบางกรณีเป็นประเภทเดียวกัน
                   (รองเท้าวิ่งคนละยี่ห้อ) บางกรณีไม่ใช่ (รองเท้าเดินแทนรองเท้าวิ่ง)
                   เก็บไว้รายงานแยกเป็นกลุ่ม "กำกวม" ไม่เอามาคิด kappa

**ทำไมดึงผ่าน HTTP API ไม่โหลดไฟล์:** ไฟล์บน HF เป็น parquet ซึ่งอ่านไม่ได้บนเครื่องนี้
(Application Control บล็อก DLL `pyarrow._fs`) — datasets-server คืนแถวเป็น JSON จึงใช้ได้

รัน:  python -m eval.pilot.build_esci_gold [--per-label 60]
"""

from __future__ import annotations

import argparse
import json
import random
import time

import httpx

from config import settings
from mark5.common.logger import get_logger

log = get_logger(__name__)

ROWS_API = "https://datasets-server.huggingface.co/rows"
DATASET = "tasksource/esci"
SPLIT_ROWS = 652_490          # ขนาด split "test" (จาก endpoint /size)
GOLD_FILE = settings.ROOT / "eval" / "data" / "esci_gold.json"

# label ของ ESCI -> คำตอบที่ถูกต้องสำหรับคำถาม "ประเภทเดียวกันไหม" (None = กำกวม ไม่ใช้คิด kappa)
LABEL_MAP = {"Exact": True, "Complement": False, "Irrelevant": False, "Substitute": None}
PAGE = 100   # datasets-server คืนได้สูงสุด 100 แถวต่อครั้ง


def _fetch_page(offset: int, max_retries: int = 6) -> list[dict]:
    """ดึงแถวดิบ 1 หน้า — endpoint `/filter` ของ HF คืน 500 กับชุดข้อมูลนี้
    จึงต้องใช้ `/rows` แล้วกรอง locale/label เองฝั่งเรา

    API สาธารณะนี้จำกัดอัตราการเรียก (429) สำหรับคำขอที่ไม่ล็อกอิน จึงต้องถอยแบบทวีคูณ
    และเคารพ `Retry-After` ถ้าเซิร์ฟเวอร์ส่งมา — ไม่ใช่ยิงรัวจนถูกตัด
    """
    params = {"dataset": DATASET, "config": "default", "split": "test",
              "offset": offset, "length": PAGE}
    for attempt in range(1, max_retries + 1):
        try:
            response = httpx.get(ROWS_API, params=params, timeout=180)
        except httpx.HTTPError as exc:      # ต่อไม่ติด/timeout ก็ถอยแล้วลองใหม่เหมือนกัน
            log.warning("ต่อ API ไม่ได้ (%s) — ลองใหม่ (%d/%d)", type(exc).__name__,
                        attempt, max_retries)
            time.sleep(min(60, 5 * 2 ** (attempt - 1)))
            continue

        # 429 = ถูกจำกัดอัตรา, 5xx = ฝั่งเซิร์ฟเวอร์มีปัญหาชั่วคราว (เจอ 502 จริง) — ถอยทั้งคู่
        if response.status_code == 429 or response.status_code >= 500:
            wait = float(response.headers.get("Retry-After", 0) or 0) or min(60, 5 * 2 ** (attempt - 1))
            log.warning("HTTP %d — รอ %.0f วินาทีแล้วลองใหม่ (%d/%d)",
                        response.status_code, wait, attempt, max_retries)
            time.sleep(wait)
            continue

        response.raise_for_status()
        return [r["row"] for r in response.json().get("rows", [])]

    log.warning("ข้ามหน้านี้ไป — เรียก API ไม่สำเร็จหลังลอง %d ครั้ง", max_retries)
    return []


def build(per_label: int, seed: int = 42, max_pages: int = 120) -> list[dict]:
    """สุ่ม offset ทั่วทั้ง split แล้วเก็บใส่ถังตาม label จนครบโควตา

    สุ่ม offset ไม่ใช่ไล่จากแถวแรก เพราะข้อมูลเรียงตามภาษาและตามคำค้น
    (offset 50,000 เจอแต่ภาษาญี่ปุ่น) การไล่จากต้นจะได้ตัวอย่างกระจุกมาก
    """
    rng = random.Random(seed)
    buckets: dict[str, list[dict]] = {label: [] for label in LABEL_MAP}
    seen: set[tuple[str, str]] = set()
    pages = kept_us = 0

    while pages < max_pages and any(len(b) < per_label for b in buckets.values()):
        pages += 1
        rows = _fetch_page(rng.randrange(0, SPLIT_ROWS - PAGE))
        rng.shuffle(rows)
        for row in rows:
            label = row.get("esci_label")
            if row.get("product_locale") != "us" or label not in LABEL_MAP:
                continue
            kept_us += 1
            if len(buckets[label]) >= per_label or not row.get("product_title"):
                continue
            key = (row["query"], row["product_title"])
            if key in seen:
                continue
            seen.add(key)
            buckets[label].append({
                "query": row["query"],
                "product_title": row["product_title"],
                "esci_label": label,
                "gold_same_type": LABEL_MAP[label],
                "product_id": row["product_id"],
            })
        if pages % 10 == 0:
            log.info("ดึงไป %d หน้า (แถว locale=us %s) | %s", pages, f"{kept_us:,}",
                     " ".join(f"{k}={len(v)}" for k, v in buckets.items()))
        time.sleep(2.0)   # API สาธารณะจำกัดอัตรา — เว้นจังหวะให้พอ

    for label, rows in buckets.items():
        log.info("ESCI '%s' -> เก็บได้ %d/%d", label, len(rows), per_label)

    gold = [row for rows in buckets.values() for row in rows]

    rng.shuffle(gold)
    GOLD_FILE.parent.mkdir(parents=True, exist_ok=True)
    GOLD_FILE.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("เขียน %s (%d คู่)", GOLD_FILE.relative_to(settings.ROOT), len(gold))
    return gold


def main() -> None:
    parser = argparse.ArgumentParser(description="สร้างชุด gold จาก Amazon ESCI")
    parser.add_argument("--per-label", type=int, default=60)
    build(parser.parse_args().per_label)


if __name__ == "__main__":
    main()
