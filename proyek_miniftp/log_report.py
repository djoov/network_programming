"""
log_report.py - Laporan dari file log Mini-FTP

Membaca logs/mini_ftp.log (dan file rotasinya .1 .2 .3) lalu menampilkan:
  1. jumlah sesi FTP
  2. 5 file yang paling sering diunduh
  3. total byte yang ditransfer
  4. daftar error (dan operasi yang ditolak)

Cara menghitung (ringkas, penjelasan lengkap ada di laporan):
  - sesi        : jumlah baris SESSION_START
  - unduhan     : baris TRANSFER_OK dengan op=GET, dikelompokkan per nama file
  - total byte  : jumlah bytes= pada semua baris TRANSFER_OK (GET + PUT)
  - error       : baris berlevel ERROR (WARNING dipisah sebagai operasi ditolak)

Jalankan:  python log_report.py [file_log] [-o laporan.txt]
"""

import argparse
import glob
import os
import re
import sys
from collections import Counter

# 2026-10-23 14:20:01,123 | INFO    | KEJADIAN kunci=nilai kunci="nilai berspasi"
BARIS = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3} \| (\w+)\s*\| (\w+)\s?(.*)$")
PASANGAN = re.compile(r'(\w+)=("[^"]*"|\S+)')


def cari_file(dasar):
    """Kembalikan [dasar.3, dasar.2, dasar.1, dasar] yang ada, urut dari yang TERTUA."""
    lama = []
    for p in glob.glob(glob.escape(dasar) + ".*"):
        akhiran = p.rsplit(".", 1)[1]
        if akhiran.isdigit():
            lama.append((int(akhiran), p))
    hasil = [p for _, p in sorted(lama, reverse=True)]
    if os.path.exists(dasar):
        hasil.append(dasar)
    return hasil


def baca_log(daftar_file):
    """Ubah tiap baris log yang valid menjadi dict. Baris yang tidak cocok diabaikan."""
    catatan = []
    for path in daftar_file:
        with open(path, encoding="utf-8", errors="replace") as f:
            for baris in f:
                m = BARIS.match(baris.rstrip("\n"))
                if not m:
                    continue
                waktu, level, kejadian, sisa = m.groups()
                kv = {k: v.strip('"') for k, v in PASANGAN.findall(sisa)}
                catatan.append({"waktu": waktu, "level": level, "kejadian": kejadian,
                                "kv": kv, "sisa": sisa})
    return catatan


def hitung(catatan):
    h = {
        "sesi_mulai": 0, "sesi_selesai": 0, "status_sesi": Counter(),
        "perintah": Counter(), "unduhan": Counter(), "byte_unduhan_per_file": Counter(),
        "byte_unduh": 0, "byte_unggah": 0, "jumlah_unduh": 0, "jumlah_unggah": 0,
        "byte_parsial": 0, "transfer_gagal": 0, "error": [], "ditolak": [],
        "pertama": None, "terakhir": None,
    }
    for c in catatan:
        h["pertama"] = h["pertama"] or c["waktu"]
        h["terakhir"] = c["waktu"]
        kv, e = c["kv"], c["kejadian"]

        if e == "SESSION_START":
            h["sesi_mulai"] += 1
        elif e == "SESSION_END":
            h["sesi_selesai"] += 1
            h["status_sesi"][kv.get("status", "?")] += 1
        elif e == "CMD":
            h["perintah"][kv.get("cmd", "?")] += 1
        elif e == "TRANSFER_OK":
            n = int(kv.get("bytes", 0))
            if kv.get("op") == "GET":
                h["unduhan"][kv.get("file", "?")] += 1
                h["byte_unduhan_per_file"][kv.get("file", "?")] += n
                h["byte_unduh"] += n
                h["jumlah_unduh"] += 1
            elif kv.get("op") == "PUT":
                h["byte_unggah"] += n
                h["jumlah_unggah"] += 1
        elif e == "TRANSFER_FAIL":
            h["transfer_gagal"] += 1
            h["byte_parsial"] += int(kv.get("bytes", 0))

        if c["level"] == "ERROR":
            h["error"].append(c)
        elif c["level"] == "WARNING":
            h["ditolak"].append(c)
    return h


