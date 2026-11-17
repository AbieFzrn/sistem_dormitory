"""
database.py - Inisialisasi database, koneksi, dan semua operasi CRUD.
Menggunakan sqlite3 standar Python.
"""

import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dormitory.db")


def get_connection():
    """Mendapatkan koneksi database dengan foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Inisialisasi semua tabel database."""
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS kamar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomor_kamar TEXT NOT NULL UNIQUE,
            lantai INTEGER NOT NULL,
            tipe TEXT NOT NULL CHECK(tipe IN ('putra', 'putri')),
            kapasitas INTEGER NOT NULL DEFAULT 2,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS penghuni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            nim TEXT NOT NULL UNIQUE,
            jurusan TEXT NOT NULL,
            no_telp TEXT NOT NULL,
            jenis_kelamin TEXT NOT NULL CHECK(jenis_kelamin IN ('L', 'P')),
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS penempatan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            penghuni_id INTEGER NOT NULL UNIQUE,
            kamar_id INTEGER NOT NULL,
            tanggal_masuk TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (penghuni_id) REFERENCES penghuni(id),
            FOREIGN KEY (kamar_id) REFERENCES kamar(id)
        );

        CREATE TABLE IF NOT EXISTS pelanggaran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            penghuni_id INTEGER NOT NULL,
            jenis_pelanggaran TEXT NOT NULL,
            deskripsi TEXT,
            tanggal TEXT NOT NULL,
            tingkat_severity TEXT NOT NULL CHECK(tingkat_severity IN ('ringan', 'sedang', 'berat')),
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (penghuni_id) REFERENCES penghuni(id)
        );

        CREATE TABLE IF NOT EXISTS izin_keluar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            penghuni_id INTEGER NOT NULL,
            tanggal_keluar TEXT NOT NULL,
            tanggal_kembali TEXT NOT NULL,
            alasan TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'disetujui', 'ditolak')),
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (penghuni_id) REFERENCES penghuni(id)
        );

        CREATE TABLE IF NOT EXISTS riwayat_perpindahan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            penghuni_id INTEGER NOT NULL,
            kamar_asal_id INTEGER NOT NULL,
            kamar_tujuan_id INTEGER NOT NULL,
            tanggal TEXT NOT NULL,
            alasan TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (penghuni_id) REFERENCES penghuni(id),
            FOREIGN KEY (kamar_asal_id) REFERENCES kamar(id),
            FOREIGN KEY (kamar_tujuan_id) REFERENCES kamar(id)
        );
    """)
    conn.commit()
    conn.close()


# ===================== KAMAR (Room) CRUD =====================

def tambah_kamar(nomor_kamar, lantai, tipe, kapasitas):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO kamar (nomor_kamar, lantai, tipe, kapasitas) VALUES (?, ?, ?, ?)",
            (nomor_kamar, lantai, tipe.lower(), kapasitas)
        )
        conn.commit()
        return True, "Kamar berhasil ditambahkan."
    except sqlite3.IntegrityError:
        return False, "Nomor kamar sudah ada."
    finally:
        conn.close()


def get_all_kamar():
    conn = get_connection()
    rows = conn.execute("""
        SELECT k.*, 
               (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) as terisi
        FROM kamar k
        ORDER BY k.lantai, k.nomor_kamar
    """).fetchall()
    conn.close()
    return rows


def get_kamar_by_id(kamar_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT k.*, 
               (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) as terisi
        FROM kamar k WHERE k.id = ?
    """, (kamar_id,)).fetchone()
    conn.close()
    return row


def get_kamar_by_nomor(nomor_kamar):
    conn = get_connection()
    row = conn.execute("""
        SELECT k.*, 
               (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) as terisi
        FROM kamar k WHERE k.nomor_kamar = ?
    """, (nomor_kamar,)).fetchone()
    conn.close()
    return row


