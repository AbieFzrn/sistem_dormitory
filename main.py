#!/usr/bin/env python3
"""
main.py - Sistem Manajemen Asrama
Entry point utama dengan sistem menu.
"""

import sys
import storage as db
from utils import (
    clear_screen, tekan_enter, print_header, print_subheader,
    print_success, print_error, print_warning, print_info,
    print_table, input_text, input_int, input_pilihan, input_tanggal,
    input_no_telp, input_menu, konfirmasi, format_gender, format_tipe_kamar,
    format_severity, format_status_izin, format_okupansi_bar, print_detail_box,
    Warna, warna, bold, sukses, error, peringatan, info
)


# ===================== MAIN MENU =====================

def menu_utama():
    while True:
        print_header("SISTEM MANAJEMEN ASRAMA")
        print(f"  {Warna.BOLD}1.{Warna.RESET} 👤 Manajemen Penghuni")
        print(f"  {Warna.BOLD}2.{Warna.RESET} 🏠 Manajemen Kamar")
        print(f"  {Warna.BOLD}3.{Warna.RESET} 🔑 Penempatan Kamar")
        print(f"  {Warna.BOLD}4.{Warna.RESET} ⚠️  Pencatatan Pelanggaran")
        print(f"  {Warna.BOLD}5.{Warna.RESET} 📋 Izin Keluar")
        print(f"  {Warna.BOLD}6.{Warna.RESET} 🔄 Riwayat Perpindahan")
        print(f"  {Warna.BOLD}7.{Warna.RESET} 📊 Statistik Okupansi")
        print(f"  {Warna.BOLD}8.{Warna.RESET} 🌱 Data Contoh (Seed)")
        print(f"  {Warna.BOLD}0.{Warna.RESET} 🚪 Keluar")

        pilihan = input_menu(8)

        if pilihan == 1:
            menu_penghuni()
        elif pilihan == 2:
            menu_kamar()
        elif pilihan == 3:
            menu_penempatan()
        elif pilihan == 4:
            menu_pelanggaran()
        elif pilihan == 5:
            menu_izin_keluar()
        elif pilihan == 6:
            menu_perpindahan()
        elif pilihan == 7:
            menu_statistik()
        elif pilihan == 8:
            menu_seed()
        elif pilihan == 0:
            clear_screen()
            print(sukses("\n  Terima kasih telah menggunakan Sistem Manajemen Asrama!"))
            print(f"  {Warna.DIM}Sampai jumpa! 👋{Warna.RESET}\n")
            sys.exit(0)


# ===================== MENU PENGHUNI =====================

def menu_penghuni():
    while True:
        print_header("MANAJEMEN PENGHUNI", ["Menu Utama", "Penghuni"])
        print(f"  {Warna.BOLD}1.{Warna.RESET} Tambah Penghuni")
        print(f"  {Warna.BOLD}2.{Warna.RESET} Lihat Daftar Penghuni")
        print(f"  {Warna.BOLD}3.{Warna.RESET} Edit Penghuni")
        print(f"  {Warna.BOLD}4.{Warna.RESET} Hapus Penghuni")
        print(f"  {Warna.BOLD}5.{Warna.RESET} Cari Penghuni")
        print(f"  {Warna.BOLD}0.{Warna.RESET} Kembali")

        pilihan = input_menu(5)
        if pilihan == 0:
            return
        elif pilihan == 1:
            tambah_penghuni()
        elif pilihan == 2:
            lihat_penghuni()
        elif pilihan == 3:
            edit_penghuni()
        elif pilihan == 4:
            hapus_penghuni()
        elif pilihan == 5:
            cari_penghuni()


