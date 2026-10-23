"""
udp_threaded_server_heartbeat.py - Praktikum 3, Soal 5 (Tugas Mandiri)

Pengembangan dari udp_threaded_server.py: client yang tidak mengirim pesan
selama lebih dari 30 detik dihapus dari known_clients (heartbeat/timeout).

Tiga thread bekerja bersamaan:
  1. Main thread           : menerima pesan, mencatat waktu terakhir tiap client aktif
  2. Announcer thread      : pengumuman berkala ke client terdaftar
  3. Timeout checker thread: tiap detik menghapus client yang terlalu lama diam

Perbedaan dari versi dasar (bisa dibandingkan dengan fitur diff):
  - known_clients berubah dari set menjadi dict {alamat: waktu_terakhir_aktif}
  - ada fungsi timeout_checker() dan konstanta CLIENT_TIMEOUT
  - client perlu mengirim pesan secara berkala (misal "ping") agar tetap terdaftar
"""

import argparse
import socket
import threading
import time
from datetime import datetime

BUFFER_SIZE = 1024
ANNOUNCE_INTERVAL = 5
CHECK_INTERVAL = 1       # detik antar pengecekan timeout

# {alamat: waktu_terakhir_aktif}. Waktu memakai time.monotonic(), jam yang hanya
# maju dan tidak terpengaruh perubahan jam sistem, cocok untuk mengukur durasi.
known_clients = {}
clients_lock = threading.Lock()


def log(pesan):
    print(f"[{datetime.now():%H:%M:%S}] {pesan}")


def background_announcer(sock):
    nomor = 0
    while True:
        with clients_lock:
            daftar = list(known_clients)  # list(dict) berisi kunci (alamat) saja

        if not daftar:
            log("[ANNOUNCER] Belum ada client terdaftar")
        else:
            nomor += 1
            pesan = f"[PENGUMUMAN #{nomor}] Server aktif pukul {datetime.now():%H:%M:%S}"
            for addr in daftar:
                try:
                    sock.sendto(pesan.encode("utf-8"), addr)
                except OSError as e:
                    log(f"[ANNOUNCER] Gagal kirim ke {addr}: {e}")
            log(f"[ANNOUNCER] Pengumuman #{nomor} dikirim ke {len(daftar)} client")

        time.sleep(ANNOUNCE_INTERVAL)


def timeout_checker(batas_detik):
    """Berjalan di thread terpisah: hapus client yang diam lebih dari batas_detik."""
    while True:
        time.sleep(CHECK_INTERVAL)
        sekarang = time.monotonic()

        # Cari sekaligus hapus dalam satu blok terkunci. Kalau dipisah, main thread
        # bisa memperbarui waktu client di antara dua langkah itu, lalu client yang
        # sebenarnya aktif ikut terhapus.
        with clients_lock:
            kadaluarsa = [addr for addr, terakhir in known_clients.items()
                          if sekarang - terakhir > batas_detik]
            for addr in kadaluarsa:
                del known_clients[addr]
            sisa = len(known_clients)

        for addr in kadaluarsa:
            log(f"[TIMEOUT] {addr} dihapus (diam lebih dari {batas_detik:g} detik), sisa {sisa} client")


def main():
    parser = argparse.ArgumentParser(description="UDP server dengan heartbeat/timeout")
    parser.add_argument("--host", default="127.0.0.1", help="IP yang di-bind (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=6000, help="port yang di-bind (default 6000)")
    parser.add_argument("--timeout", type=float, default=30,
                        help="batas diam client dalam detik (default 30)")
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        try:
            server.bind((args.host, args.port))
        except OSError as e:
            log(f"Gagal bind ke {args.host}:{args.port} -> {e}")
            return

        server.settimeout(1.0)
        log(f"UDP server (heartbeat {args.timeout:g} detik) siap di {args.host}:{args.port}")

        threading.Thread(target=background_announcer, args=(server,),
                         daemon=True, name="announcer").start()
        threading.Thread(target=timeout_checker, args=(args.timeout,),
                         daemon=True, name="timeout-checker").start()

        try:
            while True:
                try:
                    data, addr = server.recvfrom(BUFFER_SIZE)
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    continue  # kejadian khusus Windows, lihat udp_threaded_server.py

                pesan = data.decode("utf-8", errors="replace")

                # Setiap pesan, baik pesan biasa maupun "ping", dianggap tanda
                # client masih hidup, jadi waktu terakhirnya diperbarui.
                with clients_lock:
                    baru = addr not in known_clients
                    known_clients[addr] = time.monotonic()
                    jumlah = len(known_clients)

                if baru:
                    log(f"Client baru terdaftar: {addr} (total {jumlah})")
                log(f"Dari {addr}: {pesan!r}")

                balasan = f"ACK Server: pesan '{pesan}' diterima"
                server.sendto(balasan.encode("utf-8"), addr)

        except KeyboardInterrupt:
            log("Server dihentikan")


if __name__ == "__main__":
    main()
