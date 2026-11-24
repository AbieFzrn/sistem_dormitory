

from datetime import datetime
import storage_handler as db
from algo_utils import (
    parse_room_code,
    generate_next_id,
    sanitize_pipe,
    merge_sort_records,
    binary_search_by_nim,
    format_surat_izin_txt,
    format_surat_peringatan_txt,
)

# Konstanta Tuple (Immutable) untuk aturan pelanggaran baku asrama
ATURAN_PELANGGARAN = (
    ("AT-01", "Merokok / vape di area gedung asrama", 50),
    ("AT-02", "Terlambat kembali melewati jam malam (>22.00)", 15),
    ("AT-03", "Kebersihan kamar tidak memenuhi standar inspeksi", 10),
    ("AT-04", "Membawa tamu luar masuk tanpa izin pengelola", 25),
    ("AT-05", "Merusak inventaris atau fasilitas kamar", 40),
)

VALID_GENDERS = ("L", "P")


# ==============================================================================
# HELPER KOLEKSI DATA (SET & LOOKUP)
# ==============================================================================

def get_registered_nims(residents):
    """Mengembalikan SET berisi seluruh NIM terdaftar untuk validasi duplikasi O(1)."""
    return {r["nim"] for r in residents}


def get_registered_room_codes(rooms):
    """Mengembalikan SET berisi seluruh kode kamar terdaftar."""
    return {r["kode"] for r in rooms}


def _recalculate_room_occupancy(rooms, residents):
    """Sinkronisasi jumlah penghuni aktif per kamar agar data konsisten."""
    counts = {room["kode"]: 0 for room in rooms}
    for res in residents:
        if res["status"] == "Aktif" and res["kamar"] in counts:
            counts[res["kamar"]] += 1

    for room in rooms:
        room["terisi"] = counts[room["kode"]]
        if room["terisi"] >= room["kapasitas"]:
            room["status"] = "Penuh"
        else:
            room["status"] = "Tersedia"


# ==============================================================================
# CRUD KAMAR ASRAMA
# ==============================================================================

def create_room(raw_code, kapasitas):
    rooms = db.load_rooms()
    ok, parsed = parse_room_code(raw_code)
    if not ok:
        return False, parsed

    existing_codes = get_registered_room_codes(rooms)
    if parsed["kode"] in existing_codes:
        return False, f"Kamar {parsed['kode']} sudah terdaftar di sistem."

    if kapasitas < 1 or kapasitas > 8:
        return False, "Kapasitas kamar harus antara 1 sampai 8 orang."

    new_room = {
        "kode": parsed["kode"],
        "gedung": parsed["gedung"],
        "lantai": parsed["lantai"],
        "gender": parsed["gender"],
        "kapasitas": kapasitas,
        "terisi": 0,
        "status": "Tersedia",
    }
    rooms.append(new_room)
    db.save_rooms(rooms)
    return True, f"Kamar {new_room['kode']} ({new_room['gedung']}, Lantai {new_room['lantai']}) berhasil ditambahkan."


def update_room_capacity(kode_kamar, new_kapasitas):
    rooms = db.load_rooms()
    kode = kode_kamar.strip().upper()
    for room in rooms:
        if room["kode"] == kode:
            if new_kapasitas < room["terisi"]:
                return False, f"Gagal! Kapasitas baru ({new_kapasitas}) lebih kecil dari jumlah penghuni saat ini ({room['terisi']})."
            if new_kapasitas < 1 or new_kapasitas > 8:
                return False, "Kapasitas kamar harus antara 1 sampai 8 orang."
            room["kapasitas"] = new_kapasitas
            room["status"] = "Penuh" if room["terisi"] >= room["kapasitas"] else "Tersedia"
            db.save_rooms(rooms)
            return True, f"Kapasitas kamar {kode} berhasil diperbarui menjadi {new_kapasitas} orang."
    return False, f"Kamar {kode} tidak ditemukan."


def delete_room(kode_kamar):
    rooms = db.load_rooms()
    kode = kode_kamar.strip().upper()
    for idx, room in enumerate(rooms):
        if room["kode"] == kode:
            if room["terisi"] > 0:
                return False, f"Kamar {kode} tidak dapat dihapus karena masih dihuni oleh {room['terisi']} mahasiswa!"
            rooms.pop(idx)
            db.save_rooms(rooms)
            return True, f"Kamar {kode} berhasil dihapus dari sistem."
    return False, f"Kamar {kode} tidak ditemukan."


# ==============================================================================
# CRUD PENGHUNI & AUTO-ASSIGNMENT
# ==============================================================================

