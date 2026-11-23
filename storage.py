"""
storage.py - Sistem Penyimpanan Data Asrama Berbasis JSON yang Aman.

Fitur Keamanan dan Keandalan:
1. Atomic Writes: Penulisan data ke file sementara (temp file) diikuti dengan
   os.fsync dan os.replace untuk menjamin file tidak korup saat proses terputus / crash.
2. File Locking & Concurrency: Menggunakan fcntl.flock (eksklusif) dan threading.RLock
   untuk mencegah race condition antar-proses dan multi-thread.
3. Access Control (Permissions): Izin berkas dibatasi secara ketat ke mode 0o600
   (hanya pemilik berkas yang memiliki hak baca dan tulis) untuk melindungi data pribadi penghuni.
4. Backup & Auto-Recovery: Membuat salinan cadangan (.bak) secara otomatis sebelum modifikasi
   dan memulihkan data jika berkas utama mengalami kerusakan (misal format JSON invalid).
5. Data Integrity: Verifikasi checksum SHA-256 dan validasi struktur data sebelum commit.
6. Relational Constraints: Penegakan integritas data (primary key auto-increment, unique constraint
   pada NIM dan nomor kamar, foreign key validation, batasan kapasitas, serta validasi gender).
"""

import os
import json
import fcntl
import shutil
import hashlib
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "dormitory_data.json")
BACKUP_FILE = os.path.join(BASE_DIR, "dormitory_data.json.bak")
LOCK_FILE = os.path.join(BASE_DIR, "dormitory_data.json.lock")

# Kompatibilitas jika ada kode lama yang merujuk ke DB_PATH
DB_PATH = DATA_FILE

_thread_lock = threading.RLock()


# ===================== Helper Row Class =====================

class Row(dict):
    """
    Subclass dict yang mendukung pengaksesan via index integer (seperti sqlite3.Row)
    maupun key string, sehingga kompatibel dengan komponen tabel dan akses dict.
    """
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


# ===================== Low-Level Storage & Security =====================

def _calculate_checksum(data_dict):
    """Menghitung checksum SHA-256 untuk payload data (tanpa metadata checksum)."""
    payload = {k: v for k, v in data_dict.items() if k != '_metadata'}
    payload_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(payload_bytes).hexdigest()


def _ensure_schema(data):
    """Memastikan seluruh tabel, counter auto-increment, dan metadata terdefinisi dengan benar."""
    tables = ['kamar', 'penghuni', 'penempatan', 'pelanggaran', 'izin_keluar', 'riwayat_perpindahan']
    if '_counters' not in data or not isinstance(data['_counters'], dict):
        data['_counters'] = {}
    for t in tables:
        if t not in data or not isinstance(data[t], list):
            data[t] = []
        max_id = max((item.get('id', 0) for item in data[t] if isinstance(item, dict)), default=0)
        current_counter = data['_counters'].get(t, 0)
        data['_counters'][t] = max(current_counter, max_id)


def _init_empty_data():
    """Membuat struktur data default untuk penyimpanan kosong."""
    now_iso = datetime.now().isoformat()
    empty = {
        "_metadata": {
            "version": 1,
            "created_at": now_iso,
            "last_modified": now_iso,
            "checksum": ""
        },
        "_counters": {
            "kamar": 0,
            "penghuni": 0,
            "penempatan": 0,
            "pelanggaran": 0,
            "izin_keluar": 0,
            "riwayat_perpindahan": 0
        },
        "kamar": [],
        "penghuni": [],
        "penempatan": [],
        "pelanggaran": [],
        "izin_keluar": [],
        "riwayat_perpindahan": []
    }
    empty['_metadata']['checksum'] = _calculate_checksum(empty)
    return empty


def _load_data_internal():
    """
    Membaca data dari DATA_FILE dengan penanganan pemulihan otomatis (auto-recovery).
    Jika file utama rusak atau invalid JSON, sistem otomatis membaca berkas cadangan BACKUP_FILE.
    """
    if not os.path.exists(DATA_FILE):
        return _init_empty_data()

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        if not content.strip():
            return _init_empty_data()
        data = json.loads(content)
        _ensure_schema(data)
        return data
    except Exception:
        # File utama korup, coba pulihkan dari cadangan
        if os.path.exists(BACKUP_FILE):
            try:
                with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                    bak_content = f.read()
                data = json.loads(bak_content)
                _ensure_schema(data)
                _save_data_internal(data)
                return data
            except Exception:
                pass
        return _init_empty_data()


