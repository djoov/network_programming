"""
mini_ftp_server.py - Server Mini-FTP (SATU koneksi TCP) dengan logging

Satu koneksi TCP membawa tiga hal sekaligus: perintah, respons, dan isi file.
Supaya ketiganya tidak tercampur, protokol memakai FRAMING BERBASIS PANJANG:

  Client -> Server : satu baris teks berakhir "\\n"
                       HELP | LIST | GET <file> | PUT <file> <ukuran> | QUIT
  Server -> Client : satu baris header berakhir "\\n", lalu body sepanjang N byte
                       OK <N> <pesan>\\n<N byte body>      (N boleh 0)
                       ERR <kode> <pesan>\\n               (tanpa body)

Pembaca selalu tahu kapan harus berhenti membaca karena header menyebut N.

Logging: ke konsol dan ke file (RotatingFileHandler, 1 MB, simpan 3 file lama).
Format pesan log memakai pola  KEJADIAN kunci=nilai ...  agar mudah dibaca
oleh log_report.py.

Jalankan:  python mini_ftp_server.py [--host 127.0.0.1] [--port 2121] [--root server_files]
"""

import argparse
import logging
import os
import socket
import threading
import time
from logging.handlers import RotatingFileHandler

BUFFER = 64 * 1024                 # ukuran potongan saat kirim/terima file
MAX_LINE = 1024                    # batas panjang satu baris perintah
MAX_UPLOAD = 100 * 1024 * 1024     # batas ukuran file yang boleh di-PUT
IDLE_TIMEOUT = 300                 # detik; client diam lebih lama dari ini diputus
LOG_MAX_BYTES = 1024 * 1024        # 1 MB per file log
LOG_BACKUPS = 3                    # simpan 3 file lama (.1 .2 .3)

log = logging.getLogger("miniftp")


class KoneksiPutus(Exception):
    """Transfer gagal di tengah jalan; aliran data sudah tidak sinkron, koneksi harus ditutup."""


def setup_logging(log_file):
    """Pasang dua handler: konsol dan file berotasi."""
    log.setLevel(logging.INFO)
    log.propagate = False
    if log.handlers:                         # jangan pasang dua kali
        return
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")

    konsol = logging.StreamHandler()
    konsol.setFormatter(fmt)
    log.addHandler(konsol)

    os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    berkas = RotatingFileHandler(log_file, maxBytes=LOG_MAX_BYTES,
                                 backupCount=LOG_BACKUPS, encoding="utf-8")
    berkas.setFormatter(fmt)
    log.addHandler(berkas)


def q(teks):
    """Bungkus teks bebas dengan tanda kutip supaya mudah di-parse log_report.py."""
    return '"' + str(teks).replace('"', "'") + '"'


