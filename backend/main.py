import json
import re
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pythainlp.tokenize import word_tokenize

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# path ไปยังโฟลเดอร์ frontend (อยู่ระดับเดียวกับ backend)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

with open("songs.json", "r", encoding="utf-8") as f:
    SONGS_DATA = json.load(f)

def thai_tokenizer(text):
    return word_tokenize(text, engine="newmm")

corpus = [song["lyrics"] for song in SONGS_DATA]
vectorizer = TfidfVectorizer(tokenizer=thai_tokenizer, ngram_range=(1, 2))
tfidf_matrix = vectorizer.fit_transform(corpus)

def normalize_text(text):
    return re.sub(r'[\s\n\t\r,-_"\']+', '', text).lower()

@app.get("/search")
def search(q: str = Query(...), mode: str = Query("lyrics")):
    if mode == "artist":
        results = [song for song in SONGS_DATA if q.lower() in song["artist"].lower()]
        return {"mode": "artist", "results": results}
    
    query_raw = q.strip()
    query_norm = normalize_text(query_raw)
    query_tokens = set(thai_tokenizer(query_raw))
    
    # คำนวณ TF-IDF
    query_vec = vectorizer.transform([query_raw])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    
    results = []
    MIN_SCORE_THRESHOLD = 0.25  # ตัดผลลัพธ์ที่คะแนนต่ำกว่า 25% ออกทั้งหมด
    
    for idx, song in enumerate(SONGS_DATA):
        tfidf_score = float(similarities[idx])
        lyrics_norm = normalize_text(song["lyrics"])
        title_norm = normalize_text(song["title"])
        
        # 1. เช็คข้อความตรงตัวเป๊ะๆ
        is_exact_match = (query_norm in lyrics_norm) or (query_norm in title_norm)
        
        # 2. คำนวณอัตราส่วนคำที่ตรงกัน (กรณีพิมพ์ผิดหรือสลับคำบางคำ)
        song_tokens = set(thai_tokenizer(song["lyrics"]))
        overlap_ratio = len(query_tokens.intersection(song_tokens)) / len(query_tokens) if query_tokens else 0
        
        final_score = tfidf_score
        if is_exact_match:
            final_score = max(1.5, tfidf_score + 1.5)
        elif overlap_ratio >= 0.6:  # ถ้าคำตรงกันเกิน 60% ของประโยคที่พิมพ์
            final_score = max(0.8, tfidf_score + overlap_ratio)
            
        # กรองเฉพาะผลลัพธ์ที่ผ่านเกณฑ์ขั้นต่ำ
        if final_score >= MIN_SCORE_THRESHOLD:
            song_res = song.copy()
            song_res["score"] = round(final_score, 4)
            results.append(song_res)
            
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"mode": "lyrics", "results": results}