def edit_kamar(kamar_id, nomor_kamar, lantai, tipe, kapasitas):
    conn = get_connection()
    try:
        # Check current occupancy
        terisi = conn.execute(
            "SELECT COUNT(*) FROM penempatan WHERE kamar_id = ?", (kamar_id,)
        ).fetchone()[0]
        if kapasitas < terisi:
            return False, f"Kapasitas tidak boleh kurang dari jumlah penghuni saat ini ({terisi} orang)."

        # Check if any resident gender conflicts with new type
        if tipe:
            gender_map = {'putra': 'L', 'putri': 'P'}
            expected_gender = gender_map.get(tipe.lower())
            if expected_gender and terisi > 0:
                conflict = conn.execute("""
                    SELECT COUNT(*) FROM penempatan pm
                    JOIN penghuni ph ON pm.penghuni_id = ph.id
                    WHERE pm.kamar_id = ? AND ph.jenis_kelamin != ?
                """, (kamar_id, expected_gender)).fetchone()[0]
                if conflict > 0:
                    return False, "Tidak bisa mengubah tipe kamar, ada penghuni yang tidak sesuai gender."

        conn.execute(
            "UPDATE kamar SET nomor_kamar=?, lantai=?, tipe=?, kapasitas=? WHERE id=?",
            (nomor_kamar, lantai, tipe.lower(), kapasitas, kamar_id)
        )
        conn.commit()
        return True, "Kamar berhasil diperbarui."
    except sqlite3.IntegrityError:
        return False, "Nomor kamar sudah digunakan."
    finally:
        conn.close()


def hapus_kamar(kamar_id):
    conn = get_connection()
    terisi = conn.execute(
        "SELECT COUNT(*) FROM penempatan WHERE kamar_id = ?", (kamar_id,)
    ).fetchone()[0]
    if terisi > 0:
        conn.close()
        return False, "Kamar tidak bisa dihapus karena masih ada penghuni."
    conn.execute("DELETE FROM kamar WHERE id = ?", (kamar_id,))
    conn.commit()
    conn.close()
    return True, "Kamar berhasil dihapus."


def update_kapasitas_kamar(kamar_id, kapasitas_baru):
    conn = get_connection()
    terisi = conn.execute(
        "SELECT COUNT(*) FROM penempatan WHERE kamar_id = ?", (kamar_id,)
    ).fetchone()[0]
    if kapasitas_baru < terisi:
        conn.close()
        return False, f"Kapasitas tidak boleh kurang dari jumlah penghuni saat ini ({terisi} orang)."
    conn.execute("UPDATE kamar SET kapasitas = ? WHERE id = ?", (kapasitas_baru, kamar_id))
    conn.commit()
    conn.close()
    return True, "Kapasitas kamar berhasil diperbarui."


def get_kapasitas_overview():
    conn = get_connection()
    rows = conn.execute("""
        SELECT k.id, k.nomor_kamar, k.lantai, k.tipe, k.kapasitas,
               (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) as terisi
        FROM kamar k
        ORDER BY k.lantai, k.nomor_kamar
    """).fetchall()
    conn.close()
    return rows


# ===================== PENGHUNI (Resident) CRUD =====================

def tambah_penghuni(nama, nim, jurusan, no_telp, jenis_kelamin):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO penghuni (nama, nim, jurusan, no_telp, jenis_kelamin) VALUES (?, ?, ?, ?, ?)",
            (nama, nim, jurusan, no_telp, jenis_kelamin.upper())
        )
        conn.commit()
        last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return True, "Penghuni berhasil ditambahkan.", last_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "NIM sudah terdaftar.", None


def get_all_penghuni():
    conn = get_connection()
    rows = conn.execute("""
        SELECT ph.*, k.nomor_kamar
        FROM penghuni ph
        LEFT JOIN penempatan pm ON ph.id = pm.penghuni_id
        LEFT JOIN kamar k ON pm.kamar_id = k.id
        ORDER BY ph.nama
    """).fetchall()
    conn.close()
    return rows