def fmt_byte(n):
    for satuan in ("byte", "KB", "MB", "GB"):
        if n < 1024 or satuan == "GB":
            return f"{n} byte" if satuan == "byte" else f"{n:.2f} {satuan}"
        n /= 1024


def susun_laporan(h, daftar_file):
    out = []
    t = out.append
    t("=" * 66)
    t("LAPORAN LOG MINI-FTP")
    t("=" * 66)
    t("File dibaca : " + ", ".join(os.path.basename(p) for p in daftar_file))
    t(f"Rentang waktu: {h['pertama']}  s.d.  {h['terakhir']}")
    t("")

    t("1. JUMLAH SESI FTP")
    t(f"   Sesi tercatat (SESSION_START) : {h['sesi_mulai']}")
    t(f"   Sesi selesai  (SESSION_END)   : {h['sesi_selesai']}")
    belum = max(h["sesi_mulai"] - h["sesi_selesai"], 0)
    t(f"   Belum tercatat selesai        : {belum}")
    for status, n in sorted(h["status_sesi"].items()):
        t(f"     status {status:<10}: {n}")
    t("   Perintah diterima: " + (", ".join(f"{k}={v}" for k, v in sorted(h["perintah"].items())) or "-"))
    t("")

    t("2. LIMA FILE PALING SERING DIUNDUH (hanya unduhan yang berhasil)")
    if h["unduhan"]:
        t(f"   {'No':<3} {'File':<28} {'Diunduh':>8} {'Total byte':>14}")
        for i, (nama, n) in enumerate(h["unduhan"].most_common(5), 1):
            t(f"   {i:<3} {nama:<28} {n:>7}x {h['byte_unduhan_per_file'][nama]:>14}")
    else:
        t("   (belum ada unduhan berhasil)")
    t("")

    total = h["byte_unduh"] + h["byte_unggah"]
    t("3. TOTAL BYTE YANG DITRANSFER (transfer yang selesai)")
    t(f"   Unduh (GET) : {h['byte_unduh']:>12} byte  dari {h['jumlah_unduh']} transfer")
    t(f"   Unggah (PUT): {h['byte_unggah']:>12} byte  dari {h['jumlah_unggah']} transfer")
    t(f"   TOTAL       : {total:>12} byte  ({fmt_byte(total)})")
    t(f"   Byte parsial dari {h['transfer_gagal']} transfer gagal (tidak dihitung di atas): {h['byte_parsial']} byte")
    t("")

    t(f"4. DAFTAR ERROR (level ERROR): {len(h['error'])}")
    if h["error"]:
        for c in h["error"]:
            t(f"   {c['waktu']}  {c['kejadian']}  {c['sisa']}")
    else:
        t("   (tidak ada)")
    t("")
    t(f"   Operasi ditolak/gagal (level WARNING): {len(h['ditolak'])}")
    for c in h["ditolak"]:
        t(f"   {c['waktu']}  {c['kejadian']}  {c['sisa']}")
    t("=" * 66)
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Laporan dari log Mini-FTP")
    parser.add_argument("log", nargs="?", default=os.path.join("logs", "mini_ftp.log"),
                        help="file log utama (default logs/mini_ftp.log); file rotasi .1 .2 .3 ikut dibaca")
    parser.add_argument("-o", "--output", help="simpan laporan ke file ini juga")
    args = parser.parse_args()

    daftar = cari_file(args.log)
    if not daftar:
        print(f"File log tidak ditemukan: {args.log}", file=sys.stderr)
        return 1
    laporan = susun_laporan(hitung(baca_log(daftar)), daftar)
    print(laporan)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(laporan + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
