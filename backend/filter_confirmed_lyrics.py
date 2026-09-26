import json

INPUT_FILE = "songs.json"
OUTPUT_FILE = "songs.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    songs = json.load(f)

# เก็บเฉพาะเพลงที่มีที่มาของเนื้อเพลงยืนยันแล้ว (ไม่ใช่ของเดิมที่ยังไม่ยืนยัน)
CONFIRMED_SOURCES = {"lrclib", "sanook", "manual"}

kept = [s for s in songs if s.get("lyrics_source") in CONFIRMED_SOURCES]
removed = [s for s in songs if s.get("lyrics_source") not in CONFIRMED_SOURCES]

# ใส่ id ใหม่เรียงต่อเนื่อง 1..N (เผื่อ frontend อ้างอิง id แบบเรียงลำดับ)
for idx, s in enumerate(kept, start=1):
    s["id"] = idx

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(kept, f, ensure_ascii=False, indent=2)

print(f"เหลือเพลงที่มีเนื้อเพลงจริงยืนยันแล้ว: {len(kept)} เพลง")
print(f"ตัดออก (ยังไม่ยืนยันเนื้อเพลง): {len(removed)} เพลง")
print(f"บันทึกทับ {OUTPUT_FILE} เรียบร้อยแล้ว")