def get_penghuni_by_id(penghuni_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT ph.*, k.nomor_kamar, k.id as kamar_id
        FROM penghuni ph
        LEFT JOIN penempatan pm ON ph.id = pm.penghuni_id
        LEFT JOIN kamar k ON pm.kamar_id = k.id
        WHERE ph.id = ?
    """, (penghuni_id,)).fetchone()
    conn.close()
    return row


def edit_penghuni(penghuni_id, nama, nim, jurusan, no_telp, jenis_kelamin):
    conn = get_connection()
    try:
        # Check if gender change conflicts with current room
        current = conn.execute("""
            SELECT k.tipe FROM penempatan pm
            JOIN kamar k ON pm.kamar_id = k.id
            WHERE pm.penghuni_id = ?
        """, (penghuni_id,)).fetchone()
        if current:
            gender_map = {'L': 'putra', 'P': 'putri'}
            if gender_map.get(jenis_kelamin.upper()) != current['tipe']:
                conn.close()
                return False, "Tidak bisa mengubah jenis kelamin karena masih ditempatkan di kamar yang tidak sesuai."

        conn.execute(
            "UPDATE penghuni SET nama=?, nim=?, jurusan=?, no_telp=?, jenis_kelamin=? WHERE id=?",
            (nama, nim, jurusan, no_telp, jenis_kelamin.upper(), penghuni_id)
        )
        conn.commit()
        return True, "Data penghuni berhasil diperbarui."
    except sqlite3.IntegrityError:
        return False, "NIM sudah digunakan oleh penghuni lain."
    finally:
        conn.close()


def hapus_penghuni(penghuni_id):
    conn = get_connection()
    assigned = conn.execute(
        "SELECT COUNT(*) FROM penempatan WHERE penghuni_id = ?", (penghuni_id,)
    ).fetchone()[0]
    if assigned > 0:
        conn.close()
        return False, "Penghuni tidak bisa dihapus karena masih ditempatkan di kamar. Pindahkan atau keluarkan terlebih dahulu."
    conn.execute("DELETE FROM pelanggaran WHERE penghuni_id = ?", (penghuni_id,))
    conn.execute("DELETE FROM izin_keluar WHERE penghuni_id = ?", (penghuni_id,))
    conn.execute("DELETE FROM riwayat_perpindahan WHERE penghuni_id = ?", (penghuni_id,))
    conn.execute("DELETE FROM penghuni WHERE id = ?", (penghuni_id,))
    conn.commit()
    conn.close()
    return True, "Penghuni berhasil dihapus."


def cari_penghuni(keyword):
    conn = get_connection()
    rows = conn.execute("""
        SELECT ph.*, k.nomor_kamar
        FROM penghuni ph
        LEFT JOIN penempatan pm ON ph.id = pm.penghuni_id
        LEFT JOIN kamar k ON pm.kamar_id = k.id
        WHERE ph.nama LIKE ? OR ph.nim LIKE ?
        ORDER BY ph.nama
    """, (f"%{keyword}%", f"%{keyword}%")).fetchall()
    conn.close()
    return rows


# ===================== PENEMPATAN (Room Assignment) =====================

def get_available_rooms(jenis_kelamin):
    """Get rooms that match gender and have capacity."""
    tipe = 'putra' if jenis_kelamin.upper() == 'L' else 'putri'
    conn = get_connection()
    rows = conn.execute("""
        SELECT k.*,
               (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) as terisi
        FROM kamar k
        WHERE k.tipe = ?
          AND (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) < k.kapasitas
        ORDER BY k.lantai, k.nomor_kamar
    """, (tipe,)).fetchall()
    conn.close()
    return rows


def auto_assign_room(penghuni_id):
    """Auto-assign resident to available room (lowest floor, lowest room number)."""
    conn = get_connection()
    try:
        penghuni = conn.execute("SELECT * FROM penghuni WHERE id = ?", (penghuni_id,)).fetchone()
        if not penghuni:
            return False, "Penghuni tidak ditemukan."

        # Check if already assigned
        existing = conn.execute(
            "SELECT * FROM penempatan WHERE penghuni_id = ?", (penghuni_id,)
        ).fetchone()
        if existing:
            return False, "Penghuni sudah ditempatkan di kamar."

        tipe = 'putra' if penghuni['jenis_kelamin'] == 'L' else 'putri'
        room = conn.execute("""
            SELECT k.id, k.nomor_kamar, k.kapasitas,
                   (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) as terisi
            FROM kamar k
            WHERE k.tipe = ?
              AND (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) < k.kapasitas
            ORDER BY k.lantai, k.nomor_kamar
            LIMIT 1
        """, (tipe,)).fetchone()

        if not room:
            return False, "Tidak ada kamar yang tersedia untuk jenis kelamin ini."

        conn.execute(
            "INSERT INTO penempatan (penghuni_id, kamar_id, tanggal_masuk) VALUES (?, ?, ?)",
            (penghuni_id, room['id'], date.today().isoformat())
        )
        conn.commit()
        return True, f"Penghuni berhasil ditempatkan di kamar {room['nomor_kamar']}."
    except sqlite3.IntegrityError:
        return False, "Penghuni sudah ditempatkan di kamar."
    finally:
        conn.close()


def manual_assign_room(penghuni_id, kamar_id):
    """Manually assign resident to a specific room."""
    conn = get_connection()
    try:
        penghuni = conn.execute("SELECT * FROM penghuni WHERE id = ?", (penghuni_id,)).fetchone()
        if not penghuni:
            return False, "Penghuni tidak ditemukan."

        existing = conn.execute(
            "SELECT * FROM penempatan WHERE penghuni_id = ?", (penghuni_id,)
        ).fetchone()
        if existing:
            return False, "Penghuni sudah ditempatkan di kamar. Gunakan fitur perpindahan kamar."

        kamar = conn.execute("""
            SELECT k.*, (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) as terisi
            FROM kamar k WHERE k.id = ?
        """, (kamar_id,)).fetchone()
        if not kamar:
            return False, "Kamar tidak ditemukan."

        gender_map = {'L': 'putra', 'P': 'putri'}
        if gender_map[penghuni['jenis_kelamin']] != kamar['tipe']:
            return False, f"Jenis kelamin tidak sesuai dengan tipe kamar ({kamar['tipe']})."

        if kamar['terisi'] >= kamar['kapasitas']:
            return False, "Kamar sudah penuh."

        conn.execute(
            "INSERT INTO penempatan (penghuni_id, kamar_id, tanggal_masuk) VALUES (?, ?, ?)",
            (penghuni_id, kamar_id, date.today().isoformat())
        )
        conn.commit()
        return True, f"Penghuni berhasil ditempatkan di kamar {kamar['nomor_kamar']}."
    except sqlite3.IntegrityError:
        return False, "Penghuni sudah ditempatkan di kamar."
    finally:
        conn.close()


def keluarkan_penghuni(penghuni_id):
    """Remove resident from their room (checkout)."""
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM penempatan WHERE penghuni_id = ?", (penghuni_id,)
    ).fetchone()
    if not existing:
        conn.close()
        return False, "Penghuni tidak ditempatkan di kamar manapun."
    conn.execute("DELETE FROM penempatan WHERE penghuni_id = ?", (penghuni_id,))
    conn.commit()
    conn.close()
    return True, "Penghuni berhasil dikeluarkan dari kamar."


def get_penghuni_di_kamar(kamar_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT ph.* FROM penghuni ph
        JOIN penempatan pm ON ph.id = pm.penghuni_id
        WHERE pm.kamar_id = ?
        ORDER BY ph.nama
    """, (kamar_id,)).fetchall()
    conn.close()
    return rows


