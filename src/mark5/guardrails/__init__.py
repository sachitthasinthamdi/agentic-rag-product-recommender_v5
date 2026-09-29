"""ด่าน 7 — AI Guardrails: ชั้นตรวจก่อนตอบ ที่ mark4 ไม่มี

แก้ปัญหา 2 อย่างที่วัดได้จริงใน mark4:
  1. เสนอสินค้าผิดประเภท (แผ่นรองเมาส์เมื่อถามหาเมาส์) — `category_guard`
  2. ไม่เคยตอบ "ไม่พบ" เลยสักครั้ง 0/25 — `score_guard` (negative rejection ตาม RGB)

**ทำไมชั้นนี้ไม่ใช้ LLM:** ตรวจสอบแล้วว่า LLM judge บนเครื่องนี้เชื่อถือไม่ได้
(Cohen's κ = 0.246 ดู `docs/02_judge_reliability.md`) ถ้า guardrail ใช้ LLM ตัดสิน
จะเกิดปัญหาสองชั้นซ้อนกัน: ตัดสินพลาดเอง **และ** วัดผลไม่ได้เพราะจะต้องวัดด้วยเกณฑ์ตัวเอง
ชั้นนี้จึงใช้เฉพาะตัวเลขและ metadata ที่คำนวณตรวจสอบย้อนกลับได้ทั้งหมด

ข้อแลกเปลี่ยนที่รับไว้: กรองได้หยาบกว่า LLM แน่นอน — จากการวิเคราะห์ ของที่ผิดประเภท 67%
อยู่หมวดเดียวกับของที่ถูก ซึ่งชั้นนี้แตะไม่ได้ **เป็นฐานที่วัดผลได้ ไม่ใช่คำตอบสุดท้าย**
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mark5.common.logger import get_logger
from mark5.guardrails import category_guard, score_guard

log = get_logger(__name__)


@dataclass
class GuardedResult:
    """ผลลัพธ์หลังผ่านชั้น guardrails — เก็บร่องรอยการตัดสินไว้ให้ตรวจย้อนหลังได้ครบ"""
    hits: list                                   # รายการที่ผ่านทั้งหมดแล้ว (อาจว่าง)
    rejected: bool                               # ควรตอบ "ไม่พบสินค้าที่ตรง" หรือไม่
    reason: str
    dropped_by_category: list = field(default_factory=list)
    consensus_category: str | None = None
    consensus_share: float = 0.0
    category_filter_applied: bool = False
    top1_score: float = 0.0
    mean_top5_score: float = 0.0

    @property
    def n_dropped(self) -> int:
        return len(self.dropped_by_category)


def apply(pool: list, n: int = 5,
          min_top1: float = score_guard.DEFAULT_MIN_TOP1,
          min_mean5: float = score_guard.DEFAULT_MIN_MEAN5,
          min_category_share: float = category_guard.DEFAULT_MIN_CATEGORY_SHARE) -> GuardedResult:
    """ตรวจผลการค้นแล้วคืนรายการที่ปลอดภัยพอจะเสนอ

    Args:
        pool: ผลการค้นทั้งหมดที่ดึงมา (ควรกว้างกว่า n เช่น 30) เรียงจากดีที่สุด
        n: จำนวนที่ต้องการแสดงจริง

    ลำดับการตรวจ — **ปฏิเสธทั้งคำค้นก่อน แล้วค่อยกรองรายชิ้น**
    เพราะถ้าทั้งคำค้นไม่มีของตรงอยู่แล้ว การไปกรองรายชิ้นก็ไม่มีความหมาย
    """
    decision = score_guard.evaluate([h.score for h in pool], min_top1, min_mean5)
    if decision.rejected:
        return GuardedResult(hits=[], rejected=True, reason=decision.reason,
                             top1_score=decision.top1, mean_top5_score=decision.mean_top5)

    category = category_guard.apply(pool[:n], pool=pool, min_share=min_category_share)

    # กรองจนไม่เหลืออะไรเลย -> **ถอยกลับไปใช้ผลที่ยังไม่กรอง** ไม่ปฏิเสธคำค้น
    # บทเรียนจากรอบแรก: q01 "หูฟังบลูทูธ" คะแนน 0.731 ถูกปฏิเสธทั้งคำค้น เพราะหมวดพี่น้อง
    # ที่ชื่อต่างกัน (Electronics vs All Electronics) การปฏิเสธเป็นหน้าที่ของคะแนนเท่านั้น
    if category.applied and not category.kept:
        log.warning("ตัวกรองหมวดตัดจนไม่เหลือ — ถอยกลับไปใช้ผลที่ยังไม่กรอง")
        return GuardedResult(
            hits=list(pool[:n]), rejected=False,
            reason="ตัวกรองหมวดตัดจนหมด จึงถอยกลับไปใช้ผลที่ยังไม่กรอง",
            consensus_category=category.consensus_category,
            consensus_share=category.consensus_share, category_filter_applied=False,
            top1_score=decision.top1, mean_top5_score=decision.mean_top5)

    return GuardedResult(
        hits=category.kept, rejected=False, reason="ผ่านทุกด่าน",
        dropped_by_category=category.dropped,
        consensus_category=category.consensus_category,
        consensus_share=category.consensus_share,
        category_filter_applied=category.applied,
        top1_score=decision.top1, mean_top5_score=decision.mean_top5)
