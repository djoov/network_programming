"""
server.py - Praktikum 1: TCP server sederhana

Alur server:
    socket() -> bind() -> listen() -> accept() -> recv() -> sendall() -> close()

Server melayani SATU client dalam satu waktu. Setelah client selesai,
server kembali ke accept() untuk menunggu client berikutnya.
(Melayani banyak client sekaligus dibahas di praktikum multi client.)
"""

import argparse
import socket
from datetime import datetime

BUFFER_SIZE = 1024  
BACKLOG = 5         # panjang antrean koneksi yang menunggu di-accept()


def log(pesan):
    """Cetak pesan dengan jam, supaya urutan kejadian mudah dilacak saat testing."""
    print(f"[{datetime.now():%H:%M:%S}] {pesan}")


def layani_client(conn, addr):
    """Terima pesan dari satu client dan balas, sampai koneksi berakhir."""
    # 'with conn' menjamin conn.close() dipanggil, apa pun yang terjadi di dalam blok.
    with conn:
        try:
            while True:
                data = conn.recv(BUFFER_SIZE)

                # recv() mengembalikan b"" (kosong) artinya client sudah menutup
                # koneksi secara normal. Tanpa pengecekan ini, loop tidak pernah berhenti.
                if not data:
                    log(f"{addr} menutup koneksi")
                    return

                # Socket hanya mengenal bytes, jadi kita ubah ke string dulu.
                # errors="replace" mencegah server crash kalau datanya bukan UTF-8 yang valid.
                pesan = data.decode("utf-8", errors="replace")
                log(f"Dari {addr}: {pesan!r}")

                balasan = f"Server menerima: {pesan}"
                conn.sendall(balasan.encode("utf-8"))

        except ConnectionError as e:
            # ConnectionError mencakup ConnectionResetError, BrokenPipeError, dll.
            # Terjadi kalau client mati mendadak tanpa menutup koneksi dengan benar.
            log(f"{addr} terputus mendadak: {type(e).__name__}")


def main():
    parser = argparse.ArgumentParser(description="TCP server sederhana")
    parser.add_argument("--host", default="127.0.0.1", help="IP yang di-bind (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="port yang di-bind (default 5000)")
    args = parser.parse_args()

    # AF_INET = alamat IPv4, SOCK_STREAM = TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        # Izinkan port dipakai ulang segera setelah server di-restart.
        # Tanpa ini, port yang masih berstatus TIME_WAIT bisa menyebabkan
        # "Address already in use".
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server.bind((args.host, args.port))
        except OSError as e:
            log(f"Gagal bind ke {args.host}:{args.port} -> {e}")
            return

        server.listen(BACKLOG)
        log(f"Server siap di {args.host}:{args.port} (Ctrl+C untuk berhenti)")

        try:
            while True:
                conn, addr = server.accept()  # blocking: berhenti di sini sampai ada client
                log(f"Client terhubung: {addr}")
                layani_client(conn, addr)
        except KeyboardInterrupt:
            log("Server dihentikan")


if __name__ == "__main__":
    main()