def get_penghuni_tanpa_kamar():
    conn = get_connection()
    rows = conn.execute("""
        SELECT ph.* FROM penghuni ph
        WHERE ph.id NOT IN (SELECT penghuni_id FROM penempatan)
        ORDER BY ph.nama
    """).fetchall()
    conn.close()
    return rows


# ===================== PELANGGARAN (Violations) =====================

def tambah_pelanggaran(penghuni_id, jenis, deskripsi, tanggal, severity):
    conn = get_connection()
    # Check penghuni exists
    ph = conn.execute("SELECT id FROM penghuni WHERE id = ?", (penghuni_id,)).fetchone()
    if not ph:
        conn.close()
        return False, "Penghuni tidak ditemukan."
    conn.execute(
        "INSERT INTO pelanggaran (penghuni_id, jenis_pelanggaran, deskripsi, tanggal, tingkat_severity) VALUES (?, ?, ?, ?, ?)",
        (penghuni_id, jenis, deskripsi, tanggal, severity.lower())
    )
    conn.commit()
    conn.close()
    return True, "Pelanggaran berhasil dicatat."


def get_pelanggaran_by_penghuni(penghuni_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT pl.*, ph.nama, ph.nim
        FROM pelanggaran pl
        JOIN penghuni ph ON pl.penghuni_id = ph.id
        WHERE pl.penghuni_id = ?
        ORDER BY pl.tanggal DESC
    """, (penghuni_id,)).fetchall()
    conn.close()
    return rows


def get_all_pelanggaran(severity_filter=None):
    conn = get_connection()
    if severity_filter:
        rows = conn.execute("""
            SELECT pl.*, ph.nama, ph.nim
            FROM pelanggaran pl
            JOIN penghuni ph ON pl.penghuni_id = ph.id
            WHERE pl.tingkat_severity = ?
            ORDER BY pl.tanggal DESC
        """, (severity_filter,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT pl.*, ph.nama, ph.nim
            FROM pelanggaran pl
            JOIN penghuni ph ON pl.penghuni_id = ph.id
            ORDER BY pl.tanggal DESC
        """).fetchall()
    conn.close()
    return rows