def tambah_penghuni():
    print_header("TAMBAH PENGHUNI", ["Menu Utama", "Penghuni", "Tambah"])
    print_subheader("Masukkan Data Penghuni Baru")
    print()

    nama = input_text("Nama lengkap")
    nim = input_text("NIM")
    jurusan = input_text("Jurusan")
    no_telp = input_no_telp("No. Telepon")
    jk = input_pilihan("Jenis Kelamin", ["L", "P"])

    print(f"\n  {Warna.DIM}{'─' * 40}{Warna.RESET}")
    print(f"  Nama         : {bold(nama)}")
    print(f"  NIM          : {bold(nim)}")
    print(f"  Jurusan      : {bold(jurusan)}")
    print(f"  No. Telepon  : {bold(no_telp)}")
    print(f"  Jenis Kelamin: {bold(format_gender(jk))}")

    if not konfirmasi("Simpan data penghuni ini?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg, penghuni_id = db.tambah_penghuni(nama, nim, jurusan, no_telp, jk)
    if ok:
        print_success(msg)
        # Offer auto-assignment
        if konfirmasi("Tempatkan penghuni ini ke kamar secara otomatis?"):
            ok2, msg2 = db.auto_assign_room(penghuni_id)
            if ok2:
                print_success(msg2)
            else:
                print_warning(msg2)
    else:
        print_error(msg)
    tekan_enter()


def _display_penghuni_table(rows):
    headers = ["ID", "Nama", "NIM", "Jurusan", "No. Telp", "JK", "Kamar"]
    data = []
    for r in rows:
        data.append([
            r['id'], r['nama'], r['nim'], r['jurusan'],
            r['no_telp'], format_gender(r['jenis_kelamin']),
            r['nomor_kamar'] or '-'
        ])
    print_table(headers, data, [4, 20, 10, 18, 15, 10, 6])


def lihat_penghuni():
    print_header("DAFTAR PENGHUNI", ["Menu Utama", "Penghuni", "Daftar"])
    rows = db.get_all_penghuni()
    if not rows:
        print_info("Belum ada data penghuni.")
    else:
        _display_penghuni_table(rows)
    tekan_enter()


def edit_penghuni():
    print_header("EDIT PENGHUNI", ["Menu Utama", "Penghuni", "Edit"])
    rows = db.get_all_penghuni()
    if not rows:
        print_info("Belum ada data penghuni.")
        tekan_enter()
        return

    _display_penghuni_table(rows)
    pid = input_int("\n  Masukkan ID penghuni yang akan diedit", min_val=1)
    ph = db.get_penghuni_by_id(pid)
    if not ph:
        print_error("Penghuni tidak ditemukan.")
        tekan_enter()
        return

    print(f"\n  {Warna.DIM}Kosongkan input untuk mempertahankan nilai lama.{Warna.RESET}")
    print(f"  {Warna.DIM}Nilai saat ini ditampilkan dalam kurung.{Warna.RESET}\n")

    nama = input(f"  Nama [{ph['nama']}]: ").strip() or ph['nama']
    nim = input(f"  NIM [{ph['nim']}]: ").strip() or ph['nim']
    jurusan = input(f"  Jurusan [{ph['jurusan']}]: ").strip() or ph['jurusan']
    no_telp = input(f"  No. Telepon [{ph['no_telp']}]: ").strip() or ph['no_telp']
    jk = input(f"  Jenis Kelamin [{ph['jenis_kelamin']}] (L/P): ").strip().upper() or ph['jenis_kelamin']

    if jk not in ('L', 'P'):
        print_error("Jenis kelamin harus 'L' atau 'P'.")
        tekan_enter()
        return

    if not konfirmasi("Simpan perubahan?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.edit_penghuni(pid, nama, nim, jurusan, no_telp, jk)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def hapus_penghuni():
    print_header("HAPUS PENGHUNI", ["Menu Utama", "Penghuni", "Hapus"])
    rows = db.get_all_penghuni()
    if not rows:
        print_info("Belum ada data penghuni.")
        tekan_enter()
        return

    _display_penghuni_table(rows)
    pid = input_int("\n  Masukkan ID penghuni yang akan dihapus", min_val=1)
    ph = db.get_penghuni_by_id(pid)
    if not ph:
        print_error("Penghuni tidak ditemukan.")
        tekan_enter()
        return

    print(f"\n  Akan menghapus: {bold(ph['nama'])} ({ph['nim']})")
    if not konfirmasi("Yakin ingin menghapus penghuni ini?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.hapus_penghuni(pid)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def cari_penghuni():
    print_header("CARI PENGHUNI", ["Menu Utama", "Penghuni", "Cari"])
    keyword = input_text("Masukkan nama atau NIM")
    rows = db.cari_penghuni(keyword)
    if not rows:
        print_info(f"Tidak ditemukan penghuni dengan kata kunci '{keyword}'.")
    else:
        print(f"\n  Hasil pencarian untuk '{bold(keyword)}':")
        _display_penghuni_table(rows)
    tekan_enter()


# ===================== MENU KAMAR =====================

def menu_kamar():
    while True:
        print_header("MANAJEMEN KAMAR", ["Menu Utama", "Kamar"])
        print(f"  {Warna.BOLD}1.{Warna.RESET} Tambah Kamar")
        print(f"  {Warna.BOLD}2.{Warna.RESET} Lihat Daftar Kamar")
        print(f"  {Warna.BOLD}3.{Warna.RESET} Edit Kamar")
        print(f"  {Warna.BOLD}4.{Warna.RESET} Hapus Kamar")
        print(f"  {Warna.BOLD}5.{Warna.RESET} Pengaturan Kapasitas")
        print(f"  {Warna.BOLD}6.{Warna.RESET} Lihat Penghuni Kamar")
        print(f"  {Warna.BOLD}0.{Warna.RESET} Kembali")

        pilihan = input_menu(6)
        if pilihan == 0:
            return
        elif pilihan == 1:
            tambah_kamar()
        elif pilihan == 2:
            lihat_kamar()
        elif pilihan == 3:
            edit_kamar()
        elif pilihan == 4:
            hapus_kamar()
        elif pilihan == 5:
            pengaturan_kapasitas()
        elif pilihan == 6:
            lihat_penghuni_kamar()


def _display_kamar_table(rows):
    headers = ["ID", "No. Kamar", "Lantai", "Tipe", "Kapasitas", "Terisi", "Status"]
    data = []
    for r in rows:
        terisi = r['terisi']
        kap = r['kapasitas']
        if terisi >= kap:
            status = f"{Warna.MERAH}Penuh{Warna.RESET}"
        elif terisi > 0:
            status = f"{Warna.KUNING}Terisi{Warna.RESET}"
        else:
            status = f"{Warna.HIJAU}Kosong{Warna.RESET}"
        data.append([
            r['id'], r['nomor_kamar'], r['lantai'],
            format_tipe_kamar(r['tipe']), kap,
            f"{terisi}/{kap}", status
        ])
    print_table(headers, data, [4, 10, 6, 7, 9, 7, 8])


def tambah_kamar():
    print_header("TAMBAH KAMAR", ["Menu Utama", "Kamar", "Tambah"])
    print_subheader("Masukkan Data Kamar Baru")
    print()

    nomor = input_text("Nomor Kamar")
    lantai = input_int("Lantai", min_val=1, max_val=99)
    tipe = input_pilihan("Tipe Kamar", ["putra", "putri"])
    kapasitas = input_int("Kapasitas", min_val=1, max_val=10)

    if not konfirmasi("Simpan data kamar ini?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.tambah_kamar(nomor, lantai, tipe, kapasitas)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def lihat_kamar():
    print_header("DAFTAR KAMAR", ["Menu Utama", "Kamar", "Daftar"])
    rows = db.get_all_kamar()
    if not rows:
        print_info("Belum ada data kamar.")
    else:
        _display_kamar_table(rows)
    tekan_enter()


def edit_kamar():
    print_header("EDIT KAMAR", ["Menu Utama", "Kamar", "Edit"])
    rows = db.get_all_kamar()
    if not rows:
        print_info("Belum ada data kamar.")
        tekan_enter()
        return

    _display_kamar_table(rows)
    kid = input_int("\n  Masukkan ID kamar yang akan diedit", min_val=1)
    kamar = db.get_kamar_by_id(kid)
    if not kamar:
        print_error("Kamar tidak ditemukan.")
        tekan_enter()
        return

    print(f"\n  {Warna.DIM}Kosongkan input untuk mempertahankan nilai lama.{Warna.RESET}\n")

    nomor = input(f"  Nomor Kamar [{kamar['nomor_kamar']}]: ").strip() or kamar['nomor_kamar']
    lantai_str = input(f"  Lantai [{kamar['lantai']}]: ").strip()
    lantai = int(lantai_str) if lantai_str else kamar['lantai']
    tipe = input(f"  Tipe [{kamar['tipe']}] (putra/putri): ").strip().lower() or kamar['tipe']
    kap_str = input(f"  Kapasitas [{kamar['kapasitas']}]: ").strip()
    kapasitas = int(kap_str) if kap_str else kamar['kapasitas']

    if tipe not in ('putra', 'putri'):
        print_error("Tipe kamar harus 'putra' atau 'putri'.")
        tekan_enter()
        return

    if not konfirmasi("Simpan perubahan?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.edit_kamar(kid, nomor, lantai, tipe, kapasitas)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def hapus_kamar():
    print_header("HAPUS KAMAR", ["Menu Utama", "Kamar", "Hapus"])
    rows = db.get_all_kamar()
    if not rows:
        print_info("Belum ada data kamar.")
        tekan_enter()
        return

    _display_kamar_table(rows)
    kid = input_int("\n  Masukkan ID kamar yang akan dihapus", min_val=1)
    kamar = db.get_kamar_by_id(kid)
    if not kamar:
        print_error("Kamar tidak ditemukan.")
        tekan_enter()
        return

    print(f"\n  Akan menghapus kamar: {bold(kamar['nomor_kamar'])} (Lantai {kamar['lantai']})")
    if not konfirmasi("Yakin ingin menghapus kamar ini?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.hapus_kamar(kid)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def pengaturan_kapasitas():
    print_header("PENGATURAN KAPASITAS KAMAR", ["Menu Utama", "Kamar", "Kapasitas"])
    rows = db.get_kapasitas_overview()
    if not rows:
        print_info("Belum ada data kamar.")
        tekan_enter()
        return

    print_subheader("Ikhtisar Kapasitas Kamar")
    print()
    headers = ["ID", "No. Kamar", "Lantai", "Tipe", "Kapasitas", "Terisi", "Sisa"]
    data = []
    for r in rows:
        sisa = r['kapasitas'] - r['terisi']
        data.append([
            r['id'], r['nomor_kamar'], r['lantai'],
            format_tipe_kamar(r['tipe']), r['kapasitas'],
            r['terisi'], sisa
        ])
    print_table(headers, data, [4, 10, 6, 7, 9, 6, 5])

    print()
    if not konfirmasi("Ingin mengubah kapasitas kamar?"):
        return

    kid = input_int("  Masukkan ID kamar", min_val=1)
    kamar = db.get_kamar_by_id(kid)
    if not kamar:
        print_error("Kamar tidak ditemukan.")
        tekan_enter()
        return

    print(f"\n  Kamar {bold(kamar['nomor_kamar'])}: Kapasitas saat ini = {kamar['kapasitas']}, Terisi = {kamar['terisi']}")
    kap_baru = input_int("  Kapasitas baru", min_val=1, max_val=10)

    ok, msg = db.update_kapasitas_kamar(kid, kap_baru)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def lihat_penghuni_kamar():
    print_header("PENGHUNI PER KAMAR", ["Menu Utama", "Kamar", "Penghuni"])
    all_kamar = db.get_all_kamar()
    if not all_kamar:
        print_info("Belum ada data kamar.")
        tekan_enter()
        return

    _display_kamar_table(all_kamar)
    kid = input_int("\n  Masukkan ID kamar untuk melihat penghuni", min_val=1)
    kamar = db.get_kamar_by_id(kid)
    if not kamar:
        print_error("Kamar tidak ditemukan.")
        tekan_enter()
        return

    penghuni = db.get_penghuni_di_kamar(kid)
    print(f"\n  Kamar {bold(kamar['nomor_kamar'])} (Lantai {kamar['lantai']}, {format_tipe_kamar(kamar['tipe'])})")
    print(f"  Kapasitas: {kamar['terisi']}/{kamar['kapasitas']}")
    print()

    if not penghuni:
        print_info("Kamar ini kosong.")
    else:
        headers = ["ID", "Nama", "NIM", "Jurusan", "No. Telp"]
        data = [[p['id'], p['nama'], p['nim'], p['jurusan'], p['no_telp']] for p in penghuni]
        print_table(headers, data, [4, 20, 10, 18, 15])
    tekan_enter()


# ===================== MENU PENEMPATAN =====================

def menu_penempatan():
    while True:
        print_header("PENEMPATAN KAMAR", ["Menu Utama", "Penempatan"])
        print(f"  {Warna.BOLD}1.{Warna.RESET} Penempatan Otomatis")
        print(f"  {Warna.BOLD}2.{Warna.RESET} Penempatan Manual")
        print(f"  {Warna.BOLD}3.{Warna.RESET} Keluarkan Penghuni dari Kamar")
        print(f"  {Warna.BOLD}4.{Warna.RESET} Lihat Penghuni Tanpa Kamar")
        print(f"  {Warna.BOLD}0.{Warna.RESET} Kembali")

        pilihan = input_menu(4)
        if pilihan == 0:
            return
        elif pilihan == 1:
            penempatan_otomatis()
        elif pilihan == 2:
            penempatan_manual()
        elif pilihan == 3:
            keluarkan_penghuni()
        elif pilihan == 4:
            lihat_tanpa_kamar()


def penempatan_otomatis():
    print_header("PENEMPATAN OTOMATIS", ["Menu Utama", "Penempatan", "Otomatis"])

    # Show residents without rooms
    tanpa_kamar = db.get_penghuni_tanpa_kamar()
    if not tanpa_kamar:
        print_info("Semua penghuni sudah ditempatkan di kamar.")
        tekan_enter()
        return

    print_subheader("Penghuni Belum Memiliki Kamar")
    headers = ["ID", "Nama", "NIM", "JK"]
    data = [[p['id'], p['nama'], p['nim'], format_gender(p['jenis_kelamin'])] for p in tanpa_kamar]
    print_table(headers, data, [4, 20, 10, 10])

    print()
    mode = input_pilihan("Tempatkan satu per satu atau semua sekaligus?", ["satu", "semua"])

    if mode == "semua":
        if not konfirmasi("Tempatkan semua penghuni secara otomatis?"):
            print_warning("Dibatalkan.")
            tekan_enter()
            return
        berhasil = 0
        gagal = 0
        for p in tanpa_kamar:
            ok, msg = db.auto_assign_room(p['id'])
            if ok:
                berhasil += 1
                print(f"  {sukses('✓')} {p['nama']}: {msg}")
            else:
                gagal += 1
                print(f"  {error('✗')} {p['nama']}: {msg}")
        print(f"\n  Hasil: {sukses(str(berhasil) + ' berhasil')}, {error(str(gagal) + ' gagal')}")
    else:
        pid = input_int("  Masukkan ID penghuni", min_val=1)
        ok, msg = db.auto_assign_room(pid)
        if ok:
            print_success(msg)
        else:
            print_error(msg)
    tekan_enter()


def penempatan_manual():
    print_header("PENEMPATAN MANUAL", ["Menu Utama", "Penempatan", "Manual"])

    tanpa_kamar = db.get_penghuni_tanpa_kamar()
    if not tanpa_kamar:
        print_info("Semua penghuni sudah ditempatkan di kamar.")
        tekan_enter()
        return

    print_subheader("Penghuni Belum Memiliki Kamar")
    headers = ["ID", "Nama", "NIM", "JK"]
    data = [[p['id'], p['nama'], p['nim'], format_gender(p['jenis_kelamin'])] for p in tanpa_kamar]
    print_table(headers, data, [4, 20, 10, 10])

    pid = input_int("\n  Masukkan ID penghuni", min_val=1)
    ph = db.get_penghuni_by_id(pid)
    if not ph:
        print_error("Penghuni tidak ditemukan.")
        tekan_enter()
        return

    # Show available rooms for this gender
    available = db.get_available_rooms(ph['jenis_kelamin'])
    if not available:
        print_error("Tidak ada kamar tersedia yang sesuai.")
        tekan_enter()
        return

    print(f"\n  Kamar tersedia untuk {bold(format_gender(ph['jenis_kelamin']))}:")
    headers = ["ID", "No. Kamar", "Lantai", "Tipe", "Terisi/Kapasitas"]
    data = [[r['id'], r['nomor_kamar'], r['lantai'], format_tipe_kamar(r['tipe']),
             f"{r['terisi']}/{r['kapasitas']}"] for r in available]
    print_table(headers, data, [4, 10, 6, 7, 16])

    kid = input_int("\n  Masukkan ID kamar tujuan", min_val=1)

    ok, msg = db.manual_assign_room(pid, kid)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def keluarkan_penghuni():
    print_header("KELUARKAN PENGHUNI", ["Menu Utama", "Penempatan", "Keluarkan"])

    rows = db.get_all_penghuni()
    assigned = [r for r in rows if r['nomor_kamar']]
    if not assigned:
        print_info("Tidak ada penghuni yang ditempatkan di kamar.")
        tekan_enter()
        return

    headers = ["ID", "Nama", "NIM", "Kamar"]
    data = [[r['id'], r['nama'], r['nim'], r['nomor_kamar']] for r in assigned]
    print_table(headers, data, [4, 20, 10, 8])

    pid = input_int("\n  Masukkan ID penghuni yang akan dikeluarkan", min_val=1)
    ph = db.get_penghuni_by_id(pid)
    if not ph:
        print_error("Penghuni tidak ditemukan.")
        tekan_enter()
        return

    print(f"\n  Akan mengeluarkan {bold(ph['nama'])} dari kamar {bold(ph['nomor_kamar'] or '-')}")
    if not konfirmasi("Yakin ingin mengeluarkan penghuni ini dari kamar?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.keluarkan_penghuni(pid)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def lihat_tanpa_kamar():
    print_header("PENGHUNI TANPA KAMAR", ["Menu Utama", "Penempatan", "Tanpa Kamar"])
    rows = db.get_penghuni_tanpa_kamar()
    if not rows:
        print_info("Semua penghuni sudah memiliki kamar.")
    else:
        headers = ["ID", "Nama", "NIM", "Jurusan", "JK"]
        data = [[p['id'], p['nama'], p['nim'], p['jurusan'], format_gender(p['jenis_kelamin'])] for p in rows]
        print_table(headers, data, [4, 20, 10, 18, 10])
    tekan_enter()


# ===================== MENU PELANGGARAN =====================

def menu_pelanggaran():
    while True:
        print_header("PENCATATAN PELANGGARAN", ["Menu Utama", "Pelanggaran"])
        print(f"  {Warna.BOLD}1.{Warna.RESET} Catat Pelanggaran Baru")
        print(f"  {Warna.BOLD}2.{Warna.RESET} Lihat Pelanggaran per Penghuni")
        print(f"  {Warna.BOLD}3.{Warna.RESET} Lihat Semua Pelanggaran")
        print(f"  {Warna.BOLD}4.{Warna.RESET} Ringkasan Pelanggaran")
        print(f"  {Warna.BOLD}0.{Warna.RESET} Kembali")

        pilihan = input_menu(4)
        if pilihan == 0:
            return
        elif pilihan == 1:
            catat_pelanggaran()
        elif pilihan == 2:
            lihat_pelanggaran_penghuni()
        elif pilihan == 3:
            lihat_semua_pelanggaran()
        elif pilihan == 4:
            ringkasan_pelanggaran()


def catat_pelanggaran():
    print_header("CATAT PELANGGARAN", ["Menu Utama", "Pelanggaran", "Catat"])

    # Show residents
    rows = db.get_all_penghuni()
    if not rows:
        print_info("Belum ada data penghuni.")
        tekan_enter()
        return

    headers = ["ID", "Nama", "NIM", "Kamar"]
    data = [[r['id'], r['nama'], r['nim'], r['nomor_kamar'] or '-'] for r in rows]
    print_table(headers, data, [4, 20, 10, 8])

    pid = input_int("\n  ID Penghuni", min_val=1)
    ph = db.get_penghuni_by_id(pid)
    if not ph:
        print_error("Penghuni tidak ditemukan.")
        tekan_enter()
        return

    print(f"\n  Mencatat pelanggaran untuk: {bold(ph['nama'])} ({ph['nim']})")
    print()

    jenis = input_text("Jenis Pelanggaran")
    deskripsi = input_text("Deskripsi", required=False)
    tanggal = input_tanggal("Tanggal Pelanggaran")
    severity = input_pilihan("Tingkat Severity", ["ringan", "sedang", "berat"])

    if not konfirmasi("Simpan catatan pelanggaran ini?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.tambah_pelanggaran(pid, jenis, deskripsi, tanggal, severity)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def lihat_pelanggaran_penghuni():
    print_header("PELANGGARAN PER PENGHUNI", ["Menu Utama", "Pelanggaran", "Per Penghuni"])

    rows = db.get_all_penghuni()
    if not rows:
        print_info("Belum ada data penghuni.")
        tekan_enter()
        return

    headers = ["ID", "Nama", "NIM"]
    data = [[r['id'], r['nama'], r['nim']] for r in rows]
    print_table(headers, data, [4, 20, 10])

    pid = input_int("\n  Masukkan ID penghuni", min_val=1)
    violations = db.get_pelanggaran_by_penghuni(pid)

    ph = db.get_penghuni_by_id(pid)
    if not ph:
        print_error("Penghuni tidak ditemukan.")
        tekan_enter()
        return

    print(f"\n  Pelanggaran untuk: {bold(ph['nama'])} ({ph['nim']})")
    if not violations:
        print_info("Tidak ada catatan pelanggaran.")
    else:
        headers = ["ID", "Jenis", "Deskripsi", "Tanggal", "Severity"]
        data = [[v['id'], v['jenis_pelanggaran'], v['deskripsi'] or '-',
                 v['tanggal'], format_severity(v['tingkat_severity'])] for v in violations]
        print_table(headers, data, [4, 15, 25, 12, 8])
    tekan_enter()


def lihat_semua_pelanggaran():
    print_header("SEMUA PELANGGARAN", ["Menu Utama", "Pelanggaran", "Semua"])

    print(f"  Filter berdasarkan severity:")
    print(f"  1. Semua")
    print(f"  2. Ringan")
    print(f"  3. Sedang")
    print(f"  4. Berat")
    pil = input_menu(4)

    severity_map = {1: None, 2: 'ringan', 3: 'sedang', 4: 'berat'}
    sev_filter = severity_map.get(pil)

    violations = db.get_all_pelanggaran(sev_filter)
    if not violations:
        print_info("Tidak ada catatan pelanggaran.")
    else:
        headers = ["ID", "Nama", "NIM", "Jenis", "Tanggal", "Severity"]
        data = [[v['id'], v['nama'], v['nim'], v['jenis_pelanggaran'],
                 v['tanggal'], format_severity(v['tingkat_severity'])] for v in violations]
        print_table(headers, data, [4, 18, 10, 15, 12, 8])
    tekan_enter()


def ringkasan_pelanggaran():
    print_header("RINGKASAN PELANGGARAN", ["Menu Utama", "Pelanggaran", "Ringkasan"])

    summary, top_violators = db.get_ringkasan_pelanggaran()

    print_subheader("Jumlah Pelanggaran per Tingkat")
    if summary:
        total = sum(s['jumlah'] for s in summary)
        for s in summary:
            bar_len = int(s['jumlah'] / total * 30) if total > 0 else 0
            bar = "█" * bar_len
            sev = format_severity(s['tingkat_severity'])
            print(f"  {sev:20s} {bar} {s['jumlah']}")
        print(f"\n  {bold('Total')}: {total} pelanggaran")
    else:
        print_info("Belum ada data pelanggaran.")

    print()
    print_subheader("5 Penghuni dengan Pelanggaran Terbanyak")
    if top_violators:
        headers = ["Nama", "NIM", "Jumlah"]
        data = [[t['nama'], t['nim'], t['jumlah']] for t in top_violators]
        print_table(headers, data, [20, 10, 7])
    else:
        print_info("Belum ada data.")
    tekan_enter()


# ===================== MENU IZIN KELUAR =====================

def menu_izin_keluar():
    while True:
        print_header("IZIN KELUAR", ["Menu Utama", "Izin Keluar"])
        print(f"  {Warna.BOLD}1.{Warna.RESET} Ajukan Izin Keluar")
        print(f"  {Warna.BOLD}2.{Warna.RESET} Setujui/Tolak Izin")
        print(f"  {Warna.BOLD}3.{Warna.RESET} Penghuni Sedang Keluar")
        print(f"  {Warna.BOLD}4.{Warna.RESET} Riwayat Izin Keluar")
        print(f"  {Warna.BOLD}0.{Warna.RESET} Kembali")

        pilihan = input_menu(4)
        if pilihan == 0:
            return
        elif pilihan == 1:
            ajukan_izin()
        elif pilihan == 2:
            proses_izin()
        elif pilihan == 3:
            lihat_sedang_keluar()
        elif pilihan == 4:
            riwayat_izin()


def ajukan_izin():
    print_header("AJUKAN IZIN KELUAR", ["Menu Utama", "Izin Keluar", "Ajukan"])

    rows = db.get_all_penghuni()
    if not rows:
        print_info("Belum ada data penghuni.")
        tekan_enter()
        return

    headers = ["ID", "Nama", "NIM", "Kamar"]
    data = [[r['id'], r['nama'], r['nim'], r['nomor_kamar'] or '-'] for r in rows]
    print_table(headers, data, [4, 20, 10, 8])

    pid = input_int("\n  ID Penghuni", min_val=1)
    ph = db.get_penghuni_by_id(pid)
    if not ph:
        print_error("Penghuni tidak ditemukan.")
        tekan_enter()
        return

    print(f"\n  Mengajukan izin untuk: {bold(ph['nama'])} ({ph['nim']})")
    print()

    tgl_keluar = input_tanggal("Tanggal Keluar")
    tgl_kembali = input_tanggal("Tanggal Kembali")

    if tgl_kembali < tgl_keluar:
        print_error("Tanggal kembali tidak boleh sebelum tanggal keluar.")
        tekan_enter()
        return

    alasan = input_text("Alasan")

    if not konfirmasi("Ajukan izin keluar ini?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.tambah_izin_keluar(pid, tgl_keluar, tgl_kembali, alasan)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def proses_izin():
    print_header("PROSES IZIN KELUAR", ["Menu Utama", "Izin Keluar", "Proses"])

    pending = db.get_izin_pending()
    if not pending:
        print_info("Tidak ada izin yang menunggu persetujuan.")
        tekan_enter()
        return

    print_subheader("Izin Menunggu Persetujuan")
    headers = ["ID", "Nama", "NIM", "Tgl Keluar", "Tgl Kembali", "Alasan"]
    data = [[i['id'], i['nama'], i['nim'], i['tanggal_keluar'],
             i['tanggal_kembali'], i['alasan']] for i in pending]
    print_table(headers, data, [4, 18, 10, 12, 12, 20])

    izin_id = input_int("\n  Masukkan ID izin yang akan diproses", min_val=1)
    aksi = input_pilihan("Tindakan", ["setuju", "tolak"])
    status = 'disetujui' if aksi == 'setuju' else 'ditolak'

    if not konfirmasi(f"Yakin ingin {aksi} izin ini?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.update_status_izin(izin_id, status)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def lihat_sedang_keluar():
    print_header("PENGHUNI SEDANG KELUAR", ["Menu Utama", "Izin Keluar", "Sedang Keluar"])

    rows = db.get_penghuni_sedang_keluar()
    if not rows:
        print_info("Tidak ada penghuni yang sedang keluar saat ini.")
    else:
        headers = ["ID", "Nama", "NIM", "Tgl Keluar", "Tgl Kembali", "Alasan"]
        data = [[r['id'], r['nama'], r['nim'], r['tanggal_keluar'],
                 r['tanggal_kembali'], r['alasan']] for r in rows]
        print_table(headers, data, [4, 18, 10, 12, 12, 20])
    tekan_enter()


def riwayat_izin():
    print_header("RIWAYAT IZIN KELUAR", ["Menu Utama", "Izin Keluar", "Riwayat"])

    print(f"  1. Semua penghuni")
    print(f"  2. Penghuni tertentu")
    pil = input_menu(2)

    if pil == 0:
        return

    penghuni_id = None
    if pil == 2:
        rows = db.get_all_penghuni()
        headers = ["ID", "Nama", "NIM"]
        data = [[r['id'], r['nama'], r['nim']] for r in rows]
        print_table(headers, data, [4, 20, 10])
        penghuni_id = input_int("\n  Masukkan ID penghuni", min_val=1)

    izin_list = db.get_riwayat_izin(penghuni_id)
    if not izin_list:
        print_info("Tidak ada riwayat izin keluar.")
    else:
        headers = ["ID", "Nama", "NIM", "Tgl Keluar", "Tgl Kembali", "Alasan", "Status"]
        data = [[i['id'], i['nama'], i['nim'], i['tanggal_keluar'],
                 i['tanggal_kembali'], i['alasan'],
                 format_status_izin(i['status'])] for i in izin_list]
        print_table(headers, data, [4, 16, 10, 12, 12, 18, 10])
    tekan_enter()


# ===================== MENU PERPINDAHAN =====================

def menu_perpindahan():
    while True:
        print_header("RIWAYAT PERPINDAHAN KAMAR", ["Menu Utama", "Perpindahan"])
        print(f"  {Warna.BOLD}1.{Warna.RESET} Pindahkan Penghuni")
        print(f"  {Warna.BOLD}2.{Warna.RESET} Lihat Riwayat Perpindahan")
        print(f"  {Warna.BOLD}0.{Warna.RESET} Kembali")

        pilihan = input_menu(2)
        if pilihan == 0:
            return
        elif pilihan == 1:
            pindah_kamar()
        elif pilihan == 2:
            lihat_riwayat_perpindahan()


def pindah_kamar():
    print_header("PINDAHKAN PENGHUNI", ["Menu Utama", "Perpindahan", "Pindah"])

    # Show assigned residents
    rows = db.get_all_penghuni()
    assigned = [r for r in rows if r['nomor_kamar']]
    if not assigned:
        print_info("Tidak ada penghuni yang ditempatkan di kamar.")
        tekan_enter()
        return

    headers = ["ID", "Nama", "NIM", "JK", "Kamar Saat Ini"]
    data = [[r['id'], r['nama'], r['nim'], format_gender(r['jenis_kelamin']),
             r['nomor_kamar']] for r in assigned]
    print_table(headers, data, [4, 20, 10, 10, 14])

    pid = input_int("\n  ID Penghuni yang akan dipindah", min_val=1)
    ph = db.get_penghuni_by_id(pid)
    if not ph:
        print_error("Penghuni tidak ditemukan.")
        tekan_enter()
        return
    if not ph['nomor_kamar']:
        print_error("Penghuni belum ditempatkan di kamar. Gunakan menu Penempatan.")
        tekan_enter()
        return

    # Show available rooms
    available = db.get_available_rooms(ph['jenis_kelamin'])
    # Filter out current room
    available = [r for r in available if r['id'] != ph['kamar_id']]
    if not available:
        print_error("Tidak ada kamar lain yang tersedia.")
        tekan_enter()
        return

    print(f"\n  Kamar tersedia untuk dipindah:")
    headers = ["ID", "No. Kamar", "Lantai", "Tipe", "Terisi/Kapasitas"]
    data = [[r['id'], r['nomor_kamar'], r['lantai'], format_tipe_kamar(r['tipe']),
             f"{r['terisi']}/{r['kapasitas']}"] for r in available]
    print_table(headers, data, [4, 10, 6, 7, 16])

    kid = input_int("\n  ID Kamar tujuan", min_val=1)
    alasan = input_text("Alasan perpindahan")

    print(f"\n  Memindahkan {bold(ph['nama'])} dari kamar {bold(ph['nomor_kamar'])} ke kamar baru")
    if not konfirmasi("Lanjutkan perpindahan?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.pindah_kamar(pid, kid, alasan)
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


def lihat_riwayat_perpindahan():
    print_header("RIWAYAT PERPINDAHAN", ["Menu Utama", "Perpindahan", "Riwayat"])

    print(f"  1. Semua riwayat")
    print(f"  2. Per penghuni")
    pil = input_menu(2)

    if pil == 0:
        return

    penghuni_id = None
    if pil == 2:
        rows = db.get_all_penghuni()
        headers = ["ID", "Nama", "NIM"]
        data = [[r['id'], r['nama'], r['nim']] for r in rows]
        print_table(headers, data, [4, 20, 10])
        penghuni_id = input_int("\n  Masukkan ID penghuni", min_val=1)

    riwayat = db.get_riwayat_perpindahan(penghuni_id)
    if not riwayat:
        print_info("Tidak ada riwayat perpindahan.")
    else:
        headers = ["ID", "Nama", "NIM", "Dari Kamar", "Ke Kamar", "Tanggal", "Alasan"]
        data = [[r['id'], r['nama'], r['nim'], r['kamar_asal'],
                 r['kamar_tujuan'], r['tanggal'], r['alasan'] or '-'] for r in riwayat]
        print_table(headers, data, [4, 16, 10, 10, 10, 12, 18])
    tekan_enter()


# ===================== MENU STATISTIK =====================

def menu_statistik():
    print_header("STATISTIK OKUPANSI", ["Menu Utama", "Statistik"])

    stats = db.get_statistik_okupansi()

    if stats['total_kamar'] == 0:
        print_info("Belum ada data kamar. Tambahkan kamar terlebih dahulu.")
        tekan_enter()
        return

    # Overall stats
    print_subheader("Ringkasan Umum")
    print(f"  Total Kamar       : {bold(str(stats['total_kamar']))}")
    print(f"  Total Kapasitas   : {bold(str(stats['total_kapasitas']))} tempat tidur")
    print(f"  Total Penghuni    : {bold(str(stats['total_penghuni']))}")
    print(f"  Kamar Terisi      : {bold(str(stats['kamar_terisi']))}")
    print(f"  Kamar Kosong      : {bold(str(stats['kamar_kosong']))}")
    rate = stats['okupansi_rate']
    if rate >= 90:
        rate_color = Warna.MERAH
    elif rate >= 60:
        rate_color = Warna.KUNING
    else:
        rate_color = Warna.HIJAU
    print(f"  Tingkat Okupansi  : {warna(f'{rate:.1f}%', rate_color)}")
    print(f"  Okupansi Total    : {format_okupansi_bar(stats['total_penghuni'], stats['total_kapasitas'], 30)}")

    # Per-floor stats
    print()
    print_subheader("Statistik per Lantai")
    headers = ["Lantai", "Jml Kamar", "Kapasitas", "Terisi", "Okupansi"]
    data = []
    for f in stats['per_lantai']:
        kap = f['total_kapasitas']
        ter = f['terisi']
        bar = format_okupansi_bar(ter, kap, 15)
        data.append([f"Lantai {f['lantai']}", f['jumlah_kamar'], kap, ter, bar])
    print_table(headers, data, [10, 10, 10, 7, 25])

    # Per-type stats
    print()
    print_subheader("Statistik per Tipe")
    headers = ["Tipe", "Jml Kamar", "Kapasitas", "Terisi", "Okupansi"]
    data = []
    for t in stats['per_tipe']:
        kap = t['total_kapasitas']
        ter = t['terisi']
        bar = format_okupansi_bar(ter, kap, 15)
        data.append([format_tipe_kamar(t['tipe']), t['jumlah_kamar'], kap, ter, bar])
    print_table(headers, data, [10, 10, 10, 7, 25])

    # Kamar terbanyak/tersedikit
    print()
    print_subheader("Kamar Istimewa")
    if stats['kamar_terbanyak']:
        kt = stats['kamar_terbanyak']
        print(f"  Kamar Paling Banyak Penghuni : {bold(kt['nomor_kamar'])} ({kt['terisi']}/{kt['kapasitas']})")
    if stats['kamar_tersedikit']:
        ks = stats['kamar_tersedikit']
        print(f"  Kamar Paling Sedikit Penghuni: {bold(ks['nomor_kamar'])} ({ks['terisi']}/{ks['kapasitas']})")

    # ASCII bar chart per room
    print()
    print_subheader("Grafik Okupansi per Kamar")
    per_kamar = db.get_okupansi_per_kamar()
    if per_kamar:
        max_label = max(len(r['nomor_kamar']) for r in per_kamar)
        for r in per_kamar:
            label = r['nomor_kamar'].ljust(max_label)
            bar = format_okupansi_bar(r['terisi'], r['kapasitas'], 20)
            print(f"  {label} {bar} ({r['terisi']}/{r['kapasitas']})")
    print()
    tekan_enter()


# ===================== MENU SEED =====================

def menu_seed():
    print_header("DATA CONTOH (SEED)", ["Menu Utama", "Seed"])
    print(f"  {peringatan('Fitur ini akan memuat data contoh ke penyimpanan JSON.')}")
    print(f"  {peringatan('Hanya bisa dilakukan jika data masih kosong.')}")
    print()

    if not konfirmasi("Muat data contoh ke sistem?"):
        print_warning("Dibatalkan.")
        tekan_enter()
        return

    ok, msg = db.seed_data()
    if ok:
        print_success(msg)
    else:
        print_error(msg)
    tekan_enter()


# ===================== ENTRY POINT =====================

def main():
    try:
        db.init_db()
        menu_utama()
    except KeyboardInterrupt:
        clear_screen()
        print(f"\n  {peringatan('Program dihentikan oleh pengguna.')}")
        print(f"  {Warna.DIM}Sampai jumpa! 👋{Warna.RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n  {error(f'Terjadi kesalahan: {e}')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
