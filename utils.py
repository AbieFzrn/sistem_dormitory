"""
utils.py - Fungsi utilitas: validasi, format tabel, warna ANSI, dsb.
"""

import os
import sys
from datetime import datetime


# ===================== ANSI Color Codes =====================

class Warna:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    HITAM = "\033[30m"
    MERAH = "\033[31m"
    HIJAU = "\033[32m"
    KUNING = "\033[33m"
    BIRU = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    PUTIH = "\033[37m"

    BG_MERAH = "\033[41m"
    BG_HIJAU = "\033[42m"
    BG_KUNING = "\033[43m"
    BG_BIRU = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"


def warna(text, color):
    return f"{color}{text}{Warna.RESET}"


def bold(text):
    return warna(text, Warna.BOLD)


def sukses(text):
    return warna(text, Warna.HIJAU)


def error(text):
    return warna(text, Warna.MERAH)


def peringatan(text):
    return warna(text, Warna.KUNING)


def info(text):
    return warna(text, Warna.CYAN)


def header_text(text):
    return warna(text, Warna.BOLD + Warna.CYAN)


# ===================== Screen Management =====================

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')


def tekan_enter():
    input(f"\n{Warna.DIM}Tekan Enter untuk melanjutkan...{Warna.RESET}")


def print_header(title, breadcrumb=None):
    """Print header with optional breadcrumb navigation."""
    clear_screen()
    width = 60
    print(warna("=" * width, Warna.CYAN))
    centered = title.center(width)
    print(warna(centered, Warna.BOLD + Warna.CYAN))
    print(warna("=" * width, Warna.CYAN))
    if breadcrumb:
        bc_text = " > ".join(breadcrumb)
        print(warna(f"  📍 {bc_text}", Warna.DIM))
    print()


def print_subheader(title):
    width = 50
    print(warna("-" * width, Warna.BIRU))
    print(warna(f"  {title}", Warna.BOLD + Warna.BIRU))
    print(warna("-" * width, Warna.BIRU))


def print_success(msg):
    print(f"\n  {sukses('✓')} {sukses(msg)}")


def print_error(msg):
    print(f"\n  {error('✗')} {error(msg)}")


def print_warning(msg):
    print(f"\n  {peringatan('⚠')} {peringatan(msg)}")


def print_info(msg):
    print(f"\n  {info('ℹ')} {info(msg)}")


# ===================== Table Formatting =====================

def print_table(headers, rows, col_widths=None):
    """Print a formatted table with borders."""
    if not col_widths:
        col_widths = []
        for i, h in enumerate(headers):
            max_w = len(str(h))
            for row in rows:
                if i < len(row):
                    max_w = max(max_w, len(str(row[i])))
            col_widths.append(min(max_w + 2, 40))

    # Build separator
    sep_parts = ["+" + "-" * (w + 2) for w in col_widths]
    separator = "".join(sep_parts) + "+"

    # Build header
    header_parts = ["|" + warna(str(h).center(w + 2), Warna.BOLD + Warna.CYAN) for h, w in zip(headers, col_widths)]
    header_line = "".join(header_parts) + "|"

    print(f"  {separator}")
    print(f"  {header_line}")
    print(f"  {separator}")

    if not rows:
        empty_msg = "Tidak ada data"
        total_w = sum(w + 3 for w in col_widths) - 1
        print(f"  |{warna(empty_msg.center(total_w), Warna.DIM)}|")
    else:
        for row in rows:
            row_parts = []
            for i, w in enumerate(col_widths):
                val = str(row[i]) if i < len(row) else ""
                if len(val) > w:
                    val = val[:w-2] + ".."
                # Right-align numbers
                if val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
                    cell = val.rjust(w)
                else:
                    cell = val.ljust(w)
                row_parts.append(f"| {cell} ")
            print(f"  {''.join(row_parts)}|")

    print(f"  {separator}")
    print(f"  {Warna.DIM}Total: {len(rows)} baris{Warna.RESET}")


# ===================== Input Validation =====================

def input_text(prompt, required=True, max_len=100):
    """Get text input with validation."""
    while True:
        val = input(f"  {prompt}: ").strip()
        if not val and required:
            print_error("Input tidak boleh kosong.")
            continue
        if not val and not required:
            return ""
        if len(val) > max_len:
            print_error(f"Input terlalu panjang (maks {max_len} karakter).")
            continue
        return val


def input_int(prompt, min_val=None, max_val=None):
    """Get integer input with validation."""
    while True:
        val = input(f"  {prompt}: ").strip()
        if not val:
            print_error("Input tidak boleh kosong.")
            continue
        try:
            num = int(val)
            if min_val is not None and num < min_val:
                print_error(f"Nilai minimum adalah {min_val}.")
                continue
            if max_val is not None and num > max_val:
                print_error(f"Nilai maksimum adalah {max_val}.")
                continue
            return num
        except ValueError:
            print_error("Masukkan angka yang valid.")


