"""Vector store — ChromaDB แบบ local (ไม่ใช้ Chroma Cloud ดู ADR-0004)

ข้อควรรู้ของ Chroma ที่กระทบการออกแบบ:
  - **metadata รับได้เฉพาะ scalar** (str / int / float / bool) และ **ห้ามเป็น None**
    ข้อมูลเรามีค่าว่างเยอะ (price หาย 30.7%, color หาย 65%) จึงต้อง "ตัด key ที่เป็น null ทิ้ง"
    ไม่ใช่ใส่ None ลงไป — ตัวกรอง `$eq` ของ Chroma จะไม่ match แถวที่ไม่มี key นั้น ซึ่งถูกต้องแล้ว
  - ระยะทางต้องตั้งเป็น **cosine** ตั้งแต่ตอนสร้าง collection เปลี่ยนทีหลังไม่ได้
    (BGE-M3 คืนเวกเตอร์ normalize แล้ว cosine กับ dot product จึงให้ลำดับเดียวกัน)
"""

from __future__ import annotations

from typing import Any, Iterable

import chromadb

from config import settings
from mark5.common.logger import get_logger

log = get_logger(__name__)


def clean_metadata(record: dict[str, Any]) -> dict[str, Any]:
    """ตัด key ที่ค่าเป็น null/NaN ออก และแปลงค่าให้เป็น scalar ที่ Chroma รับได้"""
    cleaned: dict[str, Any] = {}
    for key, value in record.items():
        if value is None:
            continue
        if isinstance(value, float) and value != value:   # NaN
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        else:
            cleaned[key] = str(value)
    return cleaned


class ChromaStore:
    """ห่อ ChromaDB local ให้เรียกใช้ง่ายและบังคับข้อตกลงของโปรเจกต์ไว้ที่เดียว"""

    def __init__(self, collection_name: str | None = None, path: str | None = None):
        self.collection_name = collection_name or settings.COLLECTION_NAME
        self.path = path or str(settings.CHROMA_DIR)
        settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self.path)
        self.collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self.collection.count()

    def existing_ids(self, ids: Iterable[str]) -> set[str]:
        """คืน id ที่มีอยู่แล้วใน collection — ใช้ข้ามงานที่ทำไปแล้วเวลา index ถูกขัดจังหวะ"""
        ids = list(ids)
        if not ids:
            return set()
        found: set[str] = set()
        for start in range(0, len(ids), 5_000):
            got = self.collection.get(ids=ids[start:start + 5_000], include=[])
            found.update(got.get("ids", []))
        return found

    def add(self, ids: list[str], embeddings: list[list[float]],
            documents: list[str], metadatas: list[dict]) -> None:
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=documents,
            metadatas=[clean_metadata(m) for m in metadatas],
        )

    def query(self, embedding: list[float], n_results: int = 10,
              where: dict | None = None) -> dict:
        return self.collection.query(
            query_embeddings=[embedding], n_results=n_results,
            where=where or None, include=["metadatas", "documents", "distances"],
        )

    def reset(self) -> None:
        """ลบ collection ทิ้งแล้วสร้างใหม่ — ใช้เมื่อ embed_text เปลี่ยนจนต้อง index ใหม่ทั้งหมด"""
        log.warning("ลบ collection '%s' (%s รายการ) แล้วสร้างใหม่",
                    self.collection_name, f"{self.count():,}")
        self._client.delete_collection(self.collection_name)
        self.collection = self._client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"},
        )
