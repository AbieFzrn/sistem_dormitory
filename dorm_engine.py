import os
from datetime import datetime
import storage_handler as storage
from algo_utils import (
    parse_room_code,
    generate_next_id,
    sanitize_pipe,
    merge_sort_records,
    format_surat_izin_txt,
    format_surat_peringatan_txt,
)

# Aturan baku: (kode, deskripsi, poin)
ATURAN_PELANGGARAN = (
    ("AT-01", "Merokok / vape di area gedung asrama", 50),
    ("AT-02", "Terlambat kembali melewati jam malam (>22.00 WIB)", 15),
    ("AT-03", "Kebersihan kamar tidak memenuhi standar inspeksi", 10),
    ("AT-04", "Membawa tamu masuk tanpa izin pengelola", 25),
    ("AT-05", "Merusak atau mencoret inventaris/fasilitas kamar", 40),
    ("AT-06", "Membuat kegaduhan saat jam istirahat malam", 15),
    ("AT-07", "Menjemur pakaian sembarangan di luar area jemuran", 10),
    ("AT-08", "Menggunakan alat elektronik berdaya tinggi tanpa izin", 20),
    ("AT-09", "Berpindah kamar atau menggandakan kunci tanpa izin", 25),
    ("AT-10", "Menginapkan orang lain / lawan jenis di dalam kamar", 50),
    ("AT-11", "Membawa miras, alkohol, senjata tajam, atau mencuri", 100),
)

VALID_GENDERS = ("L", "P")
VALID_PERMIT_STATUS = ("Menunggu", "Disetujui", "Ditolak")
FINAL_PERMIT_STATUS = ("Disetujui", "Ditolak")


# --- Helper ---

def get_registered_nims(residents):
    return {r["nim"] for r in residents}


def get_registered_room_codes(rooms):
    return {r["kode"] for r in rooms}


def _recalculate_room_occupancy(rooms, residents):
    counts = {room["kode"]: 0 for room in rooms}
    for res in residents:
        if res["status"] == "Aktif" and res["kamar"] in counts:
            counts[res["kamar"]] += 1

    for room in rooms:
        room["terisi"] = counts[room["kode"]]
        room["status"] = "Penuh" if room["terisi"] >= room["kapasitas"] else "Tersedia"


def _recalculate_resident_points(residents, violations):
    point_map = {r["nim"]: 0 for r in residents}
    for v in violations:
        if v["nim"] in point_map:
            point_map[v["nim"]] += v["poin"]
    for r in residents:
        r["poin"] = point_map[r["nim"]]


def _cancel_pending_permits(nim):
    permits = storage.load_permits()
    changed = False
    for p in permits:
        if p["nim"] == nim and p["status"] == "Menunggu":
            p["status"] = "Ditolak"
            changed = True
    if changed:
        storage.save_permits(permits)


def _evaluate_discipline_sanctions(resident, violations, rooms, residents):
    nim = resident["nim"]
    sp_filename = f"SP_{nim}.txt"
    sp_filepath = os.path.join(storage.OUTPUT_DIR, sp_filename)

    if resident["poin"] >= 100:
        res_violations = [v for v in violations if v["nim"] == nim]
        sp_text = format_surat_peringatan_txt(resident, res_violations)
        sp_path = storage.export_document_txt(sp_filename, sp_text)

        old_kamar = resident["kamar"]
        resident["status"] = "Dikeluarkan"
        resident["kamar"] = "-"
        _recalculate_room_occupancy(rooms, residents)
        storage.save_rooms(rooms)
        _cancel_pending_permits(nim)

        return (
            f"\n[SANKSI MAKSIMAL] Akumulasi >= 100 poin! Hak tinggal dicabut "
            f"(kamar {old_kamar} dikosongkan) dan SP dicetak ke: {sp_path}"
        )

    if resident["poin"] >= 50:
        res_violations = [v for v in violations if v["nim"] == nim]
        sp_text = format_surat_peringatan_txt(resident, res_violations)
        sp_path = storage.export_document_txt(sp_filename, sp_text)
        return f"\n[PERINGATAN] Poin >= 50! Surat Peringatan dicetak/diperbarui ke: {sp_path}"

    if os.path.exists(sp_filepath):
        os.remove(sp_filepath)
        return f"\n[INFO] Poin < 50. File {sp_filename} lama telah dihapus otomatis."

    return ""


# --- CRUD Kamar ---

