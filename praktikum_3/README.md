# Praktikum 3: Pengiriman Pesan UDP Asinkron Berbasis Multi-Threading

Mata kuliah Network Programming. Server UDP dengan dua thread: main thread menerima pesan dan membalas ACK, sedangkan thread pengumuman mengirim pesan ke semua client terdaftar setiap 5 detik. Hanya memakai library standar Python (`socket`, `threading`, `time`).

## Isi folder

| File | Fungsi |
|---|---|
| `udp_threaded_server.py` | Server utama sesuai modul |
| `udp_client.py` | Client dengan dua thread (kirim dan terima) |
| `udp_threaded_server_heartbeat.py` | Soal 5 (tugas mandiri): client yang diam lebih dari 30 detik dihapus |
| `eksperimen_race_condition.py` | Percobaan kecil untuk Soal 2: apa yang terjadi tanpa Lock |
| `udp_select_server.py` | Modifikasi: fungsi yang sama dengan server utama, tetapi memakai `select()` tanpa thread |
| `udp_select_server_heartbeat.py` | Versi select dengan heartbeat/timeout (tanpa thread ketiga) |
| `catatan_select.md` | Penjelasan select(), pemetaan dari versi threading, dan latihan pemahaman |
| `catatan_laporan.md` | Kerangka jawaban 5 soal evaluasi dan tabel hasil uji |

## Arsitektur

```
                 SERVER (satu socket UDP, port 6000)
        +------------------------------------------------+
Client1 |  Main thread                                   |
   ---->|  recvfrom() -> daftarkan alamat -> sendto(ACK) |
Client2 |        |                                       |
   ---->|        v  (dilindungi clients_lock)            |
        |   known_clients  {(ip, port), ...}             |
        |        ^                                       |
        |        |  (dilindungi clients_lock)            |
        |  Announcer thread                              |
        |  tiap 5 detik: sendto(pengumuman) ke semua     |
        +------------------------------------------------+
```

## Cara menjalankan

Butuh Python 3.10 atau lebih baru. Buka 3 terminal di folder ini.

Terminal 1 (server):
```
python udp_threaded_server.py
```
Yang tampil: server siap, lalu `[ANNOUNCER] Belum ada client terdaftar` tiap 5 detik.

Terminal 2 (client 1):
```
python udp_client.py
```
Ketik `Halo Server, saya Client 1!` lalu Enter. Balasan ACK muncul, lalu pengumuman datang sendiri tiap 5 detik.

Terminal 3 (client 2):
```
python udp_client.py
```
Ketik `Halo dari Client 2!`. Sekarang pengumuman server sampai ke dua client sekaligus.

Ketik `exit` di client untuk keluar. Ctrl+C di server untuk berhenti. IP dan port bisa diganti dengan `--host` dan `--port`.

Contoh yang tampil di client:
```
Pesan> Halo Server, saya Client 1!
<< ACK Server: pesan 'Halo Server, saya Client 1!' diterima
<< [PENGUMUMAN #1] Server aktif pukul 22:45:28
<< [PENGUMUMAN #2] Server aktif pukul 22:45:33
```

## UDP dibanding TCP (Praktikum 1)

| Hal | TCP (Praktikum 1) | UDP (Praktikum 3) |
|---|---|---|
| Jenis socket | `SOCK_STREAM` | `SOCK_DGRAM` |
| Koneksi | Ada (handshake) | Tidak ada |
| Sisi server | `bind`, `listen`, `accept` | cukup `bind` |
| Kirim dan terima | `sendall()` dan `recv()` | `sendto(data, alamat)` dan `recvfrom()` |
| Mengenali client | lewat socket `conn` hasil `accept()` | lewat alamat (IP, port) hasil `recvfrom()` |
| Tahu kalau lawan mati | ya (`recv()` mengembalikan `b""` atau error) | tidak |
| Jaminan sampai dan berurutan | ya | tidak |

## Skenario pengujian

