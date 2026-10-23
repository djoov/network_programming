"""
udp_client.py - Praktikum 3: UDP client

Client punya dua thread:
  1. Main thread     : membaca ketikan keyboard dan mengirimnya ke server (sendto)
  2. Receiver thread : terus mendengarkan pesan dari server (recvfrom), baik
                       balasan ACK maupun pengumuman yang datang kapan saja

Dua thread diperlukan karena pengumuman server datang tanpa diminta. Kalau
hanya satu thread, program akan terhenti di input() dan tidak bisa menerima.
Ketik 'exit' untuk keluar.
"""

import argparse
import socket
import threading

BUFFER_SIZE = 1024


def terima_pesan(sock):
    """Berjalan di thread terpisah: cetak setiap datagram yang datang dari server."""
    while True:
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
        except ConnectionResetError:
            # Khusus Windows: muncul kalau pesan kita sebelumnya ditolak karena
            # tidak ada server di port tujuan. UDP sendiri tidak memberi tahu.
            print("\n[!] Server tidak dapat dijangkau di alamat tersebut")
            print("Pesan> ", end="", flush=True)
            continue
        except OSError:
            return  # socket sudah ditutup, thread selesai

        print(f"\n<< {data.decode('utf-8', errors='replace')}")
        print("Pesan> ", end="", flush=True)


def main():
    parser = argparse.ArgumentParser(description="UDP client")
    parser.add_argument("--host", default="127.0.0.1", help="IP server (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=6000, help="port server (default 6000)")
    args = parser.parse_args()
    alamat_server = (args.host, args.port)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # UDP tidak butuh connect(). Tapi socket perlu punya port sendiri supaya
        # server bisa membalas dan thread penerima bisa mulai mendengarkan.
        # Port 0 artinya "sistem operasi pilihkan port yang kosong".
        sock.bind(("", 0))
        print(f"Client UDP siap, server tujuan {args.host}:{args.port}")
        print("Ketik pesan lalu Enter. Ketik 'exit' untuk keluar.")

        threading.Thread(target=terima_pesan, args=(sock,), daemon=True).start()

        try:
            while True:
                pesan = input("Pesan> ").strip()
                if pesan.lower() == "exit":
                    break
                if not pesan:
                    continue
                # Tidak ada pengecekan sampai atau tidaknya: itulah sifat UDP.
                sock.sendto(pesan.encode("utf-8"), alamat_server)
        except (KeyboardInterrupt, EOFError):
            print()

    print("Client ditutup.")


if __name__ == "__main__":
    main()
