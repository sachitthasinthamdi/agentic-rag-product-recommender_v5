"""แปลคำค้นภาษาไทยเป็นภาษาอังกฤษด้วย Typhoon2 (local)

ทำไมต้องมี: คลังสินค้าเป็นภาษาอังกฤษทั้งหมด แต่ผู้ใช้พิมพ์ไทย การทดลองนำร่อง
(`eval/results/crosslingual_pilot.md`) พบว่าค้นด้วยคำค้นไทยตรง ๆ ทำให้ผลหลุดไปสินค้า
คนละประเภท (กางเกงโยคะแทนเสื่อโยคะ, ประแจแทนไขควง) — ดู ADR-0005

มี cache ในหน่วยความจำเพราะในบทสนทนาหนึ่งผู้ใช้มักถามเรื่องเดิมซ้ำ ๆ และตอนรัน eval
คำค้นชุดเดิมถูกใช้หลายรอบ
"""

from __future__ import annotations

from mark5.common.llm import OllamaChat
from mark5.common.logger import get_logger

log = get_logger(__name__)

_SYSTEM = (
    "You translate Thai e-commerce search queries into English search queries. "
    "Output ONLY the English query. No explanation, no quotes, no Thai text. "
    "Keep it short and literal — preserve the exact product type, brand names, "
    "numbers and units. Do not add words the user did not say."
)

_EXAMPLES = (
    "ตัวอย่าง:\n"
    "ไทย: หูฟังบลูทูธไร้สายกันน้ำ\nอังกฤษ: waterproof wireless bluetooth headphones\n\n"
    "ไทย: สายชาร์จ USB-C ยาว 2 เมตร\nอังกฤษ: 2 meter USB-C charging cable\n\n"
    "ไทย: เสื่อโยคะกันลื่น\nอังกฤษ: non-slip yoga mat\n\n"
)


class QueryTranslator:
    """แปลไทย → อังกฤษ สำหรับใช้เป็นคำค้น"""

    def __init__(self, chat: OllamaChat | None = None):
        self._chat = chat or OllamaChat()
        self._cache: dict[str, str] = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._chat.close()

    def translate(self, thai_query: str) -> str:
        query = thai_query.strip()
        if query in self._cache:
            return self._cache[query]

        raw = self._chat.chat(
            system=_SYSTEM,
            user=f"{_EXAMPLES}ไทย: {query}\nอังกฤษ:",
            temperature=0.0,
            num_predict=64,
        )
        english = self._clean(raw)
        if not english:
            # แปลไม่ได้ก็ใช้คำค้นเดิม ดีกว่าค้นด้วยสตริงว่าง
            log.warning("แปลคำค้นไม่สำเร็จ ใช้ต้นฉบับแทน: %r -> %r", query, raw)
            english = query

        self._cache[query] = english
        return english

    @staticmethod
    def _clean(raw: str) -> str:
        """เอาส่วนเกินที่โมเดลมักแถมมาออก (คำนำหน้า, เครื่องหมายคำพูด, หลายบรรทัด)"""
        text = raw.strip().splitlines()[0].strip() if raw.strip() else ""
        for prefix in ("อังกฤษ:", "English:", "Translation:", "Answer:"):
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
        return text.strip(' "\'`').strip()
