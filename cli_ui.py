

import os
import pyfiglet
import questionary
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box

console = Console()


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def show_banner():
    clear_screen()
    ascii_title = pyfiglet.figlet_format("DORM MANAGER", font="small").rstrip("\n")
    banner_text = Text(ascii_title, style="bold cyan")
    subtitle = Text(
        "Sistem Manajemen Asrama Mahasiswa | File-Based (.txt) CLI Edition",
        style="bold white",
    )
    panel = Panel(
        Text.assemble(banner_text, "\n\n", subtitle),
        border_style="bright_blue",
        box=box.DOUBLE,
        padding=(0, 2),
    )
    console.print(panel)


def show_message(success, message):
    style = "bold green" if success else "bold red"
    title = "BERHASIL" if success else "PERINGATAN / GAGAL"
    console.print(Panel(message, title=title, border_style=style, box=box.ROUNDED))


def make_occupancy_bar(terisi, kapasitas, width=12):
    if kapasitas <= 0:
        return "[dim]N/A[/dim]"
    ratio = min(terisi / kapasitas, 1.0)
    filled = int(round(ratio * width))
    empty = width - filled
    color = "red" if ratio >= 1.0 else ("yellow" if ratio >= 0.75 else "green")
    bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim] {terisi}/{kapasitas}"
    return bar


def show_dashboard(rooms, residents, violations, permits):
    total_kapasitas = sum(r["kapasitas"] for r in rooms)
    total_terisi = sum(r["terisi"] for r in rooms)
    sisa_kuota = total_kapasitas - total_terisi

    putra_rooms = [r for r in rooms if r["gender"] == "L"]
    putri_rooms = [r for r in rooms if r["gender"] == "P"]

    putra_terisi = sum(r["terisi"] for r in putra_rooms)
    putra_kap = sum(r["kapasitas"] for r in putra_rooms)

    putri_terisi = sum(r["terisi"] for r in putri_rooms)
    putri_kap = sum(r["kapasitas"] for r in putri_rooms)

    izin_pending = sum(1 for p in permits if p["status"] == "Menunggu")

    card_1 = Panel(
        f"[bold cyan]{total_terisi} / {total_kapasitas}[/bold cyan] Mahasiswa\n"
        f"Sisa Kuota: [bold green]{sisa_kuota} Bed[/bold green]",
        title="Okupansi Total",
        border_style="cyan",
    )
    card_2 = Panel(
        f"Putra: {make_occupancy_bar(putra_terisi, putra_kap, 8)}\n"
        f"Putri: {make_occupancy_bar(putri_terisi, putri_kap, 8)}",
        title="Per Gedung",
        border_style="blue",
    )
    card_3 = Panel(
        f"Pelanggaran: [bold yellow]{len(violations)} Kasus[/bold yellow]\n"
        f"Izin Pending: [bold magenta]{izin_pending} Ajuan[/bold magenta]",
        title="Disiplin & Izin",
        border_style="yellow",
    )

    console.print(Columns([card_1, card_2, card_3], equal=True))


def render_rooms_table(rooms, title="Daftar Kamar Asrama"):
    table = Table(title=title, box=box.ROUNDED, header_style="bold white on blue", show_lines=True)
    table.add_column("Kode", style="bold cyan", justify="center")
    table.add_column("Gedung", style="white")
    table.add_column("Lantai", justify="center")
    table.add_column("Gender", justify="center")
    table.add_column("Okupansi Visual", justify="left")
    table.add_column("Status", justify="center")

    for r in rooms:
        gender_label = "[blue]Putra (L)[/blue]" if r["gender"] == "L" else "[magenta]Putri (P)[/magenta]"
        status_badge = "[bold red]PENUH[/bold red]" if r["status"] == "Penuh" else "[bold green]TERSEDIA[/bold green]"
        bar = make_occupancy_bar(r["terisi"], r["kapasitas"], width=12)
        table.add_row(r["kode"], r["gedung"], str(r["lantai"]), gender_label, bar, status_badge)

    console.print(table)


def render_residents_table(residents, title="Daftar Penghuni Asrama"):
    table = Table(title=title, box=box.ROUNDED, header_style="bold white on dark_green", show_lines=False)
    table.add_column("NIM", style="bold cyan")
    table.add_column("Nama Lengkap", style="bold white")
    table.add_column("Prodi", justify="center")
    table.add_column("L/P", justify="center")
    table.add_column("Kamar", style="yellow", justify="center")
    table.add_column("Tgl Masuk", justify="center")
    table.add_column("Poin", justify="right")

    for res in residents:
        poin = res["poin"]
        if poin >= 50:
            poin_str = f"[bold red]{poin} (SP)[/bold red]"
        elif poin > 0:
            poin_str = f"[yellow]{poin}[/yellow]"
        else:
            poin_str = "[green]0[/green]"

        table.add_row(
            res["nim"],
            res["nama"],
            res["prodi"],
            res["gender"],
            res["kamar"],
            res["tgl_masuk"],
            poin_str,
        )

    console.print(table)


def render_violations_table(violations, residents):
    name_map = {r["nim"]: r["nama"] for r in residents}
    table = Table(title="Log Pelanggaran Tata Tertib", box=box.ROUNDED, header_style="bold white on red")
    table.add_column("ID", style="bold cyan")
    table.add_column("Tanggal", justify="center")
    table.add_column("NIM")
    table.add_column("Nama Penghuni", style="bold white")
    table.add_column("Kode", justify="center")
    table.add_column("Keterangan Pelanggaran")
    table.add_column("Poin", justify="right", style="bold red")

    for v in violations:
        table.add_row(
            v["id"],
            v["tanggal"],
            v["nim"],
            name_map.get(v["nim"], "-"),
            v["kode_aturan"],
            v["deskripsi"],
            f"+{v['poin']}",
        )
    console.print(table)


