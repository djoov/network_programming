# Catatan Laporan Praktikum 1

Ini kerangka, bukan jawaban jadi. Kolom "Cari di kode" menunjuk bagian program yang jadi bahan penjelasanmu, dan "Arah" memberi petunjuk apa yang perlu dibahas. Jawaban ditulis dengan kata-katamu sendiri supaya kamu bisa menjelaskannya saat ditanya dosen. Kalau ada poin yang belum jelas, tanyakan ke mentor sebelum menulis.

Syarat dari dosen: sertakan source code lengkap (lampiran atau link repo). Laporan tanpa kode tidak dinilai.

---

## A. Analisis setiap kode

### server.py
Untuk tiap bagian, jelaskan fungsinya, kenapa diperlukan, dan apa yang terjadi kalau dihapus.

| Bagian | Cari di kode |
|---|---|
| Konstanta `BUFFER_SIZE`, `BACKLOG` | atas file |
| `log()` | fungsi `log` |
| Pembuatan, bind, listen | `main()` |
| Loop menunggu client | `while True` di `main()` |
| Pelayanan satu client | fungsi `layani_client` |
| Penanganan error | blok `try/except` |

### client.py
| Bagian | Cari di kode |
|---|---|
| Argumen host dan port | `argparse` di `main()` |
| Koneksi | `s.connect(...)` |
| Loop kirim dan terima | `while True` di `main()` |
| Penanganan error | rangkaian `except` |

---

## B. Analisis konseptual jaringan dan protokol

| Poin dari slide | Arah |
|---|---|
| Posisi TCP di model OSI dan TCP/IP | Sebut nomor layer di masing-masing model. Apa tugas layer di atasnya (aplikasi: program kamu) dan di bawahnya (IP) terhadap data yang dikirim socket? Lihat materi sesi 1, slide 12 dan 13 |
| TCP vs UDP, kenapa TCP di sini | Bandingkan reliability, ordering, connection-oriented. Praktikum UDP (PDF Praktikum 3) bisa jadi pembanding |
| Three-way handshake | Tulis urutan SYN, SYN-ACK, ACK. Lalu jawab: handshake dikerjakan oleh siapa, dan di titik mana relatif terhadap `connect()` dan `accept()`? Slide meminta jawaban di level OS, bukan di baris Python |

---

## C. Inisiasi socket server dan client

| Poin dari slide | Cari di kode | Arah |
|---|---|---|
| Makna `AF_INET` dan `SOCK_STREAM` | `socket.socket(...)` | Satu parameter soal jenis alamat, satu soal jenis layanan |
| Binding: kenapa server perlu, client tidak | `server.bind`, bandingkan dengan client | Siapa yang harus bisa ditemukan oleh pihak lain? Port client dipilih siapa? |
| `listen()` dan backlog | `server.listen(BACKLOG)` | Antrean apa yang dimaksud? Apa yang terjadi saat antrean penuh? |
| `accept()` blocking | `server.accept()` | Dampaknya kalau ada banyak client. Bisa kamu buktikan dengan percobaan: jalankan 2 client bersamaan |

---

## D. Mekanisme transfer data

| Poin dari slide | Cari di kode | Arah |
|---|---|---|
| `send()`/`sendall()` vs `recv()` | `conn.sendall`, `conn.recv` | Apa yang dijamin dan tidak dijamin `send()`? |
| Kenapa `recv(1024)` ada angka | `BUFFER_SIZE` | Percobaan 10 di README: apa yang terjadi pada pesan panjang? |
| encode/decode | `.encode("utf-8")`, `.decode(...)` | Tulis jawabanmu soal bytes vs string. Perhatikan juga fungsi `errors="replace"` |
| Batas pesan (message boundary) | Seluruh alur kirim dan terima | Coba kirim dua pesan sangat cepat lewat script kecil lalu amati berapa kali `recv()` terpanggil. Hubungkan ke desain protokol di atas TCP |

---

## E. Penutupan koneksi

| Poin dari slide | Cari di kode | Arah |
|---|---|---|
| Four-way handshake (FIN, ACK, FIN, ACK) | `with` dan `close()` | Siapa mengirim FIN lebih dulu pada skenario `exit`? |
| Keluar dari blok `with` | `with conn`, `with socket...` | Apa yang dipanggil otomatis? |
| Koneksi tidak ditutup benar | `SO_REUSEADDR` di server | Resource leak dan status TIME_WAIT |
| **Uji: client di-kill** | Skenario 8 di README | Lihat tabel hasil di bawah |

### Hasil uji client di-kill (isi sendiri dari percobaanmu)

Slide meminta: apa yang diterima `recv()` di server jika client mati mendadak? Jalankan skenario 8 di komputermu, lalu catat:

| Cara mematikan client | OS | Yang tercetak di log server | Artinya apa |
|---|---|---|---|
| Ketik `exit` (normal) | | | |
| Tutup jendela terminal | | | |
| Kill proses lewat Task Manager | | | |

Catatan: hasilnya bisa berbeda antar OS dan cara mematikan. Jelaskan perbedaan yang kamu temukan, itu poin bagus untuk laporan.

---

## F. Lampiran

- Source code `server.py` dan `client.py`
- Screenshot terminal server dan client untuk skenario normal
- Screenshot hasil uji client di-kill
- Link repo (repo git di folder ini sudah punya remote)
