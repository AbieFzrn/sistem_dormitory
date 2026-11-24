
import questionary
from rich.console import Console

import storage_handler as storage
import dorm_engine as engine
import algo_utils as algo
import cli_ui as ui

console = Console()


def menu_kamar():
    while True:
        ui.show_banner()
        rooms = storage.load_rooms()
        ui.render_rooms_table(rooms)

        choice = questionary.select(
            "Menu Manajemen Kamar:",
            choices=[
                "1. Tambah Kamar Baru (Auto-Parse Kode Kamar)",
                "2. Ubah Kapasitas Kamar",
                "3. Hapus Kamar",
                "4. Urutkan Kamar Berdasarkan Sisa Kuota Terbanyak (Merge Sort)",
                "0. Kembali ke Menu Utama",
            ],
        ).ask()

        if not choice or choice.startswith("0."):
            break

        elif choice.startswith("1."):
            kode = questionary.text("Masukkan Kode Kamar (contoh: A-202 atau B-102):").ask()
            if not kode:
                continue
            kap_str = questionary.text("Masukkan Kapasitas Bed (1-8):", default="4").ask()
            if not kap_str or not kap_str.isdigit():
                ui.show_message(False, "Kapasitas harus berupa angka.")
            else:
                ok, msg = engine.create_room(kode, int(kap_str))
                ui.show_message(ok, msg)
            ui.pause()

        elif choice.startswith("2."):
            kode = questionary.text("Masukkan Kode Kamar yang akan diubah:").ask()
            kap_str = questionary.text("Masukkan Kapasitas Baru (1-8):").ask()
            if kode and kap_str and kap_str.isdigit():
                ok, msg = engine.update_room_capacity(kode, int(kap_str))
                ui.show_message(ok, msg)
            else:
                ui.show_message(False, "Input tidak valid.")
            ui.pause()

        elif choice.startswith("3."):
            kode = questionary.text("Masukkan Kode Kamar yang akan dihapus:").ask()
            if kode:
                confirm = questionary.confirm(f"Yakin ingin menghapus kamar {kode.upper()}?").ask()
                if confirm:
                    ok, msg = engine.delete_room(kode)
                    ui.show_message(ok, msg)
                    ui.pause()

        elif choice.startswith("4."):
            sorted_rooms = algo.merge_sort_records(
                rooms,
                key_func=lambda r: r["kapasitas"] - r["terisi"],
                reverse=True,
            )
            ui.render_rooms_table(sorted_rooms, title="Kamar Diurutkan Berdasarkan Sisa Kuota Terbanyak (Merge Sort)")
            ui.pause()


