"""
udp_select_server_heartbeat.py - Praktikum 3 versi select() + heartbeat/timeout, tanpa thread

Pengembangan dari udp_select_server.py: client yang tidak mengirim pesan lebih
dari batas waktu (default 30 detik) dihapus dari daftar.

Pada versi threading, pekerjaan ini butuh thread ketiga (timeout_checker).
Pada versi select, cukup satu jadwal tambahan di dalam perulangan yang sama:

    jadwal_pengumuman : kapan pengumuman berikutnya dikirim
    jadwal_cek        : kapan pemeriksaan client kadaluarsa berikutnya

select() menunggu sampai jadwal yang PALING DEKAT, atau sampai ada pesan masuk.

Perbedaan dari udp_select_server.py:
  - known_clients berubah dari set menjadi dict {alamat: waktu_terakhir_aktif}
  - ada fungsi hapus_kadaluarsa() dan jadwal_cek
  - client perlu mengirim pesan berkala (misal "ping") agar tetap terdaftar
"""

import argparse
import select
import socket
import time
from datetime import datetime

BUFFER_SIZE = 1024
ANNOUNCE_INTERVAL = 5     # detik antar pengumuman
CHECK_INTERVAL = 1        # detik antar pemeriksaan timeout
MAX_TUNGGU = 1.0          # batas maksimum select() menunggu (supaya Ctrl+C responsif)

# {alamat: waktu_terakhir_aktif}. Waktu memakai time.monotonic() (jam yang hanya
# maju, tidak terpengaruh perubahan jam sistem). Tanpa thread, tanpa Lock.
known_clients = {}


def log(pesan):
    print(f"[{datetime.now():%H:%M:%S}] {pesan}")


def tangani_pesan(server, data, addr):
    """Setiap pesan (termasuk 'ping') dianggap tanda client masih hidup."""
    pesan = data.decode("utf-8", errors="replace")

    baru = addr not in known_clients
    known_clients[addr] = time.monotonic()
    if baru:
        log(f"Client baru terdaftar: {addr} (total {len(known_clients)})")
    log(f"Dari {addr}: {pesan!r}")

    balasan = f"ACK Server: pesan '{pesan}' diterima"
    server.sendto(balasan.encode("utf-8"), addr)


def kirim_pengumuman(server, nomor):
    if not known_clients:
        log("[ANNOUNCER] Belum ada client terdaftar")
        return nomor

    nomor += 1
    pesan = f"[PENGUMUMAN #{nomor}] Server aktif pukul {datetime.now():%H:%M:%S}"
    for addr in list(known_clients):
        try:
            server.sendto(pesan.encode("utf-8"), addr)
        except OSError as e:
            log(f"[ANNOUNCER] Gagal kirim ke {addr}: {e}")
    log(f"[ANNOUNCER] Pengumuman #{nomor} dikirim ke {len(known_clients)} client")
    return nomor


def hapus_kadaluarsa(batas_detik):
    """Hapus client yang sudah diam lebih dari batas_detik."""
    sekarang = time.monotonic()
    kadaluarsa = [addr for addr, terakhir in known_clients.items()
                  if sekarang - terakhir > batas_detik]
    for addr in kadaluarsa:
        del known_clients[addr]
        log(f"[TIMEOUT] {addr} dihapus (diam lebih dari {batas_detik:g} detik), "
            f"sisa {len(known_clients)} client")


def main():
    parser = argparse.ArgumentParser(description="UDP server select() dengan heartbeat/timeout")
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

        log(f"UDP server select (heartbeat {args.timeout:g} detik) siap di "
            f"{args.host}:{args.port} (Ctrl+C untuk berhenti)")

        nomor = 0
        sekarang = time.monotonic()
        jadwal_pengumuman = sekarang
        jadwal_cek = sekarang + CHECK_INTERVAL

        try:
            while True:
                # Tunggu sampai jadwal terdekat, tapi tidak lebih dari MAX_TUNGGU.
                paling_dekat = min(jadwal_pengumuman, jadwal_cek)
                tunggu = min(max(paling_dekat - time.monotonic(), 0), MAX_TUNGGU)

                siap_baca, _, _ = select.select([server], [], [], tunggu)

                if server in siap_baca:
                    try:
                        data, addr = server.recvfrom(BUFFER_SIZE)
                    except ConnectionResetError:
                        pass  # khusus Windows, lihat udp_select_server.py
                    else:
                        tangani_pesan(server, data, addr)

                sekarang = time.monotonic()
                if sekarang >= jadwal_cek:
                    hapus_kadaluarsa(args.timeout)
                    jadwal_cek = sekarang + CHECK_INTERVAL
                if sekarang >= jadwal_pengumuman:
                    nomor = kirim_pengumuman(server, nomor)
                    jadwal_pengumuman = sekarang + ANNOUNCE_INTERVAL

        except KeyboardInterrupt:
            log("Server dihentikan")


if __name__ == "__main__":
    main()
