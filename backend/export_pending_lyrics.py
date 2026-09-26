import json

INPUT_FILE = "songs.json"
TEMPLATE_FILE = "lyrics_to_fill.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    songs = json.load(f)

pending = [s for s in songs if s.get("lyrics_source") == "kept_original"]

template = []
for s in pending:
    template.append({
        "id": s["id"],
        "title": s["title"],
        "artist": s["artist"],
        "lyrics": ""  # <-- ใส่เนื้อเพลงจริงตรงนี้ (คัดลอกจากแหล่งที่เชื่อถือได้)
    })

with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
    json.dump(template, f, ensure_ascii=False, indent=2)

print(f"สร้าง {TEMPLATE_FILE} แล้ว มีทั้งหมด {len(template)} เพลงที่ต้องกรอกเนื้อเพลง")
print("เปิดไฟล์นี้แล้วกรอกเนื้อเพลงจริงลงในช่อง \"lyrics\" ของแต่ละเพลง")
print("กรอกเสร็จแล้วรัน merge_lyrics.py เพื่อเอากลับเข้า songs.json")