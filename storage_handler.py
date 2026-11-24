import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output_surat")

ROOMS_FILE = os.path.join(DATA_DIR, "rooms.txt")
RESIDENTS_FILE = os.path.join(DATA_DIR, "residents.txt")
VIOLATIONS_FILE = os.path.join(DATA_DIR, "violations.txt")
PERMITS_FILE = os.path.join(DATA_DIR, "permits.txt")
TRANSFERS_FILE = os.path.join(DATA_DIR, "transfers.txt")


def ensure_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def init_storage():
    """Membuat folder dan mengisi data awal (seed) jika file .txt belum tersedia."""
    ensure_directories()

    if not os.path.exists(ROOMS_FILE):
        initial_rooms = [
            {"kode": "A-101", "gedung": "Putra A", "lantai": 1, "gender": "L", "kapasitas": 4, "terisi": 2, "status": "Tersedia"},
            {"kode": "A-102", "gedung": "Putra A", "lantai": 1, "gender": "L", "kapasitas": 4, "terisi": 4, "status": "Penuh"},
            {"kode": "A-201", "gedung": "Putra A", "lantai": 2, "gender": "L", "kapasitas": 4, "terisi": 1, "status": "Tersedia"},
            {"kode": "B-101", "gedung": "Putri B", "lantai": 1, "gender": "P", "kapasitas": 4, "terisi": 2, "status": "Tersedia"},
            {"kode": "B-201", "gedung": "Putri B", "lantai": 2, "gender": "P", "kapasitas": 4, "terisi": 0, "status": "Tersedia"},
        ]
        save_rooms(initial_rooms)

    if not os.path.exists(RESIDENTS_FILE):
        initial_residents = [
            {"nim": "J0403261001", "nama": "Rizky Pratama", "prodi": "TRPL", "gender": "L", "kamar": "A-101", "tgl_masuk": "2026-08-15", "poin": 0, "status": "Aktif"},
            {"nim": "J0403261002", "nama": "Dimas Saputra", "prodi": "TRPL", "gender": "L", "kamar": "A-101", "tgl_masuk": "2026-08-15", "poin": 15, "status": "Aktif"},
            {"nim": "J0403261003", "nama": "Fajar Nugroho", "prodi": "TEK", "gender": "L", "kamar": "A-102", "tgl_masuk": "2026-08-16", "poin": 40, "status": "Aktif"},
            {"nim": "J0403261004", "nama": "Bagas Kurniawan", "prodi": "MAB", "gender": "L", "kamar": "A-102", "tgl_masuk": "2026-08-16", "poin": 0, "status": "Aktif"},
            {"nim": "J0403261005", "nama": "Ilham Ramadhan", "prodi": "INF", "gender": "L", "kamar": "A-102", "tgl_masuk": "2026-08-17", "poin": 10, "status": "Aktif"},
            {"nim": "J0403261006", "nama": "Hendra Wijaya", "prodi": "TRPL", "gender": "L", "kamar": "A-102", "tgl_masuk": "2026-08-17", "poin": 0, "status": "Aktif"},
            {"nim": "J0403261007", "nama": "Naufal Hakim", "prodi": "GZI", "gender": "L", "kamar": "A-201", "tgl_masuk": "2026-08-18", "poin": 0, "status": "Aktif"},
            {"nim": "J0403261011", "nama": "Nadia Putri", "prodi": "TRPL", "gender": "P", "kamar": "B-101", "tgl_masuk": "2026-08-15", "poin": 0, "status": "Aktif"},
            {"nim": "J0403261012", "nama": "Siti Aisyah", "prodi": "KMN", "gender": "P", "kamar": "B-101", "tgl_masuk": "2026-08-16", "poin": 10, "status": "Aktif"},
        ]
        save_residents(initial_residents)

    if not os.path.exists(VIOLATIONS_FILE):
        initial_violations = [
            {"id": "PLG-001", "nim": "J0403261002", "kode_aturan": "AT-02", "deskripsi": "Terlambat jam malam (>22.00)", "poin": 15, "tanggal": "2026-11-10"},
            {"id": "PLG-002", "nim": "J0403261003", "kode_aturan": "AT-05", "deskripsi": "Merusak fasilitas kamar", "poin": 40, "tanggal": "2026-11-12"},
            {"id": "PLG-003", "nim": "J0403261005", "kode_aturan": "AT-03", "deskripsi": "Kamar kotor saat inspeksi", "poin": 10, "tanggal": "2026-11-14"},
            {"id": "PLG-004", "nim": "J0403261012", "kode_aturan": "AT-03", "deskripsi": "Kamar kotor saat inspeksi", "poin": 10, "tanggal": "2026-11-15"},
        ]
        save_violations(initial_violations)

    if not os.path.exists(PERMITS_FILE):
        initial_permits = [
            {"id": "IZN-001", "nim": "J0403261001", "tujuan": "Pulang ke rumah orang tua (Bandung)", "tgl_keluar": "2026-11-27", "tgl_kembali": "2026-11-29", "status": "Disetujui"},
            {"id": "IZN-002", "nim": "J0403261011", "tujuan": "Kegiatan lomba hackathon kampus", "tgl_keluar": "2026-11-25", "tgl_kembali": "2026-11-26", "status": "Menunggu"},
        ]
        save_permits(initial_permits)

    if not os.path.exists(TRANSFERS_FILE):
        initial_transfers = [
            {"id": "MTS-001", "nim": "J0403261002", "kamar_asal": "A-201", "kamar_tujuan": "A-101", "alasan": "Penyesuaian teman satu prodi", "tanggal": "2026-10-05"},
        ]
        save_transfers(initial_transfers)