def create_room(raw_code, kapasitas):
    rooms = storage.load_rooms()
    ok, parsed = parse_room_code(raw_code)
    if not ok:
        return False, parsed

    if parsed["kode"] in get_registered_room_codes(rooms):
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
    storage.save_rooms(rooms)
    return True, f"Kamar {new_room['kode']} ({new_room['gedung']}, Lantai {new_room['lantai']}) berhasil ditambahkan."


def update_room_capacity(kode_kamar, new_kapasitas):
    rooms = storage.load_rooms()
    kode = kode_kamar.strip().upper()
    for room in rooms:
        if room["kode"] == kode:
            if new_kapasitas < room["terisi"]:
                return False, f"Gagal! Kapasitas baru ({new_kapasitas}) lebih kecil dari jumlah penghuni saat ini ({room['terisi']})."
            if new_kapasitas < 1 or new_kapasitas > 8:
                return False, "Kapasitas kamar harus antara 1 sampai 8 orang."
            room["kapasitas"] = new_kapasitas
            room["status"] = "Penuh" if room["terisi"] >= room["kapasitas"] else "Tersedia"
            storage.save_rooms(rooms)
            return True, f"Kapasitas kamar {kode} berhasil diperbarui menjadi {new_kapasitas} orang."
    return False, f"Kamar {kode} tidak ditemukan."


def delete_room(kode_kamar):
    rooms = storage.load_rooms()
    kode = kode_kamar.strip().upper()
    for idx, room in enumerate(rooms):
        if room["kode"] == kode:
            if room["terisi"] > 0:
                return False, f"Kamar {kode} tidak dapat dihapus karena masih dihuni oleh {room['terisi']} mahasiswa!"
            rooms.pop(idx)
            storage.save_rooms(rooms)
            return True, f"Kamar {kode} berhasil dihapus dari sistem."
    return False, f"Kamar {kode} tidak ditemukan."


# --- CRUD Penghuni ---

def auto_assign_room(rooms, gender):
    # Prioritas sisa kuota terbanyak, lalu lantai terendah
    eligible = [r for r in rooms if r["gender"] == gender and r["terisi"] < r["kapasitas"]]
    if not eligible:
        return None

    sorted_rooms = merge_sort_records(
        eligible,
        key_func=lambda r: (r["kapasitas"] - r["terisi"], -r["lantai"]),
        reverse=True,
    )
    return sorted_rooms[0]["kode"]


def create_resident(nim, nama, prodi, gender, preferred_room=None):
    rooms = storage.load_rooms()
    residents = storage.load_residents()

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
    storage.save_residents(residents)
    storage.save_rooms(rooms)
    return True, f"Penghuni {new_resident['nama']} ({nim_clean}) berhasil ditempatkan di kamar {target_code}."


def update_resident_profile(nim, new_nama=None, new_prodi=None):
    residents = storage.load_residents()
    target_nim = nim.strip().upper()
    for res in residents:
        if res["nim"] == target_nim:
            if res["status"] != "Aktif":
                return False, f"Penghuni {target_nim} berstatus '{res['status']}', data tidak dapat diubah."
            if new_nama and new_nama.strip():
                res["nama"] = sanitize_pipe(new_nama)
            if new_prodi and new_prodi.strip():
                res["prodi"] = sanitize_pipe(new_prodi).upper()
            storage.save_residents(residents)
            return True, f"Data penghuni {target_nim} berhasil diperbarui."
    return False, f"Penghuni dengan NIM {target_nim} tidak ditemukan."


def transfer_resident_room(nim, new_room_code, alasan):
    rooms = storage.load_rooms()
    residents = storage.load_residents()
    transfers = storage.load_transfers()

    target_nim = nim.strip().upper()
    target_code = new_room_code.strip().upper()

    resident = next((r for r in residents if r["nim"] == target_nim), None)
    if not resident:
        return False, f"Penghuni dengan NIM {target_nim} tidak ditemukan."
    if resident["status"] != "Aktif":
        return False, f"Penghuni {target_nim} berstatus '{resident['status']}', tidak dapat dimutasi."

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

    storage.save_residents(residents)
    storage.save_rooms(rooms)
    storage.save_transfers(transfers)
    return True, f"Mutasi berhasil ({transfer_id}): {resident['nama']} pindah dari {old_code} ke {target_code}."