def auto_assign_room(rooms, gender):
    """
    Memilih kamar terbaik secara otomatis sesuai gender dengan sisa kuota terbanyak
    menggunakan manual Merge Sort.
    """
    eligible = [
        r for r in rooms
        if r["gender"] == gender and r["terisi"] < r["kapasitas"]
    ]
    if not eligible:
        return None

    sorted_rooms = merge_sort_records(
        eligible,
        key_func=lambda r: (r["kapasitas"] - r["terisi"], -r["lantai"]),
        reverse=True,
    )
    return sorted_rooms[0]["kode"]


def create_resident(nim, nama, prodi, gender, preferred_room=None):
    rooms = db.load_rooms()
    residents = db.load_residents()

    nim_clean = nim.strip().upper()
    if nim_clean in get_registered_nims(residents):
        return False, f"NIM {nim_clean} sudah terdaftar sebagai penghuni asrama."

    gender_clean = gender.strip().upper()
    if gender_clean not in VALID_GENDERS:
        return False, "Gender harus 'L' (Laki-laki) atau 'P' (Perempuan)."

    if preferred_room and preferred_room.upper() != "AUTO":
        target_code = preferred_room.strip().upper()
        target_room = next((r for r in rooms if r["kode"] == target_code), None)
        if not target_room:
            return False, f"Kamar {target_code} tidak ditemukan."
        if target_room["gender"] != gender_clean:
            return False, f"Kamar {target_code} khusus untuk penghuni ber-gender '{target_room['gender']}'."
        if target_room["terisi"] >= target_room["kapasitas"]:
            return False, f"Kamar {target_code} sudah penuh ({target_room['terisi']}/{target_room['kapasitas']})."
    else:
        target_code = auto_assign_room(rooms, gender_clean)
        if not target_code:
            return False, f"Tidak ada kamar kosong yang tersedia untuk gender '{gender_clean}'."

    new_resident = {
        "nim": nim_clean,
        "nama": sanitize_pipe(nama),
        "prodi": sanitize_pipe(prodi).upper(),
        "gender": gender_clean,
        "kamar": target_code,
        "tgl_masuk": datetime.now().strftime("%Y-%m-%d"),
        "poin": 0,
        "status": "Aktif",
    }
    residents.append(new_resident)
    _recalculate_room_occupancy(rooms, residents)
    db.save_residents(residents)
    db.save_rooms(rooms)
    return True, f"Penghuni {new_resident['nama']} ({nim_clean}) berhasil ditempatkan di kamar {target_code}."


def update_resident_profile(nim, new_nama=None, new_prodi=None):
    residents = db.load_residents()
    target_nim = nim.strip().upper()
    for res in residents:
        if res["nim"] == target_nim:
            if new_nama and new_nama.strip():
                res["nama"] = sanitize_pipe(new_nama)
            if new_prodi and new_prodi.strip():
                res["prodi"] = sanitize_pipe(new_prodi).upper()
            db.save_residents(residents)
            return True, f"Data penghuni {target_nim} berhasil diperbarui."
    return False, f"Penghuni dengan NIM {target_nim} tidak ditemukan."


def transfer_resident_room(nim, new_room_code, alasan):
    """Mutasi pindah kamar penghuni + pencatatan otomatis ke transfers.txt."""
    rooms = db.load_rooms()
    residents = db.load_residents()
    transfers = db.load_transfers()

    target_nim = nim.strip().upper()
    target_code = new_room_code.strip().upper()

    resident = next((r for r in residents if r["nim"] == target_nim), None)
    if not resident:
        return False, f"Penghuni dengan NIM {target_nim} tidak ditemukan."

    old_code = resident["kamar"]
    if old_code == target_code:
        return False, "Kamar tujuan sama dengan kamar saat ini."

    new_room = next((r for r in rooms if r["kode"] == target_code), None)
    if not new_room:
        return False, f"Kamar tujuan {target_code} tidak ditemukan."
    if new_room["gender"] != resident["gender"]:
        return False, f"Kamar {target_code} tidak sesuai dengan gender penghuni ({resident['gender']})."
    if new_room["terisi"] >= new_room["kapasitas"]:
        return False, f"Kamar tujuan {target_code} sudah penuh."

    resident["kamar"] = target_code
    _recalculate_room_occupancy(rooms, residents)

    transfer_id = generate_next_id(transfers, "id", "MTS")
    transfers.append({
        "id": transfer_id,
        "nim": target_nim,
        "kamar_asal": old_code,
        "kamar_tujuan": target_code,
        "alasan": sanitize_pipe(alasan),
        "tanggal": datetime.now().strftime("%Y-%m-%d"),
    })

    db.save_residents(residents)
    db.save_rooms(rooms)
    db.save_transfers(transfers)
    return True, f"Mutasi berhasil ({transfer_id}): {resident['nama']} pindah dari {old_code} ke {target_code}."


