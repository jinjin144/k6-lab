# K6 lab results

ทดสอบจริงวันที่ 30 ตุลาคม 2026 (Asia/Bangkok), Windows, K6 v2.3.0 ผ่านอินเทอร์เน็ตไปยัง QuickPizza สาธารณะ รันทีละชุด ไม่มีการรันทับกัน
หลักฐาน: `reports/raw/runs.json` เก็บเวลา คำสั่ง และ exit code; `*-summary.json` และ `.log` เก็บผลจริง หน่วย response time เป็น ms

## Part 0

- **Step 0.1:** http_req_duration = 265.15 ms (1 request)
- **Step 0.2:** 80 requests; 3.803 Req/s; p(95) = 279.23 ms. แต่ละ VU รอ response แล้ว sleep 1 วินาที จึงมีรอบงานเกิน 1 วินาที รวม overhead และการเชื่อมต่อครั้งแรก ทำให้ 5 VUs ส่งไม่ถึง 5 requests ต่อวินาที (iteration เฉลี่ย 1.302 วินาที)
- **Step 0.3:** 20 iterations รวมที่แบ่งกันทำระหว่าง 5 VUs ไม่ใช่ 20 ต่อ VU
- **Step 0.4:** ตรวจ status, ชื่อพิซซ่า และส่วนผสมมังสวิรัติ ผ่าน 100.00%
- **Step 0.5:** ได้ 401 ตามคาด checks ผ่าน 100.00% และ http_req_failed = 0.00% เพราะใช้ expectedStatuses(401)
- **Step 0.6:** ปกติ p(95) = 457.33 ms, exit code 0; P95=300 ได้ p(95) = 393.61 ms, exit code 99. `http_req_failed: rate<0.01` PASS; `checks: rate>0.99` PASS; `http_req_duration: p(95)<300` FAIL
- **Step 0.7:** 3 VUs / 30s: p(95) = 370.41 ms, p(99) = 377.27 ms. `http_req_failed: rate<0.01` PASS; `http_req_duration: p(95)<1000` PASS; `http_req_duration: p(99)<1500` PASS. เปลี่ยนข้อกำหนด p(95) เพียงค่าเดียวจาก 1000 เป็น 1 ms ด้วย P95=1 ได้ p(95) = 401.34 ms, exit code 99
- **Step 0.8:** request เดิมส่ง `pepperoni` และ `knife` แต่ API ใช้ชื่อแบบ case-sensitive คือ `Pepperoni` และ `Knife` (ดู explore.log) จึงต้องแก้ชื่อให้ตรงกัน
  - 0.8-buggy: status is 200: 75 pass / 0 fail; no pepperoni: 65 pass / 10 fail; no knife needed: 45 pass / 30 fail
  - 0.8-fixed: status is 200: 75 pass / 0 fail; no pepperoni: 75 pass / 0 fail; no knife needed: 75 pass / 0 fail
  - การสุ่มพิซซ่าหลายครั้งเปิดเผยการละเมิดเงื่อนไขที่ request เดียวอาจไม่พบ HTTP 200 ไม่ได้ยืนยันว่าพิซซ่าถูกต้อง และ checks ที่ fail ไม่ทำให้ exit code เป็น 99 หากไม่มี threshold

## Part A results

| Step | Test type | Users | Req/s | p(95) ms | Max ms | Failed | Checks |
| ---- | --------- | ----- | ----- | -------- | ------ | ------ | ------ |
| A1 | Smoke | 1 | 0.490 | 342.98 | 344.52 | 0.00% | 100.00% |
| A2 | Average load | 3 | 1.316 | 431.35 | 620.88 | 0.00% | 100.00% |
| A3 | Stress | 5 | 2.170 | 364.91 | 445.89 | 0.00% | 100.00% |
| A4 | Spike | 5 | 1.031 | 368.23 | 502.67 | 0.00% | 100.00% |
| A5 | Soak | 2 | 0.973 | 368.58 | 398.28 | 0.00% | 100.00% |

