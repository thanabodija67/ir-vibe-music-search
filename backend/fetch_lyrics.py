import json
import time
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "th-TH,th;q=0.9,en;q=0.8"
}

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def fetch_lyrics_direct(title, artist):
    query = f"{title} {artist}"
    
    # 1. ลองค้นหาตรงผ่านเว็บ Sanook Music
    try:
        search_url = f"https://www.sanook.com/music/search/{urllib.parse.quote(query)}/"
        res = requests.get(search_url, headers=HEADERS, timeout=8)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # หาลิงก์เพลง
            song_link = soup.find("a", href=re.compile(r"/music/song/"))
            if song_link and song_link.get("href"):
                url = song_link["href"]
                if not url.startswith("http"):
                    url = "https://www.sanook.com" + url if url.startswith("/") else "https:" + url
                
                # ดึงเนื้อเพลงจากหน้าเพลง
                song_res = requests.get(url, headers=HEADERS, timeout=8)
                song_soup = BeautifulSoup(song_res.text, "html.parser")
                
                # หาบล็อกเนื้อเพลง
                lyric_div = song_soup.find("div", class_=re.compile(r"lyric|Lyric|song-detail"))
                if lyric_div:
                    text = clean_text(lyric_div.get_text())
                    if len(text) > 40:
                        return text
                        
                p_tags = [p.get_text().strip() for p in song_soup.find_all("p") if len(p.get_text().strip()) > 15]
                if p_tags:
                    return " ".join(p_tags[:8])
    except Exception:
        pass
        
    return None

# อ่านไฟล์ songs.json
with open("songs.json", "r", encoding="utf-8") as f:
    songs = json.load(f)

print(f"🚀 เริ่มดึงเนื้อเพลงแบบ Direct Search ทั้งหมด {len(songs)} เพลง...\n")

success_count = 0
for idx, song in enumerate(songs):
    print(f"[{idx+1}/{len(songs)}] กำลังดึง: {song['title']} - {song['artist']}...")
    
    new_lyrics = fetch_lyrics_direct(song['title'], song['artist'])
    
    if new_lyrics:
        song['lyrics'] = new_lyrics
        success_count += 1
        print("  ✅ สำเร็จ!")
    else:
        print("  ⚠️ ไม่พบเนื้อเพลงใหม่ (คงเนื้อเพลงเดิมไว้)")
        
    time.sleep(1)

# บันทึกทับลงไฟล์ songs.json
with open("songs.json", "w", encoding="utf-8") as f:
    json.dump(songs, f, ensure_ascii=False, indent=2)

print(f"\n🎉 อัปเดตเนื้อเพลงเรียบร้อยแล้ว {success_count}/{len(songs)} เพลง")