def delete_resident(nim):
    rooms = storage.load_rooms()
    residents = storage.load_residents()
    target_nim = nim.strip().upper()

    for idx, res in enumerate(residents):
        if res["nim"] == target_nim:
            if res["status"] != "Aktif":
                return False, f"Penghuni {target_nim} berstatus '{res['status']}', tidak dapat di-checkout."
            removed = residents.pop(idx)
            _recalculate_room_occupancy(rooms, residents)
            storage.save_residents(residents)
            storage.save_rooms(rooms)
            _cancel_pending_permits(target_nim)
            return True, f"Penghuni {removed['nama']} ({target_nim}) telah checkout dari kamar {removed['kamar']}."
    return False, f"Penghuni dengan NIM {target_nim} tidak ditemukan."


# --- CRUD Pelanggaran ---

def record_violation(nim, kode_aturan):
    rooms = storage.load_rooms()
    residents = storage.load_residents()
    violations = storage.load_violations()

    target_nim = nim.strip().upper()
    resident = next((r for r in residents if r["nim"] == target_nim), None)
    if not resident:
        return False, f"Penghuni dengan NIM {target_nim} tidak ditemukan."
    if resident["status"] != "Aktif":
        return False, f"Penghuni {target_nim} berstatus '{resident['status']}', tidak dapat mencatat pelanggaran."

    aturan = next((a for a in ATURAN_PELANGGARAN if a[0] == kode_aturan), None)
    if not aturan:
        return False, f"Kode aturan {kode_aturan} tidak valid."

    plg_id = generate_next_id(violations, "id", "PLG")
    violations.append({
        "id": plg_id,
        "nim": target_nim,
        "kode_aturan": aturan[0],
        "deskripsi": aturan[1],
        "poin": aturan[2],
        "tanggal": datetime.now().strftime("%Y-%m-%d"),
    })
    resident["poin"] += aturan[2]

    msg = f"Pelanggaran {plg_id} dicatat (+{aturan[2]} poin). Total poin {resident['nama']}: {resident['poin']}."
    msg += _evaluate_discipline_sanctions(resident, violations, rooms, residents)

    storage.save_violations(violations)
    storage.save_residents(residents)
    return True, msg


def update_violation(plg_id, new_kode_aturan):
    rooms = storage.load_rooms()
    residents = storage.load_residents()
    violations = storage.load_violations()

    target_id = plg_id.strip().upper()
    violation = next((v for v in violations if v["id"] == target_id), None)
    if not violation:
        return False, f"ID Pelanggaran {target_id} tidak ditemukan."

    aturan = next((a for a in ATURAN_PELANGGARAN if a[0] == new_kode_aturan), None)
    if not aturan:
        return False, f"Kode aturan {new_kode_aturan} tidak valid."

    violation["kode_aturan"] = aturan[0]
    violation["deskripsi"] = aturan[1]
    violation["poin"] = aturan[2]

    _recalculate_resident_points(residents, violations)

    resident = next((r for r in residents if r["nim"] == violation["nim"]), None)
    msg = f"Pelanggaran {target_id} diperbarui ke {aturan[0]} (+{aturan[2]} poin)."
    if resident:
        msg += f" Total poin {resident['nama']} sekarang: {resident['poin']}."
        msg += _evaluate_discipline_sanctions(resident, violations, rooms, residents)

    storage.save_violations(violations)
    storage.save_residents(residents)
    return True, msg


def delete_violation(plg_id):
    rooms = storage.load_rooms()
    residents = storage.load_residents()
    violations = storage.load_violations()

    target_id = plg_id.strip().upper()
    for idx, v in enumerate(violations):
        if v["id"] == target_id:
            removed = violations.pop(idx)
            _recalculate_resident_points(residents, violations)

            resident = next((r for r in residents if r["nim"] == removed["nim"]), None)
            msg = f"Catatan pelanggaran {target_id} (NIM {removed['nim']}) berhasil dihapus dan poin telah disesuaikan."
            if resident:
                msg += _evaluate_discipline_sanctions(resident, violations, rooms, residents)

            storage.save_violations(violations)
            storage.save_residents(residents)
            return True, msg

    return False, f"ID Pelanggaran {target_id} tidak ditemukan."


# --- CRUD Izin Keluar ---

