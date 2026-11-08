import os
from dotenv import load_dotenv

# Mendapatkan jalur/path absolut dari folder tempat app.py berada
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Memuat file .env secara absolut dari folder tersebut
load_dotenv(os.path.join(BASE_DIR, '.env'))

import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import bcrypt
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app) # Mengizinkan Frontend mengakses API ini

SECRET_KEY = "super-secret-key-anda" # Ganti dengan key yang aman

# -----------------------------------------------------------------
# UTILITY: Membaca data awal film dari data/movies.json
# -----------------------------------------------------------------
def load_movies():
    try:
        with open('data/movies.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Mocks database sementara (Ganti dengan PostgreSQL/MySQL/SQLite nanti)
users_db = {}
watchlist_db = {} # Format: {user_id: [movie_id1, movie_id2]}
reviews_db = {}   # Format: {user_id: [{"movieId": 1, "rating": 5, "review": ""}]}

# -----------------------------------------------------------------
# 1. AUTHENTICATION ROUTERS
# -----------------------------------------------------------------
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({"message": "Data tidak lengkap"}), 400
        
    if email in users_db:
        return jsonify({"message": "Email sudah terdaftar"}), 400
        
    # Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Simpan ke db mock
    user_id = len(users_db) + 1
    users_db[email] = {
        "id": user_id,
        "username": username,
        "email": email,
        "password": hashed_password
    }
    
    return jsonify({"message": "User berhasil didaftarkan"}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = users_db.get(email)
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({"message": "Email atau password salah"}), 401
        
    # Generate JWT Token
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm='HS256')
    
    return jsonify({
        "token": token,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email']
        }
    }), 200

# -----------------------------------------------------------------
# 2. MOVIES ROUTERS
# -----------------------------------------------------------------
@app.route('/api/movies', methods=['GET'])
def get_movies():
    movies = load_movies()
    genre = request.args.get('genre')
    search = request.args.get('search')
    
    # Logika filter query params sederhana
    if genre:
        movies = [m for m in movies if genre.lower() in [g.lower() for g in m.get('genres', [])]]
    if search:
        movies = [m for m in movies if search.lower() in m.get('title', '').lower()]
        
    return jsonify(movies), 200

@app.route('/api/movies/<int:movie_id>', methods=['GET'])
def get_movie_detail(movie_id):
    movies = load_movies()
    # Mencari film berdasarkan ID
    movie = next((m for m in movies if m.get('id') == movie_id), None)
    
    if not movie:
        return jsonify({"message": "Film tidak ditemukan"}), 404
    return jsonify(movie), 200

# -----------------------------------------------------------------
# NANTI: Tambahkan middleware JWT untuk Watchlist, Watched, dan Gemini AI
# -----------------------------------------------------------------

from functools import wraps

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Mengambil token dari header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token tidak ditemukan!'}), 401
        
        try:
            # Decode token menggunakan SECRET_KEY yang sama dengan saat login
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            # Ambil data user ID dari payload token
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token sudah kedaluwarsa!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token tidak valid!'}), 401
            
        return f(current_user_id, *args, **kwargs)
    return decorated

# Ambil daftar film di watchlist user
@app.route('/api/watchlist', methods=['GET'])
@token_required
def get_watchlist(current_user_id):
    user_watchlist_ids = watchlist_db.get(current_user_id, [])
    
    # Ambil data lengkap film berdasarkan id yang ada di watchlist user
    all_movies = load_movies()
    watchlist_movies = [m for m in all_movies if m.get('id') in user_watchlist_ids]
    
    return jsonify(watchlist_movies), 200

# Tambah film ke watchlist
@app.route('/api/watchlist', methods=['POST'])
@token_required
def add_watchlist(current_user_id):
    data = request.get_json()
    movie_id = data.get('movieId') # Sesuai API contract: {"movieId": 1}
    
    if not movie_id:
        return jsonify({"message": "movieId diperlukan"}), 400
        
    if current_user_id not in watchlist_db:
        watchlist_db[current_user_id] = []
        
    if movie_id not in watchlist_db[current_user_id]:
        watchlist_db[current_user_id].append(movie_id)
        
    return jsonify({"message": "Berhasil ditambahkan ke watchlist"}), 201

# Hapus film dari watchlist
@app.route('/api/watchlist/<int:movie_id>', methods=['DELETE'])
@token_required
def delete_watchlist(current_user_id, movie_id):
    if current_user_id in watchlist_db and movie_id in watchlist_db[current_user_id]:
        watchlist_db[current_user_id].remove(movie_id)
        return jsonify({"message": "Berhasil dihapus dari watchlist"}), 200
        
    return jsonify({"message": "Film tidak ditemukan di watchlist"}), 404


# Ambil riwayat film yang sudah ditonton & diulas
@app.route('/api/watched', methods=['GET'])
@token_required
def get_watched(current_user_id):
    user_reviews = reviews_db.get(current_user_id, [])
    all_movies = load_movies()
    
    # Gabungkan data film dengan ulasan dari user
    result = []
    for review_item in user_reviews:
        movie = next((m for m in all_movies if m.get('id') == review_item['movieId']), None)
        if movie:
            # Duplikat data film dan tempelkan ulasan milik user
            movie_with_review = movie.copy()
            movie_with_review['user_rating'] = review_item['rating']
            movie_with_review['user_review'] = review_item['review']
            result.append(movie_with_review)
            
    return jsonify(result), 200

