# mark5 — Roadmap

ที่มาของกรอบ: คลิป **"Agentic AI Project End to End Roadmap: Real-Time LLMOps AI Project"**
โดย Rajeev Kanth | BEPEC (YouTube `t-E2VPVbp34`, เผยแพร่ 19 ก.ย. 2026, ความยาว ~12 นาที)
เป็นคลิป**ภาพรวม lifecycle** ไม่ใช่ code tutorial — ให้ลำดับด่าน 15 ด่าน ไม่ได้ให้โค้ด

เอกสารนี้แปลง 15 ด่านนั้นเป็นงานจริงของ mark5 (ระบบแนะนำสินค้าเชิงสนทนาภาษาไทย บนข้อมูล
Amazon Products 2023) พร้อมระบุว่าด่านไหน**ปรับ**และด่านไหน**ตัด** เพราะบริบทเราคือวิทยานิพนธ์
รันบนเครื่องเดียว ไม่ใช่ระบบ production ที่มีผู้ใช้จริง

---

## ตารางแปลง: 15 ด่านของคลิป → งานของ mark5

| # | ด่านในคลิป | เวลา | mark5 ทำอะไร | สถานะ |
|---|---|---|---|---|
| 1 | Agentic AI Project Lifecycle – Real-Time Overview | 00:00 | กรอบรวม — คือเอกสารนี้ | ✅ |
| 2 | POC vs Production-Level | 01:32 | ตัดสินระดับเป้าหมายของ mark5 ให้ชัดก่อนเขียนโค้ด | 🔲 |
| 3 | Business Objectives, Metrics, Cost, ROI | 02:12 | `docs/01_objectives.md` — นิยาม success metric **ก่อน** ลงมือ | ✅ ยืนยันแล้ว |
| 4 | Data Preparation & Vector DB Architecture | 02:50 | `src/mark5/data/` + `src/mark5/index/` — pipeline ใหม่ทั้งหมด | 🔲 |
| 5 | How to Select the Right LLM | 03:28 | `docs/03_llm_selection.md` — มีเกณฑ์วัดได้ ไม่ใช่ "ใช้ Typhoon เพราะเป็นไทย" | 🔲 |
| 6 | Prompt Engineering & Context Engineering | 04:28 | `src/mark5/prompts/` — prompt เป็นไฟล์ มีเวอร์ชัน ไม่ฝังใน .py | 🔲 |
| 7 | RAG Architecture, Databases, **AI Guardrails** | 05:15 | `src/mark5/retrieval/` + `src/mark5/guardrails/` | 🔲 |
| 8 | Agentic Orchestration: Single vs Multi-Agent | 06:02 | `docs/05_orchestration.md` | 🔲 |
| 9 | No-Code vs Python: n8n, LangGraph, CrewAI | 06:33 | `docs/adr/ADR-0001-agent-framework.md` — **ยังไม่ตัดสิน** | ⏸ รอตัดสิน |
| 10 | Fine-Tuning & Agent Evaluation | 07:24 | `eval/` 4 ชั้น (ไม่ทำ fine-tuning — เหตุผลใน ADR-0002) | 🔲 |
| 11 | How to Explain in Interviews | 08:23 | **ปรับ** → "อธิบายในเล่ม + สอบป้องกัน" `docs/` ทุกไฟล์คือวัตถุดิบบทที่ 3 | 🔲 |
| 12 | Production Deployment: CI/CD, Docker, Kubernetes | 09:01 | Docker + GitHub Actions เอา; **K8s ตัด** (เกินจำเป็น) | 🔲 |
| 13 | Agent Observability: LangSmith / LangFuse | 09:48 | Langfuse self-host (local, ฟรี, ไม่ส่งข้อมูลออก) | 🔲 |
| 14 | Continuous Monitoring, Feedback, Error Analysis | 10:39 | `eval/error_analysis/` — ตรงกับงานที่ mark4 ค้างไว้ | 🔲 |
| 15 | AI Governance, Security, Privacy, Compliance | 11:02 | `docs/07_governance.md` — license ข้อมูล, ไม่มี PII, ข้อจำกัดโมเดล | 🔲 |
| 16 | Agentic AI Engineer Job Lifecycle | 12:10 | **ตัด** — เป็นเนื้อหาสายอาชีพ ไม่ใช่งานโปรเจกต์ | ➖ |