def render_permits_table(permits, residents):
    name_map = {r["nim"]: r["nama"] for r in residents}
    table = Table(title="Daftar Izin Keluar / Pulang Malam", box=box.ROUNDED, header_style="bold white on purple")
    table.add_column("ID Izin", style="bold cyan")
    table.add_column("NIM")
    table.add_column("Nama Penghuni", style="bold white")
    table.add_column("Tujuan / Keperluan")
    table.add_column("Keluar", justify="center")
    table.add_column("Kembali", justify="center")
    table.add_column("Status", justify="center")

    for p in permits:
        st = p["status"]
        if st == "Disetujui":
            st_badge = "[bold green]Disetujui[/bold green]"
        elif st == "Ditolak":
            st_badge = "[bold red]Ditolak[/bold red]"
        else:
            st_badge = "[bold yellow]Menunggu[/bold yellow]"

        table.add_row(
            p["id"],
            p["nim"],
            name_map.get(p["nim"], "-"),
            p["tujuan"],
            p["tgl_keluar"],
            p["tgl_kembali"],
            st_badge,
        )
    console.print(table)


def render_transfers_table(transfers, residents):
    name_map = {r["nim"]: r["nama"] for r in residents}
    table = Table(title="Riwayat Mutasi Pindah Kamar", box=box.ROUNDED, header_style="bold white on dark_blue")
    table.add_column("ID Mutasi", style="bold cyan")
    table.add_column("Tanggal", justify="center")
    table.add_column("NIM")
    table.add_column("Nama Penghuni")
    table.add_column("Asal", justify="center", style="yellow")
    table.add_column("Tujuan", justify="center", style="green")
    table.add_column("Alasan Mutasi")

    for t in transfers:
        table.add_row(
            t["id"],
            t["tanggal"],
            t["nim"],
            name_map.get(t["nim"], "-"),
            t["kamar_asal"],
            t["kamar_tujuan"],
            t["alasan"],
        )
    console.print(table)


def render_rules_table(aturan_tuple):
    table = Table(title="Standar Aturan & Bobot Poin Pelanggaran", box=box.SIMPLE_HEAVY)
    table.add_column("Kode", style="bold cyan", justify="center")
    table.add_column("Deskripsi Pelanggaran", style="white")
    table.add_column("Bobot Poin", style="bold red", justify="right")
    for kode, desc, poin in aturan_tuple:
        table.add_row(kode, desc, f"+{poin}")
    console.print(table)


def pause():
    console.print()
    questionary.press_any_key_to_continue("Tekan tombol apa saja untuk kembali ke menu...").ask()

def render_dorm_matrix(rooms, title="DENAH KAMAR ASRAMA"):
    if not rooms:
        show_message(False, "Belum ada data kamar untuk ditampilkan.")
        return

    console.print(Panel(Text(title, justify="center", style="bold cyan"), box=box.DOUBLE, border_style="bright_blue"))

    sorted_rooms = sorted(rooms, key=lambda r: (r["gedung"], r["lantai"], r["kode"]))
    grouped = {}
    for r in sorted_rooms:
        grouped.setdefault(r["gedung"], {}).setdefault(r["lantai"], []).append(r)

    for gedung, lantai_dict in grouped.items():
        floor_blocks = []

        for lantai, room_list in lantai_dict.items():
            cards = []
            for r in room_list:
                terisi = r["terisi"]
                kap = r["kapasitas"]
                sisa = max(0, kap - terisi)
                if terisi >= kap:
                    border_col = "red"
                    status_tag = "[bold white on red] PENUH [/bold white on red]"
                    bed_col = "red"
                elif terisi == 0:
                    border_col = "cyan"
                    status_tag = "[bold black on cyan] KOSONG [/bold black on cyan]"
                    bed_col = "cyan"
                else:
                    border_col = "green"
                    status_tag = "[bold white on green] TERSEDIA [/bold white on green]"
                    bed_col = "green"

                sep = " " if kap <= 4 else ""
                slots = f"[{bed_col}]{sep.join(['■'] * terisi)}[/{bed_col}]"
                if sisa > 0:
                    prefix_sep = sep if terisi > 0 else ""
                    slots += f"[dim]{prefix_sep}{sep.join(['□'] * sisa)}[/dim]"

                card_content = (
                    f"[bold white]{r['kode']}[/bold white]\n"
                    f"{slots}\n"
                    f"[dim]{terisi}/{kap} Bed[/dim]\n"
                    f"{status_tag}"
                )

                cards.append(
                    Panel(
                        Text.from_markup(card_content, justify="center"),
                        border_style=border_col,
                        box=box.ROUNDED,
                        width=20,
                        padding=(0, 1),
                    )
                )

            floor_blocks.append(f"[bold yellow]📂 Lantai {lantai}[/bold yellow]")
            floor_blocks.append(Columns(cards, equal=True, expand=False))

        # Bungkus satu gedung utuh dalam satu Panel besar
        from rich.console import Group
        console.print(
            Panel(
                Group(*floor_blocks),
                title=f"[bold white]🏛️  {gedung.upper()}[/bold white]",
                border_style="blue",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    # Legenda keterangan warna di bagian bawah
    console.print(
        "  [bold]Legenda:[/bold] [green]■[/green] Terisi  [dim]□[/dim] Kosong   │   "
        "[cyan]■[/cyan] Kosong   [green]■[/green] Tersedia   [red]■[/red] Penuh\n"
    )