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

# ⚠ นี่คือ prompt "v2" ซึ่งวัดแล้วดีที่สุดใน 4 แบบที่ลอง — อย่าแก้โดยไม่วัดซ้ำ
#    ประวัติการวัดบนชุด dev อยู่ใน eval/results/type_judge_validation.md
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

# few-shot ครอบความผิดพลาดที่ "วัดได้จริง" จากการ validate กับ ESCI แต่ละรอบ:
#   v1 ปฏิเสธของที่ตรงเป๊ะเพราะตัวมันเองเป็นอุปกรณ์เสริม (ปลอกคอสุนัข)
#   v2 ปฏิเสธเพราะสินค้าไม่มีคำขยายครบ (wig/mattress/tree) -> recall เหลือ 36%
#      คำว่า "head noun" ทำให้โมเดลไปหาข้อบกพร่องแทนที่จะจับคู่ประเภท จึงเลิกใช้คำนี้
#   ตัวอย่างด้านล่างจึงเน้น "ขาดคำขยายก็ยังใช่" และเพิ่มเคสคำค้นที่เป็นชื่อแบรนด์/คน
# ⚠ ตัวอย่างทั้งหมดด้านล่าง **แต่งขึ้นเอง** ไม่ได้คัดมาจากชุด gold (ESCI)
#    ถ้าเอาเคสจากชุดที่ใช้วัดมาใส่ = train on test set ค่า kappa จะสวยแบบหลอก ๆ
#    แต่ละตัวอย่างสะท้อน "รูปแบบ" ของความผิดพลาดที่วัดได้ ไม่ใช่ตัวเคสเอง
_FEWSHOT = """Shopper wants: wireless gaming mouse
Product: Kunsaww Cloud Star Pink Large Game Mouse Pad Non Slip Stitched Edges
Reason: a mouse pad is a surface you rest a mouse on, a different kind of thing.
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


# --------------------------------------------------------------------------- แบบสองคำถาม

_ACCESSORY_SYSTEM = (
    "A shopper searched an online store. You are told what they searched for and one "
    "product from the results. Answer ONE question: is the product an ACCESSORY rather "
    "than the item itself?\n"
    "Accessories include: straps, bands, cases, covers, screen protectors, boxes, bags "
    "to carry it in, stands, mounts, holders, chargers and cables for it, cleaners, "
    "sprays, refills, replacement parts, and kits of add-ons.\n"
    "Matching brand or model name does NOT matter — a strap for a Rolex is still a strap.\n"
    "Reply with one short reason line, then 'Answer: YES' (it is an accessory) or "
    "'Answer: NO' (it is the item itself, or something unrelated)."
)

_ACCESSORY_FEWSHOT = """Shopper searched: rolex submariner mens watch
Product: Leather Watch Strap 20mm Replacement Band Compatible with Rolex Submariner
Reason: a strap is worn with a watch.
Answer: YES

Shopper searched: king size memory foam mattress
Product: Serta 8 Inch Innerspring Coil Mattress, Twin
Reason: it is a mattress itself, not something used with one.
Answer: NO

Shopper searched: wireless gaming mouse
Product: Kunsaww Large Game Mouse Pad Non Slip Stitched Edges
Reason: a mouse pad is a surface used with a mouse.
Answer: YES

Shopper searched: stainless steel water bottle
Product: Contigo Autoseal Chill Stainless Steel Water Bottle, 24oz
Reason: it is a water bottle itself.
Answer: NO

"""

_KIND_SYSTEM = (
    "A shopper searched an online store. Ignore brand, colour, size, length, count, "
    "style, material and features entirely — shoppers expect those to vary. "
    "Answer ONE question: is the product the SAME KIND OF PRODUCT as what was searched "
    "for?\n"
    "Reply with one short reason line, then 'Answer: YES' or 'Answer: NO'."
)

_KIND_FEWSHOT = """Shopper searched: white slim christmas tree with lights
Product: National Tree Company Pre-Lit Artificial Full Christmas Tree, Green
Reason: both are christmas trees.
Answer: YES

Shopper searched: non-slip yoga mat
Product: CRZ YOGA Mens Comfy Lounge Pants Open Bottom Yoga Pajama Pants
Reason: trousers are not a mat.
Answer: NO

Shopper searched: curly brown hair extensions 20 inch
Product: Straight Synthetic Hair Extension Clip In, Jet Black, 14 Inches
Reason: both are hair extensions.
Answer: YES

Shopper searched: office stapler
Product: MINTLIMIT Womens Long Sleeve Notched Lapel Blazer with Pockets
Reason: a blazer is clothing, not a stapler.
Answer: NO

"""


class TwoStepProductTypeJudge:
    """ถามสองคำถามแยกกัน คำถามละงานเดียว แล้วรวมผลด้วยโค้ด

    เหตุผล: prompt เดียวที่ใส่ทั้งเกณฑ์ "อุปกรณ์เสริมไม่นับ" และ "คำขยายไม่สำคัญ"
    ทำให้โมเดล 8B เอียงไปข้างใดข้างหนึ่งเสมอ — วัดได้จริงจาก 3 รอบ (κ = 0.292 / 0.077 / 0.111)
    การแยกให้แต่ละคำถามมีเกณฑ์เดียว แล้วให้ **โค้ด** เป็นคนรวม (ไม่ใช่โมเดล)
    เป็นวิธีเดียวกับที่ mark4 ใช้ตอนทำ Generator แบบ hybrid แล้วได้ผล
    """

    def __init__(self, chat: OllamaChat | None = None):
        self._chat = chat or OllamaChat()
        self._cache: dict[tuple[str, str], tuple[bool | None, str]] = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._chat.close()

    def _ask(self, system: str, fewshot: str, wanted: str, title: str) -> tuple[bool | None, str]:
        raw = self._chat.chat(
            system=system,
            user=f"{fewshot}Shopper searched: {wanted}\nProduct: {title}\nReason:",
            temperature=0.0, num_predict=80,
        )
        match = _ANSWER_RE.search(raw)
        verdict = None if match is None else (match.group(1).lower() == "yes")
        return verdict, raw.split("Answer:")[0].strip().replace("\n", " ")[:90]

    def judge(self, wanted: str, product_title: str) -> tuple[bool | None, str]:
        key = (wanted, product_title)
        if key in self._cache:
            return self._cache[key]

        is_accessory, why_accessory = self._ask(
            _ACCESSORY_SYSTEM, _ACCESSORY_FEWSHOT, wanted, product_title)
        same_kind, why_kind = self._ask(
            _KIND_SYSTEM, _KIND_FEWSHOT, wanted, product_title)

        if is_accessory is None or same_kind is None:
            result = (None, f"parse ไม่ได้ | เสริม: {why_accessory} | ชนิด: {why_kind}")
        else:
            # โค้ดเป็นคนรวม: ต้อง "ไม่ใช่อุปกรณ์เสริม" และ "ชนิดเดียวกัน" จึงจะผ่าน
            result = (not is_accessory and same_kind,
                      f"อุปกรณ์เสริม={is_accessory} ({why_accessory}) | "
                      f"ชนิดเดียวกัน={same_kind} ({why_kind})")

        self._cache[key] = result
        return result
