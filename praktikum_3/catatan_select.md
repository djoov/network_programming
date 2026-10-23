# Catatan: mengubah versi threading menjadi select()

File yang terkait: `udp_select_server.py` (inti) dan `udp_select_server_heartbeat.py` (tambahan Soal 5). Client tetap `udp_client.py`.

## 1. Apa itu select()

`select()` adalah fungsi dari sistem operasi untuk **menunggu beberapa socket sekaligus dengan satu alur program**. Kamu menyerahkan daftar socket yang ingin dipantau, lalu `select()` baru kembali ketika salah satu socket siap, atau ketika batas waktu habis. Teknik ini disebut **I/O multiplexing**.

```python
siap_baca, _, _ = select.select([server], [], [], tunggu)
#                              ^daftar     ^   ^   ^ batas waktu (detik)
#                              dipantau    tulis  error
```

Hasil pertama adalah daftar socket yang **siap dibaca**. Kalau waktu habis tanpa kejadian apa pun, daftarnya kosong.

## 2. Kenapa ada

Fungsi seperti `recvfrom()` itu memblokir: program berhenti sampai ada pesan. Kalau program juga harus mengerjakan hal lain (pengumuman tiap 5 detik), ada dua jalan:

- **Threading**: satu thread untuk satu pekerjaan. Mudah dibayangkan, tetapi data bersama butuh Lock.
- **select()**: satu alur saja, tetapi program **tidak pernah menunggu buta**. Ia menunggu dengan batas waktu, lalu memeriksa apa yang perlu dikerjakan.

Analogi: satu pelayan restoran yang memantau semua meja sekaligus, bukan satu pelayan per meja. Ia berdiri di tengah, melihat bel meja mana yang menyala, mengerjakan yang menyala, dan sesekali melihat jam untuk tugas berkala. Tidak ada dua pelayan yang berebut buku catatan yang sama, jadi tidak perlu aturan giliran (Lock).

## 3. Pemetaan dari versi threading

| Versi threading | Versi select |
|---|---|
| Main thread: `recvfrom()` memblokir | `select()` menunggu, lalu `recvfrom()` hanya dipanggil kalau socket siap |
| Announcer thread: `sleep(5)` lalu kirim | Variabel `jadwal_pengumuman`, dicek setiap putaran |
| `settimeout(1.0)` supaya Ctrl+C responsif | Argumen waktu tunggu `select()`, dibatasi `MAX_TUNGGU = 1.0` |
| `threading.Thread(...).start()` | Tidak ada |
| `clients_lock` dan `with clients_lock:` | Tidak ada, karena tidak ada data yang dipakai dua alur |
| `timeout_checker` (thread ketiga, heartbeat) | `jadwal_cek`, dicek di perulangan yang sama |

## 4. Cara kerja perulangannya

```python
while True:
    # 1. berapa lama boleh menunggu sampai pengumuman berikutnya?
    tunggu = min(max(jadwal_pengumuman - time.monotonic(), 0), MAX_TUNGGU)

    # 2. tunggu: ada pesan masuk, atau waktu habis
    siap_baca, _, _ = select.select([server], [], [], tunggu)

    # 3. ada pesan? baca dan layani
    if server in siap_baca:
        data, addr = server.recvfrom(BUFFER_SIZE)
        tangani_pesan(server, data, addr)

    # 4. sudah saatnya pengumuman? kirim
    if time.monotonic() >= jadwal_pengumuman:
        nomor = kirim_pengumuman(server, nomor)
        jadwal_pengumuman = time.monotonic() + ANNOUNCE_INTERVAL
```

Langkah 4 dicek **setiap putaran**, bukan hanya saat waktu habis. Jadi walaupun pesan terus berdatangan dan `select()` tidak pernah kehabisan waktu, pengumuman tetap tepat jadwal.

Di versi heartbeat, ada satu jadwal tambahan (`jadwal_cek`), dan waktu tunggu diambil dari jadwal yang paling dekat.

## 5. Kenapa tidak perlu Lock

Race condition terjadi kalau **dua alur** menyentuh data yang sama. Sekarang hanya ada satu alur: `known_clients` ditulis saat menangani pesan dan dibaca saat pengumuman, tetapi tidak pernah bersamaan, karena keduanya dikerjakan berurutan di perulangan yang sama.

