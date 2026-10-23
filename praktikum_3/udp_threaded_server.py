"""
udp_threaded_server.py - Praktikum 3: UDP server dengan multi-threading

Dua thread bekerja bersamaan:
  1. Main thread      : menerima datagram dari client (recvfrom), membalas ACK (sendto)
  2. Announcer thread : tiap 5 detik mengirim pengumuman ke semua client yang terdaftar

Tidak ada listen() dan accept() di sini, karena UDP tidak punya koneksi.
Client dikenali dari alamat (IP, port) pengirim yang dikembalikan oleh recvfrom().
"""

import argparse
import socket
import threading
import time
from datetime import datetime

BUFFER_SIZE = 1024       # ukuran maksimum satu datagram yang dibaca
ANNOUNCE_INTERVAL = 5    # detik antar pengumuman

# Daftar client yang pernah mengirim pesan. Berisi alamat (ip, port).
# Variabel ini dipakai DUA thread (main menambah, announcer membaca),
# jadi setiap akses harus dilindungi clients_lock.
known_clients = set()
clients_lock = threading.Lock()


def log(pesan):
    """Cetak pesan dengan jam, supaya urutan kejadian mudah dilacak."""
    print(f"[{datetime.now():%H:%M:%S}] {pesan}")


def background_announcer(sock):
    """Berjalan di thread terpisah: kirim pengumuman berkala ke semua client."""
    nomor = 0
    while True:
        # Ambil salinan daftar client selama dikunci, lalu lepas kunci.
        # Pengiriman ke jaringan dilakukan SETELAH kunci dilepas supaya main
        # thread tidak tertahan menunggu proses kirim yang lebih lambat.
        with clients_lock:
            daftar = list(known_clients)

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


def main():
    parser = argparse.ArgumentParser(description="UDP server dengan thread pengumuman")
    parser.add_argument("--host", default="127.0.0.1", help="IP yang di-bind (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=6000, help="port yang di-bind (default 6000)")
    args = parser.parse_args()

    # SOCK_DGRAM = UDP. Bedanya dengan TCP (SOCK_STREAM): tidak ada koneksi,
    # setiap pesan berdiri sendiri sebagai satu datagram.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        try:
            server.bind((args.host, args.port))
        except OSError as e:
            log(f"Gagal bind ke {args.host}:{args.port} -> {e}")
            return

        # Timeout 1 detik supaya recvfrom() tidak menunggu selamanya.
        # Manfaatnya: Ctrl+C tetap bisa menghentikan server (terutama di Windows).
        server.settimeout(1.0)

        log(f"UDP server siap di {args.host}:{args.port} (Ctrl+C untuk berhenti)")

        # daemon=True: thread ini otomatis ikut berhenti saat program utama berhenti.
        threading.Thread(target=background_announcer, args=(server,),
                         daemon=True, name="announcer").start()

        try:
            while True:
                try:
                    data, addr = server.recvfrom(BUFFER_SIZE)
                except socket.timeout:
                    continue  # tidak ada pesan dalam 1 detik, ulangi
                except ConnectionResetError:
                    # Khusus Windows: muncul kalau sebelumnya server mengirim ke
                    # client yang sudah mati (ICMP "port unreachable"). Bukan error
                    # fatal, cukup diabaikan.
                    continue

                pesan = data.decode("utf-8", errors="replace")

                # Daftarkan client. Cek dan tambah dilakukan dalam satu blok terkunci.
                with clients_lock:
                    baru = addr not in known_clients
                    known_clients.add(addr)
                    jumlah = len(known_clients)

                if baru:
                    log(f"Client baru terdaftar: {addr} (total {jumlah})")
                log(f"Dari {addr}: {pesan!r}")

                # Balas langsung ke alamat pengirim. UDP tidak punya "conn" seperti
                # TCP, jadi alamat tujuan harus disebut di setiap sendto().
                balasan = f"ACK Server: pesan '{pesan}' diterima"
                server.sendto(balasan.encode("utf-8"), addr)

        except KeyboardInterrupt:
            log("Server dihentikan")


if __name__ == "__main__":
    main()