| # | Skenario | Cara | Hasil yang diharapkan |
|---|---|---|---|
| 1 | Server tanpa client | Jalankan server saja | `[ANNOUNCER] Belum ada client terdaftar` tiap 5 detik |
| 2 | Client pertama | Kirim satu pesan | Server mencatat "Client baru terdaftar", client menerima ACK lalu pengumuman berkala |
| 3 | Client kedua | Jalankan di terminal lain | Pengumuman dikirim ke 2 client, log server menyebut "2 client" |
| 4 | Pesan dari client yang sama lagi | Kirim pesan kedua dari client 1 | Tidak didaftarkan dua kali, hanya dibalas ACK |
| 5 | Client mati paksa | Tutup jendela terminal client 1 tanpa `exit` | Server tidak tahu. Log tetap menyebut "dikirim ke 2 client" |
| 6 | Server tidak ada | Jalankan client tanpa server | Tidak ada error di Linux dan macOS. Di Windows bisa muncul `[!] Server tidak dapat dijangkau` |
| 7 | Port dipakai | Jalankan dua server di port sama | `Gagal bind ... Address already in use` |
| 8 | Heartbeat | Jalankan versi heartbeat dengan `--timeout 10`, biarkan satu client diam | Client itu dihapus dan berhenti dapat pengumuman |
| 9 | Eksperimen Lock | `python eksperimen_race_condition.py` | Tanpa Lock gagal dengan `RuntimeError`, dengan Lock aman |

Skenario 5 itu inti Soal 4. Di TCP, server langsung tahu client mati. Di UDP server baru bisa tahu lewat aturan buatan sendiri, misalnya heartbeat di Soal 5.

## Kenapa kodenya begini

- **`bind` di server, dan juga di client dengan port 0**: client UDP tidak wajib `bind`, tapi thread penerima perlu socket yang sudah punya port supaya bisa mulai mendengarkan, dan server perlu alamat balasan.
- **`clients_lock` selalu dipakai**: main thread menambah daftar dan announcer thread membacanya. Tanpa Lock, pembacaan bisa terjadi di tengah perubahan. `eksperimen_race_condition.py` memperlihatkan akibatnya.
- **Daftar disalin dulu, baru dikirim**: announcer menyalin `known_clients` selama dikunci, lalu mengirim setelah kunci dilepas. Kunci hanya dipegang sebentar sehingga main thread tidak ikut tertahan oleh proses kirim.
- **Thread pengumuman `daemon=True`**: ikut berhenti otomatis saat program utama berhenti.
- **`settimeout(1.0)` di server**: `recvfrom()` tidak menunggu selamanya, sehingga Ctrl+C responsif, terutama di Windows.
- **`except ConnectionResetError`**: kejadian khusus Windows saat UDP mengirim ke client yang sudah mati. Di Windows, error itu muncul pada `recvfrom()` berikutnya. Kalau tidak ditangkap, server akan berhenti mendadak.
- **Client dua thread**: pengumuman datang tanpa diminta. Satu thread yang menunggu `input()` tidak bisa sekaligus menerima.

## Keterbatasan yang disengaja

- Tidak ada jaminan pesan sampai. ACK dari server hanya berarti server menerima, bukan bahwa ACK itu sampai ke client.
- Client dikenali dari alamat saja, tanpa nama atau autentikasi.
- Pesan dibatasi satu datagram (1024 byte). Pesan lebih panjang akan terpotong.

## Tugas mandiri (Soal 5)

`udp_threaded_server_heartbeat.py` menambahkan timeout. Perbedaannya dari versi dasar kecil dan sengaja begitu:
- `known_clients` berubah dari `set` menjadi `dict` berisi alamat dan waktu terakhir aktif.
- Satu thread tambahan, `timeout_checker`, mengecek tiap detik dan menghapus client yang diam melebihi batas.

Saran: tulis versimu sendiri dulu berdasarkan perbedaan di atas, baru bandingkan dengan file ini. Untuk demo, jalankan dengan `--timeout 10` supaya tidak menunggu 30 detik. Client harus mengirim pesan berkala (misalnya `ping`) agar tetap terdaftar.

## Kalau nanti ingin dikembangkan

- Client mengirim `ping` otomatis di thread sendiri.
- Format pesan dengan perintah sederhana (misalnya `NICK nama`).
- Mengganti `print` dengan `logging`.

## Catatan Windows

Firewall Windows bisa menampilkan popup saat server pertama kali jalan, pilih Allow. Kalau praktikum dijalankan antar komputer, jalankan server dengan `--host 0.0.0.0` dan arahkan client ke IP komputer server.
