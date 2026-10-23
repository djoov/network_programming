"""
eksperimen_framing.py - Apa yang terjadi kalau batas respons dan data file salah ditangani?

Tiga kesalahan client, dijalankan terhadap server Mini-FTP yang asli:
  A. membaca balasan dengan satu recv() dan menganggap itu "satu pesan"
  B. salah menghitung panjang body (kurang 10 byte)
  C. memakai karakter newline sebagai penanda akhir data file

Jalankan:  python eksperimen_framing.py
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 21301
ISI = b"baris satu\nbaris dua\nbaris tiga\n"          # berisi newline


def sambung():
    return socket.create_connection(("127.0.0.1", PORT), timeout=5)


def main():
    tmp = tempfile.mkdtemp(prefix="miniftp_frm_")
    try:
        root = os.path.join(tmp, "root")
        os.makedirs(root)
        with open(os.path.join(root, "tiga_baris.txt"), "wb") as f:
            f.write(ISI)
        srv = subprocess.Popen([sys.executable, os.path.join(HERE, "mini_ftp_server.py"), "--port", str(PORT),
                                "--root", root, "--log", os.path.join(tmp, "x.log")],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        print(f"Isi file di server ({len(ISI)} byte): {ISI!r}\n")

        # A. satu recv() dianggap satu respons
        s = sambung()
        s.sendall(b"GET tiga_baris.txt\n")
        time.sleep(0.3)
        mentah = s.recv(1024)
        print("A. Satu recv() setelah GET:")
        print(f"   diterima {len(mentah)} byte sekaligus: {mentah!r}")
        print("   Header dan isi file menyatu. Tanpa panjang dari header, client tidak tahu\n"
              "   di mana respons berakhir dan data file dimulai.\n")
        s.close()

        # B. salah hitung panjang body (kurang 10 byte)
        s = sambung()
        r = s.makefile("rb")
        s.sendall(b"GET tiga_baris.txt\n")
        header = r.readline()
        n = int(header.split()[1])
        r.read(n - 10)                                   # SALAH: harusnya n
        s.sendall(b"LIST\n")
        baris_berikut = r.readline()
        print("B. Client membaca body kurang 10 byte, lalu mengirim LIST dan membaca header balasan:")
        print(f"   diharapkan baris 'OK <n> ...', yang terbaca: {baris_berikut!r}")
        print("   Sisa 10 byte data file dianggap awal balasan LIST. Sejak ini seluruh sesi kacau.\n")
        s.close()

        # C. newline dianggap penanda akhir data file
        s = sambung()
        r = s.makefile("rb")
        s.sendall(b"GET tiga_baris.txt\n")
        r.readline()                                     # header
        potongan = r.readline()                          # SALAH: berhenti di newline pertama
        print("C. Client membaca data file sampai newline pertama:")
        print(f"   terbaca {potongan!r} (hanya {len(potongan)} dari {len(ISI)} byte)")
        print("   File terpotong tanpa error apa pun. Data biner yang kebetulan memuat byte newline\n"
              "   akan rusak dengan cara yang sama.")
        s.close()
        srv.terminate()
        srv.wait()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
