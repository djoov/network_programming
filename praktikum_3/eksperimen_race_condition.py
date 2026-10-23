"""
eksperimen_race_condition.py - Eksperimen kecil untuk Soal 2 (kenapa perlu Lock)

Meniru situasi di server:
  - satu thread terus menambah anggota ke daftar bersama (seperti main thread
    yang mendaftarkan client baru)
  - satu thread terus membaca seluruh daftar (seperti announcer thread)

Dijalankan dua kali: tanpa Lock dan dengan Lock. Tanpa Lock, pembaca sering
gagal dengan RuntimeError karena daftar berubah ketika sedang dibaca.

Jalankan:  python eksperimen_race_condition.py
Hasil bisa sedikit berbeda tiap kali dijalankan, itu memang sifat race condition.
"""

import threading
import time

DURASI = 2  # detik


def percobaan(pakai_lock):
    daftar = set()
    lock = threading.Lock()
    selesai = threading.Event()
    error = []
    putaran_baca = [0]

    def penambah():
        i = 0
        while not selesai.is_set():
            if pakai_lock:
                with lock:
                    daftar.add(i)
            else:
                daftar.add(i)
            i += 1

    def pembaca():
        while not selesai.is_set():
            try:
                if pakai_lock:
                    with lock:
                        salinan = list(daftar)
                else:
                    for _ in daftar:  # membaca daftar sambil thread lain menambah
                        pass
                putaran_baca[0] += 1
            except RuntimeError as e:
                error.append(e)
                selesai.set()

    t1 = threading.Thread(target=penambah)
    t2 = threading.Thread(target=pembaca)
    t1.start()
    t2.start()

    mulai = time.monotonic()
    while time.monotonic() - mulai < DURASI and not selesai.is_set():
        time.sleep(0.05)
    selesai.set()
    t1.join()
    t2.join()

    nama = "DENGAN Lock" if pakai_lock else "TANPA Lock "
    if error:
        print(f"{nama}: GAGAL -> RuntimeError: {error[0]}")
    else:
        print(f"{nama}: aman, {putaran_baca[0]} kali baca selesai tanpa error")


if __name__ == "__main__":
    print(f"Menjalankan masing-masing selama maksimal {DURASI} detik...\n")
    percobaan(pakai_lock=False)
    percobaan(pakai_lock=True)
