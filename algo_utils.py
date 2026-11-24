

from datetime import datetime

def parse_room_code(raw_code):
    code = raw_code.strip().upper()
    if "-" not in code:
        return False, "Format kode kamar harus menggunakan tanda '-' (contoh: A-101)."

    parts = code.split("-")
    if len(parts) != 2:
        return False, "Format kode kamar tidak valid (contoh yang benar: A-101)."

    blok, nomor = parts[0], parts[1]
    if blok not in ("A", "B"):
        return False, "Kode blok gedung hanya boleh 'A' (Putra) atau 'B' (Putri)."

    if len(nomor) != 3 or not nomor.isdigit():
        return False, "Nomor kamar harus terdiri dari 3 digit angka (contoh: 101, 204)."

    lantai = int(nomor[0])
    if lantai < 1 or lantai > 5:
        return False, "Nomor lantai (digit pertama) harus antara 1 sampai 5."

    gedung = "Putra A" if blok == "A" else "Putri B"
    gender = "L" if blok == "A" else "P"

    return True, {
        "kode": f"{blok}-{nomor}",
        "gedung": gedung,
        "lantai": lantai,
        "gender": gender,
    }


def generate_next_id(records, id_key, prefix):
    """
    Menghasilkan ID berurutan otomatis (contoh: 'PLG-004' -> 'PLG-005')
    menggunakan string slicing dan zero-padding formatting.
    """
    max_num = 0
    prefix_dash = f"{prefix}-"
    for rec in records:
        rec_id = rec.get(id_key, "")
        if rec_id.startswith(prefix_dash):
            num_part = rec_id[len(prefix_dash):]
            if num_part.isdigit():
                num_val = int(num_part)
                if num_val > max_num:
                    max_num = num_val
    return f"{prefix}-{max_num + 1:03d}"


def validate_nim(raw_nim):
    """Validasi string NIM mahasiswa (minimal 8 karakter alfanumerik, tanpa '|')."""
    nim = raw_nim.strip().upper()
    if "|" in nim or " " in nim:
        return False, "NIM tidak boleh mengandung spasi atau karakter '|'."
    if len(nim) < 8 or not nim.isalnum():
        return False, "NIM minimal 8 karakter alfanumerik (contoh: J0403261047)."
    return True, nim


def validate_date_str(raw_date):
    """Validasi format tanggal YYYY-MM-DD menggunakan string slicing & datetime."""
    date_str = raw_date.strip()
    if len(date_str) != 10 or date_str[4] != "-" or date_str[7] != "-":
        return False, "Format tanggal wajib YYYY-MM-DD (contoh: 2026-11-25)."
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True, date_str
    except ValueError:
        return False, "Tanggal kalender tidak valid."


def sanitize_pipe(text):
    """Mencegah karakter delimiter '|' merusak struktur file .txt."""
    return text.strip().replace("|", "/")


