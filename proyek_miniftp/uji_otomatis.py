"""
uji_otomatis.py - Pengujian otomatis Mini-FTP

Menjalankan server di port uji (folder dan log sementara), lalu memeriksa
perilaku protokol lewat socket mentah. Tiap pemeriksaan dicetak PASS atau FAIL.

Jalankan:  python uji_otomatis.py           (tanpa uji rotasi, cepat)
           python uji_otomatis.py --rotasi  (tambah uji rotasi log, sekitar 1 menit)
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "mini_ftp_server.py")
HOST = "127.0.0.1"
PORT = 21210
hasil = []


def cek(nama, kondisi, detail=""):
    hasil.append(bool(kondisi))
    print(f"[{'PASS' if kondisi else 'FAIL'}] {nama}" + (f"  ({detail})" if detail else ""))


class Klien:
    """Client mentah: satu socket, satu pembaca berbuffer, seperti client sungguhan."""

    def __init__(self, port=PORT):
        self.s = socket.create_connection((HOST, port), timeout=15)
        self.r = self.s.makefile("rb")

    def kirim(self, teks):
        self.s.sendall(teks.encode())

    def balasan(self):
        h = self.r.readline().decode().rstrip("\n").split(" ", 2)
        return h[0], int(h[1]), (h[2] if len(h) > 2 else "")

    def body(self, n):
        return self.r.read(n)

    def tutup(self):
        self.r.close()
        self.s.close()


def jalankan_server(root, log, port):
    p = subprocess.Popen([sys.executable, SERVER, "--host", HOST, "--port", str(port),
                          "--root", root, "--log", log],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection((HOST, port), timeout=0.2).close()
            return p
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("server tidak mau jalan")


def isi_log(log):
    with open(log, encoding="utf-8") as f:
        return f.read()


def uji_protokol(tmp):
    root = os.path.join(tmp, "root")
    os.makedirs(root)
    log = os.path.join(tmp, "logs", "uji.log")
    with open(os.path.join(root, "halo.txt"), "wb") as f:
        f.write(b"Halo dari Mini-FTP!\n")
    # file "jebakan": isinya meniru header protokol dan berisi banyak karakter newline
    jebakan = b"OK 0 palsu\nERR 404 palsu\n\n\nGET x\n" + bytes(range(256)) * 40
    with open(os.path.join(root, "jebakan.bin"), "wb") as f:
        f.write(jebakan)
    besar = os.urandom(1024 * 1024) * 30                   # 30 MB
    with open(os.path.join(root, "besar.bin"), "wb") as f:
        f.write(besar)

    srv = jalankan_server(root, log, PORT)
    try:
        # 1. koneksi + HELP
        c = Klien()
        c.kirim("HELP\n")
        st, n, pesan = c.balasan()
        isi = c.body(n).decode()
        cek("1  koneksi dan HELP", st == "OK" and "GET <file>" in isi and "PUT" in isi)

        # 2. LIST
        c.kirim("LIST\n")
        st, n, pesan = c.balasan()
        isi = c.body(n).decode()
        cek("2  LIST menampilkan file", st == "OK" and "halo.txt\t20" in isi, pesan)

        # 3. GET file kecil
        c.kirim("GET halo.txt\n")
        st, n, _ = c.balasan()
        cek("3  GET file kecil sama persis", st == "OK" and c.body(n) == b"Halo dari Mini-FTP!\n")

        # 4. GET file tidak ada
        c.kirim("GET tidak_ada.txt\n")
        st, kode, pesan = c.balasan()
        cek("4  GET file tidak ada -> ERR 404", st == "ERR" and kode == 404, pesan)

        # 5. path traversal
        c.kirim("GET ../etc/passwd\n")
        st, kode, _ = c.balasan()
        c.kirim("GET ..\n")
        st2, kode2, _ = c.balasan()
        cek("5  nama file berbahaya ditolak (403)", (st, kode, st2, kode2) == ("ERR", 403, "ERR", 403))

        # 6. perintah tidak dikenal, koneksi tetap hidup
        c.kirim("HAPUS halo.txt\n")
        st, kode, _ = c.balasan()
        c.kirim("LIST\n")
        st2, n2, _ = c.balasan()
        c.body(n2)
        cek("6  perintah asing -> ERR 400, sesi lanjut", st == "ERR" and kode == 400 and st2 == "OK")

        # 7. PUT lalu GET kembali
        data = os.urandom(300_000)
        c.kirim(f"PUT unggahan.bin {len(data)}\n")
        st, n, pesan = c.balasan()
        c.s.sendall(data)
        st2, n2, pesan2 = c.balasan()
        c.kirim("GET unggahan.bin\n")
        st3, n3, _ = c.balasan()
        balik = c.body(n3)
        cek("7  PUT 300 KB lalu GET kembali identik", (st, pesan, st2, pesan2) == ("OK", "siap menerima", "OK", "tersimpan")
            and balik == data)

        # 8. PUT terlalu besar ditolak sebelum body dikirim, aliran tetap sinkron
        c.kirim(f"PUT raksasa.bin {10**12}\n")
        st, kode, _ = c.balasan()
        c.kirim("LIST\n")
        st2, n2, _ = c.balasan()
        c.body(n2)
        cek("8  PUT terlalu besar -> ERR 413, sesi tetap sinkron", st == "ERR" and kode == 413 and st2 == "OK")

        # 9. dua perintah dikirim sekaligus (TCP bisa menggabungkan), dua balasan terbaca benar
        c.kirim("LIST\nHELP\n")
        st1, n1, p1 = c.balasan()
        b1 = c.body(n1)
        st2, n2, p2 = c.balasan()
        b2 = c.body(n2)
        cek("9  dua perintah beruntun, dua frame terpisah benar", p1.endswith("file") and p2 == "daftar perintah"
            and b"halo.txt" in b1 and b"QUIT" in b2)

        # 10. file yang isinya meniru header tidak membingungkan pembaca
        c.kirim("GET jebakan.bin\n")
        st, n, _ = c.balasan()
        isi = c.body(n)
        c.kirim("LIST\n")
        st2, n2, _ = c.balasan()
        c.body(n2)
        cek("10 isi file mirip header tidak menggeser frame", isi == jebakan and st2 == "OK",
            f"{n} byte dibaca tepat")

        # 11. perintah dikirim SAAT transfer: dilayani sesudah transfer selesai, urutan terjaga
        c.kirim("GET besar.bin\nLIST\n")
        st, n, _ = c.balasan()
        isi = c.body(n)
        st2, n2, p2 = c.balasan()
        c.body(n2)
        cek("11 LIST yang dikirim saat GET berjalan baru dibalas setelah file selesai",
            st == "OK" and isi == besar and st2 == "OK" and p2.endswith("file"))

        c.kirim("QUIT\n")
        st, n, pesan = c.balasan()
        cek("12 QUIT dibalas dan koneksi ditutup server", st == "OK" and pesan == "sampai jumpa" and c.r.read(1) == b"")
        c.tutup()

        # 13. batalkan transfer: client menutup koneksi di tengah GET besar
        c = Klien()
        c.kirim("GET besar.bin\n")
        st, n, _ = c.balasan()
        c.body(1024 * 1024)                                # baru terima 1 MB dari 30 MB
        c.tutup()                                          # satu-satunya cara "membatalkan"
        time.sleep(1.0)
        teks = isi_log(log)
        cek("13 server mencatat TRANSFER_FAIL saat client memutus transfer",
            "TRANSFER_FAIL" in teks and "op=GET file=besar.bin" in teks and "status=terputus" in teks)

        # 14. dua client bersamaan
        hasil_thread = []

        def kerja():
            k = Klien()
            k.kirim("GET besar.bin\n")
            _, nn, _ = k.balasan()
            hasil_thread.append(k.body(nn) == besar)
            k.kirim("QUIT\n")
            k.balasan()
            k.tutup()

        ts = [threading.Thread(target=kerja) for _ in range(2)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        cek("14 dua client mengunduh 30 MB bersamaan", hasil_thread == [True, True])

        # 15. client mati tanpa QUIT dicatat sebagai terputus
        c = Klien()
        c.kirim("LIST\n")
        _, n, _ = c.balasan()
        c.body(n)
        c.tutup()
        time.sleep(0.5)
        teks = isi_log(log)
        cek("15 putus tanpa QUIT -> SESSION_END status=terputus", "status=terputus" in teks)

        # 16. file .part tidak tertinggal dan tidak muncul di LIST
        sisa = [n for n in os.listdir(root) if n.endswith(".part")]
        cek("16 tidak ada file .part tersisa", sisa == [])
    finally:
        srv.terminate()
        srv.wait()

    teks = isi_log(log)
    for kata in ("SESSION_START", "SESSION_END", "CMD ", "TRANSFER_OK", "TRANSFER_FAIL", "CMD_FAIL", "SERVER_START"):
        cek(f"L  log berisi {kata.strip()}", kata in teks)


def uji_rotasi(tmp):
    root = os.path.join(tmp, "root_rot")
    os.makedirs(root)
    log = os.path.join(tmp, "logs_rot", "rot.log")
    port = PORT + 1
    srv = jalankan_server(root, log, port)
    try:
        for i in range(14000):                             # sekitar 5 MB log
            c = Klien(port)
            c.kirim("LIST\nQUIT\n")
            c.r.read()                                     # baca sampai server menutup
            c.tutup()
        time.sleep(0.5)
    finally:
        srv.terminate()
        srv.wait()
    ada = {s: os.path.exists(f"{log}{s}") for s in ("", ".1", ".2", ".3", ".4")}
    ukuran = {s: os.path.getsize(f"{log}{s}") for s, v in ada.items() if v}
    print("   ukuran file log:", {k or "utama": v for k, v in ukuran.items()})
    cek("R1 file log berotasi: utama, .1, .2, .3 ada", ada[""] and ada[".1"] and ada[".2"] and ada[".3"])
    cek("R2 tidak ada .4 (hanya 3 file lama disimpan)", not ada[".4"])
    cek("R3 tiap file log tidak melebihi 1 MB", all(v <= 1024 * 1024 for v in ukuran.values()))


def main():
    tmp = tempfile.mkdtemp(prefix="miniftp_uji_")
    try:
        print("== Uji protokol dan logging ==")
        uji_protokol(tmp)
        if "--rotasi" in sys.argv:
            print("== Uji rotasi log (14000 sesi) ==")
            uji_rotasi(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    lulus = sum(hasil)
    print(f"\nHasil: {lulus} dari {len(hasil)} pemeriksaan lulus")
    return 0 if lulus == len(hasil) else 1


if __name__ == "__main__":
    sys.exit(main())
