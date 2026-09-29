"""Retriever — ค้นสินค้าจาก ChromaDB ด้วย semantic search

รองรับ 3 กลยุทธ์การค้นด้วยคำค้นภาษาไทย ซึ่งเป็นตัวเลือกใน ADR-0005:
  - `thai`      ค้นด้วยคำค้นไทยตรง ๆ
  - `translate` แปลเป็นอังกฤษก่อนแล้วค้นด้วยคำแปล
  - `fused`     ค้นทั้งสองภาษาแล้วรวมอันดับด้วย RRF

ยังไม่รวม Reranker เชิงคุณภาพ (popularity / value_score) — นั่นเป็นอีกชั้นที่จะเพิ่มทีหลัง
ไฟล์นี้จัดการเฉพาะ "หาของให้เจอ" ส่วน "จัดอันดับให้ดี" กับ "กรองของผิด" อยู่คนละโมดูล
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from mark5.common.logger import get_logger
from mark5.index.embedder import OllamaEmbedder
from mark5.index.vector_store import ChromaStore
from mark5.retrieval import rrf
from mark5.retrieval.query_translator import QueryTranslator

log = get_logger(__name__)

Strategy = Literal["thai", "translate", "fused", "raw"]


@dataclass
class Hit:
    id: str
    title: str
    category: str
    score: float                      # cosine similarity (ยิ่งมากยิ่งใกล้)
    metadata: dict = field(default_factory=dict)


class Retriever:
    def __init__(self, store: ChromaStore | None = None,
                 embedder: OllamaEmbedder | None = None,
                 translator: QueryTranslator | None = None):
        self.store = store or ChromaStore()
        self.embedder = embedder or OllamaEmbedder()
        self._translator = translator
        self._owns_translator = translator is None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self) -> None:
        self.embedder.close()
        if self._owns_translator and self._translator is not None:
            self._translator.__exit__()

    @property
    def translator(self) -> QueryTranslator:
        if self._translator is None:
            self._translator = QueryTranslator()
        return self._translator

    def _search(self, text: str, n: int, where: dict | None = None) -> list[Hit]:
        vector = self.embedder.embed_one(text)
        result = self.store.query(vector, n_results=n, where=where)
        hits = []
        for doc_id, meta, distance in zip(result["ids"][0], result["metadatas"][0],
                                          result["distances"][0], strict=True):
            hits.append(Hit(
                id=doc_id,
                title=str(meta.get("title", "")),
                category=str(meta.get("category", "")),
                score=1.0 - distance,          # Chroma คืน cosine distance
                metadata=meta,
            ))
        return hits

    def search(self, query: str, n: int = 10, strategy: Strategy = "fused",
               where: dict | None = None) -> list[Hit]:
        """ค้นสินค้า — `query` เป็นภาษาไทย ยกเว้น strategy="raw" ที่ค้นด้วยข้อความตามที่ให้มา"""
        if strategy in ("raw", "thai"):
            return self._search(query, n, where)

        if strategy == "translate":
            return self._search(self.translator.translate(query), n, where)

        if strategy == "fused":
            # ดึงมาเกิน n เพื่อให้ RRF มีของให้รวมพอ — รวมเสร็จค่อยตัดเหลือ n
            pool = max(n * 3, 30)
            thai_hits = self._search(query, pool, where)
            english_hits = self._search(self.translator.translate(query), pool, where)

            fused = rrf.fuse([[h.id for h in thai_hits], [h.id for h in english_hits]])
            by_id = {h.id: h for h in (*english_hits, *thai_hits)}   # ไทยทับอังกฤษไม่สำคัญ ข้อมูลเดียวกัน

            out = []
            for doc_id, rrf_score in fused[:n]:
                hit = by_id[doc_id]
                out.append(Hit(id=hit.id, title=hit.title, category=hit.category,
                               score=rrf_score, metadata=hit.metadata))
            return out

        raise ValueError(f"ไม่รู้จัก strategy '{strategy}'")
