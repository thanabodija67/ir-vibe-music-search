import json
import time
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

# ==== ตัวหลัก: LRCLIB (ฟรี, ไม่ต้องมี API key) ====
LRCLIB_URL = "https://lrclib.net/api/get"
LRCLIB_HEADERS = {
    "User-Agent": "IR-Vibe-Music-Search/1.0 (student project)"
}

# ==== ตัวสำรอง: scrape จาก Sanook Music (ใช้เมื่อ LRCLIB หาไม่เจอเท่านั้น) ====
SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "th-TH,th;q=0.9,en;q=0.8"
}

INPUT_FILE = "songs.json"
OUTPUT_FILE = "songs.json"

# รูปแบบข้อความปลอมที่ populate_full_lyrics.py เคยเติมต่อท้ายไว้
FAKE_SUFFIX_PATTERN = re.compile(r"\s*ท่อนเนื้อเพลงฉบับเต็มของเพลง.*$")


def clean_fake_suffix(text):
    """ตัดข้อความปลอมที่ต่อท้ายออก เหลือแค่เนื้อเพลงเดิมที่มีอยู่"""
    return FAKE_SUFFIX_PATTERN.sub("", text).strip()


# ---------- ตัวหลัก: LRCLIB ----------
def fetch_from_lrclib(title, artist):
    params = {"track_name": title, "artist_name": artist}
    try:
        resp = requests.get(LRCLIB_URL, params=params, headers=LRCLIB_HEADERS, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

        plain = data.get("plainLyrics") or ""
        synced = data.get("syncedLyrics") or ""

        if plain:
            return plain.strip()
        if synced:
            return re.sub(r"\[\d{2}:\d{2}\.\d{2}\]\s*", "", synced).strip()
        return None
    except Exception:
        return None


# ---------- ตัวสำรอง: scrape Sanook ----------
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()


def fetch_from_sanook(title, artist):
    query = f"{title} {artist}"
    try:
        search_url = f"https://www.sanook.com/music/search/{urllib.parse.quote(query)}/"
        res = requests.get(search_url, headers=SCRAPE_HEADERS, timeout=8)
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        candidates = soup.find_all("a", href=re.compile(r"/music/song/"))
        song_url = None
        for cand in candidates:
            link_text = cand.get_text().strip()
            if title in link_text or link_text in title:
                song_url = cand.get("href")
                break

        if not song_url:
            return None

        if not song_url.startswith("http"):
            song_url = "https://www.sanook.com" + song_url if song_url.startswith("/") else "https:" + song_url

        song_res = requests.get(song_url, headers=SCRAPE_HEADERS, timeout=8)
        song_soup = BeautifulSoup(song_res.text, "html.parser")

        lyric_div = song_soup.find("div", class_=re.compile(r"lyric|Lyric|song-detail"))
        if lyric_div:
            text = clean_text(lyric_div.get_text())
            if len(text) > 40:
                return text

        p_tags = [p.get_text().strip() for p in song_soup.find_all("p") if len(p.get_text().strip()) > 15]
        if p_tags:
            return " ".join(p_tags[:8])

        return None
    except Exception:
        return None


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        songs = json.load(f)

    print(f"🚀 เริ่มล้าง + ดึงเนื้อเพลงจริงทั้งหมด {len(songs)} เพลง...\n")

    lrclib_count = 0
    sanook_count = 0
    kept_old_count = 0

    for idx, song in enumerate(songs):
        title = song.get("title", "")
        artist = song.get("artist", "")
        old_lyrics_cleaned = clean_fake_suffix(song.get("lyrics", ""))

        print(f"[{idx+1}/{len(songs)}] {title} - {artist}")

        # 1. ลอง LRCLIB ก่อน
        lyrics = fetch_from_lrclib(title, artist)
        source = None

        if lyrics:
            source = "lrclib"
            lrclib_count += 1
            print("   ✅ เจอจาก LRCLIB")
        else:
            # 2. fallback ไป Sanook
            lyrics = fetch_from_sanook(title, artist)
            if lyrics:
                source = "sanook"
                sanook_count += 1
                print("   ✅ เจอจาก Sanook (สำรอง)")
            else:
                # 3. หาไม่เจอทั้งคู่ -> เก็บของเดิมที่ล้างข้อความปลอมแล้วไว้ก่อน
                lyrics = old_lyrics_cleaned
                source = "kept_original"
                kept_old_count += 1
                print("   ⚠️ ไม่พบทั้งสองแหล่ง (เก็บเนื้อเพลงเดิมที่ล้างแล้วไว้)")

        song["lyrics"] = lyrics
        song["lyrics_source"] = source

        time.sleep(0.6)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 บันทึก {OUTPUT_FILE} เรียบร้อย")
    print(f"   จาก LRCLIB: {lrclib_count} เพลง")
    print(f"   จาก Sanook (สำรอง): {sanook_count} เพลง")
    print(f"   เก็บของเดิม (ล้างข้อความปลอมแล้ว): {kept_old_count} เพลง")
    print("\n💡 เช็คเพลงที่ lyrics_source = 'kept_original' อีกรอบ")
    print("   เพราะเนื้อเพลงกลุ่มนี้ยังไม่ยืนยันว่าตรงต้นฉบับจริง 100%")


if __name__ == "__main__":
    main()