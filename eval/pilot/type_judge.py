"""LLM judge แบบ binary: "สินค้าชิ้นนี้เป็นประเภทเดียวกับที่ผู้ใช้ถามหาไหม"

**ทำไมถามแบบ binary ไม่ใช่ให้คะแนน 0/1/2:** mark4 ใช้ judge แบบให้คะแนน relevance
แล้วได้ Cohen's κ = 0.267 (fair) เท่านั้น คำถาม "เป็นสินค้าประเภทเดียวกันไหม" แคบกว่ามาก
และเป็นสิ่งที่ตัดสินได้จากชื่อสินค้าโดยตรง จึงควรได้ความน่าเชื่อถือสูงกว่า
— แต่ **ต้องวัดจริง** ไม่ใช่สมมุติ (ดูหัวข้อการตรวจสอบในรายงาน)

บทเรียนจาก mark4 ที่นำมาใช้ที่นี่:
  - ใช้ `/api/chat` + system override เสมอ (persona ใน Modelfile ครอบคำสั่ง) — จัดการใน OllamaChat
  - ให้เขียนเหตุผลสั้น ๆ ก่อนตอบ (CoT) แล้ว parse บรรทัด "Answer:" — ช่วย κ ขึ้นชัดเจน
  - ใส่ few-shot ที่ครอบทั้งคำตอบ YES และ NO รวมถึงเคส "ใกล้เคียงแต่คนละประเภท"
    ซึ่งเป็นความผิดพลาดที่พบจริงใน mark4 (แผ่นรองเมาส์เมื่อถามหาเมาส์)
"""

from __future__ import annotations

import re

from mark5.common.llm import OllamaChat
from mark5.common.logger import get_logger

log = get_logger(__name__)

_SYSTEM = (
    "You evaluate an e-commerce search result. "
    "Compare ONLY the HEAD NOUN — the thing itself that the shopper asked for. "
    "Ignore every describing word: colour, size, length, brand, price, material, and "
    "feature words such as 'adjustable', 'dust-free', 'waterproof', 'non-slip', "
    "'lightweight', '2 meter'. A product that is the right thing but lacks a described "
    "feature still counts as YES. "
    "Answer NO only when the product is a DIFFERENT thing from what was asked — for "
    "example a container for it, a stand for it, a cleaner for it, or an unrelated item. "
    "Reply with one short reason line, then a final line exactly 'Answer: YES' or 'Answer: NO'."
)

# few-shot ครอบ 3 ความผิดพลาดที่พบจริง:
#   1. ของประกอบ/ของที่ใช้คู่กัน แต่คนละชิ้น (แผ่นรองเมาส์ vs เมาส์) -> NO
#   2. รอบแรก judge ปฏิเสธ "ของที่ตรงเป๊ะ" เพราะมันเป็นอุปกรณ์เสริมอยู่แล้วโดยธรรมชาติ
#      (ปลอกคอสุนัข) -> ต้องเป็น YES
#   3. รอบแรก judge ปฏิเสธเพราะขาดคำขยาย (ทรายแมวธรรมดา เมื่อถามทรายแมว "ไร้ฝุ่น") -> ต้องเป็น YES
_FEWSHOT = """Shopper wants: wireless gaming mouse
Product: Kunsaww Cloud Star Pink Large Game Mouse Pad Non Slip Stitched Edges
Reason: the head noun is "mouse pad", a surface you put a mouse on, not a mouse.
Answer: NO

Shopper wants: adjustable dog collar
Product: Soft Durable Dog Collar with Metal Buckle, Quick Release Puppy Collars
Reason: the head noun is "dog collar", exactly what was asked; "adjustable" is just a feature.
Answer: YES

Shopper wants: dust free cat litter
Product: PrettyLitter Lotus Flower Scented Health Monitoring Cat Pet Litter (8 lbs)
Reason: the head noun is "cat litter"; "dust free" is a feature, not a different product.
Answer: YES

Shopper wants: dust free cat litter
Product: Amazon Basics Sifting Scoop-Free Easy-to-Clean Cat Litter Box, Large
Reason: the head noun is "litter box", a container, not the litter itself.
Answer: NO

Shopper wants: non-slip yoga mat
Product: CRZ YOGA Mens Comfy Lounge Pants Open Bottom Yoga Casual Pajama Pants
Reason: the head noun is "pants", not a mat.
Answer: NO

Shopper wants: multipurpose screwdriver set
Product: Screwdriver Set 10 Piece, Cushion Grip, 5 Phillips and 5 Flat Head Tips
Reason: the head noun is "screwdriver set", exactly what was asked.
Answer: YES

"""

_ANSWER_RE = re.compile(r"answer\s*:\s*(yes|no)", re.IGNORECASE)


class ProductTypeJudge:
    def __init__(self, chat: OllamaChat | None = None):
        self._chat = chat or OllamaChat()
        self._cache: dict[tuple[str, str], tuple[bool | None, str]] = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._chat.close()

    def judge(self, wanted: str, product_title: str) -> tuple[bool | None, str]:
        """คืน (ตรงประเภทไหม, เหตุผล) — คืน None เมื่อ parse คำตอบไม่ได้ (นับแยก ไม่เดา)"""
        key = (wanted, product_title)
        if key in self._cache:
            return self._cache[key]

        raw = self._chat.chat(
            system=_SYSTEM,
            user=f"{_FEWSHOT}Shopper wants: {wanted}\nProduct: {product_title}\nReason:",
            temperature=0.0,
            num_predict=96,
        )
        match = _ANSWER_RE.search(raw)
        verdict = None if match is None else (match.group(1).lower() == "yes")
        if verdict is None:
            log.warning("parse คำตอบ judge ไม่ได้: %r", raw[:120])

        reason = raw.split("Answer:")[0].strip().replace("\n", " ")[:160]
        self._cache[key] = (verdict, reason)
        return verdict, reason
