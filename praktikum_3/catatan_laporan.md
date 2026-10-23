# Catatan Laporan Praktikum 3

Ini kerangka, bukan jawaban jadi. Kolom "Cari di kode" menunjuk bagian program yang bisa kamu tunjuk saat menjelaskan, "Arah" memberi petunjuk apa yang perlu dibahas. Jawaban ditulis dengan kata-katamu sendiri supaya bisa kamu jelaskan ketika ditanya dosen. Kalau ada poin yang belum jelas, tanyakan ke mentor sebelum menulis.

---

## Soal 1: Analisis protokol dan socket

Pertanyaan: kenapa tidak ada `listen()` dan `accept()` seperti server TCP? Jelaskan peran `recvfrom()` dan `sendto()`.

| Bahan | Cari di kode | Arah |
|---|---|---|
| Jenis socket | `socket.SOCK_DGRAM` di server dan client | Bandingkan dengan `SOCK_STREAM` di Praktikum 1 |
| Kenapa `listen`/`accept` tidak perlu | Seluruh `main()` server | Apa yang dilakukan `listen()` dan `accept()` di TCP, dan kenapa UDP tidak punya hal itu? |
| Peran `recvfrom()` | Loop utama server | Apa dua hal yang dikembalikannya, dan kenapa alamat pengirim penting? |
| Peran `sendto()` | `server.sendto(balasan..., addr)` | Kenapa alamat tujuan harus disebut di setiap pengiriman? |
| Tabel pembanding | README bagian "UDP dibanding TCP" | Bisa jadi dasar tabel di laporan |

## Soal 2: Konkurensi dan sinkronisasi

Pertanyaan: kenapa `known_clients` dilindungi `threading.Lock()`? Apa bahayanya tanpa Lock?

| Bahan | Cari di kode | Arah |
|---|---|---|
| Siapa saja yang mengakses | `with clients_lock:` di loop utama dan di `background_announcer` | Thread mana yang menulis, thread mana yang membaca? |
| Bahayanya | Jalankan `eksperimen_race_condition.py` | Salin hasil dan jelaskan arti `RuntimeError: Set changed size during iteration` |
| Cara kerja Lock | Blok `with clients_lock` | Apa yang terjadi pada thread kedua yang datang saat Lock dipegang? |
| Kenapa daftar disalin dulu | `daftar = list(known_clients)` | Apa untungnya mengirim ke jaringan setelah Lock dilepas? |

## Soal 3: Arsitektur threading

Pertanyaan: kenapa `background_announcer()` harus di thread terpisah? Apa yang terjadi kalau dijalankan di main loop?

| Bahan | Cari di kode | Arah |
|---|---|---|
| Pembuatan thread | `threading.Thread(target=background_announcer, ...)` | Apa arti `daemon=True`? |
| Sifat `recvfrom()` | Loop utama | Sifat blocking: apa yang terjadi pada pengumuman kalau tidak ada client yang mengirim pesan? |
| Percobaan | Bayangkan `time.sleep(5)` ada di dalam loop utama | Apa yang terjadi pada balasan ACK selama server tidur? Kamu bisa mencobanya dengan memindahkan kode sementara |

## Soal 4: Simulasi paket hilang (unreliability)

Pertanyaan: kalau client dimatikan paksa, apakah server UDP langsung tahu? Bandingkan dengan TCP.

| Bahan | Cari di kode | Arah |
|---|---|---|
| Percobaan | Skenario 5 di README | Tutup jendela terminal client 1 tanpa `exit`. Apa yang tampil di log server? |
| Bandingan TCP | Praktikum 1, skenario client mati | Di TCP, apa yang diterima `recv()` server? Kenapa TCP tahu dan UDP tidak? |
| Dampak | Log announcer | Apakah pengumuman masih dikirim ke client yang sudah mati? Apa dampaknya untuk server? |
| Solusi | Soal 5 | Heartbeat adalah cara yang dibuat sendiri oleh aplikasi untuk menutup kekurangan ini |

## Soal 5: Heartbeat dan timeout

Pertanyaan: hapus client dari `known_clients` kalau diam lebih dari 30 detik. Tuliskan potongan kode atau algoritmanya.

Pegangan: lihat `udp_threaded_server_heartbeat.py`, tapi cobalah dulu sendiri. Pertanyaan pemandu:
1. Informasi apa yang perlu disimpan per client selain alamatnya? (jawabannya mengubah tipe data `known_clients`)
2. Di mana waktu itu diperbarui, dan di thread mana?
3. Siapa yang menghapus client kadaluarsa? Perlu thread baru atau cukup bagian yang sudah ada?
4. Kenapa pencarian client kadaluarsa dan penghapusannya harus dalam satu blok terkunci?
5. Kenapa memakai `time.monotonic()` dan bukan `time.time()`?

---

## Tabel hasil uji (isi sendiri dari percobaanmu)

| Skenario | Yang kamu lihat di server | Yang kamu lihat di client | Sesuai harapan? |
|---|---|---|---|
| Client pertama kirim pesan | | | |
| Client kedua bergabung | | | |
| Client 1 ditutup paksa | | | |
| Heartbeat, client diam | | | |
| Eksperimen tanpa Lock | | | |

## Lampiran

- Source code `udp_threaded_server.py`, `udp_client.py`, dan `udp_threaded_server_heartbeat.py`
- Screenshot 3 terminal (server dan dua client) yang menunjukkan ACK dan pengumuman
- Screenshot hasil `eksperimen_race_condition.py`
- Link repo
