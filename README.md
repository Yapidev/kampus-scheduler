# CampusFlow (`kampus-scheduler`)

Website **Penjadwalan Mata Kuliah Kampus Otomatis** berbasis optimasi **Google OR-Tools CP-SAT** yang berfokus pada **efisiensi penggunaan setiap ruangan** (*Best-Fit Capacity*, pemadatan jadwal / minimasi *idle gap*, dan kesesuaian tipe/fasilitas/gedung).

## Fitur Utama

- **Generate Jadwal Otomatis (OR-Tools CP-SAT)**:
  - Bebas bentrok ruangan, dosen (+ co-dosen), dan kelas (+ kelas gabungan MKU).
  - Memenuhi blok SKS berurutan tanpa memotong jam istirahat (ISHOMA / Sholat Jumat).
  - Mendukung shift **Reguler** & **Karyawan**, batas SKS/hari, dan jam berhalangan dosen.
  - **Optimasi Efisiensi Ruangan**:
    1. *Best-Fit Kapasitas* (kelas kecil otomatis ditempatkan pada ruang kecil agar ruang besar hemat).
    2. *Anti-Gap & Pemadatan Ruangan* (menghilangkan celah slot menganggur antar perkuliahan).
    3. *Minimasi Pindah Gedung* & *Preferensi Waktu Dosen*.
- **Dashboard Analitik Efisiensi Ruangan**:
  - Skor Efisiensi Komposit, *Seat Fill Efficiency (%)*, Utilisasi Waktu Ruangan, Jumlah *Idle Gap*, status tiap ruangan (`Optimal`, `Oversized Match`, `Underutilized`, `High Load`, `Idle`), perbandingan gedung, dan heatmap okupansi (Hari × Slot).
- **Grid Jadwal Interaktif & Drag-and-Drop**:
  - Mode tampilan: **Matriks Semua Ruangan**, **Per Kelas/Prodi**, **Per Dosen**, **Per Ruangan**.
  - Validasi bentrok & proyeksi efisiensi kursi secara *real-time* saat memindah jadwal.
  - Kunci slot (`is_locked`) agar jadwal tertentu tidak berubah saat generate ulang.
- **Multi-Fakultas, Multi-Prodi & Periode Akademik** (`Draft` / `Published`).
- **Export Lengkap**: PDF, Excel (`.xlsx` dengan sheet Analitik Ruangan), dan iCalendar (`.ics`).

## Cara Menjalankan

### 1. Backend (FastAPI — Port 8000)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Database SQLite (`backend/kampus_scheduler.db`) otomatis dibuat dan diisi data contoh kampus saat pertama kali dijalankan. Untuk PostgreSQL produksi, atur environment variable `KAMPUS_DATABASE_URL`.

### 2. Frontend (Next.js — Port 3000)

```bash
cd frontend
npm install
npm run dev
```

Buka `http://localhost:3000` di browser.

## Pengujian Otomatis

```bash
# Backend unit & integration tests
cd backend && python -m pytest -v

# Frontend TypeScript & production build check
cd frontend && npx tsc --noEmit && npm run build
```
