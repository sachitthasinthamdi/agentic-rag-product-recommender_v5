# เทียบกลยุทธ์ Cross-lingual Retrieval บนคลังเต็ม

ดัชนีเต็ม 117,243 รายการ · คำค้น 25 คู่ · top-5 · ตัดสินประเภทสินค้าด้วย Typhoon2-8B (binary)

> **ข้อจำกัด:** ความน่าเชื่อถือของ judge ยังไม่ได้ตรวจสอบกับ label ของคน
> ตัวเลข precision จึงเป็นหลักฐานระดับ indicative — ใช้เปรียบเทียบกลยุทธ์กันเองได้
> แต่ยังอ้างเป็นค่าสัมบูรณ์ในเล่มไม่ได้จนกว่าจะ validate judge

## ผลรวม

| กลยุทธ์ | product-type precision@5 | คำค้นที่ไม่ได้ของตรงเลย | overlap กับเพดานบน |
|---|---|---|---|
| ก. ไทยล้วน | **34.4%** (43/125) | 9/25 | 26.4% |
| ข. แปลก่อนค้น | **46.4%** (58/125) | 6/25 | 84.8% |
| ค. สองภาษา + RRF | **44.8%** (56/125) | 6/25 | 51.2% |
| (เพดานบน) คำค้นอังกฤษที่คนเขียน | **51.2%** (64/125) | 5/25 | 100.0% |

## รายคำค้น

| id | คำค้นไทย | คำแปลที่ Typhoon2 ได้ | ก.ไทย | ข.แปล | ค.รวม | เพดานบน |
|---|---|---|---|---|---|---|
| q01 | หูฟังบลูทูธไร้สายกันน้ำ | waterproof wireless bluetooth headphones | 80% | 100% | 100% | 100% |
| q02 | เคสมือถือกันกระแทก | shockproof mobile phone case | 20% | 0% | 0% | 0% |
| q03 | สายชาร์จ USB-C ยาว 2 เมตร | 2 meter usb-c charging cable | 20% | 60% | 60% | 60% |
| q04 | รองเท้าวิ่งผู้ชายน้ำหนักเบา | lightweight men's running shoes | 40% | 60% | 60% | 60% |
| q05 | กระเป๋าสะพายข้างหนังแท้ | genuine leather crossbody bag | 0% | 60% | 20% | 60% |
| q06 | เสื้อยืดผ้าฝ้ายสีดำ | black cotton t-shirt | 40% | 100% | 80% | 100% |
| q07 | หมอนหนุนเมมโมรี่โฟม | memory foam pillow | 0% | 0% | 20% | 0% |
| q08 | ผ้าม่านกันแสงสำหรับห้องนอน | blackout curtains for bedroom | 0% | 20% | 20% | 20% |
| q09 | กระทะเหล็กหล่อ | cast iron skillet | 0% | 40% | 0% | 40% |
| q10 | เครื่องชงกาแฟแบบดริป | coffee maker drip coffee | 60% | 60% | 40% | 40% |
| q11 | ชุดไขควงอเนกประสงค์ | multi-tool screwdriver set | 0% | 80% | 80% | 100% |
| q12 | สว่านไร้สายแบบใช้แบตเตอรี่ | cordless battery-powered drill | 0% | 20% | 0% | 20% |
| q13 | ที่ชาร์จในรถยนต์แบบ 2 ช่อง | dual port car charger | 100% | 100% | 100% | 100% |
| q14 | ใบปัดน้ำฝนรถยนต์ | car windshield wiper | 0% | 20% | 0% | 60% |
| q15 | เสื่อโยคะกันลื่น | non-slip yoga mat | 40% | 80% | 80% | 80% |
| q16 | ดัมเบลปรับน้ำหนักได้ | adjustable dumbbells | 60% | 60% | 80% | 80% |
| q17 | อาหารเสริมวิตามินซี | vitamin C supplement | 60% | 40% | 40% | 40% |
| q18 | แปรงสีฟันไฟฟ้า | electric toothbrush | 100% | 100% | 100% | 100% |
| q19 | ปากกาเจลสีน้ำเงิน | blue gel pen | 20% | 20% | 20% | 20% |
| q20 | เครื่องเย็บกระดาษสำหรับสำนักงาน | office paper punch | 40% | 0% | 20% | 60% |
| q21 | เมาส์ไร้สายสำหรับเล่นเกม | wireless gaming mouse | 80% | 60% | 80% | 60% |
| q22 | คีย์บอร์ดเมคานิคอล | mechanical keyboard | 80% | 80% | 80% | 80% |
| q23 | ปลอกคอสุนัขปรับขนาดได้ | adjustable dog collar | 0% | 0% | 0% | 0% |
| q24 | ทรายแมวไร้ฝุ่น | dust-free cat litter | 0% | 0% | 0% | 0% |
| q25 | ขาตั้งกล้องสามขา | tripod stand | 20% | 0% | 40% | 0% |

