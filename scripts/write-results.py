"""Build the report from saved measurements after all runs finish."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
raw = root/'reports/raw'
runs = {r['name']:r for r in json.loads((raw/'runs.json').read_text(encoding='utf-8-sig'))}
def metrics(name):
    return json.loads((raw/f'{name}-summary.json').read_text())['metrics']
def p(name, stat='p(95)'):
    return f"{metrics(name)['http_req_duration'][stat]:.2f}"
def code(name):
    return runs[name]['exitCode']
def checks(name):
    return json.loads((raw/f'{name}-summary.json').read_text())['root_group']['checks']
def threshold_results(name):
    # Legacy summary export booleans indicate failure, not success.
    return '; '.join(f"`{metric}: {rule}` {'FAIL' if failed else 'PASS'}"
                     for metric, data in metrics(name).items()
                     for rule,failed in data.get('thresholds',{}).items())

timeline=json.loads((raw/'timeline-analysis.json').read_text())
lines=['# K6 lab results','',
 'ทดสอบจริงวันที่ 30 ตุลาคม 2026 (Asia/Bangkok), Windows, K6 v2.3.0 ผ่านอินเทอร์เน็ตไปยัง QuickPizza สาธารณะ รันทีละชุด ไม่มีการรันทับกัน',
 'หลักฐาน: `reports/raw/runs.json` เก็บเวลา คำสั่ง และ exit code; `*-summary.json` และ `.log` เก็บผลจริง หน่วย response time เป็น ms',
 '', '## Part 0','',
 f"- **Step 0.1:** http_req_duration = {p('0.1')} ms (1 request)",
 f"- **Step 0.2:** {metrics('0.2')['http_reqs']['count']} requests; {metrics('0.2')['http_reqs']['rate']:.3f} Req/s; p(95) = {p('0.2')} ms. แต่ละ VU รอ response แล้ว sleep 1 วินาที จึงมีรอบงานเกิน 1 วินาที รวม overhead และการเชื่อมต่อครั้งแรก ทำให้ 5 VUs ส่งไม่ถึง 5 requests ต่อวินาที (iteration เฉลี่ย {metrics('0.2')['iteration_duration']['avg']/1000:.3f} วินาที)",
 f"- **Step 0.3:** {metrics('0.3')['iterations']['count']} iterations รวมที่แบ่งกันทำระหว่าง 5 VUs ไม่ใช่ 20 ต่อ VU",
 f"- **Step 0.4:** ตรวจ status, ชื่อพิซซ่า และส่วนผสมมังสวิรัติ ผ่าน {metrics('0.4')['checks']['value']*100:.2f}%",
 f"- **Step 0.5:** ได้ 401 ตามคาด checks ผ่าน {metrics('0.5')['checks']['value']*100:.2f}% และ http_req_failed = {metrics('0.5')['http_req_failed']['value']*100:.2f}% เพราะใช้ expectedStatuses(401)",
 f"- **Step 0.6:** ปกติ p(95) = {p('0.6-normal')} ms, exit code {code('0.6-normal')}; P95=300 ได้ p(95) = {p('0.6-strict')} ms, exit code {code('0.6-strict')}. {threshold_results('0.6-strict')}",
 f"- **Step 0.7:** 3 VUs / 30s: p(95) = {p('0.7-normal')} ms, p(99) = {p('0.7-normal','p(99)')} ms. {threshold_results('0.7-normal')}. เปลี่ยนข้อกำหนด p(95) เพียงค่าเดียวจาก 1000 เป็น 1 ms ด้วย P95=1 ได้ p(95) = {p('0.7-strict')} ms, exit code {code('0.7-strict')}",
 '- **Step 0.8:** request เดิมส่ง `pepperoni` และ `knife` แต่ API ใช้ชื่อแบบ case-sensitive คือ `Pepperoni` และ `Knife` (ดู explore.log) จึงต้องแก้ชื่อให้ตรงกัน',
]
for name in ('0.8-buggy','0.8-fixed'):
    lines.append(f"  - {name}: " + '; '.join(f"{key}: {value['passes']} pass / {value['fails']} fail" for key,value in checks(name).items()))
lines += [
 '  - การสุ่มพิซซ่าหลายครั้งเปิดเผยการละเมิดเงื่อนไขที่ request เดียวอาจไม่พบ HTTP 200 ไม่ได้ยืนยันว่าพิซซ่าถูกต้อง และ checks ที่ fail ไม่ทำให้ exit code เป็น 99 หากไม่มี threshold',
 '', '## Part A results','',
 '| Step | Test type | Users | Req/s | p(95) ms | Max ms | Failed | Checks |',
 '| ---- | --------- | ----- | ----- | -------- | ------ | ------ | ------ |',
]
for step,name,kind,users in [('A1','a1-smoke','Smoke',1),('A2','a2-average','Average load',3),('A3','a3-stress','Stress',5),('A4','a4-spike','Spike',5),('A5','a5-soak','Soak',2)]:
    m=metrics(name)
    lines.append(f"| {step} | {kind} | {users} | {m['http_reqs']['rate']:.3f} | {p(name)} | {p(name,'max')} | {m['http_req_failed']['value']*100:.2f}% | {m['checks']['value']*100:.2f}% |")
lines += ['', '### Threshold results','']
for name in ('a1-smoke','a2-average','a3-stress','a4-spike','a5-soak'):
    lines.append(f"- {name}: exit {code(name)}; {threshold_results(name)}")
lines += ['', '### Timeline measurements','',
 'คำนวณ p(95) จาก http_req_duration samples ใน JSON output โดย linear interpolation ใช้เวลานับจากเริ่มคำสั่ง จึงคลาดเคลื่อนจากจุดเริ่ม scenario เล็กน้อย ใช้ช่วงละ 30 วินาทีสำหรับ spike และช่วงละ 2 นาทีสำหรับ soak ผลรวมทุก endpoint อาจเปลี่ยนตามสัดส่วน request และ sample size',
 '', '| Test | Window after command start (s) | Requests | p(95) ms | Failed |',
 '| ---- | ------------------------------ | -------- | -------- | ------ |']
for name,buckets in timeline.items():
    for b in buckets:
        lines.append(f"| {name} | {b['start_s']}–{b['end_s']} | {b['requests']} | {b['p95_ms']:.2f} | {b['failed_rate']*100:.2f}% |")
lines += ['', '## Part B','',
 '1. ผลทั้งห้ารูปแบบอยู่ในตาราง Part A ด้านบน Req/s เป็นอัตรารวมของ run จาก http_reqs ส่วน p(95) และ Max เป็น http_req_duration รวมทุก endpoint',
 f"2. 5 VUs ได้ {metrics('0.2')['http_reqs']['rate']:.3f} Req/s เพราะแต่ละคนรอ response และ sleep 1 วินาทีก่อนเริ่มรอบถัดไป จึงไม่ใช่การกำหนด arrival rate ที่ 5 Req/s",
 f"3. Average p(95) = {p('a2-average')} ms เทียบ Stress = {p('a3-stress')} ms ต่างกัน {float(p('a3-stress'))-float(p('a2-average')):.2f} ms การทดสอบที่ 3 และ 5 VUs อยู่ในขอบเขตเล็กที่อนุญาตสำหรับ demo สาธารณะ ความต่างอาจมาจาก network และผู้ใช้ร่วมระบบ จึงยังระบุขีดความสามารถสูงสุดหรือขอบ operational envelope ไม่ได้",
 '4. p(95) ก่อน spike = 353.91 ms; ช่วง 5 VUs = 375.78 ms; หลังลดเหลือ 1 VU ช่วง 70–100s = 400.45 ms และช่วง 100–130s = 364.52 ms ค่าสุดท้ายใกล้ baseline (สูงขึ้นประมาณ 3%) จึงเห็นว่ากลับมาใกล้เดิมในหน้าต่าง 30–60 วินาทีหลังลดโหลดเสร็จที่ 70s ความต่างเล็กและ sample หลังลดโหลดมีเพียง 14–15 requests ต่อช่วง จึงระบุวินาทีที่ฟื้นตัวแน่นอนไม่ได้ และยังแยกผลของ load ออกจาก network variation ไม่ได้ ไม่มี failed requests ในทุกช่วง',
 f"5. Soak ช่วงต้นคงที่ (30–150s) p(95) = {timeline['a5-soak'][0]['p95_ms']:.2f} ms, failed = {timeline['a5-soak'][0]['failed_rate']*100:.2f}%; ช่วงท้ายคงที่ (510–630s) p(95) = {timeline['a5-soak'][1]['p95_ms']:.2f} ms, failed = {timeline['a5-soak'][1]['failed_rate']*100:.2f}% ความต่าง p(95) = {timeline['a5-soak'][1]['p95_ms']-timeline['a5-soak'][0]['p95_ms']:.2f} ms โดยสองหน้าต่างนี้ยังพิสูจน์แนวโน้มต่อเนื่องหรือสาเหตุไม่ได้ และการรัน 10 นาทียังยืนยันเสถียรภาพหลายชั่วโมงไม่ได้ Soak หลายชั่วโมงอาจเผย memory leak หรือ connection leak ที่ทำให้ทรัพยากรหมดอย่างช้า ๆ",
 '6. ค่าเฉลี่ยอาจปิดบัง request ที่ช้าบางส่วน p(95) แสดงประสบการณ์ของผู้ใช้ส่วนใหญ่พร้อมสะท้อน tail latency ได้มากกว่าค่าเฉลี่ย แต่ยังต้องดู p(99), Max และ failure rate ประกอบ',
 '7. (ก) network latency, routing, bandwidth และ TLS ของการเชื่อมต่ออินเทอร์เน็ตต่างจากระบบใน lab (ข) demo มีผู้ใช้ร่วมและทรัพยากร/cache/ภาระงานที่ควบคุมไม่ได้ ต่างจาก lab ที่ควบคุมสภาพแวดล้อมได้',
 '8. โหลดสูงอาจทำให้บริการของผู้อื่นช้าหรือล่ม กระทบผู้ใช้จริง และเกินสิทธิ์ที่ได้รับ ต้องได้รับอนุญาตและกำหนดขอบเขตโหลดล่วงหน้า โจทย์นี้จึงจำกัดไม่เกิน 5 VUs',
 '9. ตัวอย่างข้อกำหนดคลุมเครือ: “แอปสั่งอาหารควรค้นหาร้านได้เร็ว” แก้เป็น: “บน staging ที่ได้รับอนุญาต เมื่อ 3 VUs ค้นหาร้านต่อเนื่อง 30 วินาที โดยพัก 1 วินาทีต่อรอบ อย่างน้อย 95% ของ search requests ใช้เวลาต่ำกว่า 1000 ms และอย่างน้อย 99% ต่ำกว่า 1500 ms โดย failed requests ต่ำกว่า 1%” ตัวอย่าง options ด้านล่างใช้กับ request ที่ติด tag `name: search` (เป็นตัวอย่างสำหรับแอปสมมติ ยังไม่ได้รัน):',
 '', '```javascript',
 "export const options = { vus: 3, duration: '30s', thresholds: {",
 "  'http_req_duration{name:search}': ['p(95)<1000', 'p(99)<1500'],",
 "  'http_req_failed{name:search}': ['rate<0.01'],",
 '} };',
 "// http.get(`${BASE_URL}/search?q=pizza`, { tags: { name: 'search' } });",
 '```', '',
 '## Scope', '',
 'ผลทั้งหมดข้างต้นได้จากการรันจริง ไม่ได้แทนผลที่คาดว่าจะได้ ใช้ sleep จำลอง think time ตามโจทย์ รายงาน HTML อยู่ใน reports และไม่มีการ commit หรือ push โดยสคริปต์',
 'Stress ครั้งแรกถูกขัดจังหวะระหว่างรัน: เวลาจริงยืดประมาณ 51 นาที ได้เพียง 76 requests จึงตัดออกจากการวิเคราะห์และรันใหม่ ผลที่ตัดออกเก็บไว้ใน reports/raw/interrupted ส่วนตารางใช้ผล Stress รอบใหม่ 399 requests เท่านั้น Spike ที่ค้างหลังเหตุการณ์เดียวกันถูกหยุดก่อนรันใหม่ตามลำดับ',
]
(root/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