### Threshold results

- a1-smoke: exit 0; `http_req_failed: rate<0.01` PASS; `checks: rate>0.99` PASS
- a2-average: exit 0; `checks: rate>0.99` PASS; `http_req_duration{group:::recommendation}: p(95)<1500` PASS; `http_req_duration{group:::home}: p(95)<1000` PASS; `http_req_failed: rate<0.01` PASS
- a3-stress: exit 0; `http_req_failed: rate<0.01` PASS; `http_req_duration{group:::recommendation}: p(95)<1500` PASS; `http_req_duration{group:::home}: p(95)<1000` PASS; `checks: rate>0.99` PASS
- a4-spike: exit 0; `http_req_failed: rate<0.01` PASS; `checks: rate>0.99` PASS; `http_req_duration{group:::recommendation}: p(95)<1500` PASS; `http_req_duration{group:::home}: p(95)<1000` PASS
- a5-soak: exit 0; `checks: rate>0.99` PASS; `http_req_duration{group:::home}: p(95)<1000` PASS; `http_req_duration{group:::recommendation}: p(95)<1500` PASS; `http_req_failed: rate<0.01` PASS

### Timeline measurements

คำนวณ p(95) จาก http_req_duration samples ใน JSON output โดย linear interpolation ใช้เวลานับจากเริ่มคำสั่ง จึงคลาดเคลื่อนจากจุดเริ่ม scenario เล็กน้อย ใช้ช่วงละ 30 วินาทีสำหรับ spike และช่วงละ 2 นาทีสำหรับ soak ผลรวมทุก endpoint อาจเปลี่ยนตามสัดส่วน request และ sample size

| Test | Window after command start (s) | Requests | p(95) ms | Failed |
| ---- | ------------------------------ | -------- | -------- | ------ |
| a4-spike | 0–30 | 15 | 353.91 | 0.00% |
| a4-spike | 35–65 | 75 | 375.78 | 0.00% |
| a4-spike | 70–100 | 15 | 400.45 | 0.00% |
| a4-spike | 100–130 | 14 | 364.52 | 0.00% |
| a5-soak | 30–150 | 118 | 364.12 | 0.00% |
| a5-soak | 510–630 | 119 | 370.74 | 0.00% |

## Part B

