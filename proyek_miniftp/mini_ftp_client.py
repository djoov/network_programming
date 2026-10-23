"""
mini_ftp_client.py - Client Mini-FTP interaktif (SATU koneksi TCP)

Perintah di prompt:
  help                   daftar perintah dari server
  ls                     daftar file di server (perintah LIST)
  get <file>             unduh file ke folder 'unduhan'
  put <file>             unggah file lokal ke server
  quit                   keluar

Pengujian pembatalan: 'get <file> --batal <KB>' mensimulasikan Ctrl+C setelah
<KB> kilobyte diterima. Ctrl+C sungguhan juga ditangani dengan cara yang sama.

Jalankan:  python mini_ftp_client.py [--host 127.0.0.1] [--port 2121]
"""

import argparse
import os
import socket
import sys

MAX_LINE = 1024
BUFFER = 64 * 1024


class MiniFTPClient:
    def __init__(self, host, port, folder_unduh):
        self.host = host
        self.port = port
        self.folder_unduh = folder_unduh
        self.sock = None
        self.rfile = None

    # ---------- koneksi ----------

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        self.sock.settimeout(60)
        # Satu pembaca berbuffer untuk SEMUA yang datang dari server:
        # baris header (readline) dan isi file (read) lewat objek yang sama.
        self.rfile = self.sock.makefile("rb")

    def tutup(self):
        for obj in (self.rfile, self.sock):
            try:
                obj.close()
            except (OSError, AttributeError):
                pass
        self.rfile = self.sock = None

    # ---------- bahasa protokol ----------

    def kirim_perintah(self, teks):
        self.sock.sendall((teks + "\n").encode("utf-8"))

    def baca_balasan(self):
        """Baca satu baris header. Hasil: (status, angka, pesan).
        OK  -> angka = panjang body yang menyusul.  ERR -> angka = kode error."""
        baris = self.rfile.readline(MAX_LINE + 1)
        if not baris:
            raise ConnectionError("server menutup koneksi")
        bagian = baris.decode("utf-8").rstrip("\n").split(" ", 2)
        if bagian[0] not in ("OK", "ERR") or len(bagian) < 2 or not bagian[1].isdigit():
            raise ConnectionError(f"balasan server tidak dikenali: {baris[:60]!r}")
        pesan = bagian[2] if len(bagian) > 2 else ""
        return bagian[0], int(bagian[1]), pesan

    def baca_tepat(self, n):
        """Baca TEPAT n byte dari aliran (menunggu sampai lengkap)."""
        data = self.rfile.read(n)
        if len(data) < n:
            raise ConnectionError(f"koneksi terputus ({len(data)} dari {n} byte)")
        return data

    # ---------- perintah ----------

    def perintah_teks(self, perintah):
        """HELP dan LIST: balasan berupa teks."""
        self.kirim_perintah(perintah)
        status, angka, pesan = self.baca_balasan()
        if status == "ERR":
            print(f"[ERR {angka}] {pesan}")
            return
        isi = self.baca_tepat(angka).decode("utf-8")
        if perintah == "LIST":
            print(f"{pesan}:")
            for baris in isi.splitlines():
                nama, ukuran = baris.split("\t")
                print(f"  {nama:<30} {int(ukuran):>12} byte")
        else:
            print(isi, end="")

    def unduh(self, nama, batal_kb=None):
        self.kirim_perintah(f"GET {nama}")
        status, angka, pesan = self.baca_balasan()
        if status == "ERR":
            print(f"[ERR {angka}] {pesan}")
            return
        os.makedirs(self.folder_unduh, exist_ok=True)
        tujuan = os.path.join(self.folder_unduh, os.path.basename(nama))
        sementara = tujuan + ".part"
        diterima = 0
        try:
            with open(sementara, "wb") as f:
                while diterima < angka:                       # baca sampai 'angka' byte
                    blok = self.rfile.read(min(BUFFER, angka - diterima))
                    if not blok:
                        raise ConnectionError(f"koneksi terputus ({diterima} dari {angka} byte)")
                    f.write(blok)
                    diterima += len(blok)
                    if batal_kb is not None and diterima >= batal_kb * 1024:
                        raise KeyboardInterrupt()             # simulasi Ctrl+C
            os.replace(sementara, tujuan)
        except KeyboardInterrupt:
            # Tidak ada "perintah batal": satu-satunya cara menghentikan transfer
            # adalah menutup koneksi, lalu membuat koneksi (sesi) baru.
            print(f"\n[BATAL] {nama}: {diterima} dari {angka} byte diterima. Koneksi ditutup.")
            self.tutup()
            self._hapus(sementara)
            self.connect()
            print("[INFO] Koneksi baru dibuat (sesi baru di server).")
            return
        except (OSError, ConnectionError):
            self._hapus(sementara)
            raise
        print(f"[OK] {nama}: {diterima} byte disimpan di {tujuan}")

    def unggah(self, path):
        if not os.path.isfile(path):
            print(f"[ERR] file lokal tidak ada: {path}")
            return
        nama = os.path.basename(path)
        ukuran = os.path.getsize(path)
        self.kirim_perintah(f"PUT {nama} {ukuran}")
        status, angka, pesan = self.baca_balasan()            # tunggu izin server
        if status == "ERR":
            print(f"[ERR {angka}] {pesan}")
            return
        with open(path, "rb") as f:                           # isi file lewat koneksi yang sama
            while True:
                blok = f.read(BUFFER)
                if not blok:
                    break
                self.sock.sendall(blok)
        status, angka, pesan = self.baca_balasan()            # konfirmasi akhir
        if status == "OK":
            print(f"[OK] {nama}: {ukuran} byte terkirim ({pesan})")
        else:
            print(f"[ERR {angka}] {pesan}")

    @staticmethod
    def _hapus(path):
        try:
            os.remove(path)
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description="Client Mini-FTP (satu koneksi TCP)")
    parser.add_argument("--host", default="127.0.0.1", help="alamat server (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2121, help="port server (default 2121)")
    parser.add_argument("--unduhan", default="unduhan", help="folder tujuan unduhan (default unduhan)")
    args = parser.parse_args()

    klien = MiniFTPClient(args.host, args.port, args.unduhan)
    try:
        klien.connect()
    except OSError as e:
        print(f"[!] Tidak bisa terhubung ke {args.host}:{args.port} -> {e}")
        return
    print(f"Terhubung ke {args.host}:{args.port}. Ketik 'help' untuk bantuan, 'quit' untuk keluar.")

    try:
        while True:
            try:
                masukan = input("miniftp> ").strip()
            except EOFError:
                break
            if not sys.stdin.isatty():           # masukan dari pipe/skrip: tampilkan perintahnya
                print(masukan)
            if not masukan:
                continue
            kata = masukan.split()
            perintah, argumen = kata[0].lower(), kata[1:]
            try:
                if perintah in ("quit", "exit"):
                    klien.kirim_perintah("QUIT")
                    status, angka, pesan = klien.baca_balasan()
                    print(f"[{status}] {pesan}")
                    break
                elif perintah == "help":
                    klien.perintah_teks("HELP")
                elif perintah in ("ls", "list"):
                    klien.perintah_teks("LIST")
                elif perintah == "get" and len(argumen) == 1:
                    klien.unduh(argumen[0])
                elif perintah == "get" and len(argumen) == 3 and argumen[1] == "--batal" and argumen[2].isdigit():
                    klien.unduh(argumen[0], int(argumen[2]))
                elif perintah == "put" and len(argumen) == 1:
                    klien.unggah(argumen[0])
                else:
                    print("Perintah tidak dikenal atau argumen salah. Ketik 'help'.")
            except (OSError, ConnectionError) as e:
                print(f"[!] Koneksi bermasalah: {e}")
                break
    finally:
        klien.tutup()


if __name__ == "__main__":
    main()