---

## สิ่งที่ mark4 ขาด และ roadmap นี้บังคับให้มี

นี่คือเหตุผลหลักที่คุ้มจะรื้อทำใหม่ ไม่ใช่ patch mark4 ต่อ:

| ประเด็น | mark4 | mark5 (ตาม roadmap) |
|---|---|---|
| **นิยาม metric ก่อนเขียนโค้ด** | ไม่มี — สร้างระบบก่อน แล้วค่อยหาว่าจะวัดอะไร ทำให้ eval ออกมาแล้วเถียงกันเองว่าดีหรือไม่ดี | ด่าน 3 บังคับให้เขียน success metric + ค่าเป้าหมายลงเอกสารก่อน |
| **Guardrails** | ไม่มีชั้นนี้ — กฎกรองอยู่ปนใน `generate.py` (`audience_mismatch`) | ด่าน 7 แยกเป็นโมดูล — ตรงกับปัญหาใหญ่สุดของ mark4 คือ "ประเภทสินค้าผิด ~20-25%" |
| **Prompt versioning** | prompt ฝังใน `generate.py` แก้ 3 รอบ ทับของเก่า ย้อนดูไม่ได้ | ด่าน 6 prompt เป็นไฟล์ มีเวอร์ชัน เทียบผลข้ามเวอร์ชันได้ |
| **Observability** | ไม่มี — debug ด้วย print | ด่าน 13 Langfuse เห็น trace ทุก call ว่า agent ตัดสินใจอะไร |
| **Conversation state** | ไม่มี single-turn ล้วน | ด่าน 8 คือหัวใจของ mark5 |
| **Error analysis เป็นระบบ** | มี แต่ทำแบบอ่านมือ 73 ข้อครั้งเดียว | ด่าน 14 เป็น loop ที่รันซ้ำได้ |

---

## ลำดับการทำจริง (Phase)

roadmap ในคลิปเรียงตาม *ขั้นตอนความคิด* ไม่ใช่ *ลำดับลงมือ* — ด้านล่างคือลำดับลงมือจริงของเรา

### Phase 0 — ตั้งฐาน (ด่าน 2, 3, 5, 15)
เขียนเอกสารก่อนโค้ด ทั้ง 4 ด่านนี้ไม่ต้องแตะโค้ดเลย
- [ ] `docs/00_scope.md` — POC หรือ production-grade แค่ไหน ขอบเขตชัด
- [x] `docs/01_objectives.md` — success metric + ค่าเป้าหมาย + ต้นทุนที่ยอมรับได้
      ✅ **ยืนยันแล้ว 2026-09-28** — ไทยล้วน / product-type ≥90% / ไม่ตั้งเพดาน latency
      ✅ ปิดครบทุกข้อแล้ว — รวมถึง ADR-0004 (Chroma local อย่างเดียว ไม่ใช้ cloud)
- [ ] `docs/03_llm_selection.md` — เกณฑ์เลือก LLM + ผลทดสอบเทียบ
- [ ] `docs/07_governance.md` — license ข้อมูล, privacy, ข้อจำกัดที่ต้องประกาศ
- [ ] `git init` + commit แรก (mark4 ไม่เคยทำ — รอบนี้ทำตั้งแต่ต้น)

### Phase 1 — Data + Index (ด่าน 4)
- [x] `src/mark5/data/` — ingest → clean → feature (Medallion) + Pandera gate ทุกชั้น
      ✅ เสร็จ 2026-09-28 — 117,243 แถว, category ไม่ว่าง 100% (**ใช้ได้จริง 99.5%** —
      541 แถวได้ค่า "Unknown"), brand **99.8%**, embed_text **100%**, 33 unit test ผ่าน
      ⚠ `datasets` ของ HF ใช้ไม่ได้บนเครื่องนี้ (Application Control บล็อก DLL `pyarrow._dataset`)
      → โหลด `.arrow` ตรงแล้วอ่านด้วย `pyarrow.ipc` แทน