## 6. Hal yang sering salah

- **Pekerjaan lama di dalam perulangan menghalangi semuanya.** Ini kelemahan terbesar select. Kalau `tangani_pesan()` memakai `sleep(3)`, pengumuman dan pesan client lain ikut tertunda 3 detik. Di versi threading, thread lain tetap jalan. Aturan emasnya: tiap pekerjaan di dalam perulangan harus singkat.
- **Lupa waktu tunggu.** `select.select([server], [], [])` tanpa timeout menunggu selamanya, sehingga pengumuman tidak pernah terkirim saat tidak ada pesan.
- **Membaca socket yang tidak ada di `siap_baca`.** Setelah `select()`, hanya socket di daftar hasil yang dijamin tidak memblokir.
- **`select()` di Windows hanya untuk socket.** Tidak bisa memantau `input()` atau keyboard. Karena itu client tetap memakai dua thread. Di Linux dan macOS, `sys.stdin` bisa dimasukkan ke `select()`, tetapi kode itu tidak akan jalan di Windows.
- **Ada batas jumlah socket** (sekitar 512 sampai 1024 tergantung sistem operasi). Untuk ribuan koneksi, dipakai `poll`, `epoll`, atau modul `selectors`.

## 7. Jujur soal manfaatnya di praktikum ini

Pada server UDP ini hanya ada **satu socket**, jadi yang dipakai dari select adalah **fungsi waktu tunggunya** sebagai pengatur jadwal. Kekuatan multiplexing yang sebenarnya terlihat pada **TCP multi-client** (Praktikum 2): satu socket penerima ditambah banyak socket `conn`, semuanya dipantau dalam satu `select()` tanpa thread per client. Pola yang sama berlaku: daftar socket dipantau, yang siap dikerjakan, yang lain dibiarkan.

## 8. Threading dibanding select

| Hal | Threading | select |
|---|---|---|
| Jumlah alur | Banyak thread | Satu |
| Data bersama | Perlu Lock | Tidak perlu |
| Pekerjaan lambat | Aman (thread lain jalan) | Menghalangi semua |
| Kemudahan debug | Sulit (urutan tidak pasti) | Lebih mudah (urutan jelas) |
| Beban memori | Satu thread per pekerjaan | Ringan |
| Cocok untuk | Pekerjaan lama atau CPU berat | Banyak koneksi dengan pekerjaan singkat |

## 9. Cek pemahaman

1. Apa yang dikembalikan `select.select()`, dan apa artinya kalau daftar pertamanya kosong?
2. Kenapa waktu tunggu `select()` dibatasi `MAX_TUNGGU`? Apa yang terjadi di Windows kalau tidak dibatasi?
3. Kenapa versi ini tidak butuh `Lock`?
4. Apa yang terjadi pada pengumuman kalau `tangani_pesan()` butuh 10 detik?
5. Kenapa pengumuman tetap tepat waktu walaupun pesan terus berdatangan?
6. Kenapa client tidak diubah ke select?

Pokok jawaban: (1) tiga daftar, kosong berarti waktu habis tanpa kejadian; (2) supaya Ctrl+C responsif dan jadwal tetap dicek, karena panggilan yang memblokir lama di Windows tidak langsung bereaksi; (3) hanya satu alur yang menyentuh data; (4) tertunda 10 detik, bersama semua pesan lain; (5) jadwal dicek tiap putaran, bukan hanya saat timeout; (6) `select()` di Windows tidak mendukung keyboard.

## 10. Hasil uji

Diuji di Linux dengan skrip uji:

- ACK diterima, pengumuman datang tiap sekitar 5 detik ke dua client.
- Dengan lima pesan per detik dari satu client, pengumuman tetap datang dengan jarak sekitar 5 detik.
- Ctrl+C menghentikan server dalam kurang dari satu detik.
- Versi heartbeat dengan `--timeout 3`: client yang diam dihapus sekitar 3 sampai 4 detik setelah pesan terakhir dan berhenti menerima pengumuman, sedangkan client yang mengirim ping tiap detik tetap terdaftar.
- `udp_client.py` (versi thread) bekerja dengan server select tanpa perubahan.

Belum diuji di Windows. Jalankan sendiri dan ganti hasilnya dengan tangkapan layar milikmu.
