"""Embedder — เรียก BGE-M3 ผ่าน Ollama HTTP API

**ทำไมไม่ใช้ `sentence_transformers`:** มันลาก `sklearn`/`scipy` มาด้วย ซึ่ง Windows
Application Control บนเครื่องพัฒนานี้บล็อก DLL อยู่ (โปรเจกต์ก่อนเจอปัญหานี้จน import ไม่ผ่าน)
เรียกผ่าน Ollama จึงเป็นทางที่ทำงานได้จริงและไม่ต้องลง dependency หนัก

**ข้อเท็จจริงที่วัดจากเครื่องนี้ (2026-09-28):**
  - `/api/embed` รับ `input` เป็น list ได้ (batch) คืน `embeddings` เป็น list ของ list
  - มิติ 1,024 และเวกเตอร์ **normalize มาแล้ว** (‖v‖ = 1.000000) → cosine = dot product
  - batch=32 ใช้เวลา ~104 ms/doc → ทั้งชุด 117,243 รายการประมาณ 3.4 ชั่วโมง

⚠ ต้องสตาร์ต Ollama server เองก่อนใช้งานทุกเซสชัน: `ollama.exe serve`
"""

from __future__ import annotations

import time

import httpx

from config import settings
from mark5.common.exception import LLMError
from mark5.common.logger import get_logger

log = get_logger(__name__)

EMBED_DIM = 1024


class OllamaEmbedder:
    """เข้ารหัสข้อความเป็นเวกเตอร์ด้วยโมเดล embedding บน Ollama"""

    def __init__(self, model: str | None = None, base_url: str | None = None,
                 batch_size: int = 32, timeout: float = 600.0, max_retries: int = 3):
        self.model = model or settings.OLLAMA_EMBED_MODEL
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.batch_size = batch_size
        self.max_retries = max_retries
        self._client = httpx.Client(timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self) -> None:
        self._client.close()

    def health_check(self) -> None:
        """ตรวจว่า server ตอบและมีโมเดลที่ต้องใช้ — เรียกก่อนงานยาว ๆ จะได้ไม่พังกลางทาง"""
        try:
            response = self._client.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(
                f"ต่อ Ollama ที่ {self.base_url} ไม่ได้ — สตาร์ต server ก่อนด้วย `ollama.exe serve`"
            ) from exc

        available = {m["name"].split(":")[0] for m in response.json().get("models", [])}
        if self.model.split(":")[0] not in available:
            raise LLMError(
                f"ไม่พบโมเดล '{self.model}' บน Ollama (มีอยู่: {sorted(available)}) "
                f"— ดึงก่อนด้วย `ollama pull {self.model}`"
            )

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": texts},
                )
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    log.warning("embed ล้มเหลว (ครั้งที่ %d/%d) รอ %ds แล้วลองใหม่: %s",
                                attempt, self.max_retries, wait, exc)
                    time.sleep(wait)
                continue

            vectors = payload.get("embeddings")
            if vectors is None and "embedding" in payload:
                vectors = [payload["embedding"]]
            if not vectors or len(vectors) != len(texts):
                raise LLMError(
                    f"Ollama คืนเวกเตอร์ {len(vectors or [])} ตัว แต่ส่งข้อความไป {len(texts)} ตัว"
                )
            return vectors

        raise LLMError(f"embed ไม่สำเร็จหลังลอง {self.max_retries} ครั้ง") from last_error

    def embed(self, texts: list[str], show_progress: bool = False) -> list[list[float]]:
        """เข้ารหัสข้อความทั้งชุด — ข้อความว่างถูกแทนด้วยช่องว่างเพื่อให้ index ตรงกับ input เสมอ"""
        if not texts:
            return []
        prepared = [t if (t and t.strip()) else " " for t in texts]

        vectors: list[list[float]] = []
        started = time.perf_counter()
        for start in range(0, len(prepared), self.batch_size):
            vectors.extend(self._embed_batch(prepared[start:start + self.batch_size]))
            if show_progress:
                done = len(vectors)
                elapsed = time.perf_counter() - started
                log.info("embed %s/%s (%.0f%%) | %.1f ms/doc | เหลือประมาณ %.1f นาที",
                         f"{done:,}", f"{len(prepared):,}", done / len(prepared) * 100,
                         elapsed / done * 1000, (len(prepared) - done) * elapsed / done / 60)
        return vectors

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


def cosine(a: list[float], b: list[float]) -> float:
    """cosine similarity — BGE-M3 ผ่าน Ollama คืนเวกเตอร์ที่ normalize แล้ว จึงเป็น dot product ตรง ๆ

    ไม่ใช้ numpy/scipy ตรงนี้เพื่อให้ฟังก์ชันนี้ทดสอบได้โดยไม่พึ่ง dependency ที่อาจถูกบล็อก
    """
    return sum(x * y for x, y in zip(a, b, strict=True))