- [x] `src/mark5/index/` — embed + vector store abstraction
      ✅ เสร็จ 2026-09-29 — index เต็ม 117,243 รายการ ลง Chroma local ใน **52.7 นาที**
      (27 ms/doc, BGE-M3 ผ่าน Ollama, ดัชนี 2.0 GB) สร้างต่อจากจุดที่ค้างได้ถ้าถูกขัดจังหวะ
- [ ] ⚠ **อย่ารัน index เต็มจนกว่า `embed_text` จะล็อก** — รอบละ ~84 นาที (ไม่มีค่าใช้จ่ายแล้ว
      เพราะใช้ Chroma local แต่เสียเวลา)

### Phase 2 — Retrieval + Guardrails (ด่าน 7)
- [x] **Cross-lingual retrieval** — ✅ ตัดสินแล้ว (ADR-0005): แปลคำค้นเป็นอังกฤษก่อนค้น
      ทดลอง 3 รอบ เทียบ 6 กลยุทธ์ · **เพดานบนอยู่แค่ 70.4% → ปัญหาสินค้าผิดประเภท
      ส่วนใหญ่ไม่ใช่ปัญหาภาษา ต้องปิดช่องว่างด้วย guardrail**
- [x] Retriever (semantic + metadata filter) — `src/mark5/retrieval/retriever.py` 3 กลยุทธ์
- [ ] Reranker (RRF — ยกหลักการจาก mark4 ที่พิสูจน์แล้วว่าได้ผล เขียนใหม่ให้สะอาด)
- [ ] **Guardrails** — ตัวกรองประเภทสินค้า + audience + out-of-scope → แก้ปัญหาหลักของ mark4

### Phase 3 — Agent (ด่าน 6, 8, 9)
- [ ] ⏸ **ตัดสิน ADR-0001 ก่อน** — framework อะไร
- [ ] `src/mark5/prompts/` — prompt registry
- [ ] Memory / Planner / Tools / orchestration loop

### Phase 4 — Evaluation (ด่าน 10, 14)
- [ ] `eval/retrieval/` — nDCG, beyond-accuracy (เดิมเรียก quality-lift), judge validation (ESCI),
      **ชุดทดสอบ negative** สำหรับวัด negative rejection ตาม RGB (Chen et al., AAAI 2024)
      และ **คำค้นคู่ไทย-อังกฤษ 25 คู่** สำหรับวัด cross-lingual gap
- [ ] `eval/generation/` — groundedness, style checks
- [ ] `eval/agent/` — **ใหม่**: multi-turn (จำ context ได้ไหม, ถามกลับถูกจังหวะไหม)
- [ ] `eval/operational/` — latency, token cost
- [ ] `eval/error_analysis/` — จัดหมวดความผิดพลาด รันซ้ำได้

### Phase 5 — Observability + Deploy (ด่าน 12, 13)
- [ ] Langfuse self-host + instrument ทุก LLM call
- [ ] Dockerfile + docker-compose (app + Langfuse + Chroma)
- [ ] GitHub Actions: pytest + lint

### Phase 6 — เขียนเล่ม (ด่าน 11)
- [ ] `docs/` ทุกไฟล์ → บทที่ 3 (วิธีดำเนินการวิจัย)
- [ ] `eval/results/` ทุกรายงาน → บทที่ 4 (ผลการวิจัย)

---

## การตัดสินใจที่ยังค้าง

| ID | เรื่อง | สถานะ |
|---|---|---|
| ADR-0001 | Agent framework: pure Python / LangGraph / CrewAI / n8n | ⏸ **รอตัดสิน** — ดู `docs/adr/ADR-0001-agent-framework.md` |
| ADR-0002 | ทำ fine-tuning ไหม | 🔲 ยังไม่เขียน (เอนไปทาง "ไม่ทำ") |
| ADR-0003 | Single-agent หรือ multi-agent | 🔲 ยังไม่เขียน |
| ADR-0004 | Vector store | ✅ **ตัดสินแล้ว: Chroma local เท่านั้น ไม่ใช้ Chroma Cloud** |
| ADR-0005 | Cross-lingual retrieval | ✅ **ตัดสินแล้ว: แปลคำค้นเป็นอังกฤษก่อนค้น** (64.0% เทียบไทยล้วน 47.2%) RRF ถ่วงน้ำหนักลองแล้วไม่ช่วย |
