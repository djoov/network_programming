"""
client.py - Praktikum 1: TCP client sederhana

Alur client:
    socket() -> connect() -> sendall() -> recv() -> close()

Client membaca pesan dari keyboard, mengirimnya ke server,
lalu mencetak balasan dari server. Ketik 'exit' untuk keluar.
"""

import argparse
import socket

BUFFER_SIZE = 1024  # jumlah byte maksimum yang dibaca sekali recv()
TIMEOUT = 5         # detik; supaya client tidak menunggu selamanya kalau server diam


def main():
    parser = argparse.ArgumentParser(description="TCP client sederhana")
    parser.add_argument("--host", default="127.0.0.1", help="IP server (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="port server (default 5000)")
    args = parser.parse_args()

    try:
        # Client tidak perlu bind(): OS otomatis memilihkan port sementara saat connect().
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((args.host, args.port))
            print(f"Terhubung ke {args.host}:{args.port}")

            while True:
                pesan = input("Pesan (ketik 'exit' untuk keluar): ").strip()

                if pesan.lower() == "exit":
                    break
                if not pesan:
                    print("Pesan kosong, tidak dikirim.")
                    continue

                s.sendall(pesan.encode("utf-8"))

                data = s.recv(BUFFER_SIZE)
                if not data:
                    # b"" artinya server menutup koneksi
                    print("Server menutup koneksi.")
                    break
                print("Balasan:", data.decode("utf-8", errors="replace"))

        print("Koneksi ditutup.")

    # Urutan except penting: ConnectionRefusedError adalah turunan ConnectionError,
    # jadi harus ditulis lebih dulu supaya pesannya lebih spesifik.
    except ConnectionRefusedError:
        print(f"Gagal terhubung ke {args.host}:{args.port}. Server belum jalan atau port salah.")
    except socket.timeout:
        print(f"Timeout: tidak ada respons dalam {TIMEOUT} detik.")
    except socket.gaierror:
        print(f"Alamat '{args.host}' tidak dikenali.")
    except ConnectionError as e:
        print(f"Koneksi terputus: {type(e).__name__}")
    except (KeyboardInterrupt, EOFError):
        print("\nClient dihentikan.")


if __name__ == "__main__":
    main()
