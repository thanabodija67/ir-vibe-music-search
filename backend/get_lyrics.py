import json
import time
import re
import requests

# ==== LRCLIB API ====
# ฟรี ไม่ต้องสมัคร ไม่ต้องมี API key
# เอกสาร: https://lrclib.net/docs
BASE_URL = "https://lrclib.net/api/get"
HEADERS = {
    # LRCLIB แนะนำให้ตั้ง User-Agent ของแอปตัวเองไว้ (ไม่บังคับ แต่ควรทำ)
    "User-Agent": "IR-Vibe-Music-Search/1.0 (student project)"
}

song_list = [
    {"id": 1, "title": "ยาพิษ", "artist": "Bodyslam"},
    {"id": 2, "title": "พิง", "artist": "NONT TANONT"},
    {"id": 3, "title": "ฝนตกไหม", "artist": "Three Man Down"},
    {"id": 4, "title": "วัดใจ", "artist": "Silly Fools"},
    {"id": 5, "title": "คิดแต่ไม่ถึง", "artist": "Tilly Birds"},
]


def fetch_lyrics(title: str, artist: str) -> dict:
    """ดึงเนื้อเพลงจาก LRCLIB ด้วยชื่อเพลง + ศิลปิน"""
    params = {
        "track_name": title,
        "artist_name": artist,
    }
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)

    if resp.status_code == 404:
        return {"lyrics": "", "found": False}

    resp.raise_for_status()
    data = resp.json()

    # บางเพลงมีแต่ synced lyrics ไม่มี plain lyrics หรือกลับกัน
    plain = data.get("plainLyrics") or ""
    synced = data.get("syncedLyrics") or ""

    if plain:
        lyrics_text = plain
    elif synced:
        # ตัด timestamp แบบ [00:17.12] ออก เหลือแต่เนื้อร้อง
        lyrics_text = re.sub(r"\[\d{2}:\d{2}\.\d{2}\]\s*", "", synced)
    else:
        lyrics_text = ""

    return {"lyrics": lyrics_text.strip(), "found": bool(lyrics_text)}


def main():
    full_songs_data = []
    print("กำลังดึงเนื้อเพลงจาก LRCLIB...")

    for song in song_list:
        result = fetch_lyrics(song["title"], song["artist"])

        if not result["found"]:
            print(f"  ❌ ไม่พบเนื้อเพลง: {song['title']} - {song['artist']}")
            lyrics_value = ""
        else:
            print(f"  ✅ พบเนื้อเพลง: {song['title']} - {song['artist']}")
            lyrics_value = result["lyrics"]

        full_songs_data.append({
            "id": song["id"],
            "title": song["title"],
            "artist": song["artist"],
            "lyrics": lyrics_value,
        })

        time.sleep(0.5)  # เว้นจังหวะเรียก API เพื่อมารยาทในการใช้งาน

    with open("songs.json", "w", encoding="utf-8") as f:
        json.dump(full_songs_data, f, ensure_ascii=False, indent=2)

    found_count = sum(1 for s in full_songs_data if s["lyrics"])
    print(f"\nบันทึก songs.json เรียบร้อยแล้ว ({found_count}/{len(song_list)} เพลงเจอเนื้อร้อง)")
    print("เพลงที่ lyrics เป็นค่าว่าง = LRCLIB ไม่มีข้อมูลเพลงนั้น")
    print("ลองปรับชื่อเพลง/ศิลปินให้เขียนแบบเดียวกับที่คนอื่นอัปโหลดไว้ (เช่นสลับภาษาไทย/อังกฤษของชื่อศิลปิน)")


if __name__ == "__main__":
    main()