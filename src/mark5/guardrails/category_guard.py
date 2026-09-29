"""กรองสินค้าที่อยู่คนละหมวดกับ "หมวดที่ผลการค้นเห็นพ้องกัน" ออก

**แนวคิด:** ไม่ต้องรู้ล่วงหน้าว่าคำค้นควรอยู่หมวดอะไร (ซึ่งต้องใช้ LLM หรือตารางที่เขียนมือ)
แต่ให้ **ผลการค้นโหวตกันเอง** — ดึงผู้สมัครมามากกว่าที่จะแสดง แล้วดูว่าหมวดไหนครองเสียง
สินค้าที่หลุดออกนอกหมวดนั้นมักเป็นของที่ค้นมาผิดประเภท

อ้างอิงแนวคิด: *cluster hypothesis* ในงาน IR — เอกสารที่เกี่ยวข้องกับคำค้นเดียวกัน
มักคล้ายกันเอง (van Rijsbergen 1979)

**⚠ บทเรียนจากรอบแรก — ทำไมไม่บังคับ "หมวดเดียว":**
รอบแรกออกแบบให้เก็บเฉพาะหมวดที่ครองเสียงมากสุด แล้วทดสอบพบว่า q01 "หูฟังบลูทูธไร้สายกันน้ำ"
ถูกตัดทิ้งทั้งหมด ทั้งที่คะแนนดีมาก (0.731) เพราะ 5 อันดับแรกอยู่ `Cell Phones & Accessories`
กับ `Electronics` ขณะที่ฉันทามติของกลุ่มผู้สมัครคือ `All Electronics`
— **ข้อมูลมีหมวดที่ความหมายทับกันหลายชื่อ** การบังคับหมวดเดียวจึงฆ่าของที่ถูก

จึงเปลี่ยนเป็น: **ตัดเฉพาะของที่มาจากหมวดซึ่งโผล่น้อยผิดปกติในกลุ่มผู้สมัคร**
เป็นการตัด "ของหลงมา" ไม่ใช่การบังคับให้ทุกชิ้นอยู่หมวดเดียวกัน วิธีนี้ทนต่อหมวดพี่น้อง
ที่ชื่อต่างกันโดยไม่ต้องเขียนตารางจับคู่หมวดด้วยมือ (ซึ่งจะกลายเป็นการตัดสินใจที่ตรวจสอบยาก)

**ข้อจำกัดที่วัดได้จริง (ต้องรู้ก่อนคาดหวัง):**
1. จากการวิเคราะห์ของที่ผิดประเภท **67% อยู่หมวดเดียวกับของที่ถูก** (เช่น ถามหากระทะเหล็กหล่อ
   แล้วได้น้ำยาล้างกระทะ ซึ่งอยู่ Amazon Home เหมือนกัน) → ตัวกรองนี้แตะได้แค่ 33% ที่เหลือ
2. หมวดในข้อมูลหยาบมาก (61 ค่า, `AMAZON FASHION` กินไปเอง 31%) การกรองด้วยหมวดจึงหยาบตาม
3. มี 541 แถว (0.46%) ที่หมวดเป็น `"Unknown"` ตรง ๆ — **ปล่อยผ่านเสมอ ไม่ตัดทิ้ง**
   เพราะ "ไม่รู้หมวด" ไม่เท่ากับ "หมวดผิด" การตัดทิ้งคือการลงโทษข้อมูลที่ขาด
4. **ชั้นนี้ไม่มีสิทธิ์ปฏิเสธทั้งคำค้น** — การปฏิเสธเป็นหน้าที่ของ `score_guard` เท่านั้น
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

UNKNOWN_CATEGORY = "Unknown"

# หมวดที่กินสัดส่วนในกลุ่มผู้สมัครน้อยกว่านี้ ถือว่า "หลงมา" -> ตัดทิ้ง
# ตั้งไว้ต่ำโดยตั้งใจ: เป้าหมายคือตัดของแปลกปลอม ไม่ใช่บังคับให้ทุกชิ้นอยู่หมวดเดียวกัน
DEFAULT_MIN_CATEGORY_SHARE = 0.10

# ถ้ากลุ่มผู้สมัครเล็กกว่านี้ สัดส่วนจะผันผวนเกินกว่าจะเชื่อถือได้ -> ไม่กรอง
MIN_POOL_SIZE = 10


@dataclass
class CategoryDecision:
    kept: list                    # รายการที่ผ่าน
    dropped: list                 # รายการที่ถูกตัด
    accepted_categories: set      # หมวดที่ถือว่าอยู่ในกลุ่มหลัก
    consensus_category: str | None
    consensus_share: float
    applied: bool                 # ได้กรองจริงไหม


def category_shares(categories: list[str]) -> dict[str, float]:
    """สัดส่วนของแต่ละหมวดในกลุ่มผู้สมัคร

    ไม่นับ `Unknown` เพราะไม่ใช่หมวดจริง ถ้านับจะไปเจือจางสัดส่วนของหมวดที่ถูกต้อง
    """
    usable = [c for c in categories if c and c != UNKNOWN_CATEGORY]
    if not usable:
        return {}
    counts = Counter(usable)
    return {category: count / len(usable) for category, count in counts.items()}


def consensus(categories: list[str]) -> tuple[str | None, float]:
    """หมวดที่ครองเสียงมากสุด พร้อมสัดส่วน — ใช้รายงานเท่านั้น ไม่ได้ใช้กรอง"""
    shares = category_shares(categories)
    if not shares:
        return None, 0.0
    category = max(shares, key=lambda c: (shares[c], c))
    return category, shares[category]


def apply(hits: list, pool: list | None = None,
          min_share: float = DEFAULT_MIN_CATEGORY_SHARE) -> CategoryDecision:
    """ตัดสินค้าที่มาจากหมวดซึ่งโผล่น้อยผิดปกติในกลุ่มผู้สมัคร

    Args:
        hits: รายการที่จะแสดงจริง (เช่น top-5)
        pool: กลุ่มผู้สมัครที่ใช้ประเมินสัดส่วน — ควรกว้างกว่า `hits` (เช่น top-30)
              ถ้าไม่ส่งมาจะใช้ `hits` เอง
    """
    voters = pool if pool else hits
    shares = category_shares([h.category for h in voters])
    top_category, top_share = consensus([h.category for h in voters])

    if len(voters) < MIN_POOL_SIZE or not shares:
        return CategoryDecision(list(hits), [], set(), top_category, top_share, applied=False)

    accepted = {category for category, share in shares.items() if share >= min_share}
    if not accepted:
        return CategoryDecision(list(hits), [], set(), top_category, top_share, applied=False)

    kept, dropped = [], []
    for hit in hits:
        # ปล่อยผ่านหมวดในกลุ่มหลัก และของที่ไม่รู้หมวด (ไม่ลงโทษข้อมูลที่ขาด)
        if (not hit.category or hit.category == UNKNOWN_CATEGORY
                or hit.category in accepted):
            kept.append(hit)
        else:
            dropped.append(hit)

    return CategoryDecision(kept, dropped, accepted, top_category, top_share, applied=True)