def delete_resident(nim):
    """Checkout / hapus data penghuni dan kurangi keterisian kamar secara otomatis."""
    rooms = db.load_rooms()
    residents = db.load_residents()
    target_nim = nim.strip().upper()

    for idx, res in enumerate(residents):
        if res["nim"] == target_nim:
            removed = residents.pop(idx)
            _recalculate_room_occupancy(rooms, residents)
            db.save_residents(residents)
            db.save_rooms(rooms)
            return True, f"Penghuni {removed['nama']} ({target_nim}) telah checkout dari kamar {removed['kamar']}."
    return False, f"Penghuni dengan NIM {target_nim} tidak ditemukan."


# ==============================================================================
# PELANGGARAN & SURAT PERINGATAN OTOMATIS
# ==============================================================================

def record_violation(nim, kode_aturan):
    residents = db.load_residents()
    violations = db.load_violations()

    target_nim = nim.strip().upper()
    resident = next((r for r in residents if r["nim"] == target_nim), None)
    if not resident:
        return False, f"Penghuni dengan NIM {target_nim} tidak ditemukan."

    aturan = next((a for a in ATURAN_PELANGGARAN if a[0] == kode_aturan), None)
    if not aturan:
        return False, f"Kode aturan {kode_aturan} tidak valid."

    plg_id = generate_next_id(violations, "id", "PLG")
    new_v = {
        "id": plg_id,
        "nim": target_nim,
        "kode_aturan": aturan[0],
        "deskripsi": aturan[1],
        "poin": aturan[2],
        "tanggal": datetime.now().strftime("%Y-%m-%d"),
    }
    violations.append(new_v)
    resident["poin"] += aturan[2]

    db.save_violations(violations)
    db.save_residents(residents)

    msg = f"Pelanggaran {plg_id} dicatat (+{aturan[2]} poin). Total poin {resident['nama']}: {resident['poin']}."

    # Jika poin >= 50, otomatis generate Surat Peringatan ke file .txt
    if resident["poin"] >= 50:
        res_violations = [v for v in violations if v["nim"] == target_nim]
        sp_text = format_surat_peringatan_txt(resident, res_violations)
        sp_path = db.export_document_txt(f"SP_{target_nim}.txt", sp_text)
        msg += f"\n[PERINGATAN] Poin >= 50! Surat Peringatan otomatis dicetak ke: {sp_path}"

    return True, msg


# ==============================================================================
# IZIN KELUAR / PULANG MALAM & EKSPOR SURAT .TXT
# ==============================================================================

def create_permit(nim, tujuan, tgl_keluar, tgl_kembali):
    residents = db.load_residents()
    permits = db.load_permits()

    target_nim = nim.strip().upper()
    resident, _ = binary_search_by_nim(residents, target_nim)
    if not resident:
        return False, f"Penghuni dengan NIM {target_nim} tidak ditemukan."

    izin_id = generate_next_id(permits, "id", "IZN")
    new_permit = {
        "id": izin_id,
        "nim": target_nim,
        "tujuan": sanitize_pipe(tujuan),
        "tgl_keluar": tgl_keluar,
        "tgl_kembali": tgl_kembali,
        "status": "Menunggu",
    }
    permits.append(new_permit)
    db.save_permits(permits)
    return True, f"Pengajuan izin {izin_id} atas nama {resident['nama']} berhasil dibuat (Status: Menunggu)."


def update_permit_status(permit_id, new_status):
    residents = db.load_residents()
    permits = db.load_permits()

    pid = permit_id.strip().upper()
    permit = next((p for p in permits if p["id"] == pid), None)
    if not permit:
        return False, f"ID Izin {pid} tidak ditemukan."

    permit["status"] = new_status
    db.save_permits(permits)

    msg = f"Status izin {pid} diubah menjadi '{new_status}'."
    if new_status == "Disetujui":
        resident, _ = binary_search_by_nim(residents, permit["nim"])
        if resident:
            surat_text = format_surat_izin_txt(permit, resident)
            filepath = db.export_document_txt(f"Surat_Izin_{pid}_{resident['nim']}.txt", surat_text)
            msg += f"\nSurat izin resmi berhasil diekspor ke: {filepath}"

    return True, msg
