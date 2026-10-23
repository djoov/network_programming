# Praktikum 1: TCP Client-Server Sederhana

Mata kuliah Network Programming. Dua program Python (hanya library standar) yang berkomunikasi lewat TCP: client mengirim pesan, server membalas.

## Isi folder

| File | Fungsi |
|---|---|
| `server.py` | Mendengarkan koneksi di sebuah port, menerima pesan, membalas |
| `client.py` | Terhubung ke server, mengirim pesan dari keyboard, mencetak balasan |
| `catatan_laporan.md` | Kerangka isi laporan, dipetakan ke poin-poin dari slide sesi 2 |

## Arsitektur

```
Client                                   Server
------                                   ------
socket()                                 socket()
                                         bind(ip, port)
                                         listen()
connect(ip, port)  ---- handshake --->   accept()   (menunggu di sini)
sendall("halo")    ---- pesan ------->   recv()
recv()             <--- balasan ------   sendall("Server menerima: halo")
close()            ---- FIN -------->    recv() -> b""  (tanda client selesai)
```

## Cara menjalankan

Butuh Python 3.10 atau lebih baru. Buka dua terminal di folder ini.

Terminal 1:
```
python server.py
```

Terminal 2:
```
python client.py
```

Ketik pesan lalu Enter. Ketik `exit` untuk keluar. Server tetap hidup dan siap menerima client berikutnya.

IP dan port bisa diganti:
```
python server.py --host 127.0.0.1 --port 6000
python client.py --host 127.0.0.1 --port 6000
```

Contoh output client:
```
Terhubung ke 127.0.0.1:5000
Pesan (ketik 'exit' untuk keluar): halo server
Balasan: Server menerima: halo server
```

## Skenario pengujian

Semua skenario di bawah sudah diuji, hasil yang diharapkan ada di kolom kanan.

| # | Skenario | Cara | Hasil yang diharapkan |
|---|---|---|---|
| 1 | Normal | Kirim beberapa pesan, lalu `exit` | Setiap pesan dibalas, server mencatat "menutup koneksi" |
| 2 | Pesan kosong | Tekan Enter tanpa mengetik | Client menolak, tidak ada yang dikirim |
| 3 | Server mati | Jalankan client tanpa server | "Gagal terhubung ... server belum jalan atau port salah" |
| 4 | Port salah | `python client.py --port 9999` | Pesan yang sama dengan skenario 3 |
| 5 | Host salah | `python client.py --host salah.invalid` | "Alamat ... tidak dikenali" |
| 6 | Port bentrok | Jalankan dua server di port yang sama | "Gagal bind ... Address already in use" |
| 7 | Client berpindah | Client 1 `exit`, lalu jalankan client 2 | Server melayani client 2 tanpa restart |
| 8 | Client mati mendadak | Tutup jendela terminal client (jangan ketik `exit`) | Server mencatat terputus mendadak, atau koneksi ditutup. Hasilnya bisa berbeda antar OS, catat apa yang kamu lihat |
| 9 | Server mati saat client aktif | Ctrl+C di server, lalu kirim pesan dari client | Client menampilkan koneksi terputus atau server menutup koneksi |
| 10 | Pesan lebih dari 1024 byte | Tempel teks yang sangat panjang di client | Server membacanya dalam beberapa potongan |

## Kenapa kodenya begini

- **`with socket...` dan `with conn`**: socket otomatis ditutup walau terjadi error, jadi tidak ada yang bocor.
- **`if not data`**: `recv()` yang mengembalikan `b""` adalah satu-satunya tanda client menutup koneksi. Tanpa ini server berputar tanpa henti.
- **`SO_REUSEADDR`**: supaya server bisa di-restart langsung tanpa error "Address already in use" akibat status TIME_WAIT.
- **`sendall()` bukan `send()`**: `send()` boleh mengirim sebagian data saja, `sendall()` mengulang sampai semua terkirim.
- **`timeout` di client**: supaya client tidak menunggu selamanya kalau server diam.
- **`except ConnectionError`**: satu kelas induk yang menangkap beberapa error koneksi sekaligus (reset, broken pipe, dst).

## Keterbatasan yang disengaja

Server ini melayani satu client dalam satu waktu. Selama server sibuk dengan client 1, client 2 hanya menunggu di antrean `listen()` (backlog). Ini sengaja dibiarkan supaya perilaku `accept()` yang blocking bisa diamati langsung, dan menjadi alasan kenapa praktikum multi client butuh thread.

TCP juga tidak menjaga batas pesan. Satu `recv()` bisa mendapat potongan pesan atau gabungan dua pesan. Program ini aman karena pesannya pendek dan dikirim satu per satu, tapi untuk protokol yang serius perlu aturan batas pesan (misalnya diakhiri newline atau diawali panjang pesan).

## Kalau nanti ingin dikembangkan

- Message framing: pesan diakhiri `\n`, atau diawali 4 byte panjang pesan.
- Banyak client sekaligus dengan `threading` (praktikum multi client).
- Library `logging` sebagai pengganti `print` untuk log.

## Catatan Windows

Kalau Ctrl+C tidak langsung menghentikan server saat sedang menunggu di `accept()`, itu perilaku Windows. Tekan Ctrl+Break, atau sambungkan satu client lalu tutup. Firewall Windows mungkin menampilkan popup saat server pertama kali jalan, pilih Allow.