# Tambah riwayat film yang sudah ditonton + ulasan
@app.route('/api/watched', methods=['POST'])
@token_required
def add_watched(current_user_id):
    data = request.get_json()
    movie_id = data.get('movieId')
    rating = data.get('rating')
    review = data.get('review')
    
    if not movie_id:
        return jsonify({"message": "movieId diperlukan"}), 400
        
    if current_user_id not in reviews_db:
        reviews_db[current_user_id] = []
        
    # Simpan atau update ulasan film
    # Hapus ulasan lama jika user mengulas film yang sama lagi
    reviews_db[current_user_id] = [r for r in reviews_db[current_user_id] if r['movieId'] != movie_id]
    
    reviews_db[current_user_id].append({
        "movieId": movie_id,
        "rating": rating,
        "review": review
    })
    
    return jsonify({"message": "Berhasil menambahkan ke riwayat tontonan"}), 201


from google import genai
from pydantic import BaseModel, Field

# Initialize client Gemini secara otomatis membaca os.environ["GEMINI_API_KEY"]
# Client otomatis membaca GEMINI_API_KEY dari environment (.env)
client = genai.Client()

# 1. Definisikan Skema Output Terstruktur sesuai Kontrak API Penugasan
class MovieRecommendation(BaseModel):
    movie_id: int = Field(description="ID dari film yang dipilih dari database lokal")
    reasoning: str = Field(description="Alasan mengapa film ini cocok dengan prompt user dalam bahasa Indonesia")

# 2. Endpoint Rekomendasi AI
# 2. Endpoint Rekomendasi AI (Versi Super Stabil & Ringan)
@app.route('/api/movies/recommend', methods=['POST'])
def recommend_movie():
    data = request.get_json()
    user_prompt = data.get('prompt') # Ambil prompt masukan dari frontend
    
    if not user_prompt:
        return jsonify({"message": "Prompt tidak boleh kosong"}), 400
        
    # Ambil 20 film lokal sebagai konteks rujukan AI
    local_movies = load_movies()
    if not local_movies:
        return jsonify({"message": "Database film lokal kosong"}), 500
        
    # Sederhanakan data film agar menghemat token prompt AI
    simplified_movies_context = [
        {"id": m.get("id"), "title": m.get("title"), "genres": m.get("genres"), "description": m.get("description")}
        for m in local_movies
    ]

    # Menyusun instruksi ketat (System Prompt) agar Gemini memilih dari basis data lokal
    system_instruction = (
        "Anda adalah sistem rekomendasi film ahli. Tugas Anda adalah memilih SATU film terbaik "
        "dari daftar kandidat film lokal yang disediakan di bawah ini berdasarkan preferensi pengguna.\n\n"
        f"DAFTAR FILM LOKAL YANG TERSEDIA:\n{json.dumps(simplified_movies_context)}\n\n"
        "ATURAN MUTLAK:\n"
        "1. Pilihlah 'movie_id' yang BENAR-BENAR ada di dalam daftar film lokal di atas.\n"
        "2. Jangan merekomendasikan film di luar daftar tersebut.\n"
        "3. Berikan alasan ('reasoning') yang logis dan persuasif dalam Bahasa Indonesia."
    )

    try:
        # Menggunakan model gemini-3.1-flash-lite dengan struktur parameter standar SDK terbaru
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=f"User Preference: {user_prompt}",
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": MovieRecommendation, # Menggunakan objek Pydantic langsung
            }
        )
        
        # Saring hasil teks JSON dari Gemini
        ai_result = json.loads(response.text)
        return jsonify(ai_result), 200

    except Exception as e:
        # PETA CADANGAN EXTREME: Jika terjadi masalah pada struktur JSON otomatis Google,
        # kita lakukan parsing teks manual agar Frontend Anda tidak mendeteksi crash 500.
        print(f"Eror utama terdeteksi: {str(e)}")
        try:
            # Panggilan manual tanpa paksaan skema kaku
            fallback_response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=f"User Preference: {user_prompt}\n\nPilihlah satu movie_id dari daftar ini dan berikan alasan dalam format JSON seperti ini: {{\"movie_id\": 14, \"reasoning\": \"Alasan...\"}}\n\nKonteks film:\n{json.dumps(simplified_movies_context)}",
            )
            # Bersihkan karakter pembungkus markdown jika ada (seperti ```json ... ```)
            clean_text = fallback_response.text.replace("```json", "").replace("```", "").strip()
            ai_result = json.loads(clean_text)
            return jsonify(ai_result), 200
        except Exception as fallback_error:
            return jsonify({"message": f"Gagal memproses rekomendasi AI: {str(fallback_error)}"}), 500



if __name__ == '__main__':
    app.run(debug=True, port=5000)
