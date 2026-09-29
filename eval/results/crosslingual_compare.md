# เทียบกลยุทธ์ Cross-lingual Retrieval บนคลังเต็ม

ดัชนีเต็ม 117,243 รายการ · คำค้น 25 คู่ · top-5 · ตัดสินประเภทสินค้าด้วย Typhoon2-8B (binary)

> **ข้อจำกัด:** ความน่าเชื่อถือของ judge ยังไม่ได้ตรวจสอบกับ label ของคน
> ตัวเลข precision จึงเป็นหลักฐานระดับ indicative — ใช้เปรียบเทียบกลยุทธ์กันเองได้
> แต่ยังอ้างเป็นค่าสัมบูรณ์ในเล่มไม่ได้จนกว่าจะ validate judge

## ผลรวม

| กลยุทธ์ | product-type precision@5 | คำค้นที่ไม่ได้ของตรงเลย | overlap กับเพดานบน |
|---|---|---|---|
| ก. ไทยล้วน | **47.2%** (59/125) | 7/25 | 26.4% |
| ข. แปลก่อนค้น | **64.0%** (80/125) | 1/25 | 84.8% |
| ค. สองภาษา + RRF (1:1) | **57.6%** (72/125) | 3/25 | 51.2% |
| ง. สองภาษา + RRF (ไทย:อังกฤษ = 1:3) | **56.8%** (71/125) | 2/25 | 64.0% |
| จ. สองภาษา + RRF (1:5) | **61.6%** (77/125) | 2/25 | 72.0% |
| (เพดานบน) คำค้นอังกฤษที่คนเขียน | **70.4%** (88/125) | 0/25 | 100.0% |

## รายคำค้น

| id | คำค้นไทย | คำแปลที่ Typhoon2 ได้ | ก.ไทย | ข.แปล | ค.1:1 | ง.1:3 | จ.1:5 | เพดานบน |
|---|---|---|---|---|---|---|---|---|
| q01 | หูฟังบลูทูธไร้สายกันน้ำ | waterproof wireless bluetooth headphones | 80% | 100% | 100% | 100% | 100% | 100% |
| q02 | เคสมือถือกันกระแทก | shockproof mobile phone case | 80% | 80% | 80% | 60% | 60% | 100% |
| q03 | สายชาร์จ USB-C ยาว 2 เมตร | 2 meter usb-c charging cable | 0% | 20% | 20% | 20% | 20% | 20% |
| q04 | รองเท้าวิ่งผู้ชายน้ำหนักเบา | lightweight men's running shoes | 40% | 40% | 40% | 40% | 40% | 40% |
| q05 | กระเป๋าสะพายข้างหนังแท้ | genuine leather crossbody bag | 0% | 20% | 20% | 20% | 20% | 20% |
| q06 | เสื้อยืดผ้าฝ้ายสีดำ | black cotton t-shirt | 40% | 80% | 40% | 40% | 80% | 80% |
| q07 | หมอนหนุนเมมโมรี่โฟม | memory foam pillow | 40% | 100% | 100% | 100% | 100% | 100% |
| q08 | ผ้าม่านกันแสงสำหรับห้องนอน | blackout curtains for bedroom | 100% | 100% | 100% | 100% | 100% | 100% |
| q09 | กระทะเหล็กหล่อ | cast iron skillet | 0% | 60% | 0% | 40% | 60% | 60% |
| q10 | เครื่องชงกาแฟแบบดริป | coffee maker drip coffee | 60% | 60% | 40% | 40% | 40% | 40% |
| q11 | ชุดไขควงอเนกประสงค์ | multi-tool screwdriver set | 0% | 80% | 60% | 80% | 80% | 100% |
| q12 | สว่านไร้สายแบบใช้แบตเตอรี่ | cordless battery-powered drill | 0% | 20% | 0% | 0% | 0% | 20% |
| q13 | ที่ชาร์จในรถยนต์แบบ 2 ช่อง | dual port car charger | 100% | 100% | 100% | 100% | 100% | 100% |
| q14 | ใบปัดน้ำฝนรถยนต์ | car windshield wiper | 0% | 80% | 0% | 20% | 60% | 100% |
| q15 | เสื่อโยคะกันลื่น | non-slip yoga mat | 0% | 20% | 20% | 20% | 20% | 20% |
| q16 | ดัมเบลปรับน้ำหนักได้ | adjustable dumbbells | 100% | 80% | 100% | 80% | 80% | 100% |
| q17 | อาหารเสริมวิตามินซี | vitamin C supplement | 80% | 100% | 80% | 80% | 100% | 100% |
| q18 | แปรงสีฟันไฟฟ้า | electric toothbrush | 80% | 100% | 100% | 100% | 100% | 100% |
| q19 | ปากกาเจลสีน้ำเงิน | blue gel pen | 80% | 40% | 80% | 60% | 60% | 60% |
| q20 | เครื่องเย็บกระดาษสำหรับสำนักงาน | office paper punch | 40% | 0% | 20% | 0% | 0% | 60% |
| q21 | เมาส์ไร้สายสำหรับเล่นเกม | wireless gaming mouse | 60% | 40% | 80% | 60% | 60% | 40% |
| q22 | คีย์บอร์ดเมคานิคอล | mechanical keyboard | 40% | 80% | 60% | 60% | 60% | 80% |
| q23 | ปลอกคอสุนัขปรับขนาดได้ | adjustable dog collar | 100% | 100% | 100% | 100% | 100% | 100% |
| q24 | ทรายแมวไร้ฝุ่น | dust-free cat litter | 20% | 40% | 20% | 20% | 20% | 40% |
| q25 | ขาตั้งกล้องสามขา | tripod stand | 40% | 60% | 80% | 80% | 80% | 80% |