def menu_penghuni():
    while True:
        ui.show_banner()
        residents = storage.load_residents()
        ui.render_residents_table(residents)

        choice = questionary.select(
            "Menu Manajemen Penghuni:",
            choices=[
                "1. Registrasi Penghuni Baru (Auto-Assign / Pilih Kamar)",
                "2. Update Biodata Penghuni",
                "3. Mutasi / Pindah Kamar Penghuni",
                "4. Checkout / Hapus Penghuni",
                "5. Lihat Riwayat Mutasi Kamar",
                "0. Kembali ke Menu Utama",
            ],
        ).ask()

        if not choice or choice.startswith("0."):
            break

        elif choice.startswith("1."):
            raw_nim = questionary.text("Masukkan NIM Mahasiswa:").ask()
            if not raw_nim:
                continue
            valid_nim, nim_or_err = algo.validate_nim(raw_nim)
            if not valid_nim:
                ui.show_message(False, nim_or_err)
                ui.pause()
                continue

            nama = questionary.text("Masukkan Nama Lengkap:").ask()
            prodi = questionary.text("Masukkan Program Studi (contoh: TRPL):").ask()
            gender = questionary.select("Pilih Gender:", choices=["L", "P"]).ask()
            mode_kamar = questionary.select(
                "Metode Penempatan Kamar:",
                choices=[
                    "AUTO (Pilihkan otomatis kamar terbaik)",
                    "MANUAL (Input kode kamar sendiri)",
                ],
            ).ask()

            preferred = "AUTO"
            if mode_kamar and mode_kamar.startswith("MANUAL"):
                preferred = questionary.text("Masukkan Kode Kamar Tujuan (contoh: A-101):").ask() or "AUTO"

            if nama and prodi:
                ok, msg = engine.create_resident(nim_or_err, nama, prodi, gender, preferred)
                ui.show_message(ok, msg)
            else:
                ui.show_message(False, "Nama dan Prodi wajib diisi.")
            ui.pause()

        elif choice.startswith("2."):
            nim = questionary.text("Masukkan NIM Penghuni yang akan diubah:").ask()
            if nim:
                new_nama = questionary.text("Nama Baru (kosongkan jika tidak diubah):").ask()
                new_prodi = questionary.text("Prodi Baru (kosongkan jika tidak diubah):").ask()
                ok, msg = engine.update_resident_profile(nim, new_nama, new_prodi)
                ui.show_message(ok, msg)
                ui.pause()

        elif choice.startswith("3."):
            nim = questionary.text("Masukkan NIM Penghuni yang akan pindah kamar:").ask()
            kamar_baru = questionary.text("Masukkan Kode Kamar Tujuan:").ask()
            alasan = questionary.text("Alasan Mutasi Kamar:").ask()
            if nim and kamar_baru and alasan:
                ok, msg = engine.transfer_resident_room(nim, kamar_baru, alasan)
                ui.show_message(ok, msg)
            else:
                ui.show_message(False, "Semua kolom mutasi wajib diisi.")
            ui.pause()

        elif choice.startswith("4."):
            nim = questionary.text("Masukkan NIM Penghuni yang akan checkout:").ask()
            if nim:
                confirm = questionary.confirm(f"Konfirmasi checkout penghuni {nim.upper()}?").ask()
                if confirm:
                    ok, msg = engine.delete_resident(nim)
                    ui.show_message(ok, msg)
                    ui.pause()

        elif choice.startswith("5."):
            transfers = storage.load_transfers()
            ui.render_transfers_table(transfers, residents)
            ui.pause()


def menu_searching_sorting():
    while True:
        ui.show_banner()
        residents = storage.load_residents()

        choice = questionary.select(
            "Menu Searching & Sorting (Algoritma Manual):",
            choices=[
                "1. Cari Penghuni via NIM (Manual Binary Search)",
                "2. Cari Penghuni via Potongan Nama (Substring Search)",
                "3. Urutkan Penghuni Berdasarkan Poin Pelanggaran Tertinggi (Merge Sort)",
                "4. Urutkan Penghuni Berdasarkan NIM Ascending (Merge Sort)",
                "0. Kembali ke Menu Utama",
            ],
        ).ask()

        if not choice or choice.startswith("0."):
            break

        elif choice.startswith("1."):
            target_nim = questionary.text("Masukkan NIM yang dicari:").ask()
            if target_nim:
                found, steps = algo.binary_search_by_nim(residents, target_nim)
                if found:
                    ui.show_message(True, f"Ditemukan dalam {steps} iterasi Binary Search!")
                    ui.render_residents_table([found], title="Hasil Binary Search NIM")
                else:
                    ui.show_message(False, f"NIM '{target_nim.upper()}' tidak ditemukan (dicek dalam {steps} iterasi).")
                ui.pause()

        elif choice.startswith("2."):
            keyword = questionary.text("Masukkan potongan nama penghuni:").ask()
            if keyword:
                matches = algo.linear_search_by_name(residents, keyword)
                if matches:
                    ui.show_message(True, f"Ditemukan {len(matches)} penghuni yang cocok dengan '{keyword}'.")
                    ui.render_residents_table(matches, title=f"Hasil Pencarian Nama: '{keyword}'")
                else:
                    ui.show_message(False, f"Tidak ada penghuni dengan nama mengandung '{keyword}'.")
                ui.pause()

        elif choice.startswith("3."):
            sorted_res = algo.merge_sort_records(residents, key_func=lambda r: r["poin"], reverse=True)
            ui.render_residents_table(sorted_res, title="Peringkat Poin Pelanggaran Tertinggi (Merge Sort)")
            ui.pause()

        elif choice.startswith("4."):
            sorted_res = algo.merge_sort_records(residents, key_func=lambda r: r["nim"], reverse=False)
            ui.render_residents_table(sorted_res, title="Daftar Penghuni Terurut NIM (Merge Sort)")
            ui.pause()