## คำค้นที่การรวมสองภาษาช่วยได้มากที่สุด (ตรวจด้วยตา)

### q11 — “ชุดไขควงอเนกประสงค์” → แปลเป็น “multi-tool screwdriver set”

**ก. ไทยล้วน** (0%)
- ❌ 6Pcs Fix Zip Puller 3 Sizes Universal Instant Fix Zipper Repair Kit, Replacement Zip   _[Arts, Crafts & Sewing]_
- ❌ 6Pcs Fix Zip Puller 3 Sizes Universal Instant Fix Zipper Repair Kit, Replacement Zip   _[Arts, Crafts & Sewing]_
- ❌ 6 Pcs Fix Zip Puller - Zip Slider Repair Instant Kit - Fix Zipper Removable Rescue Re  _[Unknown]_

**ค. สองภาษา + RRF** (80%)
- ✅ 11 PCS Mini Screwdriver Set, Small Screwdriver Set of Flathead and Phillips Screwdriv  _[Tools & Home Improvement]_
- ✅ Electric Screwdriver Precision Screwdriver Set Cordless Screwdriver Mini Screwdriver   _[Tools & Home Improvement]_
- ✅ Aokeleilei 23-in-1 Snowflake Multitool, Stainless Steel Snowflake Wrench Bottle Opene  _[Tools & Home Improvement]_

### q06 — “เสื้อยืดผ้าฝ้ายสีดำ” → แปลเป็น “black cotton t-shirt”

**ก. ไทยล้วน** (40%)
- ❌ Fire Force Akitaru OBI Men's Tank Tops Tshirt Sleeveless Shirts Shirt Running Workout  _[Clothing, Shoes & Jewelry]_
- ❌ Topstype Womens Knit Crop Tops V Neck Sweater Tank Button Down Cami  _[AMAZON FASHION]_
- ✅ Tank Tops (as1, Alpha, x_l, Regular, Regular, Cotton) Black  _[Clothing, Shoes & Jewelry]_

**ค. สองภาษา + RRF** (80%)
- ✅ TRIUMPH Cartmel Black T-Shirt  _[Automotive]_
- ✅ Moc.Deamiarr Mazinger z Shirt Mens Cool wear Fashion T-Shirt Tops Black  _[AMAZON FASHION]_
- ✅ Bioworld mens Classic Fit Short Sleeve T-shirt  _[AMAZON FASHION]_

### q15 — “เสื่อโยคะกันลื่น” → แปลเป็น “non-slip yoga mat”

**ก. ไทยล้วน** (40%)
- ❌ Jexine 6 Pcs Yoga Ball Exercise Ball PVC Stability Balance Yoga Ball Chair Quick Pump  _[Sports & Outdoors]_
- ✅ ODODOS Yoga Mat for Women Men, Eco-Friendly Non Slip Exercise & Fitness Mat for Yoga   _[Sports & Outdoors]_
- ❌ Wllead Orange Anti Slip Kayak Seat Cushion Waterproof Gel Boat Canoe Rowing Stadium I  _[Sports & Outdoors]_

**ค. สองภาษา + RRF** (80%)
- ✅ ODODOS Yoga Mat for Women Men, Eco-Friendly Non Slip Exercise & Fitness Mat for Yoga   _[Sports & Outdoors]_
- ✅ Yoga Mat - Premium 15 Mm Extra Thick Non Slip Exercise & Fitness Mat,Anti-Skid Sports  _[Sports & Outdoors]_
- ✅ Jovely TPE Non-Slip Yoga Mat, 72"x24", 1/4"(6mm) Thick, Extra Thick Eco Friendly Exer  _[Sports & Outdoors]_

### q03 — “สายชาร์จ USB-C ยาว 2 เมตร” → แปลเป็น “2 meter usb-c charging cable”

**ก. ไทยล้วน** (20%)
- ❌ [1Pack, 3.2ft] USB Type C Cable 5A Fast Charging, USB C to USB A Charger Cord Support  _[Electronics]_
- ✅ Apple USB C to USB C Cable 6ft,2 Pack Long Type C Charger Fast Charging Cord for Appl  _[Industrial & Scientific]_
- ❌ 2 Pack USB C Fast Charge,6FT USB C to USB C  _[Cell Phones & Accessories]_

**ค. สองภาษา + RRF** (60%)
- ✅ Apple USB C to USB C Cable 6ft,2 Pack Long Type C Charger Fast Charging Cord for Appl  _[Industrial & Scientific]_
- ❌ [1Pack, 3.2ft] USB Type C Cable 5A Fast Charging, USB C to USB A Charger Cord Support  _[Electronics]_
- ❌ (3-Pack) 3.3 ft USB C Cable 20w Fast Charging USB C-to-C Cable Compatible with All US  _[Electronics]_