def get_ringkasan_pelanggaran():
    conn = get_connection()
    summary = conn.execute("""
        SELECT tingkat_severity, COUNT(*) as jumlah
        FROM pelanggaran
        GROUP BY tingkat_severity
        ORDER BY CASE tingkat_severity
            WHEN 'ringan' THEN 1
            WHEN 'sedang' THEN 2
            WHEN 'berat' THEN 3
        END
    """).fetchall()
    top_violators = conn.execute("""
        SELECT ph.nama, ph.nim, COUNT(*) as jumlah
        FROM pelanggaran pl
        JOIN penghuni ph ON pl.penghuni_id = ph.id
        GROUP BY pl.penghuni_id
        ORDER BY jumlah DESC
        LIMIT 5
    """).fetchall()
    conn.close()
    return summary, top_violators


# ===================== IZIN KELUAR (Leave Permits) =====================

def tambah_izin_keluar(penghuni_id, tanggal_keluar, tanggal_kembali, alasan):
    conn = get_connection()
    ph = conn.execute("SELECT id FROM penghuni WHERE id = ?", (penghuni_id,)).fetchone()
    if not ph:
        conn.close()
        return False, "Penghuni tidak ditemukan."
    conn.execute(
        "INSERT INTO izin_keluar (penghuni_id, tanggal_keluar, tanggal_kembali, alasan) VALUES (?, ?, ?, ?)",
        (penghuni_id, tanggal_keluar, tanggal_kembali, alasan)
    )
    conn.commit()
    conn.close()
    return True, "Izin keluar berhasil dicatat."


def update_status_izin(izin_id, status):
    conn = get_connection()
    izin = conn.execute("SELECT * FROM izin_keluar WHERE id = ?", (izin_id,)).fetchone()
    if not izin:
        conn.close()
        return False, "Izin tidak ditemukan."
    if izin['status'] != 'pending':
        conn.close()
        return False, f"Izin sudah berstatus '{izin['status']}', tidak bisa diubah."
    conn.execute("UPDATE izin_keluar SET status = ? WHERE id = ?", (status, izin_id))
    conn.commit()
    conn.close()
    return True, f"Status izin berhasil diubah menjadi '{status}'."


