# ADR-0001 — เลือก framework สำหรับ Agent orchestration

- **สถานะ:** ⏸ เสนอ (ยังไม่ตัดสิน)
- **วันที่:** 2026-09-28
- **ด่านใน roadmap:** #9 — "No-Code vs Python: n8n, LangGraph and CrewAI" (06:33)

## บริบทที่ใช้ตัดสิน

1. นี่คือ**วิทยานิพนธ์** — ต้องอธิบายกลไกทุกส่วนในเล่มและตอบกรรมการได้
   (feedback อาจารย์รอบที่แล้ว: "Reranker ต้องมีเกณฑ์วัดได้จากงานวิจัย" → เขาขุดกลไก)
2. LLM รัน **local ผ่าน Ollama** (Typhoon2-8B) ไม่ใช่ OpenAI API
3. เครื่องพัฒนามี **Windows Application Control** ที่บล็อก DLL ของ `sklearn`/`scipy.stats`
   จน `import sentence_transformers` พังมาแล้วในโปรเจกต์ก่อน → dependency tree ใหญ่ = ความเสี่ยงจริง
4. ขนาดงาน: agent เดียว, tool ประมาณ 3-5 ตัว, multi-turn conversation

## ตัวเลือก

| | **pure Python** | **LangGraph** | **CrewAI** | **n8n (no-code)** |
|---|---|---|---|---|
| เขียนลงเล่มได้ | ★★★ อธิบายได้ทุกบรรทัด | ★★ ต้องอธิบายว่า framework ทำอะไรให้ | ★★ | ★ กรรมการจะถามว่า "แล้วคุณทำอะไร" |
| แรงที่ต้องลง | มาก (~300-500 บรรทัด: state, checkpoint, routing) | น้อย — `StateGraph` + checkpointer พร้อมใช้ | น้อย — abstraction ระดับ "ทีมงาน" | น้อยมาก |
| Multi-turn memory | ออกแบบเอง (จริง ๆ คือ dict + JSON/SQLite ไม่ยากเท่าที่กลัว) | ฟรี (`SqliteSaver`) | ฟรี | ฟรี |
| เสี่ยงชน Application Control | ★★★ แทบไม่เพิ่ม dependency | ⚠ ลาก `langchain-core` + deps ยาว | ⚠ หนักกว่า LangGraph | ➖ (คนละ runtime) |
| เข้ากับ Ollama local | ตรง ๆ ผ่าน HTTP | ได้ แต่ผ่าน adapter | ได้ แต่ adapter จู้จี้กว่า | ได้ |
| Debug ตอนพัง | เห็นตรง ๆ | อ่าน trace ของ framework | abstraction หนา เจาะยาก | UI ดูง่าย แต่ version control ยาก |
| เหมาะกับ multi-agent | ต้องเขียนเอง (แพง) | ★★★ | ★★★ ออกแบบมาเพื่อสิ่งนี้ | ★★ |
| ต่อ Langfuse (ด่าน 13) | เขียน wrapper เอง ~30 บรรทัด | มี integration สำเร็จ | มี integration | มี |

## ข้อเสนอ

**เลือก pure Python** ด้วยเหตุผล 3 ข้อ:

1. **ความเสี่ยงบนเครื่องนี้เป็นของจริง ไม่ใช่สมมุติ** — เคยโดน `sklearn` ถูกบล็อกจนต้องเปลี่ยนวิธี
   encode query มาแล้ว การลาก dependency tree ใหญ่เข้ามาตอนเริ่มโปรเจกต์คือเชิญปัญหาเดิมกลับมา
2. **เป็นวิทยานิพนธ์** — คำตอบว่า "LangGraph จัดการ state ให้" เป็นคำตอบที่อ่อนในห้องสอบ
3. **สิ่งที่ LangGraph ให้จริง ๆ คือ checkpointer + graph routing** — ในสเกลนี้ (agent เดียว,
   tool 3-5 ตัว) เขียนเองประมาณ 200-300 บรรทัด และคุมได้เต็ม

**จะกลับมาเลือก LangGraph ถ้า** ขอบเขตขยายเป็น multi-agent หลายตัวคุยกัน, human-in-the-loop,
หรือต้องการ time-travel debugging — สามอย่างนี้เขียนเองแพงจริง

**ไม่เลือก n8n** — version control ไม่ได้ (workflow เป็น JSON ใน UI) และเขียนลงเล่มลำบาก

## ผลกระทบถ้าเลือกตามข้อเสนอ

- ต้องเขียนเองเพิ่ม: conversation state store, tool dispatch loop, checkpoint/resume
- `requirements.txt` เพิ่มแค่ `httpx` (คุยกับ Ollama) — ไม่มี dependency ใหม่ที่เสี่ยง
- Langfuse ต้องเขียน wrapper เอง (ประมาณ 30 บรรทัด — ใช้ SDK ตรง ๆ ได้)

---

**ยังไม่ตัดสิน — รอผู้ใช้เคาะ**
