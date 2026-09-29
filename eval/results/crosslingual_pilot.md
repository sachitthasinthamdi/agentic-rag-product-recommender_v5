# การทดลองนำร่อง: Cross-lingual retrieval (คำค้นไทย → คลังสินค้าอังกฤษ)

BGE-M3 ผ่าน Ollama · ตัวอย่าง 5,018 รายการ (สุ่มตามสัดส่วนหมวด) · คำค้น 25 คู่ · top-10

> **ตัวชี้วัดนี้วัด _ความสอดคล้อง_ ไม่ใช่ _ความถูกต้อง_** — ถ้าฝั่งอังกฤษค้นผิดอยู่แล้ว
> overlap สูงก็แปลว่าผิดเหมือนกันทั้งสองภาษา ต้องอ่านตารางท้ายรายงานประกอบเสมอ

## ผลรวม

| ตัวชี้วัด | ค่า |
|---|---|
| overlap@5 (ผลไทย ∩ ผลอังกฤษ) | **54.4%** |
| overlap@10 | **49.2%** |
| อันดับ 1 ของอังกฤษ ติด top-10 ของไทย | 92.0% |
| อันดับ 1 ของไทย ติด top-10 ของอังกฤษ | 80.0% |
| cosine เฉลี่ย top-5 (ไทย) | 0.5727 |
| cosine เฉลี่ย top-5 (อังกฤษ) | 0.6161 |
| cosine ระหว่างคำค้นไทยกับอังกฤษที่คู่กัน | 0.7425 |

## รายคำค้น

| id | คำค้นไทย | overlap@5 | overlap@10 | cosine ไทย | cosine อังกฤษ |
|---|---|---|---|---|---|
| q01 | หูฟังบลูทูธไร้สายกันน้ำ | 80% | 80% | 0.647 | 0.670 |
| q02 | เคสมือถือกันกระแทก | 80% | 50% | 0.640 | 0.661 |
| q03 | สายชาร์จ USB-C ยาว 2 เมตร | 80% | 90% | 0.641 | 0.677 |
| q04 | รองเท้าวิ่งผู้ชายน้ำหนักเบา | 60% | 80% | 0.590 | 0.621 |
| q05 | กระเป๋าสะพายข้างหนังแท้ | 20% | 40% | 0.591 | 0.665 |
| q06 | เสื้อยืดผ้าฝ้ายสีดำ | 0% | 0% | 0.538 | 0.605 |
| q07 | หมอนหนุนเมมโมรี่โฟม | 40% | 50% | 0.533 | 0.591 |
| q08 | ผ้าม่านกันแสงสำหรับห้องนอน | 60% | 50% | 0.567 | 0.659 |
| q09 | กระทะเหล็กหล่อ | 40% | 30% | 0.472 | 0.552 |
| q10 | เครื่องชงกาแฟแบบดริป | 100% | 70% | 0.562 | 0.596 |
| q11 | ชุดไขควงอเนกประสงค์ | 20% | 20% | 0.525 | 0.623 |
| q12 | สว่านไร้สายแบบใช้แบตเตอรี่ | 40% | 40% | 0.547 | 0.552 |
| q13 | ที่ชาร์จในรถยนต์แบบ 2 ช่อง | 60% | 60% | 0.568 | 0.610 |
| q14 | ใบปัดน้ำฝนรถยนต์ | 20% | 40% | 0.579 | 0.623 |
| q15 | เสื่อโยคะกันลื่น | 20% | 10% | 0.563 | 0.634 |
| q16 | ดัมเบลปรับน้ำหนักได้ | 100% | 70% | 0.612 | 0.659 |
| q17 | อาหารเสริมวิตามินซี | 80% | 50% | 0.571 | 0.595 |
| q18 | แปรงสีฟันไฟฟ้า | 100% | 70% | 0.604 | 0.646 |
| q19 | ปากกาเจลสีน้ำเงิน | 80% | 50% | 0.548 | 0.606 |
| q20 | เครื่องเย็บกระดาษสำหรับสำนักงาน | 60% | 30% | 0.576 | 0.576 |
| q21 | เมาส์ไร้สายสำหรับเล่นเกม | 80% | 70% | 0.616 | 0.633 |
| q22 | คีย์บอร์ดเมคานิคอล | 60% | 50% | 0.500 | 0.534 |
| q23 | ปลอกคอสุนัขปรับขนาดได้ | 60% | 70% | 0.658 | 0.700 |
| q24 | ทรายแมวไร้ฝุ่น | 20% | 50% | 0.553 | 0.596 |
| q25 | ขาตั้งกล้องสามขา | 0% | 10% | 0.517 | 0.514 |

## 5 คำค้นที่สอดคล้องกันน้อยที่สุด (ตรวจด้วยตา)

### q06 — ไทย: “เสื้อยืดผ้าฝ้ายสีดำ” · อังกฤษ: “black cotton t-shirt” (overlap@10 = 0%)

**ไทย**
- Tommy Hilfiger Womens Cazidine Logo Casual Thong Sandals  _[AMAZON FASHION]_
- Tommy Hilfiger Girls' Big Core Lightweight Cardigan Sweater  _[AMAZON FASHION]_
- Smino Men's Ice Cream X Zero Fatigue Cones N' Bones Tee  _[AMAZON FASHION]_