def get_izin_pending():
    conn = get_connection()
    rows = conn.execute("""
        SELECT iz.*, ph.nama, ph.nim
        FROM izin_keluar iz
        JOIN penghuni ph ON iz.penghuni_id = ph.id
        WHERE iz.status = 'pending'
        ORDER BY iz.tanggal_keluar
    """).fetchall()
    conn.close()
    return rows


def get_penghuni_sedang_keluar():
    """Get residents currently out (approved, departure passed, return not yet)."""
    conn = get_connection()
    today = date.today().isoformat()
    rows = conn.execute("""
        SELECT iz.*, ph.nama, ph.nim
        FROM izin_keluar iz
        JOIN penghuni ph ON iz.penghuni_id = ph.id
        WHERE iz.status = 'disetujui'
          AND iz.tanggal_keluar <= ?
          AND iz.tanggal_kembali >= ?
        ORDER BY iz.tanggal_kembali
    """, (today, today)).fetchall()
    conn.close()
    return rows


def get_riwayat_izin(penghuni_id=None):
    conn = get_connection()
    if penghuni_id:
        rows = conn.execute("""
            SELECT iz.*, ph.nama, ph.nim
            FROM izin_keluar iz
            JOIN penghuni ph ON iz.penghuni_id = ph.id
            WHERE iz.penghuni_id = ?
            ORDER BY iz.tanggal_keluar DESC
        """, (penghuni_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT iz.*, ph.nama, ph.nim
            FROM izin_keluar iz
            JOIN penghuni ph ON iz.penghuni_id = ph.id
            ORDER BY iz.tanggal_keluar DESC
        """).fetchall()
    conn.close()
    return rows


# ===================== RIWAYAT PERPINDAHAN (Transfer History) =====================

def pindah_kamar(penghuni_id, kamar_tujuan_id, alasan):
    conn = get_connection()
    try:
        penghuni = conn.execute("SELECT * FROM penghuni WHERE id = ?", (penghuni_id,)).fetchone()
        if not penghuni:
            return False, "Penghuni tidak ditemukan."

        current = conn.execute("""
            SELECT pm.*, k.nomor_kamar FROM penempatan pm
            JOIN kamar k ON pm.kamar_id = k.id
            WHERE pm.penghuni_id = ?
        """, (penghuni_id,)).fetchone()
        if not current:
            return False, "Penghuni belum ditempatkan di kamar manapun."

        kamar_asal_id = current['kamar_id']
        if kamar_asal_id == kamar_tujuan_id:
            return False, "Kamar tujuan sama dengan kamar saat ini."

        kamar_tujuan = conn.execute("""
            SELECT k.*, (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) as terisi
            FROM kamar k WHERE k.id = ?
        """, (kamar_tujuan_id,)).fetchone()
        if not kamar_tujuan:
            return False, "Kamar tujuan tidak ditemukan."

        gender_map = {'L': 'putra', 'P': 'putri'}
        if gender_map[penghuni['jenis_kelamin']] != kamar_tujuan['tipe']:
            return False, f"Tipe kamar tujuan ({kamar_tujuan['tipe']}) tidak sesuai dengan jenis kelamin."

        if kamar_tujuan['terisi'] >= kamar_tujuan['kapasitas']:
            return False, "Kamar tujuan sudah penuh."

        # Perform transfer in transaction
        conn.execute("UPDATE penempatan SET kamar_id = ? WHERE penghuni_id = ?",
                      (kamar_tujuan_id, penghuni_id))
        conn.execute(
            "INSERT INTO riwayat_perpindahan (penghuni_id, kamar_asal_id, kamar_tujuan_id, tanggal, alasan) VALUES (?, ?, ?, ?, ?)",
            (penghuni_id, kamar_asal_id, kamar_tujuan_id, date.today().isoformat(), alasan)
        )
        conn.commit()
        return True, f"Penghuni berhasil dipindahkan ke kamar {kamar_tujuan['nomor_kamar']}."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal memindahkan: {e}"
    finally:
        conn.close()


def get_riwayat_perpindahan(penghuni_id=None):
    conn = get_connection()
    if penghuni_id:
        rows = conn.execute("""
            SELECT rp.*, ph.nama, ph.nim,
                   ka.nomor_kamar as kamar_asal, kt.nomor_kamar as kamar_tujuan
            FROM riwayat_perpindahan rp
            JOIN penghuni ph ON rp.penghuni_id = ph.id
            JOIN kamar ka ON rp.kamar_asal_id = ka.id
            JOIN kamar kt ON rp.kamar_tujuan_id = kt.id
            WHERE rp.penghuni_id = ?
            ORDER BY rp.tanggal DESC
        """, (penghuni_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT rp.*, ph.nama, ph.nim,
                   ka.nomor_kamar as kamar_asal, kt.nomor_kamar as kamar_tujuan
            FROM riwayat_perpindahan rp
            JOIN penghuni ph ON rp.penghuni_id = ph.id
            JOIN kamar ka ON rp.kamar_asal_id = ka.id
            JOIN kamar kt ON rp.kamar_tujuan_id = kt.id
            ORDER BY rp.tanggal DESC
        """).fetchall()
    conn.close()
    return rows


# ===================== STATISTIK =====================

def get_statistik_okupansi():
    conn = get_connection()
    total_kamar = conn.execute("SELECT COUNT(*) FROM kamar").fetchone()[0]
    total_kapasitas = conn.execute("SELECT COALESCE(SUM(kapasitas), 0) FROM kamar").fetchone()[0]
    total_penghuni = conn.execute("SELECT COUNT(*) FROM penempatan").fetchone()[0]

    kamar_terisi = conn.execute("""
        SELECT COUNT(DISTINCT kamar_id) FROM penempatan
    """).fetchone()[0]
    kamar_kosong = total_kamar - kamar_terisi

    # Per-floor stats
    per_lantai = conn.execute("""
        SELECT k.lantai,
               COUNT(k.id) as jumlah_kamar,
               SUM(k.kapasitas) as total_kapasitas,
               (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id IN 
                   (SELECT id FROM kamar WHERE lantai = k.lantai)) as terisi
        FROM kamar k
        GROUP BY k.lantai
        ORDER BY k.lantai
    """).fetchall()

    # Per-type stats
    per_tipe = conn.execute("""
        SELECT k.tipe,
               COUNT(k.id) as jumlah_kamar,
               SUM(k.kapasitas) as total_kapasitas,
               (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id IN 
                   (SELECT id FROM kamar WHERE tipe = k.tipe)) as terisi
        FROM kamar k
        GROUP BY k.tipe
        ORDER BY k.tipe
    """).fetchall()

    # Room with most occupants
    kamar_terbanyak = conn.execute("""
        SELECT k.nomor_kamar, k.kapasitas, COUNT(p.id) as terisi
        FROM kamar k
        LEFT JOIN penempatan p ON k.id = p.kamar_id
        GROUP BY k.id
        ORDER BY terisi DESC
        LIMIT 1
    """).fetchone()

    # Room with least occupants (among occupied rooms)
    kamar_tersedikit = conn.execute("""
        SELECT k.nomor_kamar, k.kapasitas, COUNT(p.id) as terisi
        FROM kamar k
        LEFT JOIN penempatan p ON k.id = p.kamar_id
        GROUP BY k.id
        ORDER BY terisi ASC
        LIMIT 1
    """).fetchone()

    conn.close()

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
    """For ASCII bar chart."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT k.nomor_kamar, k.kapasitas,
               (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) as terisi
        FROM kamar k
        ORDER BY k.lantai, k.nomor_kamar
    """).fetchall()
    conn.close()
    return rows


