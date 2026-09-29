"""Client คุยกับ LLM บน Ollama — ใช้ร่วมกันทั้งตัวแปลคำค้น, judge และ Generator

⚠ **ต้องใช้ `/api/chat` พร้อมส่ง system message ทับเสมอ ห้ามใช้ `/api/generate`**
โมเดล Typhoon2 ที่ติดตั้งบนเครื่องนี้มี persona ฝังอยู่ใน Modelfile ("ผู้ช่วยใจดี...")
ซึ่ง **ครอบคำสั่งที่เราส่งไป** จนโมเดลตอบตาม persona แทนที่จะทำตามที่สั่ง
mark4 เจอปัญหานี้จน LLM judge ตอบ "2" เกือบทุกครั้ง (Cohen's κ = 0.054 = ใช้ไม่ได้เลย)
พอเปลี่ยนมาเป็น `/api/chat` + system override ค่าขยับขึ้นทันที — อย่าถอยกลับไปใช้ `/api/generate`
"""

from __future__ import annotations

import time

import httpx

from config import settings
from mark5.common.exception import LLMError
from mark5.common.logger import get_logger

log = get_logger(__name__)


class OllamaChat:
    def __init__(self, model: str | None = None, base_url: str | None = None,
                 timeout: float = 300.0, max_retries: int = 3):
        self.model = model or settings.OLLAMA_CHAT_MODEL
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.max_retries = max_retries
        self._client = httpx.Client(timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._client.close()

    def close(self) -> None:
        self._client.close()

    def chat(self, system: str, user: str, temperature: float = 0.0,
             num_predict: int = 256) -> str:
        """ส่งข้อความเดียวแล้วรับคำตอบ — `system` ทับ persona ใน Modelfile

        temperature=0 เป็นค่าตั้งต้นเพราะงานส่วนใหญ่ที่เรียกฟังก์ชันนี้ (แปลภาษา, ตัดสิน
        ใช่/ไม่ใช่) ต้องการผลที่ทำซ้ำได้ ไม่ใช่ความสร้างสรรค์
        """
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": num_predict},
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                return response.json()["message"]["content"].strip()
            except (httpx.HTTPError, KeyError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
        raise LLMError(f"เรียก LLM ไม่สำเร็จหลังลอง {self.max_retries} ครั้ง") from last_error