def _parse_date(text):
    try:
        return datetime.strptime(str(text).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def validate_permit_dates(tgl_keluar, tgl_kembali):
    keluar = _parse_date(tgl_keluar)
    kembali = _parse_date(tgl_kembali)
    if keluar is None or kembali is None:
        return False, "Format tanggal harus YYYY-MM-DD dan tanggalnya harus valid (contoh: 2026-12-01)."
    if kembali < keluar:
        return False, f"Tanggal kembali ({kembali.isoformat()}) tidak boleh lebih awal dari tanggal keluar ({keluar.isoformat()})."
    return True, (keluar.isoformat(), kembali.isoformat())


def _has_overlapping_permit(permits, nim, keluar_iso, kembali_iso):
    new_start = _parse_date(keluar_iso)
    new_end = _parse_date(kembali_iso)
    for p in permits:
        if p["nim"] != nim or p["status"] not in ("Menunggu", "Disetujui"):
            continue
        old_start = _parse_date(p["tgl_keluar"])
        old_end = _parse_date(p["tgl_kembali"])
        if old_start and old_end and new_start <= old_end and old_start <= new_end:
            return p["id"]
    return None


def create_permit(nim, tujuan, tgl_keluar, tgl_kembali):
    ok, result = validate_permit_dates(tgl_keluar, tgl_kembali)
    if not ok:
        return False, result
    tgl_keluar, tgl_kembali = result

    residents = storage.load_residents()
    permits = storage.load_permits()

    target_nim = nim.strip().upper()
    resident = next((r for r in residents if r["nim"] == target_nim), None)
    if not resident:
        return False, f"Penghuni dengan NIM {target_nim} tidak ditemukan."
    if resident["status"] != "Aktif":
        return False, f"Penghuni {target_nim} berstatus '{resident['status']}', tidak dapat mengajukan izin."
    if not tujuan or not tujuan.strip():
        return False, "Tujuan izin tidak boleh kosong."

    bentrok = _has_overlapping_permit(permits, target_nim, tgl_keluar, tgl_kembali)
    if bentrok:
        return False, f"Tanggal izin bertabrakan dengan izin {bentrok} milik NIM {target_nim}."

    izin_id = generate_next_id(permits, "id", "IZN")
    permits.append({
        "id": izin_id,
        "nim": target_nim,
        "tujuan": sanitize_pipe(tujuan),
        "tgl_keluar": tgl_keluar,
        "tgl_kembali": tgl_kembali,
        "status": "Menunggu",
    })
    storage.save_permits(permits)
    return True, f"Pengajuan izin {izin_id} atas nama {resident['nama']} berhasil dibuat (Status: Menunggu)."


def delete_permit(permit_id):
    permits = storage.load_permits()
    pid = permit_id.strip().upper()
    for idx, p in enumerate(permits):
        if p["id"] == pid:
            if p["status"] == "Disetujui":
                return False, f"Izin {pid} sudah berstatus 'Disetujui' dan tidak dapat dihapus."
            permits.pop(idx)
            storage.save_permits(permits)
            return True, f"Pengajuan izin {pid} berhasil dibatalkan/dihapus."
    return False, f"ID Izin {pid} tidak ditemukan."


def update_permit_status(permit_id, new_status):
    residents = storage.load_residents()
    permits = storage.load_permits()

    pid = permit_id.strip().upper()
    status_clean = new_status.strip().capitalize()
    if status_clean not in VALID_PERMIT_STATUS:
        return False, f"Status '{new_status}' tidak valid. Pilihan: {', '.join(VALID_PERMIT_STATUS)}."

    permit = next((p for p in permits if p["id"] == pid), None)
    if not permit:
        return False, f"ID Izin {pid} tidak ditemukan."
    if permit["status"] in FINAL_PERMIT_STATUS:
        return False, f"Izin {pid} sudah berstatus final '{permit['status']}' dan tidak dapat diubah lagi."
    if status_clean == permit["status"]:
        return False, f"Izin {pid} sudah berstatus '{status_clean}'."

    permit["status"] = status_clean
    storage.save_permits(permits)

    msg = f"Status izin {pid} diubah menjadi '{status_clean}'."
    if status_clean == "Disetujui":
        resident = next((r for r in residents if r["nim"] == permit["nim"]), None)
        if resident:
            surat_text = format_surat_izin_txt(permit, resident)
            filepath = storage.export_document_txt(f"Surat_Izin_{pid}_{resident['nim']}.txt", surat_text)
            msg += f"\nSurat izin resmi berhasil diekspor ke: {filepath}"

    return True, msg