# ===================== SEED DATA =====================

def seed_data():
    conn = get_connection()
    try:
        # Check if data already exists
        existing = conn.execute("SELECT COUNT(*) FROM kamar").fetchone()[0]
        if existing > 0:
            conn.close()
            return False, "Database sudah memiliki data. Hapus database terlebih dahulu untuk seed ulang."

        # Seed rooms
        kamar_data = [
            ('101', 1, 'putra', 3), ('102', 1, 'putra', 3), ('103', 1, 'putra', 2),
            ('104', 1, 'putri', 3), ('105', 1, 'putri', 3), ('106', 1, 'putri', 2),
            ('201', 2, 'putra', 3), ('202', 2, 'putra', 2), ('203', 2, 'putra', 2),
            ('204', 2, 'putri', 3), ('205', 2, 'putri', 2), ('206', 2, 'putri', 2),
            ('301', 3, 'putra', 2), ('302', 3, 'putra', 2),
            ('303', 3, 'putri', 2), ('304', 3, 'putri', 2),
        ]
        conn.executemany(
            "INSERT INTO kamar (nomor_kamar, lantai, tipe, kapasitas) VALUES (?, ?, ?, ?)",
            kamar_data
        )

        # Seed residents
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
        conn.executemany(
            "INSERT INTO penghuni (nama, nim, jurusan, no_telp, jenis_kelamin) VALUES (?, ?, ?, ?, ?)",
            penghuni_data
        )

        # Auto-assign rooms
        penghuni_ids = conn.execute("SELECT id, jenis_kelamin FROM penghuni ORDER BY id").fetchall()
        for ph in penghuni_ids:
            tipe = 'putra' if ph['jenis_kelamin'] == 'L' else 'putri'
            room = conn.execute("""
                SELECT k.id FROM kamar k
                WHERE k.tipe = ?
                  AND (SELECT COUNT(*) FROM penempatan p WHERE p.kamar_id = k.id) < k.kapasitas
                ORDER BY k.lantai, k.nomor_kamar
                LIMIT 1
            """, (tipe,)).fetchone()
            if room:
                conn.execute(
                    "INSERT INTO penempatan (penghuni_id, kamar_id, tanggal_masuk) VALUES (?, ?, ?)",
                    (ph['id'], room['id'], '2024-08-15')
                )

        # Seed some violations
        conn.executemany(
            "INSERT INTO pelanggaran (penghuni_id, jenis_pelanggaran, deskripsi, tanggal, tingkat_severity) VALUES (?, ?, ?, ?, ?)",
            [
                (1, 'Kebisingan', 'Membuat keributan di malam hari', '2024-09-10', 'ringan'),
                (2, 'Kebersihan', 'Kamar tidak bersih saat inspeksi', '2024-09-15', 'ringan'),
                (1, 'Jam Malam', 'Pulang lewat jam malam', '2024-10-01', 'sedang'),
                (5, 'Merokok', 'Merokok di dalam kamar', '2024-10-05', 'berat'),
                (9, 'Kebersihan', 'Membuang sampah sembarangan', '2024-10-10', 'ringan'),
            ]
        )

        # Seed some leave permits
        conn.executemany(
            "INSERT INTO izin_keluar (penghuni_id, tanggal_keluar, tanggal_kembali, alasan, status) VALUES (?, ?, ?, ?, ?)",
            [
                (3, '2024-10-20', '2024-10-22', 'Acara keluarga', 'disetujui'),
                (7, '2024-10-25', '2024-10-27', 'Sakit, perlu perawatan di rumah', 'disetujui'),
                (11, '2024-11-01', '2024-11-03', 'Menghadiri wisuda kakak', 'pending'),
            ]
        )

        conn.commit()
        conn.close()
        return True, "Data contoh berhasil dimuat (16 kamar, 15 penghuni, 5 pelanggaran, 3 izin keluar)."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Gagal memuat data contoh: {e}"
