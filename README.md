# Dormitory Management System (CLI)

Aplikasi Manajemen Asrama Mahasiswa berbasis terminal menggunakan Python dengan penyimpanan murni file teks `.txt` (tanpa GUI dan tanpa DBMS).

## Cara Instalasi & Menjalankan
1. Buka terminal di dalam folder `dormitory_manager`.
2. Install library yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi:
   ```bash
   python main.py
   ```

## Pembagian Jobdesk Kelompok (3 Orang)
- **Anggota 1 (`storage_handler.py`)**: Manajemen File I/O `.txt` dengan delimiter pipa (`|`), inisialisasi data awal, serta ekspor dokumen surat resmi ke folder `output_surat/`.
- **Anggota 2 (`dorm_engine.py`)**: Logika bisnis CRUD (Kamar, Penghuni, Pelanggaran, Izin Keluar, Mutasi Kamar), penggunaan tipe data koleksi (`tuple`, `set`, `list`, `dict`), serta fitur *Auto-Assign* kamar.
- **Anggota 3 (`algo_utils.py` & `cli_ui.py`)**: Implementasi algoritma *Searching* (Binary Search & Linear Substring Search) dan *Sorting* manual (Merge Sort), manipulasi string (parser kode kamar & generator ID otomatis), serta antarmuka CLI (`rich`, `questionary`, `pyfiglet`).