class Session:
    """Melayani satu client selama koneksinya hidup (dijalankan di satu thread)."""

    def __init__(self, conn, addr, sid, root):
        self.conn = conn
        self.peer = f"{addr[0]}:{addr[1]}"
        self.sid = sid
        self.root = root
        # makefile() memberi pembaca berbuffer: readline() untuk perintah dan
        # read(n) untuk isi file keluar dari SATU aliran yang sama.
        self.rfile = conn.makefile("rb")
        self.cmd = "-"
        self.jumlah_perintah = 0
        self.status_akhir = "normal"
        self.perintah = {
            "HELP": self.cmd_help,
            "LIST": self.cmd_list,
            "GET": self.cmd_get,
            "PUT": self.cmd_put,
            "QUIT": self.cmd_quit,
        }

    # ---------- balasan ke client ----------

    def ok(self, panjang, pesan):
        """Kirim header sukses. Body (sebanyak 'panjang' byte) dikirim sesudahnya."""
        self.conn.sendall(f"OK {panjang} {pesan}\n".encode("utf-8"))
        return True

    def err(self, kode, pesan):
        """Kirim balasan gagal (tanpa body) dan catat sebagai WARNING."""
        log.warning("CMD_FAIL sid=%s cmd=%s kode=%s pesan=%s", self.sid, self.cmd, kode, q(pesan))
        self.conn.sendall(f"ERR {kode} {pesan}\n".encode("utf-8"))
        return True

    # ---------- siklus hidup sesi ----------

    def run(self):
        mulai = time.monotonic()
        log.info("SESSION_START sid=%s client=%s", self.sid, self.peer)
        try:
            self.conn.settimeout(IDLE_TIMEOUT)
            self.loop()
        except socket.timeout:
            self.status_akhir = "timeout"
            log.warning("SESSION_TIMEOUT sid=%s client=%s batas=%ss", self.sid, self.peer, IDLE_TIMEOUT)
        except KoneksiPutus:
            self.status_akhir = "terputus"       # penyebabnya sudah dicatat oleh TRANSFER_FAIL
        except OSError as e:
            self.status_akhir = "terputus"
            log.error("SESSION_ERROR sid=%s client=%s jenis=%s alasan=%s",
                      self.sid, self.peer, type(e).__name__, q(e))
        except Exception as e:                   # bug tak terduga: catat, jangan matikan server
            self.status_akhir = "error"
            log.error("SESSION_ERROR sid=%s client=%s jenis=%s alasan=%s",
                      self.sid, self.peer, type(e).__name__, q(e))
        finally:
            try:
                self.rfile.close()
                self.conn.close()
            except OSError:
                pass
            log.info("SESSION_END sid=%s client=%s durasi=%.2fs perintah=%d status=%s",
                     self.sid, self.peer, time.monotonic() - mulai,
                     self.jumlah_perintah, self.status_akhir)

    def loop(self):
        """Baca satu baris perintah, jalankan, ulangi sampai QUIT atau koneksi putus."""
        while True:
            baris = self.rfile.readline(MAX_LINE + 1)
            if not baris:                        # client menutup koneksi tanpa QUIT
                self.status_akhir = "terputus"
                return
            if len(baris) > MAX_LINE:
                self.cmd = "?"
                self.err(400, "baris perintah terlalu panjang")
                self.status_akhir = "error"
                return
            try:
                teks = baris.decode("utf-8").strip()
            except UnicodeDecodeError:
                self.cmd = "?"
                self.err(400, "perintah bukan teks UTF-8")
                continue
            if not teks:
                continue

            bagian = teks.split()
            self.cmd = bagian[0].upper()
            args = bagian[1:]
            self.jumlah_perintah += 1
            log.info("CMD sid=%s cmd=%s arg=%s", self.sid, self.cmd, q(" ".join(args)) if args else "-")

            handler = self.perintah.get(self.cmd)
            if handler is None:
                self.err(400, "perintah tidak dikenal, ketik HELP")
                continue
            if handler(args) is False:           # hanya QUIT yang mengembalikan False
                return

    # ---------- keamanan nama file ----------

    def path_aman(self, nama):
        """Hanya nama polos di dalam folder root. Tolak '..', '/', '\\', awalan '.', dan '.part'."""
        if (not nama or nama != os.path.basename(nama) or "\\" in nama
                or nama.startswith(".") or nama.endswith(".part")):
            return None
        return os.path.join(self.root, nama)

    # ---------- perintah ----------

    def cmd_help(self, args):
        isi = ("HELP                     daftar perintah\n"
               "LIST                     daftar file di server\n"
               "GET <file>               unduh file\n"
               "PUT <file> <ukuran>      unggah file\n"
               "QUIT                     keluar\n").encode("utf-8")
        self.ok(len(isi), "daftar perintah")
        self.conn.sendall(isi)
        return True

    def cmd_list(self, args):
        try:
            nama_file = sorted(n for n in os.listdir(self.root)
                               if os.path.isfile(os.path.join(self.root, n)) and not n.endswith(".part"))
            baris = [f"{n}\t{os.path.getsize(os.path.join(self.root, n))}" for n in nama_file]
        except OSError as e:
            log.error("LIST_ERROR sid=%s jenis=%s alasan=%s", self.sid, type(e).__name__, q(e))
            return self.err(500, "gagal membaca folder server")
        isi = ("\n".join(baris) + ("\n" if baris else "")).encode("utf-8")
        self.ok(len(isi), f"{len(baris)} file")
        self.conn.sendall(isi)
        return True

    def cmd_get(self, args):
        if len(args) != 1:
            return self.err(400, "pemakaian: GET <nama_file>")
        nama = args[0]
        path = self.path_aman(nama)
        if path is None:
            return self.err(403, "nama file tidak diizinkan")
        if not os.path.isfile(path):
            return self.err(404, "file tidak ditemukan")
        try:
            ukuran = os.path.getsize(path)
            f = open(path, "rb")
        except OSError as e:
            log.error("TRANSFER_FAIL sid=%s op=GET file=%s bytes=0 dari=0 alasan=%s", self.sid, nama, q(e))
            return self.err(500, "file tidak bisa dibuka")

        log.info("TRANSFER_START sid=%s op=GET file=%s bytes=%d", self.sid, nama, ukuran)
        mulai = time.monotonic()
        terkirim = 0
        try:
            with f:
                self.ok(ukuran, "mengirim file")          # header dulu
                while True:                               # lalu isi file, potong demi potong
                    blok = f.read(BUFFER)
                    if not blok:
                        break
                    self.conn.sendall(blok)
                    terkirim += len(blok)
            if terkirim != ukuran:                        # file berubah saat dikirim
                raise OSError(f"ukuran file berubah ({terkirim} dari {ukuran} byte)")
        except OSError as e:
            log.error("TRANSFER_FAIL sid=%s op=GET file=%s bytes=%d dari=%d alasan=%s",
                      self.sid, nama, terkirim, ukuran, q(f"{type(e).__name__}: {e}"))
            raise KoneksiPutus() from e                   # aliran tidak sinkron lagi: tutup
        log.info("TRANSFER_OK sid=%s op=GET file=%s bytes=%d detik=%.3f",
                 self.sid, nama, terkirim, time.monotonic() - mulai)
        return True

    def cmd_put(self, args):
        if len(args) != 2 or not args[1].isdigit():
            return self.err(400, "pemakaian: PUT <nama_file> <ukuran>")
        nama = args[0]
        ukuran = int(args[1])
        path = self.path_aman(nama)
        if path is None:
            return self.err(403, "nama file tidak diizinkan")
        if ukuran > MAX_UPLOAD:
            return self.err(413, f"file terlalu besar (maks {MAX_UPLOAD} byte)")

        self.ok(0, "siap menerima")                       # izin: client baru boleh kirim isi file
        log.info("TRANSFER_START sid=%s op=PUT file=%s bytes=%d", self.sid, nama, ukuran)
        mulai = time.monotonic()
        sementara = path + ".part"                        # tulis ke file sementara dulu
        diterima = 0
        try:
            with open(sementara, "wb") as f:
                while diterima < ukuran:                  # baca TEPAT 'ukuran' byte, tidak lebih
                    blok = self.rfile.read(min(BUFFER, ukuran - diterima))
                    if not blok:
                        raise ConnectionError("koneksi terputus saat menerima file")
                    f.write(blok)
                    diterima += len(blok)
            os.replace(sementara, path)                   # baru dipublikasikan setelah lengkap
        except OSError as e:
            try:
                os.remove(sementara)
            except OSError:
                pass
            log.error("TRANSFER_FAIL sid=%s op=PUT file=%s bytes=%d dari=%d alasan=%s",
                      self.sid, nama, diterima, ukuran, q(f"{type(e).__name__}: {e}"))
            raise KoneksiPutus() from e
        log.info("TRANSFER_OK sid=%s op=PUT file=%s bytes=%d detik=%.3f",
                 self.sid, nama, diterima, time.monotonic() - mulai)
        return self.ok(0, "tersimpan")

    def cmd_quit(self, args):
        self.ok(0, "sampai jumpa")
        self.status_akhir = "normal"
        return False