def input_pilihan(prompt, options):
    """Get choice input from list of valid options."""
    opts_str = "/".join(options)
    while True:
        val = input(f"  {prompt} ({opts_str}): ").strip().lower()
        if val in [o.lower() for o in options]:
            return val
        print_error(f"Pilihan tidak valid. Gunakan: {opts_str}")


def input_tanggal(prompt):
    """Get date input (YYYY-MM-DD format)."""
    while True:
        val = input(f"  {prompt} (YYYY-MM-DD): ").strip()
        if not val:
            print_error("Tanggal tidak boleh kosong.")
            continue
        try:
            datetime.strptime(val, "%Y-%m-%d")
            return val
        except ValueError:
            print_error("Format tanggal tidak valid. Gunakan format YYYY-MM-DD.")


def input_no_telp(prompt):
    """Get phone number input with validation."""
    while True:
        val = input(f"  {prompt}: ").strip()
        if not val:
            print_error("Nomor telepon tidak boleh kosong.")
            continue
        # Remove common separators
        clean = val.replace("-", "").replace(" ", "").replace("+", "")
        if not clean.isdigit():
            print_error("Nomor telepon hanya boleh berisi angka (dan opsional +, -, spasi).")
            continue
        if len(clean) < 10 or len(clean) > 15:
            print_error("Nomor telepon harus antara 10-15 digit.")
            continue
        return val


def input_menu(max_option):
    """Get menu choice."""
    while True:
        val = input(f"\n  {Warna.BOLD}Pilih menu [0-{max_option}]: {Warna.RESET}").strip()
        if not val:
            continue
        try:
            num = int(val)
            if 0 <= num <= max_option:
                return num
            print_error(f"Pilihan harus antara 0-{max_option}.")
        except ValueError:
            print_error("Masukkan angka yang valid.")


def konfirmasi(prompt):
    """Yes/no confirmation prompt."""
    while True:
        val = input(f"  {peringatan(prompt)} (y/n): ").strip().lower()
        if val in ('y', 'ya', 'yes'):
            return True
        if val in ('n', 'no', 'tidak'):
            return False
        print_error("Masukkan 'y' untuk ya atau 'n' untuk tidak.")


# ===================== Formatting Helpers =====================

def format_gender(code):
    if code == 'L':
        return 'Laki-laki'
    elif code == 'P':
        return 'Perempuan'
    return code


def format_tipe_kamar(tipe):
    return tipe.capitalize() if tipe else '-'


def format_severity(severity):
    colors = {
        'ringan': Warna.HIJAU,
        'sedang': Warna.KUNING,
        'berat': Warna.MERAH,
    }
    color = colors.get(severity, Warna.RESET)
    return f"{color}{severity.capitalize()}{Warna.RESET}"


def format_status_izin(status):
    colors = {
        'pending': Warna.KUNING,
        'disetujui': Warna.HIJAU,
        'ditolak': Warna.MERAH,
    }
    color = colors.get(status, Warna.RESET)
    return f"{color}{status.capitalize()}{Warna.RESET}"


def format_okupansi_bar(terisi, kapasitas, bar_width=20):
    """Create ASCII bar chart for occupancy."""
    if kapasitas == 0:
        return "[" + " " * bar_width + "] 0%"
    ratio = terisi / kapasitas
    filled = int(ratio * bar_width)
    empty = bar_width - filled

    if ratio >= 0.9:
        color = Warna.MERAH
    elif ratio >= 0.6:
        color = Warna.KUNING
    else:
        color = Warna.HIJAU

    bar = f"{color}{'█' * filled}{Warna.RESET}{'░' * empty}"
    pct = f"{ratio * 100:.0f}%"
    return f"[{bar}] {pct}"


def print_detail_box(title, items):
    """Print a detail box with key-value pairs."""
    max_key = max(len(k) for k, v in items) if items else 10
    width = max(max_key + 30, 50)
    print(f"\n  {'┌' + '─' * (width - 2) + '┐'}")
    print(f"  │{warna(title.center(width - 2), Warna.BOLD + Warna.CYAN)}│")
    print(f"  {'├' + '─' * (width - 2) + '┤'}")
    for key, val in items:
        line = f"  {key.ljust(max_key)} : {val}"
        padding = width - 2 - len(key) - 3 - len(str(val))
        # Can't accurately measure ANSI-colored text, so use simple approach
        print(f"  │ {key.ljust(max_key)} : {val}")
    print(f"  {'└' + '─' * (width - 2) + '┘'}")
