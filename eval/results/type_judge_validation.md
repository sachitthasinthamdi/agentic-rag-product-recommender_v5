# ตรวจสอบความน่าเชื่อถือของ LLM judge (ประเภทสินค้า)

เทียบคำตัดสินของ Typhoon2-8B กับ **label จากคนจริง** ใน Amazon Shopping Queries Dataset (ESCI, Reddy et al. 2022, arXiv:2206.06588)

**ชุดที่ใช้: `test`** — ปรับ prompt ด้วย `dev` เท่านั้น ตัวเลขที่รายงานเป็นทางการต้องมาจาก `test` ที่ไม่เคยใช้ปรับ

การแมป label: `Exact` → ประเภทเดียวกัน | `Complement` และ `Irrelevant` → คนละประเภท | `Substitute` → **ตัดออก** เพราะกำกวมสำหรับคำถามนี้

## ผลรวม

| ตัวชี้วัด | ค่า |
|---|---|
| จำนวนคู่ที่ใช้คิด | 73 |
| **Cohen's κ** | **0.246** (fair (พอใช้)) |
| Accuracy | 68.5% |
| Precision (judge ว่าใช่ แล้วใช่จริง) | 52.6% |
| Recall (ของที่ใช่จริง judge จับได้) | 41.7% |
| สัดส่วน "ใช่" ใน gold | 32.9% |
| สัดส่วน "ใช่" ที่ judge ตอบ | 26.0% |
| คู่ที่ parse คำตอบไม่ได้ | 0 |
| คู่ที่ตัดออกเพราะกำกวม (Substitute) | 27 |

> **เกณฑ์ตีความ κ** ใช้ของ Landis & Koch (1977) — รายงาน accuracy เดี่ยว ๆ ไม่พอ
> เพราะถ้า label เอียงไปทางเดียว ผู้ตัดสินที่ตอบเหมือนกันทุกครั้งก็ได้ accuracy สูงได้

## ตารางความสับสน

| gold \ judge | ว่าใช่ | ว่าไม่ใช่ |
|---|---|---|
| **ใช่** | 10 | 14 |
| **ไม่ใช่** | 9 | 40 |

## ความถูกต้องแยกตาม label ของ ESCI

| label | จำนวน | ถูก |
|---|---|---|
| Exact | 24 | 41.7% |
| Complement | 22 | 81.8% |
| Irrelevant | 27 | 81.5% |

กลุ่มกำกวม `Substitute`: judge ตอบว่าเป็นประเภทเดียวกัน 37.0% (ไม่นำมาคิด κ)

## ตัวอย่างที่ judge ไม่ตรงกับคน (23 คู่)

- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: ashley longshore
  - ได้: Ashley Longshore: I Do Not Cook, I Do Not Clean, I Do Not Fly Commercial
  - เหตุผลของ judge: _the head noun is "book", not a person or product._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: gucci cologne for men gift set
  - ได้: Gucci(グッチ) グッチ ギルティ プールオム EDT SP 90ml [並行輸入品] アロマティック フゼア 90ミリリットル (x 1)
  - เหตุผลของ judge: _the head noun is "cologne", not a gift set._
- **คนว่าไม่ใช่ judge ว่าใช่** · ESCI=Complement
  - ถามหา: archery target
  - ได้: MILAEM Archery Target Pins Plastic Archery Paper Target Face Pins Target Accessories Archery 24 Pcs (White)
  - เหตุผลของ judge: _the head noun is "archery target", exactly what was asked; "plastic" and "paper" are just materials._
- **คนว่าไม่ใช่ judge ว่าใช่** · ESCI=Irrelevant
  - ถามหา: cintos gucci originales para mujer
  - ได้: Gucci GG0225S Gold One Size
  - เหตุผลของ judge: _the head noun is "cintos gucci originales para mujer", exactly what was asked._
- **คนว่าไม่ใช่ judge ว่าใช่** · ESCI=Complement
  - ถามหา: archery target
  - ได้: Perfect Strike Archery SCOREBOOK with Rules and Scoring Instructions : Heavy Duty. Great for Practice and Comp
  - เหตุผลของ judge: _the head noun is "archery target", exactly what was asked._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: medium size modern end table lamps for the living room
  - ได้: Signature Design by Ashley - Laurentia Glass Table Lamp with Drum Shade - Champagne Toned
  - เหตุผลของ judge: _the head noun is "table lamp", not an end table or a specific size, style, or location._
