"""อ่าน/เขียนตารางข้อมูล — รวมไว้ที่เดียวเพื่อให้เปลี่ยนรูปแบบไฟล์ได้จากจุดเดียว

**ทำไมใช้ Feather ไม่ใช่ Parquet (ตัดสิน 2026-09-29):**
Windows Application Control บนเครื่องพัฒนานี้บล็อก DLL `pyarrow._fs` ซึ่ง `pyarrow.parquet`
ต้องใช้ → อ่าน/เขียน parquet ไม่ได้เลยทั้ง library (เป็น DLL ตัวที่ 3 ที่โดน ต่อจาก
`pyarrow._dataset` และ `pandas._libs.window.indexers`)

`pyarrow.ipc` และ `pyarrow.feather` ยังทำงานปกติ — เป็น library ตัวเดียวกัน คนละ DLL
Feather v2 **คือ Arrow IPC file format** จึงเป็นการเปลี่ยน "ภาชนะ" ไม่ใช่เปลี่ยน library
และไม่ต้องลง dependency ใหม่

ข้อแลกเปลี่ยนที่รับไว้: Feather ไม่มี predicate pushdown และไม่มี row-group statistics
แบบ parquet — แต่เราอ่านทั้งไฟล์หรืออ่านเป็นคอลัมน์อยู่แล้ว จึงไม่กระทบ

หมายเหตุ: ถ้าวันหนึ่ง DLL ถูก allowlist แล้วอยากกลับไปใช้ parquet ให้แก้แค่ไฟล์นี้
กับนามสกุลใน `config/settings.py`
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc

from mark5.common.logger import get_logger

log = get_logger(__name__)

# เรียงตามความชอบ — pyarrow บางรุ่นไม่ได้คอมไพล์มาพร้อม zstd
_COMPRESSION_PREFERENCE = ["zstd", "lz4", None]


def _write_options() -> ipc.IpcWriteOptions:
    """เลือกวิธีบีบอัดที่ pyarrow ตัวนี้รองรับจริง — ไม่เดา"""
    for codec in _COMPRESSION_PREFERENCE:
        try:
            return ipc.IpcWriteOptions(compression=codec)
        except (ValueError, pa.ArrowNotImplementedError, OSError):
            continue
    return ipc.IpcWriteOptions()


def read_table(path: Path | str, columns: list[str] | None = None) -> pd.DataFrame:
    """อ่านตารางทั้งไฟล์ (เลือกเฉพาะบางคอลัมน์ได้)"""
    return pd.read_feather(path, columns=columns)


def write_table(df: pd.DataFrame, path: Path | str) -> None:
    """เขียนตาราง — รีเซ็ต index ก่อนเสมอเพราะ Feather ไม่รองรับ index ที่ไม่ใช่ค่าเริ่มต้น"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reset_index(drop=True).to_feather(path)


class TableWriter:
    """เขียนตารางทีละก้อน (streaming) โดยไม่ต้องรวมทุกอย่างในหน่วยความจำก่อน

    จำเป็นตอน ingest เพราะข้อมูลดิบ ~1.6 GB ถ้าต่อกันทั้งหมดก่อนเขียนจะกินแรมหลาย GB
    ไฟล์ที่ได้เป็น Arrow IPC file format ซึ่ง `pd.read_feather` อ่านได้ตรง ๆ
    """

    def __init__(self, path: Path | str, schema: pa.Schema):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.schema = schema
        options = _write_options()
        log.info("เขียน %s (บีบอัดแบบ %s)", self.path.name, options.compression or "ไม่บีบอัด")
        self._sink = self.path.open("wb")
        self._writer = ipc.new_file(self._sink, schema, options=options)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def write(self, table: pa.Table) -> None:
        self._writer.write_table(table)

    def close(self) -> None:
        self._writer.close()
        self._sink.close()
