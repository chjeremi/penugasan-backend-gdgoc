# 🎬 FilmLog — GDGoC Backend Recruitment Penugasan (Python/Flask)

Repositori ini berisi implementasi layanan **RESTful API** untuk aplikasi pelacak film (*movie watchlist*) bernama **FilmLog**. Backend ini dibangun menggunakan **Python & Flask** serta telah dikonfigurasi secara penuh agar terhubung secara instan dan interaktif dengan *Frontend Companion* bertema Letterboxd yang disediakan.

---

## 🎯 Fitur yang Diimplementasikan

1. **Authentication (Rute Publik):** Sistem Registrasi (`POST /api/auth/register`) dengan *password hashing* menggunakan `bcrypt` serta Login (`POST /api/auth/login`) yang menghasilkan token JWT.
2. **Movies Data (Rute Publik):** Menampilkan daftar 20 film kurasi awal dengan fitur pencarian dan filter genre, serta pencarian detail spesifik film berdasarkan ID.
3. **Protected Watchlist (Rute Privat):** Menambah, melihat, dan menghapus daftar film ke dalam *watchlist* user menggunakan proteksi middleware JWT (`Authorization: Bearer <token>`).
4. **Protected Watched & Review (Rute Privat):** Menyimpan riwayat tontonan user lengkap dengan pemberian rating angka dan ulasan teks tertulis.
5. **AI Movie Recommendation:** Integrasi **Google Gemini LLM (Model: `gemini-3.1-flash-lite`)** yang dikunci secara ketat agar hanya merekomendasikan film dari 20 subset data lokal berdasarkan preferensi prompt pengguna dengan keluaran format JSON terstruktur.

---

## 💻 Prasyarat Sistem (Prerequisites)

Pastikan perangkat Anda sudah terpasang:
* Python 3.10 atau versi yang lebih baru.
* `pip3` (Python Package Installer).
* Google Gemini API Key (bisa didapatkan gratis melalui [Google AI Studio](https://google.com)).

---

## 🛠️ Langkah-Langkah Instalasi & Pengaturan (Setup Instructions)

Ikuti urutan perintah di bawah ini melalui terminal Linux Anda:

### 1. Kloning dan Masuk ke Folder Project
```bash
cd ~/movie-watchlist-starter
```

### 2. Install Seluruh Dependensi / Library yang Dibutuhkan
Instalasi Flask, CORS handler, sistem enkripsi password, JWT token generator, serta SDK resmi Google GenAI terbaru:
```bash
pip3 install Flask flask-cors PyJWT bcrypt google-genai python-dotenv pydantic
```

### 3. Konfigurasi API Key Gemini AI
Buat file bernama `.env` di direktori utama project (sejajar dengan file `app.py`):
```bash
nano .env
```
Masukkan baris berikut (ganti dengan kunci otorisasi rahasia `AQ.` atau `AIzaSy` milik Anda sendiri tanpa menggunakan tanda kutip):
```text
GEMINI_API_KEY=isi_api_key_anda_di_sini
```
*Simpan perubahan dengan menekan `Ctrl + O`, `Enter`, lalu keluar dengan `Ctrl + X`.*

---

## 🚀 Cara Menjalankan Aplikasi

### 1. Menyalakan Server Backend (Flask)
Eksekusi file utama backend menggunakan Python:
```bash
python3 app.py
```
Server backend akan aktif berjalan secara default di alamat `http://127.0.0.1:5000`.

### 2. Membuka Aplikasi Frontend
Buka folder `frontend/` dan jalankan file `index.html` menggunakan browser pilihan Anda. 
* Frontend secara otomatis dikonfigurasi untuk melakukan panggilan AJAX/Fetch langsung ke endpoint lokal port `5000` milik Flask.
* Anda bisa langsung menguji alur pembuatan akun baru (*Register*), masuk (*Login*), menandai *Watchlist*, mengisi *Review*, serta berinteraksi dengan kotak pencarian *AI Recommendation* secara visual.

---

## 📑 Spesifikasi Struktur Kontrak API (API Contract)

### 🔐 Autentikasi
* `POST /api/auth/register` - Mendaftarkan user baru. (Body: `username`, `email`, `password`)
* `POST /api/auth/login` - Masuk sistem & mendapatkan JWT Token. (Response: `token`, `user` object)

### 🎬 Movies
* `GET /api/movies` - Mengambil semua film. (Query params opsional: `?genre=...&search=...`)
* `GET /api/movies/:id` - Mengambil detail satu film berdasarkan ID.

### 📌 Watchlist (Protected)
* `GET /api/watchlist` - Melihat daftar film yang ingin ditonton oleh user aktif.
* `POST /api/watchlist` - Menambahkan film ke daftar. (Body: `movieId`)
* `DELETE /api/watchlist/:movieId` - Menghapus film dari daftar.

### 📝 Watched & Review (Protected)
* `GET /api/watched` - Melihat daftar riwayat film yang telah selesai ditonton beserta rating & ulasannya.
* `POST /api/watched` - Menambahkan riwayat tontonan baru. (Body: `movieId`, `rating`, `review`)

### 🤖 AI Recommendation
* `POST /api/movies/recommend` - Mengirimkan prompt preferensi ke Gemini AI untuk mendapatkan rekomendasi 1 film lokal terbaik dalam format JSON terstruktur (`movie_id` & `reasoning`).