def format_surat_izin_txt(permit, resident):
    """Menyusun teks formal Surat Izin Keluar Asrama untuk diekspor ke .txt."""
    garis = "=" * 62
    subgaris = "-" * 62
    return (
        f"{garis}\n"
        f"{'SURAT IZIN KELUAR / PULANG MALAM ASRAMA':^62}\n"
        f"{'UNIT PENGELOLA ASRAMA MAHASISWA':^62}\n"
        f"{garis}\n"
        f"Nomor Surat   : {permit['id']}/ASR-IZN/2026\n"
        f"Status Izin   : {permit['status'].upper()}\n"
        f"{subgaris}\n"
        f"Data Penghuni yang Mengajukan:\n"
        f"  Nama Lengkap : {resident['nama']}\n"
        f"  NIM          : {resident['nim']}\n"
        f"  Program Studi: {resident['prodi']}\n"
        f"  Kamar Asrama : {resident['kamar']}\n"
        f"{subgaris}\n"
        f"Rincian Perizinan:\n"
        f"  Keperluan    : {permit['tujuan']}\n"
        f"  Tgl Keluar   : {permit['tgl_keluar']}\n"
        f"  Tgl Kembali  : {permit['tgl_kembali']}\n"
        f"{subgaris}\n"
        f"Catatan: Harap menunjukkan surat ini kepada petugas gerbang\n"
        f"asrama saat keluar maupun kembali ke lingkungan asrama.\n"
        f"{garis}\n"
        f"Dicetak otomatis pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )


def format_surat_peringatan_txt(resident, resident_violations):
    """Menyusun teks Surat Peringatan (SP) otomatis jika poin pelanggaran >= 50."""
    garis = "=" * 62
    subgaris = "-" * 62
    tingkat_sp = "SP-2 (KRITIS / EVALUASI KELAYAKAN)" if resident["poin"] >= 80 else "SP-1 (PERINGATAN KERAS)"

    riwayat_lines = []
    for idx, v in enumerate(resident_violations, start=1):
        riwayat_lines.append(
            f"  {idx}. [{v['tanggal']}] {v['kode_aturan']} - {v['deskripsi']} (+{v['poin']} poin)"
        )
    riwayat_str = "\n".join(riwayat_lines) if riwayat_lines else "  - Tidak ada rincian"

    return (
        f"{garis}\n"
        f"{'SURAT PERINGATAN PELANGGARAN TATA TERTIB ASRAMA':^62}\n"
        f"{tingkat_sp:^62}\n"
        f"{garis}\n"
        f"Kepada Yth. Saudara/i:\n"
        f"  Nama Lengkap : {resident['nama']}\n"
        f"  NIM          : {resident['nim']}\n"
        f"  Prodi / Kamar: {resident['prodi']} / {resident['kamar']}\n"
        f"  Akumulasi    : {resident['poin']} Poin Pelanggaran\n"
        f"{subgaris}\n"
        f"Rincian Catatan Pelanggaran:\n"
        f"{riwayat_str}\n"
        f"{subgaris}\n"
        f"Berdasarkan tata tertib asrama, penghuni dengan akumulasi poin\n"
        f">= 50 dikenakan pembinaan khusus. Apabila mencapai 100 poin,\n"
        f"hak tinggal di asrama akan dicabut.\n"
        f"{garis}\n"
        f"Dicetak otomatis pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )


# ==============================================================================
# 2. ALGORITMA SORTING MANUAL (MERGE SORT - O(n log n))
# ==============================================================================

def merge_sort_records(records, key_func, reverse=False):
    """
    Implementasi manual algoritma Merge Sort untuk mengurutkan list of dict
    tanpa menggunakan fungsi sort() / sorted() bawaan Python.
    """
    if len(records) <= 1:
        return list(records)

    mid = len(records) // 2
    left_half = merge_sort_records(records[:mid], key_func, reverse=reverse)
    right_half = merge_sort_records(records[mid:], key_func, reverse=reverse)

    return _merge(left_half, right_half, key_func, reverse)


def _merge(left, right, key_func, reverse):
    merged = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        left_val = key_func(left[i])
        right_val = key_func(right[j])

        if not reverse:
            condition = left_val <= right_val
        else:
            condition = left_val >= right_val

        if condition:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    while i < len(left):
        merged.append(left[i])
        i += 1

    while j < len(right):
        merged.append(right[j])
        j += 1

    return merged


# ==============================================================================
# 3. ALGORITMA SEARCHING MANUAL (BINARY SEARCH & LINEAR SUBSTRING SEARCH)
# ==============================================================================

def binary_search_by_nim(residents, target_nim):
    """
    Implementasi manual algoritma Binary Search untuk mencari penghuni
    berdasarkan NIM. Data diurutkan terlebih dahulu menggunakan Merge Sort.
    Returns: (found_resident_dict_or_None, steps_taken)
    """
    sorted_residents = merge_sort_records(residents, key_func=lambda r: r["nim"], reverse=False)
    target = target_nim.strip().upper()

    low = 0
    high = len(sorted_residents) - 1
    steps = 0

    while low <= high:
        steps += 1
        mid = (low + high) // 2
        mid_nim = sorted_residents[mid]["nim"]

        if mid_nim == target:
            return sorted_residents[mid], steps
        elif mid_nim < target:
            low = mid + 1
        else:
            high = mid - 1

    return None, steps


def linear_search_by_name(residents, keyword):
    """
    Implementasi Linear Substring Search (case-insensitive) untuk mencari
    penghuni berdasarkan potongan nama.
    """
    query = keyword.strip().lower()
    results = []
    for res in residents:
        if query in res["nama"].lower():
            results.append(res)
    return results