def load_rooms():
    rooms = []
    if not os.path.exists(ROOMS_FILE):
        return rooms
    with open(ROOMS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) == 7:
                rooms.append({
                    "kode": parts[0].strip(),
                    "gedung": parts[1].strip(),
                    "lantai": int(parts[2].strip()),
                    "gender": parts[3].strip(),
                    "kapasitas": int(parts[4].strip()),
                    "terisi": int(parts[5].strip()),
                    "status": parts[6].strip(),
                })
    return rooms


def save_rooms(rooms):
    ensure_directories()
    with open(ROOMS_FILE, "w", encoding="utf-8") as f:
        f.write("# KodeKamar|Gedung|Lantai|Gender|Kapasitas|Terisi|Status\n")
        for r in rooms:
            line = f"{r['kode']}|{r['gedung']}|{r['lantai']}|{r['gender']}|{r['kapasitas']}|{r['terisi']}|{r['status']}\n"
            f.write(line)


def load_residents():
    residents = []
    if not os.path.exists(RESIDENTS_FILE):
        return residents
    with open(RESIDENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) == 8:
                residents.append({
                    "nim": parts[0].strip(),
                    "nama": parts[1].strip(),
                    "prodi": parts[2].strip(),
                    "gender": parts[3].strip(),
                    "kamar": parts[4].strip(),
                    "tgl_masuk": parts[5].strip(),
                    "poin": int(parts[6].strip()),
                    "status": parts[7].strip(),
                })
    return residents


def save_residents(residents):
    ensure_directories()
    with open(RESIDENTS_FILE, "w", encoding="utf-8") as f:
        f.write("# NIM|Nama|Prodi|Gender|KodeKamar|TanggalMasuk|TotalPoin|Status\n")
        for res in residents:
            line = f"{res['nim']}|{res['nama']}|{res['prodi']}|{res['gender']}|{res['kamar']}|{res['tgl_masuk']}|{res['poin']}|{res['status']}\n"
            f.write(line)


def load_violations():
    violations = []
    if not os.path.exists(VIOLATIONS_FILE):
        return violations
    with open(VIOLATIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) == 6:
                violations.append({
                    "id": parts[0].strip(),
                    "nim": parts[1].strip(),
                    "kode_aturan": parts[2].strip(),
                    "deskripsi": parts[3].strip(),
                    "poin": int(parts[4].strip()),
                    "tanggal": parts[5].strip(),
                })
    return violations


def save_violations(violations):
    ensure_directories()
    with open(VIOLATIONS_FILE, "w", encoding="utf-8") as f:
        f.write("# IDPelanggaran|NIM|KodeAturan|Deskripsi|Poin|Tanggal\n")
        for v in violations:
            line = f"{v['id']}|{v['nim']}|{v['kode_aturan']}|{v['deskripsi']}|{v['poin']}|{v['tanggal']}\n"
            f.write(line)


def load_permits():
    permits = []
    if not os.path.exists(PERMITS_FILE):
        return permits
    with open(PERMITS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) == 6:
                permits.append({
                    "id": parts[0].strip(),
                    "nim": parts[1].strip(),
                    "tujuan": parts[2].strip(),
                    "tgl_keluar": parts[3].strip(),
                    "tgl_kembali": parts[4].strip(),
                    "status": parts[5].strip(),
                })
    return permits


def save_permits(permits):
    ensure_directories()
    with open(PERMITS_FILE, "w", encoding="utf-8") as f:
        f.write("# IDIzin|NIM|Tujuan|TanggalKeluar|TanggalKembali|Status\n")
        for p in permits:
            line = f"{p['id']}|{p['nim']}|{p['tujuan']}|{p['tgl_keluar']}|{p['tgl_kembali']}|{p['status']}\n"
            f.write(line)


def load_transfers():
    transfers = []
    if not os.path.exists(TRANSFERS_FILE):
        return transfers
    with open(TRANSFERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) == 6:
                transfers.append({
                    "id": parts[0].strip(),
                    "nim": parts[1].strip(),
                    "kamar_asal": parts[2].strip(),
                    "kamar_tujuan": parts[3].strip(),
                    "alasan": parts[4].strip(),
                    "tanggal": parts[5].strip(),
                })
    return transfers


def save_transfers(transfers):
    ensure_directories()
    with open(TRANSFERS_FILE, "w", encoding="utf-8") as f:
        f.write("# IDMutasi|NIM|KamarAsal|KamarTujuan|Alasan|Tanggal\n")
        for t in transfers:
            line = f"{t['id']}|{t['nim']}|{t['kamar_asal']}|{t['kamar_tujuan']}|{t['alasan']}|{t['tanggal']}\n"
            f.write(line)


def export_document_txt(filename, content):
    """Menyimpan dokumen resmi (Surat Izin / Surat Peringatan) ke file .txt fisik."""
    ensure_directories()
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.join("output_surat", filename)
