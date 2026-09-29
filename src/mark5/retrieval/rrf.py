"""Reciprocal Rank Fusion (RRF) — รวมหลายรายการอันดับเป็นรายการเดียว

อ้างอิง: Cormack, G. V., Clarke, C. L. A., & Büttcher, S. (2009).
*Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods*. SIGIR '09
สูตร: `score(d) = Σ_i 1 / (k + rank_i(d))` โดย k = 60 ตามบทความต้นฉบับ

**ทำไม RRF เหมาะกับงานนี้:** ใช้แค่ "อันดับ" ไม่ใช้ "คะแนนดิบ" จึงรวมสัญญาณที่มีหน่วยต่างกัน
ได้โดยไม่ต้อง normalize หรือกำหนดน้ำหนักเอง — ซึ่งสำคัญมากเพราะคะแนน cosine ของคำค้นไทย
ต่ำกว่าของอังกฤษอย่างเป็นระบบ (~0.045 วัดจาก `eval/results/crosslingual_pilot.md`)
ถ้ารวมด้วยคะแนนดิบ ฝั่งไทยจะเสียเปรียบโดยอัตโนมัติทั้งที่อันดับอาจถูกต้อง

**การจัดการเอกสารที่ไม่ปรากฏในบางรายการ:** ไม่บวกเทอมของรายการนั้นเลย (ไม่ใช่ให้อันดับท้ายสุด)
เอกสารที่ทุกรายการเห็นตรงกันจึงได้เปรียบโดยธรรมชาติ ซึ่งเป็นพฤติกรรมที่ต้องการ
"""

from __future__ import annotations

RRF_K = 60


def fuse(rankings: list[list[str]], k: int = RRF_K,
         weights: list[float] | None = None) -> list[tuple[str, float]]:
    """รวมรายการอันดับหลายชุดเป็นชุดเดียว เรียงจากคะแนนมากไปน้อย

    Args:
        rankings: รายการของ "ลำดับ id" แต่ละชุดเรียงจากดีที่สุดไปแย่ที่สุด
        k: ค่าคงที่ของสูตร (60 ตามบทความต้นฉบับ)
        weights: น้ำหนักของแต่ละรายการ (ไม่ใส่ = เท่ากันหมด)

    Returns:
        [(id, คะแนน), ...] เรียงจากคะแนนมากไปน้อย
    """
    if weights is None:
        weights = [1.0] * len(rankings)
    if len(weights) != len(rankings):
        raise ValueError(f"มี ranking {len(rankings)} ชุด แต่ weight {len(weights)} ค่า")

    scores: dict[str, float] = {}
    for ranking, weight in zip(rankings, weights, strict=True):
        for position, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + weight / (k + position)

    # เรียงตามคะแนน แล้วตามด้วย id เพื่อให้ผลลัพธ์คงที่เมื่อคะแนนเท่ากัน (ทำซ้ำได้)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
