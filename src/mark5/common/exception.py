"""Exception เฉพาะของ mark5

เหตุผลที่มี: แยกได้ว่าพังเพราะ "ข้อมูลไม่ผ่าน quality gate" หรือ "Ollama ไม่ตอบ"
โดยไม่ต้องอ่าน traceback ทั้งก้อน — และ except ได้ตรงจุดโดยไม่กลืน error อื่น
"""


class Mark5Error(Exception):
    """ฐานของทุก error ในโปรเจกต์"""


class ConfigError(Mark5Error):
    """ค่าตั้งขาดหายหรือไม่ถูกต้อง (เช่น ชี้ path ที่ไม่มีอยู่ หรือค่าใน .env ผิดรูปแบบ)"""


class DataValidationError(Mark5Error):
    """ข้อมูลไม่ผ่าน quality gate ของชั้นนั้น (Pandera)"""


class LLMError(Mark5Error):
    """เรียก LLM ไม่สำเร็จ — server ไม่ตอบ, timeout, หรือรูปแบบผลลัพธ์ผิด"""


class RetrievalError(Mark5Error):
    """ค้นจาก vector store ไม่สำเร็จ"""


class GuardrailViolation(Mark5Error):
    """ผลลัพธ์ไม่ผ่านเกณฑ์ guardrails — ไม่ใช่บั๊ก แต่เป็นการปฏิเสธโดยตั้งใจ"""
