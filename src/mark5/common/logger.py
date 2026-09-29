"""Logger กลางของโปรเจกต์

เหตุผลที่มี: mark4 ใช้ print() ทำให้ย้อนดูไม่ได้ว่าเกิดอะไรตอนรัน pipeline 90 นาที
ที่นี่เขียนลง console (อ่านง่ายตอนพัฒนา) และไฟล์รายวัน (ย้อนดูได้) พร้อมกัน
"""

import logging
import sys
from datetime import date

from config import settings

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_configured: set[str] = set()


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """คืน logger ที่ตั้งค่าแล้ว — เรียกซ้ำด้วยชื่อเดิมได้ ไม่เพิ่ม handler ซ้ำ"""
    logger = logging.getLogger(name)
    if name in _configured:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(
        settings.LOG_DIR / f"{date.today():%Y-%m-%d}.log", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _configured.add(name)
    return logger
