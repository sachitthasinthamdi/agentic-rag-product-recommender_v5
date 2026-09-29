"""ด่าน 4 — Embedding + Vector store

    embedder.py   เรียก BGE-M3 ผ่าน Ollama HTTP API (ไม่ใช้ sentence_transformers
                  เพราะลาก sklearn มาด้วย ซึ่งถูก Application Control บล็อกบนเครื่องนี้)

ยังไม่มี: vector_store.py, build_index.py — Phase 2

**ตัวเลขที่วัดจากเครื่องนี้ (2026-09-28):** BGE-M3 ผ่าน Ollama คืนเวกเตอร์ 1,024 มิติ
ที่ normalize มาแล้ว · throughput ~43 ms/doc บนข้อความจริง (batch=32)
→ embed ทั้งชุด 117,243 รายการประมาณ **84 นาที**

⚠ อย่ารัน build_index เต็มจนกว่า `embed_text` จะล็อก และ ADR-0005 (cross-lingual) จะได้ข้อสรุป
"""