**อังกฤษ**
- New York Kane Logo Shirt T-Shirt, Mens, Short Sleeve, Blue  _[AMAZON FASHION]_
- Men's Marvel Avengers: Infinity War Armor T-Shirt - Black - 3X Large  _[AMAZON FASHION]_
- DAZZO Premium Slim-Fit Artistic Tees for Men with Ultimate Comfort & Style - Soft Black T-  _[Clothing, Shoes & Jewelry]_

### q15 — ไทย: “เสื่อโยคะกันลื่น” · อังกฤษ: “non-slip yoga mat” (overlap@10 = 10%)

**ไทย**
- Bottone 4mm Thickness Yoga Mat Non-slip EVA Foam Yoga Pad,Dampproof Sleeping Mattress Mat,  _[Sports & Outdoors]_
- CRZ YOGA Mens Comfy Lounge Pants 30" - Super-Soft Open Bottom Yoga Casual Pajama Pants Ath  _[AMAZON FASHION]_
- FREDS SWIM ACADEMY Kickboard & Swimboard Training Aid Float for Toddlers and Children Aged  _[Sports & Outdoors]_

**อังกฤษ**
- Bottone 4mm Thickness Yoga Mat Non-slip EVA Foam Yoga Pad,Dampproof Sleeping Mattress Mat,  _[Sports & Outdoors]_
- AOYEGO Mandala Flower Bath Mat Set Purple Floral Lotus Star Galaxy Bohemian Constellation   _[Amazon Home]_
- Haull 3 Pcs Boho Kitchen Rugs Set Non Skid Thick Washable Mandala Ethnic Flower Kitchen Ma  _[Amazon Home]_

### q25 — ไทย: “ขาตั้งกล้องสามขา” · อังกฤษ: “camera tripod stand” (overlap@10 = 10%)

**ไทย**
- Mid Century Boho Mountain Moon Light Switch Cover 3 Gang Wall Plate Decorative Triple Togg  _[Tools & Home Improvement]_
- PellKing Head Mount Strap Chest Mount Harness Chesty Kit Compatible with Insta360 one X3,X  _[Electronics]_
- Wopuzr Vinyl Siding Angle Adjustment Mount Compatible with Video Doorbell/Video Doorbell 2  _[Camera & Photo]_

**อังกฤษ**
- Riedler 1080P Webcam with Tripod, Microphone and Privacy Cover, High Resolution 30FPS 1920  _[All Electronics]_
- bodbop Cell Phone Stand for Desk Mobile Phone Holder Desktop Cell Phone Bracket Desk Folda  _[Cell Phones & Accessories]_
- 2-Set Class of 2023 Black Gold 3-Tiered Graduation Round Cardboard Cupcake Stands 24 Cake   _[Amazon Home]_

### q11 — ไทย: “ชุดไขควงอเนกประสงค์” · อังกฤษ: “multipurpose screwdriver set” (overlap@10 = 20%)

**ไทย**
- Instant Power NON ACIDIC Heavy Duty Drain Opener KIT by J&L Supply – 1 Liter Hair & Grease  _[Health & Personal Care]_
- The Original Hydraulic Quick Coupling Pressure Decompression Relief Release Tool 1/2" Ag/P  _[Tools & Home Improvement]_
- Teamoda Universal Adjustable Double-ended Wrench, 2023 Upgrade Bathroom Multifunctional Wr  _[Tools & Home Improvement]_

**อังกฤษ**
- Screwdriver Set 10 Piece, Cushion Grip, 5 Phillips and 5 Flat Head Tips  _[Tools & Home Improvement]_
- Nuyoah Precision Screwdriver Set, 138 in 1 Computer Repair Tool Kit, Magnetic Screwdriver   _[Tools & Home Improvement]_
- Precision Screwdriver Set with Durable S2 Microbits, NECAMOCU Professional 46 in 1 Magneti  _[Tools & Home Improvement]_

### q09 — ไทย: “กระทะเหล็กหล่อ” · อังกฤษ: “cast iron skillet” (overlap@10 = 30%)

**ไทย**
- AMABEApdg Frying Pan Cast Iron Frying Pan Non-Stick Uncoated Saucepan Egg Pancake Cooking   _[Home & Kitchen]_
- Spatula Metal Spatula For Cooking Pancake Spatula Steak Spatula Hamburger Spatula Stainles  _[Amazon Home]_
- Restaurantware Eco Pie Kraft Paper Corrugated Flatbread Box - 24" x 8" x 2" - 50 count box  _[Amazon Home]_

**อังกฤษ**
- AMABEApdg Frying Pan Cast Iron Frying Pan Non-Stick Uncoated Saucepan Egg Pancake Cooking   _[Home & Kitchen]_
- Spatula Metal Spatula For Cooking Pancake Spatula Steak Spatula Hamburger Spatula Stainles  _[Amazon Home]_
- KITCHENLESTAR Spoon Rest for Stove Top Cooking Spoon Holder for Kitchen Countertop Large H  _[Home & Kitchen]_