def main():
    parser = argparse.ArgumentParser(description="Server Mini-FTP (satu koneksi TCP)")
    parser.add_argument("--host", default="127.0.0.1", help="IP yang di-bind (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2121, help="port (default 2121)")
    parser.add_argument("--root", default="server_files", help="folder file server (default server_files)")
    parser.add_argument("--log", default=os.path.join("logs", "mini_ftp.log"), help="file log")
    args = parser.parse_args()

    setup_logging(args.log)
    os.makedirs(args.root, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((args.host, args.port))
        except OSError as e:
            log.error("SERVER_ERROR gagal bind %s:%s alasan=%s", args.host, args.port, q(e))
            return
        server.listen()
        server.settimeout(1.0)               # supaya Ctrl+C responsif, terutama di Windows
        log.info("SERVER_START alamat=%s:%s root=%s log=%s", args.host, args.port,
                 q(args.root), q(args.log))

        nomor = 0
        try:
            while True:
                try:
                    conn, addr = server.accept()
                except socket.timeout:
                    continue
                nomor += 1
                sesi = Session(conn, addr, nomor, args.root)
                threading.Thread(target=sesi.run, daemon=True).start()
        except KeyboardInterrupt:
            log.info("SERVER_STOP sesi_dilayani=%d", nomor)


if __name__ == "__main__":
    main()