- **คนว่าไม่ใช่ judge ว่าใช่** · ESCI=Complement
  - ถามหา: stylus pen for samsung note 9 with bluetooth
  - ได้: for Samsung Galaxy Note 9 Stylus Pen Touch Screen - Touch Screen Stylus S Pen Replacement Part for for Samsung
  - เหตุผลของ judge: _the head noun is "stylus pen", exactly what was asked; "for Samsung Galaxy Note 9" is just a feature._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: cintos gucci originales para mujer
  - ได้: Gucci Women's Sensual Romanticism Rectangle Sunglasses, Black/Grey, One Size
  - เหตุผลของ judge: _the head noun is "sunglasses", not a different product._
- **คนว่าไม่ใช่ judge ว่าใช่** · ESCI=Irrelevant
  - ถามหา: cintos gucci originales para mujer
  - ได้: Gucci GG0418S Black/Crystal/Grey Gradient One Size
  - เหตุผลของ judge: _the head noun is "cintos gucci originales para mujer", exactly what was asked._
- **คนว่าไม่ใช่ judge ว่าใช่** · ESCI=Irrelevant
  - ถามหา: ashley straw
  - ได้: Wendigo
  - เหตุผลของ judge: _the head noun is "straw", exactly what was asked; "ashley" is a brand, not a different product._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: gucci perfume for men
  - ได้: Gucci Pour Homme 3.0 oz Eau de Toilette Spray
  - เหตุผลของ judge: _the head noun is "perfume", not a specific brand or size._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: shoot rubber bullets
  - ได้: Dan Wesson ASG 2.5" CO2 Powered Air Revolver, Silver
  - เหตุผลของ judge: _the head noun is "revolver", not a bullet._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: light up christmas decorations
  - ได้: Hairui Lighted Brown Twig Branches Plug in with Dimmer and Timer 32IN 150 LED Fairy Lights, Lighted Willow Bra
  - เหตุผลของ judge: _the head noun is "twig branches", not a decoration._
- **คนว่าไม่ใช่ judge ว่าใช่** · ESCI=Irrelevant
  - ถามหา: ashley longshore
  - ได้: Ashley
  - เหตุผลของ judge: _the head noun is "Ashley", exactly what was asked._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: gucci cologne for men gift set
  - ได้: Gucci Guilty by Gucci for Men Eau de Toilette Spray, 3 Fl Oz (Pack of 1)
  - เหตุผลของ judge: _the head noun is "cologne", not a gift set._
- **คนว่าไม่ใช่ judge ว่าใช่** · ESCI=Irrelevant
  - ถามหา: cintos gucci originales para mujer
  - ได้: Gucci 0036S 002 Black 0036S Square Sunglasses Lens Category 3 Size 54mm
  - เหตุผลของ judge: _the head noun is "sunglasses", not a different product._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: plaid shirts for women
  - ได้: Amazon Brand - Goodthreads Women's Modal Twill Relaxed Fit Short Sleeve Button Front Shirt, Blue/Red Plaid, La
  - เหตุผลของ judge: _the head noun is "shirt", not a specific style or pattern._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: halloween miniatures
  - ได้: Department 56 Halloween Accessories for Village Collections Tombstones Figurine Set, Multiple Sizes, Multicolo
  - เหตุผลของ judge: _the head noun is "figurines", not the same as "miniatures"._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: plaid pants pajamas
  - ได้: Just Love Women Pajama Pants/Sleepwear,Pink - Plaid,Medium
  - เหตุผลของ judge: _the head noun is "pajama pants", not the same as "plaid pants"._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: hair extensions halo
  - ได้: SARLA Highlight Halo Hair Extension Wavy Curly for Women Dirty Blonde Hidden Wire Headband Size Adjustable Syn
  - เหตุผลของ judge: _the head noun is "halo", a different kind of thing from what was asked._
- **คนว่าไม่ใช่ judge ว่าใช่** · ESCI=Complement
  - ถามหา: boy doll clothes 15 inch
  - ได้: Manhattan Toy Baby Stella Happy Little Cloud Baby Doll Clothes for 15" Dolls
  - เหตุผลของ judge: _the head noun is "doll clothes", not a different product._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: ashley longshore
  - ได้: Mose Mary and Me Ashley Longshore Devotional Prayer Saint Candle
  - เหตุผลของ judge: _the head noun is "candle", not a person or brand._
- **คนว่าใช่ judge ว่าไม่ใช่** · ESCI=Exact
  - ถามหา: ashley longshore
  - ได้: You Don't Look Fat, You Look Crazy: An Unapologetic Guide to Being Ambitchous
  - เหตุผลของ judge: _the head noun is "book", not a person's name._