"""
models.py - Definisi struktur data dan konstanta untuk Sistem Manajemen Asrama.
File ini berisi konstanta, enum-like values, dan helper untuk sistem berbasis JSON.
"""

# Jenis Kelamin
LAKI_LAKI = 'L'
PEREMPUAN = 'P'
JENIS_KELAMIN = {
    'L': 'Laki-laki',
    'P': 'Perempuan',
}

# Tipe Kamar
TIPE_KAMAR = ('putra', 'putri')

# Tingkat Severity Pelanggaran
SEVERITY_LEVELS = ('ringan', 'sedang', 'berat')
SEVERITY_LABELS = {
    'ringan': 'Ringan',
    'sedang': 'Sedang',
    'berat': 'Berat',
}

# Status Izin Keluar
STATUS_IZIN = ('pending', 'disetujui', 'ditolak')
STATUS_LABELS = {
    'pending': 'Pending',
    'disetujui': 'Disetujui',
    'ditolak': 'Ditolak',
}

# Gender to room type mapping
GENDER_TO_TIPE = {
    'L': 'putra',
    'P': 'putri',
}

TIPE_TO_GENDER = {
    'putra': 'L',
    'putri': 'P',
}