def menu_disiplin_izin():
    while True:
        ui.show_banner()
        residents = storage.load_residents()
        violations = storage.load_violations()
        permits = storage.load_permits()

        choice = questionary.select(
            "Menu Pelanggaran & Perizinan Keluar:",
            choices=[
                "1. Lihat Log Pelanggaran & Standar Aturan",
                "2. Catat Pelanggaran Baru (Auto-Generate SP .txt jika Poin >= 50)",
                "3. Lihat Daftar Pengajuan Izin Keluar",
                "4. Ajukan Izin Keluar / Pulang Malam Baru",
                "5. Proses Persetujuan Izin (Auto-Cetak Surat Izin .txt)",
                "0. Kembali ke Menu Utama",
            ],
        ).ask()

        if not choice or choice.startswith("0."):
            break

        elif choice.startswith("1."):
            ui.render_rules_table(engine.ATURAN_PELANGGARAN)
            ui.render_violations_table(violations, residents)
            ui.pause()

        elif choice.startswith("2."):
            ui.render_rules_table(engine.ATURAN_PELANGGARAN)
            nim = questionary.text("Masukkan NIM Penghuni yang melanggar:").ask()
            rule_choices = [f"{a[0]} | {a[1]} (+{a[2]} poin)" for a in engine.ATURAN_PELANGGARAN]
            selected_rule = questionary.select("Pilih Jenis Pelanggaran:", choices=rule_choices).ask()
            if nim and selected_rule:
                kode_aturan = selected_rule.split("|")[0].strip()
                ok, msg = engine.record_violation(nim, kode_aturan)
                ui.show_message(ok, msg)
                ui.pause()

        elif choice.startswith("3."):
            ui.render_permits_table(permits, residents)
            ui.pause()

        elif choice.startswith("4."):
            nim = questionary.text("Masukkan NIM Pemohon:").ask()
            tujuan = questionary.text("Keperluan / Tujuan Izin:").ask()
            tgl_keluar = questionary.text("Tanggal Keluar (YYYY-MM-DD):").ask()
            tgl_kembali = questionary.text("Tanggal Kembali (YYYY-MM-DD):").ask()

            if not (nim and tujuan and tgl_keluar and tgl_kembali):
                ui.show_message(False, "Semua kolom izin wajib diisi.")
                ui.pause()
                continue

            ok1, d1 = algo.validate_date_str(tgl_keluar)
            ok2, d2 = algo.validate_date_str(tgl_kembali)
            if not ok1 or not ok2:
                ui.show_message(False, d1 if not ok1 else d2)
                ui.pause()
                continue

            ok, msg = engine.create_permit(nim, tujuan, d1, d2)
            ui.show_message(ok, msg)
            ui.pause()

        elif choice.startswith("5."):
            ui.render_permits_table(permits, residents)
            pid = questionary.text("Masukkan ID Izin (contoh: IZN-002):").ask()
            status = questionary.select("Keputusan Pengelola:", choices=["Disetujui", "Ditolak"]).ask()
            if pid and status:
                ok, msg = engine.update_permit_status(pid, status)
                ui.show_message(ok, msg)
                ui.pause()


def main():
    storage.init_storage()

    while True:
        ui.show_banner()
        rooms = storage.load_rooms()
        residents = storage.load_residents()
        violations = storage.load_violations()
        permits = storage.load_permits()

        ui.show_dashboard(rooms, residents, violations, permits)

        choice = questionary.select(
            "Pilih Modul Utama:",
            choices=[
                "1. Manajemen Kamar Asrama (CRUD & Okupansi)",
                "2. Manajemen Penghuni & Mutasi Kamar (CRUD & Auto-Assign)",
                "3. Pencarian & Pengurutan Data (Binary Search & Merge Sort)",
                "4. Pelanggaran Disiplin & Surat Izin Keluar (.txt Export)",
                "0. Keluar Aplikasi",
            ],
        ).ask()

        if not choice or choice.startswith("0."):
            console.print("[bold cyan]Terima kasih! Seluruh data telah tersimpan di folder data/*.txt[/bold cyan]")
            break
        elif choice.startswith("1."):
            menu_kamar()
        elif choice.startswith("2."):
            menu_penghuni()
        elif choice.startswith("3."):
            menu_searching_sorting()
        elif choice.startswith("4."):
            menu_disiplin_izin()


if __name__ == "__main__":
    main()
