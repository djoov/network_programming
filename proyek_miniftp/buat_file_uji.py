"""
buat_file_uji.py - Membuat file besar untuk uji pembatalan transfer.

Pembatalan hanya terlihat jelas pada file yang besar, karena file kecil
selesai terkirim sebelum sempat dibatalkan.

Jalankan:  python buat_file_uji.py [ukuran_mb]      (default 50 MB)
Hasil   :  server_files/besar_<n>mb.bin
"""

import os
import sys

mb = int(sys.argv[1]) if len(sys.argv) > 1 else 50
os.makedirs("server_files", exist_ok=True)
path = os.path.join("server_files", f"besar_{mb}mb.bin")
blok = os.urandom(1024 * 1024)
with open(path, "wb") as f:
    for _ in range(mb):
        f.write(blok)
print(f"Dibuat: {path} ({mb} MB)")
