# mark5 — ระบบแนะนำสินค้าเชิงสนทนา (Agentic RAG)

สร้างใหม่จากศูนย์แทน [mark4](../mark4) โดยเดินตาม **lifecycle 15 ด่าน** ของคลิป
["Agentic AI Project End to End Roadmap: Real-Time LLMOps AI Project"](https://www.youtube.com/watch?v=t-E2VPVbp34)
(Rajeev Kanth | BEPEC) — รายละเอียดการแปลง roadmap เป็นงานจริงอยู่ที่ [`docs/roadmap.md`](docs/roadmap.md)

**ต่างจาก mark4 อย่างไร:** เป้าหมายและข้อมูลเหมือนเดิม (แนะนำสินค้า Amazon ด้วยภาษาไทย)
แต่ทำ **อย่างเป็นระบบมากขึ้น** — นิยาม metric ก่อนเขียนโค้ด, แยกชั้น guardrails ออกมา,
prompt มีเวอร์ชัน, มี observability, และเพิ่ม **Conversational Agent (multi-turn)** ที่ mark4 ไม่มี

> **สถานะ: Phase 1 เสร็จ · Phase 2 กำลังทำ**
> `docs/01_objectives.md` ยืนยันแล้ว · pipeline raw→clean→feature ผ่าน quality gate ทั้ง 3 ชั้น ·
> **ดัชนีเวกเตอร์ครบ 117,243 รายการบน Chroma local** (52.7 นาที) · Retriever ค้นได้ 3 กลยุทธ์ ·
> 47 unit test ผ่าน · ค้างที่ ADR-0005 (cross-lingual) ซึ่งกำลังรันการทดลองเทียบอยู่

## ผลของ data pipeline (2026-09-28)

| ชั้น | ไฟล์ | ขนาด | หมายเหตุ |
|---|---|---|---|
| raw | `data/raw/products_raw.parquet` | 1,504 MB | เก็บตามที่ได้รับ 16 คอลัมน์ + `manifest.json` (sha256, revision) |
| clean | `data/clean/products_clean.parquet` | 129 MB | ตัด `embeddings` (1,374 MB) ออก — ดูเหตุผลใน `clean.py` |
| feature | `data/feature/products_feature.parquet` | 165 MB | 24 คอลัมน์ พร้อม embed |

| feature | coverage | ที่มา |
|---|---|---|
| `category` | ไม่ว่าง 100% / **ใช้ได้จริง 99.5%** | กู้ 3 ชั้น: `main_category` 78.8% → `categories[0]` 20.7% → ชื่อไฟล์ต้นทาง 0.5% ⚠ ชั้นที่ 3 ได้ค่า `"Unknown"` ทั้ง 541 แถว (ไฟล์ต้นทางชื่อ `meta_Unknown`) — guardrail กรองตามหมวดไม่ได้ |
| `brand` | **99.8%** | `details` 84.5% → `store` 15.3% (บันทึก provenance ไว้ใน `brand_source`) |
| `popularity` | 100% | Bayesian weighted rating (C=4.0673, m=30) |
| `embed_text` | 100% | title + features + description + details (ตัดที่ 2,000 ตัวอักษร) |
| `weight_g` / `best_sellers_rank` / `color` / `material` | 43.3% / 44.0% / 34.9% / 26.3% | สกัดจาก `details` เท่านั้น ไม่เดาจากข้อความ |
| `value_score` / `price_tier` | 69.3% | จำกัดด้วย price ที่หาย 30.7% |

## สถาปัตยกรรมเป้าหมาย

```
                        ┌─────────────── Observability (Langfuse) ───────────────┐
                        │                                                         │
  ผู้ใช้ ──▶ Agent Loop ──▶ Planner ──▶ Tools ──▶ Retriever ──▶ Reranker ──▶ Guardrails ──▶ Generator ──▶ คำตอบ
             │   ▲                                    │
             ▼   │                                    ▼
          Memory ┘                            Vector Store (Chroma)
       (conversation state)                          ▲
                                                     │
                     raw ──▶ clean ──▶ feature ──▶ embed
                          (Medallion + Pandera gate)
```

## โครงสร้างโฟลเดอร์

```
docs/                 เอกสารออกแบบ — วัตถุดิบบทที่ 3 ของเล่ม
  roadmap.md            แปลง 15 ด่านของคลิปเป็นงานจริง + ลำดับ Phase
  adr/                  Architecture Decision Record (เหตุผลของทุกการตัดสินใจ)
config/               ค่าตั้งทั้งหมดรวมที่เดียว (settings.py + config.yaml)
src/mark5/
  common/               logger, exception — ใช้ร่วมทุกโมดูล
  data/                 ingest → clean → feature (Medallion) + Pandera gate
  index/                embedding + vector store
  retrieval/            Retriever + Reranker
  guardrails/           ตัวกรองก่อน/หลัง generate (ของใหม่ที่ mark4 ไม่มี)
  prompts/              prompt เป็นไฟล์ มีเวอร์ชัน
  agent/                memory, planner, tools, orchestration loop
  generation/           ประกอบคำตอบภาษาไทย
eval/                 การประเมิน 5 ชั้น — retrieval / generation / agent / operational / error_analysis
tests/                unit test (pytest)
app/                  FastAPI + UI
deploy/               Dockerfile, docker-compose, CI
```

## เริ่มใช้งาน

```powershell
cd E:\work\teach\mark5
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env    # แล้วใส่ค่าจริง

$env:PYTHONPATH = ".;src"
python -m mark5.data.pipeline     # raw -> clean -> feature (--force เพื่อสร้างใหม่)
python -m pytest tests/ -q        # 33 tests
```

## ข้อควรระวังที่ยกมาจาก mark4 (อย่าเจอซ้ำ)

- **อย่ารัน index เต็มจนกว่า `embed_text` จะล็อก** — รอบละ ~84 นาที (วัดจริง 41-43 ms/doc)
  แก้ feature แล้วต้อง rebuild + re-index ทีเดียว ไม่ทำทีละนิด
- **ใช้ Chroma local เท่านั้น ไม่ใช้ Chroma Cloud** ([ADR-0004](docs/adr/ADR-0004-vector-store.md))
  → ต้นทุนโปรเจกต์ $0, ไม่ต้องมี API key, ข้อมูลไม่ออกนอกเครื่อง
  แลกกับการที่ต้องคัดลอกโฟลเดอร์ `data/embed/chroma/` เองถ้าจะแชร์ดัชนีให้คนอื่น
- **Windows Application Control บนเครื่องนี้บล็อก DLL ของ `sklearn`/`scipy.stats`** →
  `import sentence_transformers` พัง ต้องใช้ Ollama `bge-m3` encode แทน หรือให้ผู้ใช้ allowlist ก่อน
- **Ollama server ต้องสตาร์ตเองทุกเซสชัน** (`ollama.exe serve`)
- **เก็บ `details_json` เป็น JSON string ไม่ใช่ dict** — เก็บ dict ลง parquet แล้ว pyarrow พัง
  (`ArrayMemoryError`) เพราะแต่ละแถวมี key ไม่เหมือนกัน