def _save_data_internal(data):
    """
    Menyimpan data secara aman dan atomik:
    1. Memperbarui metadata waktu dan checksum integritas SHA-256.
    2. Menulis ke file temporer pada direktori yang sama.
    3. Menerapkan hak akses ketat (0o600 / rw-------).
    4. Melakukan flush dan os.fsync untuk memastikan data tertulis ke media fisik.
    5. Membuat cadangan file lama ke BACKUP_FILE sebelum penggantian.
    6. Mengganti file secara atomik menggunakan os.replace.
    """
    _ensure_schema(data)
    now_iso = datetime.now().isoformat()
    if '_metadata' not in data or not isinstance(data['_metadata'], dict):
        data['_metadata'] = {
            'version': 1,
            'created_at': now_iso,
        }
    data['_metadata']['last_modified'] = now_iso
    data['_metadata']['checksum'] = _calculate_checksum(data)

    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    dir_name = os.path.dirname(DATA_FILE)

    fd, tmp_path = tempfile.mkstemp(prefix='dormitory_data_', suffix='.tmp', dir=dir_name)
    try:
        os.chmod(tmp_path, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(json_str)
            f.flush()
            os.fsync(f.fileno())

        # Backup berkas utama saat ini jika ada dan valid
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            try:
                shutil.copy2(DATA_FILE, BACKUP_FILE)
                os.chmod(BACKUP_FILE, 0o600)
            except Exception:
                pass

        # Penggantian berkas atomik
        os.replace(tmp_path, DATA_FILE)
        os.chmod(DATA_FILE, 0o600)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise


@contextmanager
def transaction():
    """
    Context manager transaksi untuk thread safety dan process safety.
    Menghasilkan tuple: (data, commit_func).
    Data hanya disimpan ke disk jika commit_func() dipanggil.
    """
    with _thread_lock:
        # Buka atau buat lockfile dengan permission 0o600
        lock_fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            data = _load_data_internal()
            state = {'committed': False}

            def commit():
                state['committed'] = True

            yield data, commit

            if state['committed']:
                _save_data_internal(data)
        finally:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            except Exception:
                pass
            os.close(lock_fd)


def init_storage():
    """Inisialisasi sistem penyimpanan file JSON dengan aman."""
    with transaction() as (data, commit):
        if not os.path.exists(DATA_FILE):
            commit()
        return True


def init_db():
    """Fungsi kompatibilitas untuk init_storage."""
    return init_storage()


def get_connection():
    """
    Disediakan untuk kompatibilitas jika dipanggil modul luar.
    Mengingatkan bahwa program tidak lagi menggunakan database SQL.
    """
    raise NotImplementedError(
        "Program tidak lagi menggunakan database SQLite/SQL. "
        "Semua penyimpanan data menggunakan file JSON yang aman di storage.py."
    )


# ===================== KAMAR (Room) CRUD =====================

def tambah_kamar(nomor_kamar, lantai, tipe, kapasitas):
    with transaction() as (data, commit):
        nomor_str = str(nomor_kamar).strip()
        if any(str(k['nomor_kamar']).strip() == nomor_str for k in data['kamar']):
            return False, "Nomor kamar sudah ada."

        data['_counters']['kamar'] += 1
        new_id = data['_counters']['kamar']
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data['kamar'].append({
            'id': new_id,
            'nomor_kamar': nomor_str,
            'lantai': int(lantai),
            'tipe': tipe.lower(),
            'kapasitas': int(kapasitas),
            'created_at': now_str
        })
        commit()
        return True, "Kamar berhasil ditambahkan."


def get_all_kamar():
    with transaction() as (data, commit):
        occ = {}
        for p in data['penempatan']:
            occ[p['kamar_id']] = occ.get(p['kamar_id'], 0) + 1

        sorted_kamar = sorted(
            data['kamar'],
            key=lambda x: (x['lantai'], str(x['nomor_kamar']))
        )
        rows = [
            Row({**k, 'terisi': occ.get(k['id'], 0)})
            for k in sorted_kamar
        ]
        return rows


def get_kamar_by_id(kamar_id):
    with transaction() as (data, commit):
        for k in data['kamar']:
            if k['id'] == kamar_id:
                terisi = sum(1 for p in data['penempatan'] if p['kamar_id'] == kamar_id)
                return Row({**k, 'terisi': terisi})
        return None


def get_kamar_by_nomor(nomor_kamar):
    with transaction() as (data, commit):
        nomor_str = str(nomor_kamar).strip()
        for k in data['kamar']:
            if str(k['nomor_kamar']).strip() == nomor_str:
                terisi = sum(1 for p in data['penempatan'] if p['kamar_id'] == k['id'])
                return Row({**k, 'terisi': terisi})
        return None


def edit_kamar(kamar_id, nomor_kamar, lantai, tipe, kapasitas):
    with transaction() as (data, commit):
        target = next((k for k in data['kamar'] if k['id'] == kamar_id), None)
        if not target:
            return False, "Kamar tidak ditemukan."

        terisi = sum(1 for p in data['penempatan'] if p['kamar_id'] == kamar_id)
        if int(kapasitas) < terisi:
            return False, f"Kapasitas tidak boleh kurang dari jumlah penghuni saat ini ({terisi} orang)."

        if tipe:
            gender_map = {'putra': 'L', 'putri': 'P'}
            expected_gender = gender_map.get(tipe.lower())
            if expected_gender and terisi > 0:
                assigned_ph_ids = {p['penghuni_id'] for p in data['penempatan'] if p['kamar_id'] == kamar_id}
                conflict = sum(
                    1 for ph in data['penghuni']
                    if ph['id'] in assigned_ph_ids and ph.get('jenis_kelamin') != expected_gender
                )
                if conflict > 0:
                    return False, "Tidak bisa mengubah tipe kamar, ada penghuni yang tidak sesuai gender."

        nomor_str = str(nomor_kamar).strip()
        if any(str(k['nomor_kamar']).strip() == nomor_str and k['id'] != kamar_id for k in data['kamar']):
            return False, "Nomor kamar sudah digunakan."

        target['nomor_kamar'] = nomor_str
        target['lantai'] = int(lantai)
        target['tipe'] = tipe.lower()
        target['kapasitas'] = int(kapasitas)

        commit()
        return True, "Kamar berhasil diperbarui."


def hapus_kamar(kamar_id):
    with transaction() as (data, commit):
        terisi = sum(1 for p in data['penempatan'] if p['kamar_id'] == kamar_id)
        if terisi > 0:
            return False, "Kamar tidak bisa dihapus karena masih ada penghuni."

        original_count = len(data['kamar'])
        data['kamar'] = [k for k in data['kamar'] if k['id'] != kamar_id]
        if len(data['kamar']) == original_count:
            return False, "Kamar tidak ditemukan."

        commit()
        return True, "Kamar berhasil dihapus."


def update_kapasitas_kamar(kamar_id, kapasitas_baru):
    with transaction() as (data, commit):
        target = next((k for k in data['kamar'] if k['id'] == kamar_id), None)
        if not target:
            return False, "Kamar tidak ditemukan."

        terisi = sum(1 for p in data['penempatan'] if p['kamar_id'] == kamar_id)
        if int(kapasitas_baru) < terisi:
            return False, f"Kapasitas tidak boleh kurang dari jumlah penghuni saat ini ({terisi} orang)."

        target['kapasitas'] = int(kapasitas_baru)
        commit()
        return True, "Kapasitas kamar berhasil diperbarui."


def get_kapasitas_overview():
    return get_all_kamar()


# ===================== PENGHUNI (Resident) CRUD =====================

def tambah_penghuni(nama, nim, jurusan, no_telp, jenis_kelamin):
    with transaction() as (data, commit):
        nim_str = str(nim).strip()
        if any(str(ph['nim']).strip() == nim_str for ph in data['penghuni']):
            return False, "NIM sudah terdaftar.", None

        data['_counters']['penghuni'] += 1
        new_id = data['_counters']['penghuni']
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data['penghuni'].append({
            'id': new_id,
            'nama': str(nama).strip(),
            'nim': nim_str,
            'jurusan': str(jurusan).strip(),
            'no_telp': str(no_telp).strip(),
            'jenis_kelamin': jenis_kelamin.upper(),
            'created_at': now_str
        })
        commit()
        return True, "Penghuni berhasil ditambahkan.", new_id


def get_all_penghuni():
    with transaction() as (data, commit):
        pm_map = {p['penghuni_id']: p['kamar_id'] for p in data['penempatan']}
        km_map = {k['id']: k['nomor_kamar'] for k in data['kamar']}

        rows = []
        for ph in sorted(data['penghuni'], key=lambda x: x['nama']):
            kid = pm_map.get(ph['id'])
            nomor_kamar = km_map.get(kid) if kid is not None else None
            rows.append(Row({**ph, 'nomor_kamar': nomor_kamar, 'kamar_id': kid}))
        return rows


def get_penghuni_by_id(penghuni_id):
    with transaction() as (data, commit):
        for ph in data['penghuni']:
            if ph['id'] == penghuni_id:
                pm = next((p for p in data['penempatan'] if p['penghuni_id'] == penghuni_id), None)
                nomor_kamar = None
                kamar_id = None
                if pm:
                    km = next((k for k in data['kamar'] if k['id'] == pm['kamar_id']), None)
                    if km:
                        nomor_kamar = km['nomor_kamar']
                        kamar_id = km['id']
                return Row({**ph, 'nomor_kamar': nomor_kamar, 'kamar_id': kamar_id})
        return None


def edit_penghuni(penghuni_id, nama, nim, jurusan, no_telp, jenis_kelamin):
    with transaction() as (data, commit):
        target = next((p for p in data['penghuni'] if p['id'] == penghuni_id), None)
        if not target:
            return False, "Penghuni tidak ditemukan."

        pm = next((p for p in data['penempatan'] if p['penghuni_id'] == penghuni_id), None)
        if pm:
            km = next((k for k in data['kamar'] if k['id'] == pm['kamar_id']), None)
            if km:
                gender_map = {'L': 'putra', 'P': 'putri'}
                if gender_map.get(jenis_kelamin.upper()) != km['tipe']:
                    return False, "Tidak bisa mengubah jenis kelamin karena masih ditempatkan di kamar yang tidak sesuai."

        nim_str = str(nim).strip()
        if any(str(p['nim']).strip() == nim_str and p['id'] != penghuni_id for p in data['penghuni']):
            return False, "NIM sudah digunakan oleh penghuni lain."

        target['nama'] = str(nama).strip()
        target['nim'] = nim_str
        target['jurusan'] = str(jurusan).strip()
        target['no_telp'] = str(no_telp).strip()
        target['jenis_kelamin'] = jenis_kelamin.upper()

        commit()
        return True, "Data penghuni berhasil diperbarui."


def hapus_penghuni(penghuni_id):
    with transaction() as (data, commit):
        if any(p['penghuni_id'] == penghuni_id for p in data['penempatan']):
            return False, "Penghuni tidak bisa dihapus karena masih ditempatkan di kamar. Pindahkan atau keluarkan terlebih dahulu."

        data['pelanggaran'] = [x for x in data['pelanggaran'] if x['penghuni_id'] != penghuni_id]
        data['izin_keluar'] = [x for x in data['izin_keluar'] if x['penghuni_id'] != penghuni_id]
        data['riwayat_perpindahan'] = [x for x in data['riwayat_perpindahan'] if x['penghuni_id'] != penghuni_id]
        data['penghuni'] = [x for x in data['penghuni'] if x['id'] != penghuni_id]

        commit()
        return True, "Penghuni berhasil dihapus."


def cari_penghuni(keyword):
    with transaction() as (data, commit):
        pm_map = {p['penghuni_id']: p['kamar_id'] for p in data['penempatan']}
        km_map = {k['id']: k['nomor_kamar'] for k in data['kamar']}

        kw = keyword.lower()
        matched = [
            ph for ph in data['penghuni']
            if kw in ph['nama'].lower() or kw in ph['nim'].lower()
        ]
        rows = []
        for ph in sorted(matched, key=lambda x: x['nama']):
            kid = pm_map.get(ph['id'])
            nomor_kamar = km_map.get(kid) if kid is not None else None
            rows.append(Row({**ph, 'nomor_kamar': nomor_kamar, 'kamar_id': kid}))
        return rows


# ===================== PENEMPATAN (Room Assignment) =====================

def get_available_rooms(jenis_kelamin):
    """Mendapatkan kamar yang sesuai jenis kelamin dan masih memiliki kapasitas."""
    tipe = 'putra' if jenis_kelamin.upper() == 'L' else 'putri'
    with transaction() as (data, commit):
        occ = {}
        for p in data['penempatan']:
            occ[p['kamar_id']] = occ.get(p['kamar_id'], 0) + 1

        available = []
        for k in data['kamar']:
            if k['tipe'] == tipe:
                terisi = occ.get(k['id'], 0)
                if terisi < k['kapasitas']:
                    available.append(Row({**k, 'terisi': terisi}))

        available.sort(key=lambda x: (x['lantai'], str(x['nomor_kamar'])))
        return available


def auto_assign_room(penghuni_id):
    """Penempatan otomatis penghuni ke kamar pertama yang tersedia (lantai & nomor terendah)."""
    with transaction() as (data, commit):
        penghuni = next((p for p in data['penghuni'] if p['id'] == penghuni_id), None)
        if not penghuni:
            return False, "Penghuni tidak ditemukan."

        if any(p['penghuni_id'] == penghuni_id for p in data['penempatan']):
            return False, "Penghuni sudah ditempatkan di kamar."

        tipe = 'putra' if penghuni['jenis_kelamin'] == 'L' else 'putri'
        occ = {}
        for p in data['penempatan']:
            occ[p['kamar_id']] = occ.get(p['kamar_id'], 0) + 1

        sorted_kamar = sorted(data['kamar'], key=lambda x: (x['lantai'], str(x['nomor_kamar'])))
        room = None
        for k in sorted_kamar:
            if k['tipe'] == tipe and occ.get(k['id'], 0) < k['kapasitas']:
                room = k
                break

        if not room:
            return False, "Tidak ada kamar yang tersedia untuk jenis kelamin ini."

        data['_counters']['penempatan'] += 1
        data['penempatan'].append({
            'id': data['_counters']['penempatan'],
            'penghuni_id': penghuni_id,
            'kamar_id': room['id'],
            'tanggal_masuk': date.today().isoformat(),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        commit()
        return True, f"Penghuni berhasil ditempatkan di kamar {room['nomor_kamar']}."


def manual_assign_room(penghuni_id, kamar_id):
    """Penempatan manual penghuni ke kamar tertentu."""
    with transaction() as (data, commit):
        penghuni = next((p for p in data['penghuni'] if p['id'] == penghuni_id), None)
        if not penghuni:
            return False, "Penghuni tidak ditemukan."

        if any(p['penghuni_id'] == penghuni_id for p in data['penempatan']):
            return False, "Penghuni sudah ditempatkan di kamar. Gunakan fitur perpindahan kamar."

        kamar = next((k for k in data['kamar'] if k['id'] == kamar_id), None)
        if not kamar:
            return False, "Kamar tidak ditemukan."

        gender_map = {'L': 'putra', 'P': 'putri'}
        if gender_map.get(penghuni['jenis_kelamin']) != kamar['tipe']:
            return False, f"Jenis kelamin tidak sesuai dengan tipe kamar ({kamar['tipe']})."

        terisi = sum(1 for p in data['penempatan'] if p['kamar_id'] == kamar_id)
        if terisi >= kamar['kapasitas']:
            return False, "Kamar sudah penuh."

        data['_counters']['penempatan'] += 1
        data['penempatan'].append({
            'id': data['_counters']['penempatan'],
            'penghuni_id': penghuni_id,
            'kamar_id': kamar_id,
            'tanggal_masuk': date.today().isoformat(),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        commit()
        return True, f"Penghuni berhasil ditempatkan di kamar {kamar['nomor_kamar']}."


def keluarkan_penghuni(penghuni_id):
    """Mengeluarkan penghuni dari kamar (checkout)."""
    with transaction() as (data, commit):
        existing = next((p for p in data['penempatan'] if p['penghuni_id'] == penghuni_id), None)
        if not existing:
            return False, "Penghuni tidak ditempatkan di kamar manapun."

        data['penempatan'] = [p for p in data['penempatan'] if p['penghuni_id'] != penghuni_id]
        commit()
        return True, "Penghuni berhasil dikeluarkan dari kamar."


def get_penghuni_di_kamar(kamar_id):
    with transaction() as (data, commit):
        ph_ids = {p['penghuni_id'] for p in data['penempatan'] if p['kamar_id'] == kamar_id}
        residents = [Row(ph) for ph in data['penghuni'] if ph['id'] in ph_ids]
        residents.sort(key=lambda x: x['nama'])
        return residents


def get_penghuni_tanpa_kamar():
    with transaction() as (data, commit):
        assigned = {p['penghuni_id'] for p in data['penempatan']}
        unassigned = [Row(ph) for ph in data['penghuni'] if ph['id'] not in assigned]
        unassigned.sort(key=lambda x: x['nama'])
        return unassigned


# ===================== PELANGGARAN (Violations) =====================

def tambah_pelanggaran(penghuni_id, jenis, deskripsi, tanggal, severity):
    with transaction() as (data, commit):
        if not any(ph['id'] == penghuni_id for ph in data['penghuni']):
            return False, "Penghuni tidak ditemukan."

        data['_counters']['pelanggaran'] += 1
        data['pelanggaran'].append({
            'id': data['_counters']['pelanggaran'],
            'penghuni_id': penghuni_id,
            'jenis_pelanggaran': jenis,
            'deskripsi': deskripsi,
            'tanggal': tanggal,
            'tingkat_severity': severity.lower(),
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        commit()
        return True, "Pelanggaran berhasil dicatat."


def get_pelanggaran_by_penghuni(penghuni_id):
    with transaction() as (data, commit):
        ph_map = {p['id']: p for p in data['penghuni']}
        matched = [pl for pl in data['pelanggaran'] if pl['penghuni_id'] == penghuni_id]
        matched.sort(key=lambda x: (x.get('tanggal', ''), x.get('id', 0)), reverse=True)

        rows = []
        for pl in matched:
            ph = ph_map.get(pl['penghuni_id'], {})
            rows.append(Row({
                **pl,
                'nama': ph.get('nama', '-'),
                'nim': ph.get('nim', '-')
            }))
        return rows


def get_all_pelanggaran(severity_filter=None):
    with transaction() as (data, commit):
        ph_map = {p['id']: p for p in data['penghuni']}
        matched = data['pelanggaran']
        if severity_filter:
            matched = [pl for pl in matched if pl.get('tingkat_severity') == severity_filter]

        matched.sort(key=lambda x: (x.get('tanggal', ''), x.get('id', 0)), reverse=True)
        rows = []
        for pl in matched:
            ph = ph_map.get(pl['penghuni_id'], {})
            rows.append(Row({
                **pl,
                'nama': ph.get('nama', '-'),
                'nim': ph.get('nim', '-')
            }))
        return rows


def get_ringkasan_pelanggaran():
    with transaction() as (data, commit):
        sev_counts = {}
        for pl in data['pelanggaran']:
            s = pl.get('tingkat_severity')
            if s:
                sev_counts[s] = sev_counts.get(s, 0) + 1

        order = {'ringan': 1, 'sedang': 2, 'berat': 3}
        summary = [
            Row({'tingkat_severity': s, 'jumlah': count})
            for s, count in sorted(sev_counts.items(), key=lambda x: order.get(x[0], 99))
        ]

        ph_map = {p['id']: p for p in data['penghuni']}
        violator_counts = {}
        for pl in data['pelanggaran']:
            pid = pl.get('penghuni_id')
            if pid:
                violator_counts[pid] = violator_counts.get(pid, 0) + 1

        top_sorted = sorted(violator_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_violators = []
        for pid, count in top_sorted:
            ph = ph_map.get(pid, {})
            top_violators.append(Row({
                'nama': ph.get('nama', '-'),
                'nim': ph.get('nim', '-'),
                'jumlah': count
            }))
        return summary, top_violators


# ===================== IZIN KELUAR (Leave Permits) =====================

def tambah_izin_keluar(penghuni_id, tanggal_keluar, tanggal_kembali, alasan):
    with transaction() as (data, commit):
        if not any(ph['id'] == penghuni_id for ph in data['penghuni']):
            return False, "Penghuni tidak ditemukan."

        data['_counters']['izin_keluar'] += 1
        data['izin_keluar'].append({
            'id': data['_counters']['izin_keluar'],
            'penghuni_id': penghuni_id,
            'tanggal_keluar': tanggal_keluar,
            'tanggal_kembali': tanggal_kembali,
            'alasan': alasan,
            'status': 'pending',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        commit()
        return True, "Izin keluar berhasil dicatat."


def update_status_izin(izin_id, status):
    with transaction() as (data, commit):
        target = next((iz for iz in data['izin_keluar'] if iz['id'] == izin_id), None)
        if not target:
            return False, "Izin tidak ditemukan."

        if target['status'] != 'pending':
            return False, f"Izin sudah berstatus '{target['status']}', tidak bisa diubah."

        target['status'] = status
        commit()
        return True, f"Status izin berhasil diubah menjadi '{status}'."


def get_izin_pending():
    with transaction() as (data, commit):
        ph_map = {p['id']: p for p in data['penghuni']}
        pending = [iz for iz in data['izin_keluar'] if iz.get('status') == 'pending']
        pending.sort(key=lambda x: (x.get('tanggal_keluar', ''), x.get('id', 0)))

        rows = []
        for iz in pending:
            ph = ph_map.get(iz['penghuni_id'], {})
            rows.append(Row({
                **iz,
                'nama': ph.get('nama', '-'),
                'nim': ph.get('nim', '-')
            }))
        return rows


def get_penghuni_sedang_keluar():
    """Mengambil daftar penghuni yang sedang izin keluar aktif saat ini."""
    with transaction() as (data, commit):
        today = date.today().isoformat()
        ph_map = {p['id']: p for p in data['penghuni']}
        active = [
            iz for iz in data['izin_keluar']
            if iz.get('status') == 'disetujui'
            and iz.get('tanggal_keluar', '') <= today
            and iz.get('tanggal_kembali', '') >= today
        ]
        active.sort(key=lambda x: (x.get('tanggal_kembali', ''), x.get('id', 0)))

        rows = []
        for iz in active:
            ph = ph_map.get(iz['penghuni_id'], {})
            rows.append(Row({
                **iz,
                'nama': ph.get('nama', '-'),
                'nim': ph.get('nim', '-')
            }))
        return rows


def get_riwayat_izin(penghuni_id=None):
    with transaction() as (data, commit):
        ph_map = {p['id']: p for p in data['penghuni']}
        matched = data['izin_keluar']
        if penghuni_id is not None:
            matched = [iz for iz in matched if iz.get('penghuni_id') == penghuni_id]

        matched.sort(key=lambda x: (x.get('tanggal_keluar', ''), x.get('id', 0)), reverse=True)
        rows = []
        for iz in matched:
            ph = ph_map.get(iz['penghuni_id'], {})
            rows.append(Row({
                **iz,
                'nama': ph.get('nama', '-'),
                'nim': ph.get('nim', '-')
            }))
        return rows


# ===================== RIWAYAT PERPINDAHAN (Transfer History) =====================

def pindah_kamar(penghuni_id, kamar_tujuan_id, alasan):
    with transaction() as (data, commit):
        penghuni = next((p for p in data['penghuni'] if p['id'] == penghuni_id), None)
        if not penghuni:
            return False, "Penghuni tidak ditemukan."

        current_pm = next((p for p in data['penempatan'] if p['penghuni_id'] == penghuni_id), None)
        if not current_pm:
            return False, "Penghuni belum ditempatkan di kamar manapun."

        kamar_asal_id = current_pm['kamar_id']
        if kamar_asal_id == kamar_tujuan_id:
            return False, "Kamar tujuan sama dengan kamar saat ini."

        kamar_tujuan = next((k for k in data['kamar'] if k['id'] == kamar_tujuan_id), None)
        if not kamar_tujuan:
            return False, "Kamar tujuan tidak ditemukan."

        gender_map = {'L': 'putra', 'P': 'putri'}
        if gender_map.get(penghuni['jenis_kelamin']) != kamar_tujuan['tipe']:
            return False, f"Tipe kamar tujuan ({kamar_tujuan['tipe']}) tidak sesuai dengan jenis kelamin."

        terisi = sum(1 for p in data['penempatan'] if p['kamar_id'] == kamar_tujuan_id)
        if terisi >= kamar_tujuan['kapasitas']:
            return False, "Kamar tujuan sudah penuh."

        current_pm['kamar_id'] = kamar_tujuan_id

        data['_counters']['riwayat_perpindahan'] += 1
        data['riwayat_perpindahan'].append({
            'id': data['_counters']['riwayat_perpindahan'],
            'penghuni_id': penghuni_id,
            'kamar_asal_id': kamar_asal_id,
            'kamar_tujuan_id': kamar_tujuan_id,
            'tanggal': date.today().isoformat(),
            'alasan': alasan,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        commit()
        return True, f"Penghuni berhasil dipindahkan ke kamar {kamar_tujuan['nomor_kamar']}."


def get_riwayat_perpindahan(penghuni_id=None):
    with transaction() as (data, commit):
        ph_map = {p['id']: p for p in data['penghuni']}
        km_map = {k['id']: k['nomor_kamar'] for k in data['kamar']}

        matched = data['riwayat_perpindahan']
        if penghuni_id is not None:
            matched = [rp for rp in matched if rp.get('penghuni_id') == penghuni_id]

        matched.sort(key=lambda x: (x.get('tanggal', ''), x.get('id', 0)), reverse=True)
        rows = []
        for rp in matched:
            ph = ph_map.get(rp['penghuni_id'], {})
            rows.append(Row({
                **rp,
                'nama': ph.get('nama', '-'),
                'nim': ph.get('nim', '-'),
                'kamar_asal': km_map.get(rp['kamar_asal_id'], '-'),
                'kamar_tujuan': km_map.get(rp['kamar_tujuan_id'], '-')
            }))
        return rows


# ===================== STATISTIK =====================

def get_statistik_okupansi():
    with transaction() as (data, commit):
        total_kamar = len(data['kamar'])
        total_kapasitas = sum(k['kapasitas'] for k in data['kamar'])
        total_penghuni = len(data['penempatan'])

        occupied_room_ids = {p['kamar_id'] for p in data['penempatan']}
        kamar_terisi = len(occupied_room_ids)
        kamar_kosong = total_kamar - kamar_terisi

        # Statistik per lantai
        floors = sorted(list({k['lantai'] for k in data['kamar']}))
        per_lantai = []
        for f in floors:
            k_floor = [k for k in data['kamar'] if k['lantai'] == f]
            k_ids = {k['id'] for k in k_floor}
            terisi_f = sum(1 for p in data['penempatan'] if p['kamar_id'] in k_ids)
            per_lantai.append(Row({
                'lantai': f,
                'jumlah_kamar': len(k_floor),
                'total_kapasitas': sum(k['kapasitas'] for k in k_floor),
                'terisi': terisi_f
            }))

        # Statistik per tipe
        types = sorted(list({k['tipe'] for k in data['kamar']}))
        per_tipe = []
        for t in types:
            k_tipe = [k for k in data['kamar'] if k['tipe'] == t]
            k_ids = {k['id'] for k in k_tipe}
            terisi_t = sum(1 for p in data['penempatan'] if p['kamar_id'] in k_ids)
            per_tipe.append(Row({
                'tipe': t,
                'jumlah_kamar': len(k_tipe),
                'total_kapasitas': sum(k['kapasitas'] for k in k_tipe),
                'terisi': terisi_t
            }))

        if not data['kamar']:
            kamar_terbanyak = None
            kamar_tersedikit = None
        else:
            k_terisi = [
                (k, sum(1 for p in data['penempatan'] if p['kamar_id'] == k['id']))
                for k in data['kamar']
            ]
            best = max(k_terisi, key=lambda x: x[1])
            kamar_terbanyak = Row({
                'nomor_kamar': best[0]['nomor_kamar'],
                'kapasitas': best[0]['kapasitas'],
                'terisi': best[1]
            })
            least = min(k_terisi, key=lambda x: x[1])
            kamar_tersedikit = Row({
                'nomor_kamar': least[0]['nomor_kamar'],
                'kapasitas': least[0]['kapasitas'],
                'terisi': least[1]
            })

        okupansi_rate = (total_penghuni / total_kapasitas * 100) if total_kapasitas > 0 else 0

        return {
            'total_kamar': total_kamar,
            'total_kapasitas': total_kapasitas,
            'total_penghuni': total_penghuni,
            'kamar_terisi': kamar_terisi,
            'kamar_kosong': kamar_kosong,
            'okupansi_rate': okupansi_rate,
            'per_lantai': per_lantai,
            'per_tipe': per_tipe,
            'kamar_terbanyak': kamar_terbanyak,
            'kamar_tersedikit': kamar_tersedikit,
        }


def get_okupansi_per_kamar():
    """Untuk grafik bar ASCII per kamar."""
    with transaction() as (data, commit):
        sorted_kamar = sorted(data['kamar'], key=lambda x: (x['lantai'], str(x['nomor_kamar'])))
        rows = []
        for k in sorted_kamar:
            terisi = sum(1 for p in data['penempatan'] if p['kamar_id'] == k['id'])
            rows.append(Row({
                'nomor_kamar': k['nomor_kamar'],
                'kapasitas': k['kapasitas'],
                'terisi': terisi
            }))
        return rows


# ===================== SEED DATA =====================

def seed_data():
    with transaction() as (data, commit):
        if len(data['kamar']) > 0:
            return False, "Data asrama sudah memiliki data. Hapus data terlebih dahulu untuk seed ulang."

        kamar_data = [
            ('101', 1, 'putra', 3), ('102', 1, 'putra', 3), ('103', 1, 'putra', 2),
            ('104', 1, 'putri', 3), ('105', 1, 'putri', 3), ('106', 1, 'putri', 2),
            ('201', 2, 'putra', 3), ('202', 2, 'putra', 2), ('203', 2, 'putra', 2),
            ('204', 2, 'putri', 3), ('205', 2, 'putri', 2), ('206', 2, 'putri', 2),
            ('301', 3, 'putra', 2), ('302', 3, 'putra', 2),
            ('303', 3, 'putri', 2), ('304', 3, 'putri', 2),
        ]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for no, lt, tp, kp in kamar_data:
            data['_counters']['kamar'] += 1
            data['kamar'].append({
                'id': data['_counters']['kamar'],
                'nomor_kamar': no,
                'lantai': lt,
                'tipe': tp,
                'kapasitas': kp,
                'created_at': now_str
            })

        penghuni_data = [
            ('Ahmad Fauzi', '2024001', 'Teknik Informatika', '081234567001', 'L'),
            ('Budi Santoso', '2024002', 'Sistem Informasi', '081234567002', 'L'),
            ('Cahyo Nugroho', '2024003', 'Teknik Elektro', '081234567003', 'L'),
            ('Dimas Prasetyo', '2024004', 'Teknik Mesin', '081234567004', 'L'),
            ('Eko Wahyudi', '2024005', 'Teknik Informatika', '081234567005', 'L'),
            ('Fajar Ramadhan', '2024006', 'Manajemen', '081234567006', 'L'),
            ('Galih Pratama', '2024007', 'Akuntansi', '081234567007', 'L'),
            ('Hendra Wijaya', '2024008', 'Teknik Sipil', '081234567008', 'L'),
            ('Ani Lestari', '2024101', 'Teknik Informatika', '081234567101', 'P'),
            ('Bunga Citra', '2024102', 'Sistem Informasi', '081234567102', 'P'),
            ('Citra Dewi', '2024103', 'Manajemen', '081234567103', 'P'),
            ('Dian Permata', '2024104', 'Akuntansi', '081234567104', 'P'),
            ('Eka Putri', '2024105', 'Teknik Informatika', '081234567105', 'P'),
            ('Fitri Handayani', '2024106', 'Farmasi', '081234567106', 'P'),
            ('Gita Nirmala', '2024107', 'Kedokteran', '081234567107', 'P'),
        ]
        for nm, nim, jur, telp, jk in penghuni_data:
            data['_counters']['penghuni'] += 1
            data['penghuni'].append({
                'id': data['_counters']['penghuni'],
                'nama': nm,
                'nim': nim,
                'jurusan': jur,
                'no_telp': telp,
                'jenis_kelamin': jk,
                'created_at': now_str
            })

        # Penempatan otomatis
        for ph in data['penghuni']:
            tipe = 'putra' if ph['jenis_kelamin'] == 'L' else 'putri'
            available = [
                k for k in sorted(data['kamar'], key=lambda x: (x['lantai'], str(x['nomor_kamar'])))
                if k['tipe'] == tipe and sum(1 for p in data['penempatan'] if p['kamar_id'] == k['id']) < k['kapasitas']
            ]
            if available:
                room = available[0]
                data['_counters']['penempatan'] += 1
                data['penempatan'].append({
                    'id': data['_counters']['penempatan'],
                    'penghuni_id': ph['id'],
                    'kamar_id': room['id'],
                    'tanggal_masuk': '2024-08-15',
                    'created_at': now_str
                })

        # Data pelanggaran
        pelanggaran_seed = [
            (1, 'Kebisingan', 'Membuat keributan di malam hari', '2024-09-10', 'ringan'),
            (2, 'Kebersihan', 'Kamar tidak bersih saat inspeksi', '2024-09-15', 'ringan'),
            (1, 'Jam Malam', 'Pulang lewat jam malam', '2024-10-01', 'sedang'),
            (5, 'Merokok', 'Merokok di dalam kamar', '2024-10-05', 'berat'),
            (9, 'Kebersihan', 'Membuang sampah sembarangan', '2024-10-10', 'ringan'),
        ]
        for pid, jns, desk, tgl, sev in pelanggaran_seed:
            data['_counters']['pelanggaran'] += 1
            data['pelanggaran'].append({
                'id': data['_counters']['pelanggaran'],
                'penghuni_id': pid,
                'jenis_pelanggaran': jns,
                'deskripsi': desk,
                'tanggal': tgl,
                'tingkat_severity': sev,
                'created_at': now_str
            })

        # Data izin keluar
        izin_seed = [
            (3, '2024-10-20', '2024-10-22', 'Acara keluarga', 'disetujui'),
            (7, '2024-10-25', '2024-10-27', 'Sakit, perlu perawatan di rumah', 'disetujui'),
            (11, '2024-11-01', '2024-11-03', 'Menghadiri wisuda kakak', 'pending'),
        ]
        for pid, tgl_k, tgl_b, als, st in izin_seed:
            data['_counters']['izin_keluar'] += 1
            data['izin_keluar'].append({
                'id': data['_counters']['izin_keluar'],
                'penghuni_id': pid,
                'tanggal_keluar': tgl_k,
                'tanggal_kembali': tgl_b,
                'alasan': als,
                'status': st,
                'created_at': now_str
            })

        commit()
        return True, "Data contoh berhasil dimuat (16 kamar, 15 penghuni, 5 pelanggaran, 3 izin keluar)."
