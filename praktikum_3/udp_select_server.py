"""
udp_select_server.py - Praktikum 3 versi select() (I/O multiplexing), tanpa thread

Fungsinya sama dengan udp_threaded_server.py:
  - menerima pesan client dan membalas ACK
  - tiap 5 detik mengirim pengumuman ke semua client yang terdaftar

Bedanya: hanya ada SATU alur program (satu thread). Dua pekerjaan itu dibagi
waktu di dalam satu perulangan dengan bantuan select():

    select([server], [], [], tunggu)
      -> menunggu sampai ADA PESAN MASUK, atau sampai WAKTU TUNGGU HABIS

  - Kalau ada pesan masuk, kerjakan pesan itu.
  - Kalau waktu tunggu habis dan sudah saatnya pengumuman, kirim pengumuman.

Karena tidak ada thread, tidak ada data yang dipakai bersama oleh dua alur,
jadi Lock tidak diperlukan sama sekali.

Client yang dipakai tetap udp_client.py (protokolnya tidak berubah).
"""

import argparse
import select
import socket
import time
from datetime import datetime

BUFFER_SIZE = 1024
ANNOUNCE_INTERVAL = 5     # detik antar pengumuman
MAX_TUNGGU = 1.0          # select() tidak menunggu lebih lama dari ini, supaya Ctrl+C responsif

# Daftar client (alamat) yang pernah mengirim pesan. Hanya satu alur yang
# menyentuh variabel ini, jadi tidak perlu Lock.
known_clients = set()


def log(pesan):
    print(f"[{datetime.now():%H:%M:%S}] {pesan}")


def tangani_pesan(server, data, addr):
    """Kerjakan satu datagram: daftarkan pengirim, catat log, balas ACK."""
    pesan = data.decode("utf-8", errors="replace")

    if addr not in known_clients:
        known_clients.add(addr)
        log(f"Client baru terdaftar: {addr} (total {len(known_clients)})")
    log(f"Dari {addr}: {pesan!r}")

    balasan = f"ACK Server: pesan '{pesan}' diterima"
    server.sendto(balasan.encode("utf-8"), addr)


def kirim_pengumuman(server, nomor):
    """Kirim pengumuman ke semua client. Mengembalikan nomor pengumuman terbaru."""
    if not known_clients:
        log("[ANNOUNCER] Belum ada client terdaftar")
        return nomor

    nomor += 1
    pesan = f"[PENGUMUMAN #{nomor}] Server aktif pukul {datetime.now():%H:%M:%S}"
    # list(...) membuat salinan, jadi aman walaupun daftar berubah di tengah jalan
    for addr in list(known_clients):
        try:
            server.sendto(pesan.encode("utf-8"), addr)
        except OSError as e:
            log(f"[ANNOUNCER] Gagal kirim ke {addr}: {e}")
    log(f"[ANNOUNCER] Pengumuman #{nomor} dikirim ke {len(known_clients)} client")
    return nomor


def main():
    parser = argparse.ArgumentParser(description="UDP server dengan select() (tanpa thread)")
    parser.add_argument("--host", default="127.0.0.1", help="IP yang di-bind (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=6000, help="port yang di-bind (default 6000)")
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        try:
            server.bind((args.host, args.port))
        except OSError as e:
            log(f"Gagal bind ke {args.host}:{args.port} -> {e}")
            return

        log(f"UDP server (select) siap di {args.host}:{args.port} (Ctrl+C untuk berhenti)")

        nomor = 0
        jadwal_pengumuman = time.monotonic()   # pengumuman pertama langsung

        try:
            while True:
                # 1. Hitung berapa lama boleh menunggu sampai pengumuman berikutnya.
                sisa = jadwal_pengumuman - time.monotonic()
                tunggu = min(max(sisa, 0), MAX_TUNGGU)

                # 2. Tunggu: ada pesan masuk di socket, atau waktu habis.
                #    Hasil pertama berisi daftar socket yang SIAP DIBACA.
                siap_baca, _, _ = select.select([server], [], [], tunggu)

                # 3. Kalau socket siap dibaca, recvfrom() dijamin tidak memblokir.
                if server in siap_baca:
                    try:
                        data, addr = server.recvfrom(BUFFER_SIZE)
                    except ConnectionResetError:
                        # Khusus Windows: sisa error dari pengiriman ke client yang sudah mati.
                        pass
                    else:
                        tangani_pesan(server, data, addr)

                # 4. Sudah saatnya pengumuman? (dicek setiap putaran, termasuk
                #    saat pesan terus berdatangan, jadi pengumuman tidak terlewat)
                if time.monotonic() >= jadwal_pengumuman:
                    nomor = kirim_pengumuman(server, nomor)
                    jadwal_pengumuman = time.monotonic() + ANNOUNCE_INTERVAL

        except KeyboardInterrupt:
            log("Server dihentikan")


if __name__ == "__main__":
    main()