1. ผลทั้งห้ารูปแบบอยู่ในตาราง Part A ด้านบน Req/s เป็นอัตรารวมของ run จาก http_reqs ส่วน p(95) และ Max เป็น http_req_duration รวมทุก endpoint
2. 5 VUs ได้ 3.803 Req/s เพราะแต่ละคนรอ response และ sleep 1 วินาทีก่อนเริ่มรอบถัดไป จึงไม่ใช่การกำหนด arrival rate ที่ 5 Req/s
3. Average p(95) = 431.35 ms เทียบ Stress = 364.91 ms ต่างกัน -66.44 ms การทดสอบที่ 3 และ 5 VUs อยู่ในขอบเขตเล็กที่อนุญาตสำหรับ demo สาธารณะ ความต่างอาจมาจาก network และผู้ใช้ร่วมระบบ จึงยังระบุขีดความสามารถสูงสุดหรือขอบ operational envelope ไม่ได้
4. p(95) ก่อน spike = 353.91 ms; ช่วง 5 VUs = 375.78 ms; หลังลดเหลือ 1 VU ช่วง 70–100s = 400.45 ms และช่วง 100–130s = 364.52 ms ค่าสุดท้ายใกล้ baseline (สูงขึ้นประมาณ 3%) จึงเห็นว่ากลับมาใกล้เดิมในหน้าต่าง 30–60 วินาทีหลังลดโหลดเสร็จที่ 70s ความต่างเล็กและ sample หลังลดโหลดมีเพียง 14–15 requests ต่อช่วง จึงระบุวินาทีที่ฟื้นตัวแน่นอนไม่ได้ และยังแยกผลของ load ออกจาก network variation ไม่ได้ ไม่มี failed requests ในทุกช่วง
5. Soak ช่วงต้นคงที่ (30–150s) p(95) = 364.12 ms, failed = 0.00%; ช่วงท้ายคงที่ (510–630s) p(95) = 370.74 ms, failed = 0.00% ความต่าง p(95) = 6.62 ms โดยสองหน้าต่างนี้ยังพิสูจน์แนวโน้มต่อเนื่องหรือสาเหตุไม่ได้ และการรัน 10 นาทียังยืนยันเสถียรภาพหลายชั่วโมงไม่ได้ Soak หลายชั่วโมงอาจเผย memory leak หรือ connection leak ที่ทำให้ทรัพยากรหมดอย่างช้า ๆ
6. ค่าเฉลี่ยอาจปิดบัง request ที่ช้าบางส่วน p(95) แสดงประสบการณ์ของผู้ใช้ส่วนใหญ่พร้อมสะท้อน tail latency ได้มากกว่าค่าเฉลี่ย แต่ยังต้องดู p(99), Max และ failure rate ประกอบ
7. (ก) network latency, routing, bandwidth และ TLS ของการเชื่อมต่ออินเทอร์เน็ตต่างจากระบบใน lab (ข) demo มีผู้ใช้ร่วมและทรัพยากร/cache/ภาระงานที่ควบคุมไม่ได้ ต่างจาก lab ที่ควบคุมสภาพแวดล้อมได้
8. โหลดสูงอาจทำให้บริการของผู้อื่นช้าหรือล่ม กระทบผู้ใช้จริง และเกินสิทธิ์ที่ได้รับ ต้องได้รับอนุญาตและกำหนดขอบเขตโหลดล่วงหน้า โจทย์นี้จึงจำกัดไม่เกิน 5 VUs
9. ตัวอย่างข้อกำหนดคลุมเครือ: “แอปสั่งอาหารควรค้นหาร้านได้เร็ว” แก้เป็น: “บน staging ที่ได้รับอนุญาต เมื่อ 3 VUs ค้นหาร้านต่อเนื่อง 30 วินาที โดยพัก 1 วินาทีต่อรอบ อย่างน้อย 95% ของ search requests ใช้เวลาต่ำกว่า 1000 ms และอย่างน้อย 99% ต่ำกว่า 1500 ms โดย failed requests ต่ำกว่า 1%” ตัวอย่าง options ด้านล่างใช้กับ request ที่ติด tag `name: search` (เป็นตัวอย่างสำหรับแอปสมมติ ยังไม่ได้รัน):

```javascript
export const options = { vus: 3, duration: '30s', thresholds: {
  'http_req_duration{name:search}': ['p(95)<1000', 'p(99)<1500'],
  'http_req_failed{name:search}': ['rate<0.01'],
} };
// http.get(`${BASE_URL}/search?q=pizza`, { tags: { name: 'search' } });
```

## Scope

ผลทั้งหมดข้างต้นได้จากการรันจริง ไม่ได้แทนผลที่คาดว่าจะได้ ใช้ sleep จำลอง think time ตามโจทย์ รายงาน HTML อยู่ใน reports และไม่มีการ commit หรือ push โดยสคริปต์
Stress ครั้งแรกถูกขัดจังหวะระหว่างรัน: เวลาจริงยืดประมาณ 51 นาที ได้เพียง 76 requests จึงตัดออกจากการวิเคราะห์และรันใหม่ ผลที่ตัดออกเก็บไว้ใน reports/raw/interrupted ส่วนตารางใช้ผล Stress รอบใหม่ 399 requests เท่านั้น Spike ที่ค้างหลังเหตุการณ์เดียวกันถูกหยุดก่อนรันใหม่ตามลำดับ
