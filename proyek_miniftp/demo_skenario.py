"""
demo_skenario.py - Menjalankan skenario client sungguhan untuk menghasilkan contoh log

Server dan client yang dipakai adalah program asli (mini_ftp_server.py dan
mini_ftp_client.py), bukan tiruan. Hasil:
  contoh_log/mini_ftp_contoh.log      file log (format sama dengan logs/mini_ftp.log)
  contoh_log/konsol_server.txt        yang tampil di konsol server
  contoh_log/transkrip_client.txt     yang tampil di client tiap sesi
  contoh_log/laporan_contoh.txt       hasil log_report.py atas log di atas

Jalankan:  python demo_skenario.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 21299
KELUAR = os.path.join(HERE, "contoh_log")

SKENARIO = [
    ("Sesi 1: bantuan, daftar file, unduh halo dua kali", ["help", "ls", "get halo.txt", "get catatan.txt", "get halo.txt", "quit"]),
    ("Sesi 2: unduh tiga file lalu unggah satu file", ["ls", "get halo.txt", "get jadwal.csv", "get data_200kb.bin", "put laporan_baru.txt", "quit"]),
    ("Sesi 3: file tidak ada, nama berbahaya, perintah asing", ["get catatan.txt", "get laporan.txt", "get tidak_ada.txt", "get ../rahasia.txt", "get halo.txt", "quit"]),
    ("Sesi 4: batalkan unduhan file besar (koneksi diputus lalu sesi baru)", ["get besar_20mb.bin --batal 512", "ls", "quit"]),
    ("Sesi 5: unduh tiga file", ["get data_200kb.bin", "get readme.txt", "get catatan.txt", "quit"]),
]


def main():
    tmp = tempfile.mkdtemp(prefix="miniftp_demo_")
    try:
        root = os.path.join(tmp, "server_files")
        shutil.copytree(os.path.join(HERE, "server_files"), root)
        with open(os.path.join(root, "besar_20mb.bin"), "wb") as f:
            f.write(os.urandom(1024 * 1024) * 20)
        kerja = os.path.join(tmp, "client")
        os.makedirs(kerja)
        with open(os.path.join(kerja, "laporan_baru.txt"), "w", encoding="utf-8") as f:
            f.write("Isi laporan baru yang diunggah dari client.\n" * 20)

        os.makedirs(KELUAR, exist_ok=True)
        log = os.path.join(KELUAR, "mini_ftp_contoh.log")
        for p in (log, log + ".1"):
            if os.path.exists(p):
                os.remove(p)

        # server dijalankan dari folder sementara dengan path relatif, seperti pemakaian biasa
        srv = subprocess.Popen([sys.executable, os.path.join(HERE, "mini_ftp_server.py"), "--port", str(PORT),
                                "--root", "server_files", "--log", os.path.join("logs", "mini_ftp.log")],
                               stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, cwd=tmp)
        time.sleep(1.0)

        transkrip = []
        for judul, perintah in SKENARIO:
            masukan = "\n".join(perintah) + "\n"
            r = subprocess.run([sys.executable, os.path.join(HERE, "mini_ftp_client.py"), "--port", str(PORT)],
                               input=masukan, capture_output=True, text=True, cwd=kerja, timeout=60)
            transkrip.append(f"##### {judul}\n$ python mini_ftp_client.py --port {PORT}\n" + r.stdout)
            time.sleep(0.3)

        time.sleep(0.5)
        srv.terminate()
        konsol = srv.stderr.read() + srv.stdout.read()
        srv.wait()

        with open(os.path.join(KELUAR, "konsol_server.txt"), "w", encoding="utf-8") as f:
            f.write(konsol)
        with open(os.path.join(KELUAR, "transkrip_client.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(transkrip))
        shutil.copy(os.path.join(tmp, "logs", "mini_ftp.log"), log)
        r = subprocess.run([sys.executable, os.path.join(HERE, "log_report.py"), log,
                            "-o", os.path.join(KELUAR, "laporan_contoh.txt")], capture_output=True, text=True)
        print(r.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