## คำค้นที่การรวมสองภาษาช่วยได้มากที่สุด (ตรวจด้วยตา)

### q07 — “หมอนหนุนเมมโมรี่โฟม” → แปลเป็น “memory foam pillow”

**ก. ไทยล้วน** (40%)
- ❌ HARNY 3 Inch Gel Memory Foam Mattress Topper Twin Size, High Density Cooling Pad Pres  _[Amazon Home]_
- ❌ ORTHOMTEX 3 Inch Cooling Gel Memory Foam Mattress Topper Super Twin Size Bed,Removabl  _[Amazon Home]_
- ❌ BedStory 2.5 Inch Memory Foam Mattress Topper, Gel Infused Toppers for Twin XL Bed, P  _[Amazon Home]_

**ค. สองภาษา + RRF (1:1)** (100%)
- ✅ Comfort and Softness Memory Foam Pillow Sleep Mask, Smooth Pillow That Feel Like Cat   _[Amazon Home]_
- ✅ Memory Foam Pillows Neck Pillow for Sleeping Ergonomic Pillow Contour Cervical Pillow  _[Home & Kitchen]_
- ✅ COYMOS Bean Bag Filler 10lbs Pillow Stuffing for Couch Pillows, Soft Shredded Memory   _[Home & Kitchen]_

### q11 — “ชุดไขควงอเนกประสงค์” → แปลเป็น “multi-tool screwdriver set”

**ก. ไทยล้วน** (0%)
- ❌ 6Pcs Fix Zip Puller 3 Sizes Universal Instant Fix Zipper Repair Kit, Replacement Zip   _[Arts, Crafts & Sewing]_
- ❌ 6Pcs Fix Zip Puller 3 Sizes Universal Instant Fix Zipper Repair Kit, Replacement Zip   _[Arts, Crafts & Sewing]_
- ❌ 6 Pcs Fix Zip Puller - Zip Slider Repair Instant Kit - Fix Zipper Removable Rescue Re  _[Unknown]_

**ค. สองภาษา + RRF (1:1)** (60%)
- ✅ 11 PCS Mini Screwdriver Set, Small Screwdriver Set of Flathead and Phillips Screwdriv  _[Tools & Home Improvement]_
- ✅ Electric Screwdriver Precision Screwdriver Set Cordless Screwdriver Mini Screwdriver   _[Tools & Home Improvement]_
- ❌ Aokeleilei 23-in-1 Snowflake Multitool, Stainless Steel Snowflake Wrench Bottle Opene  _[Tools & Home Improvement]_

### q25 — “ขาตั้งกล้องสามขา” → แปลเป็น “tripod stand”

**ก. ไทยล้วน** (40%)
- ❌ UNIXYZ Third Person Bike Handlebar Mount + 28cm Invisible Carbon Fiber Extension Arm   _[Cell Phones & Accessories]_
- ❌ Collapsible Octopus Camera Mini Tripod, Flexible Cell Phone Holder Stand Selfie Stick  _[Camera & Photo]_
- ✅ WILDGAMEPLUS Portable Shooting Tripod Rest Rapid Rifle Shooting Stand, Adjustable Com  _[Sports & Outdoors]_

**ค. สองภาษา + RRF (1:1)** (80%)
- ❌ Collapsible Octopus Camera Mini Tripod, Flexible Cell Phone Holder Stand Selfie Stick  _[Camera & Photo]_
- ✅ WILDGAMEPLUS Portable Shooting Tripod Rest Rapid Rifle Shooting Stand, Adjustable Com  _[Sports & Outdoors]_
- ✅ Phone Tripod, Cell Phone Holder for iPhone and Android Phones, with Small Portable Tr  _[Camera & Photo]_

### q21 — “เมาส์ไร้สายสำหรับเล่นเกม” → แปลเป็น “wireless gaming mouse”

**ก. ไทยล้วน** (60%)
- ❌ Wired Gaming Mouse , Optical USB Mice for Laptop/Desktop, 800 to 1600 3 Adjustable DP  _[All Electronics]_
- ✅ Wireless Mouse Bluetooth Pink Mouse Cute Hamster Shape Kawaii Portable Ergonomic Sile  _[All Electronics]_
- ✅ Uioaso 2.4G Wireless Mouse with USB Receiver, Portable Gaming & Office Mice for Deskt  _[Video Games]_

**ค. สองภาษา + RRF (1:1)** (80%)
- ❌ Wired Gaming Mouse , Optical USB Mice for Laptop/Desktop, 800 to 1600 3 Adjustable DP  _[All Electronics]_
- ✅ Wireless Mouse Bluetooth Pink Mouse Cute Hamster Shape Kawaii Portable Ergonomic Sile  _[All Electronics]_
- ✅ soputry Wireless Ergonomics Metal Mouse, Rechargeable Wireless Mouse with 2.4GHz Nano  _[All Electronics]_
