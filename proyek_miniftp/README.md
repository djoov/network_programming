# Proyek Mini-FTP: logging, log_report.py, dan analisis FTP standar vs Mini-FTP

Proyek ujian Network Programming. Mini-FTP memakai **satu koneksi TCP** untuk perintah, respons, dan isi file. Server memakai satu thread per client, dilengkapi logging (konsol + file berotasi 1 MB x 3), dan `log_report.py` membaca log untuk membuat laporan.

> Catatan: kode Mini-FTP dari Sesi 7 tidak tersedia saat proyek ini dibuat, jadi Mini-FTP ditulis ulang mengikuti ciri yang disebut soal (satu koneksi, LIST, GET). Semua rujukan baris di laporan mengacu pada kode di folder ini.

## Isi folder

| File | Fungsi |
|---|---|
| `mini_ftp_server.py` | Server Mini-FTP + logging (`setup_logging`, `RotatingFileHandler`) |
| `mini_ftp_client.py` | Client interaktif (`help`, `ls`, `get`, `put`, `quit`) |
| `log_report.py` | Laporan dari log: jumlah sesi, top 5 unduhan, total byte, daftar error |
| `uji_otomatis.py` | Pengujian otomatis (26 pemeriksaan, `--rotasi` untuk uji rotasi log) |
| `demo_skenario.py` | Menjalankan client asli untuk membuat contoh log di `contoh_log/` |
| `eksperimen_framing.py` | Percobaan tiga kesalahan framing (bahan Bagian 4.4 laporan) |
| `buat_file_uji.py` | Membuat file besar untuk uji pembatalan transfer |
| `buat_diagram_ftp.py`, `buat_diagram_mini.py` | Pembuat diagram di `diagram/` |
| `server_files/` | Folder file yang dilayani server |
| `contoh_log/` | Contoh log, konsol, transkrip client, hasil `log_report.py`, hasil uji |
| `diagram/` | 4 diagram urutan FTP standar + 3 diagram tambahan |
| `Laporan_Analisis_MiniFTP.docx` | Laporan analisis |

## Cara menjalankan

Butuh Python 3.10 atau lebih baru, tanpa library tambahan. Buka dua terminal di folder ini.

```
# Terminal 1
python mini_ftp_server.py

# Terminal 2
python mini_ftp_client.py
miniftp> help
miniftp> ls
miniftp> get halo.txt
miniftp> put namafile.txt
miniftp> quit
```

Log ditulis ke `logs/mini_ftp.log` (dibuat otomatis) dan tampil juga di konsol server. Setelah ada aktivitas:

```
python log_report.py
```

Opsi: `--host`, `--port`, `--root`, `--log` pada server; `--host`, `--port`, `--unduhan` pada client.

## Protokol singkat

Client mengirim satu baris perintah. Server membalas satu baris header lalu isi:

```
OK <N> <pesan>\n  + N byte isi     (N boleh 0)
ERR <kode> <pesan>\n               (tanpa isi)
```

Perintah: `HELP`, `LIST`, `GET <file>`, `PUT <file> <ukuran>`, `QUIT`. Kode error: 400 (salah perintah), 403 (nama file tidak diizinkan), 404 (tidak ada), 413 (terlalu besar), 500 (error server).

## Pengujian

```
python uji_otomatis.py --rotasi
python demo_skenario.py
python eksperimen_framing.py
```

Diuji di Linux (Python 3.13, loopback): 26 dari 26 pemeriksaan lulus. **Belum diuji di Windows.**

## Uji pembatalan transfer

```
python buat_file_uji.py 50
python mini_ftp_server.py
python mini_ftp_client.py
miniftp> get besar_50mb.bin --batal 512
python log_report.py
```

`--batal 512` mensimulasikan Ctrl+C setelah 512 KB. Client menutup koneksi dan membuat sesi baru. Server mencatat `TRANSFER_FAIL`.

## Tangkapan layar

Folder `tangkapan_layar/` berisi tangkapan layar terminal Linux dari eksekusi asli: (A) koneksi client ke server, (B) `help` dan `ls`, (C) `get` file, (D) konsol server, (E) isi `logs/mini_ftp.log`, (F) hasil `python3 log_report.py`, (G) pembatalan unduhan. Semuanya sudah ditempel di Bagian 5.4 laporan. Kalau dosen meminta bukti dari Windows, ulangi perintah yang sama dengan `python` sebagai pengganti `python3`.

## Keterbatasan

Tidak ada autentikasi dan enkripsi, jumlah client tidak dibatasi, hanya satu folder tanpa subfolder, nama file tanpa spasi.
