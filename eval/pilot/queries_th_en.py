"""คำค้นคู่ไทย-อังกฤษ 25 คู่ สำหรับวัด cross-lingual gap

หลักการเลือก:
  - แต่ละคู่ต้อง **มีความหมายเดียวกัน** ฝั่งไทยเขียนแบบที่ผู้ใช้ไทยพิมพ์จริง
    (ไม่ใช่แปลตรงตัวจากอังกฤษแบบแข็ง ๆ)
  - กระจายให้ครอบคลุมหมวดที่มีสินค้าเยอะในชุดข้อมูลจริง (แฟชั่น, บ้าน, เครื่องมือ, ยานยนต์,
    มือถือ, กีฬา, สุขภาพ, ออฟฟิศ, คอมพิวเตอร์, สัตว์เลี้ยง, กล้อง)
  - มีทั้งคำค้นกว้าง ("เสื้อยืดผ้าฝ้ายสีดำ") และคำค้นที่มีสเปกเจาะจง ("สายชาร์จ USB-C ยาว 2 เมตร")
    เพราะโมเดล multilingual มักพลาดกับตัวเลข/หน่วย/ชื่อมาตรฐานทางเทคนิคมากกว่าคำทั่วไป
"""

QUERY_PAIRS: list[dict[str, str]] = [
    {"id": "q01", "th": "หูฟังบลูทูธไร้สายกันน้ำ", "en": "waterproof wireless bluetooth headphones"},
    {"id": "q02", "th": "เคสมือถือกันกระแทก", "en": "shockproof phone case"},
    {"id": "q03", "th": "สายชาร์จ USB-C ยาว 2 เมตร", "en": "2 meter USB-C charging cable"},
    {"id": "q04", "th": "รองเท้าวิ่งผู้ชายน้ำหนักเบา", "en": "lightweight running shoes for men"},
    {"id": "q05", "th": "กระเป๋าสะพายข้างหนังแท้", "en": "genuine leather crossbody bag"},
    {"id": "q06", "th": "เสื้อยืดผ้าฝ้ายสีดำ", "en": "black cotton t-shirt"},
    {"id": "q07", "th": "หมอนหนุนเมมโมรี่โฟม", "en": "memory foam pillow"},
    {"id": "q08", "th": "ผ้าม่านกันแสงสำหรับห้องนอน", "en": "blackout curtains for bedroom"},
    {"id": "q09", "th": "กระทะเหล็กหล่อ", "en": "cast iron skillet"},
    {"id": "q10", "th": "เครื่องชงกาแฟแบบดริป", "en": "drip coffee maker"},
    {"id": "q11", "th": "ชุดไขควงอเนกประสงค์", "en": "multipurpose screwdriver set"},
    {"id": "q12", "th": "สว่านไร้สายแบบใช้แบตเตอรี่", "en": "cordless battery powered drill"},
    {"id": "q13", "th": "ที่ชาร์จในรถยนต์แบบ 2 ช่อง", "en": "dual port car charger"},
    {"id": "q14", "th": "ใบปัดน้ำฝนรถยนต์", "en": "car windshield wiper blades"},
    {"id": "q15", "th": "เสื่อโยคะกันลื่น", "en": "non-slip yoga mat"},
    {"id": "q16", "th": "ดัมเบลปรับน้ำหนักได้", "en": "adjustable dumbbell weights"},
    {"id": "q17", "th": "อาหารเสริมวิตามินซี", "en": "vitamin C supplement"},
    {"id": "q18", "th": "แปรงสีฟันไฟฟ้า", "en": "electric toothbrush"},
    {"id": "q19", "th": "ปากกาเจลสีน้ำเงิน", "en": "blue gel ink pen"},
    {"id": "q20", "th": "เครื่องเย็บกระดาษสำหรับสำนักงาน", "en": "office stapler"},
    {"id": "q21", "th": "เมาส์ไร้สายสำหรับเล่นเกม", "en": "wireless gaming mouse"},
    {"id": "q22", "th": "คีย์บอร์ดเมคานิคอล", "en": "mechanical keyboard"},
    {"id": "q23", "th": "ปลอกคอสุนัขปรับขนาดได้", "en": "adjustable dog collar"},
    {"id": "q24", "th": "ทรายแมวไร้ฝุ่น", "en": "dust free cat litter"},
    {"id": "q25", "th": "ขาตั้งกล้องสามขา", "en": "camera tripod stand"},
]
