# Praktikum Network Programming 1

## File
- server_basic.py dan client_basic.py: versi awal sesuai instruksi praktikum.
- server_json.py dan client_json.py: versi pengembangan dengan pengiriman JSON.

## Menjalankan versi dasar
1. Buka dua jendela Python IDLE.
2. Buka `server_basic.py` di jendela pertama lalu tekan F5/Run Module.
3. Buka `client_basic.py` di jendela kedua lalu tekan F5/Run Module.
4. Ketik pesan pada client.
5. Server membalas tanggal dan waktu.
6. Ketik `exit` untuk menutup koneksi.

## Menjalankan versi JSON
1. Pastikan server versi dasar sudah dihentikan.
2. Jalankan `server_json.py` pada IDLE pertama.
3. Jalankan `client_json.py` pada IDLE kedua.
4. Isi nama dan pesan.
5. Client mengirim object JSON sebagai string yang di-encode menjadi bytes.
6. Server melakukan `json.loads()`, memproses data, lalu mengirim response JSON.
7. Client melakukan `json.loads()` untuk mengubah response kembali menjadi object Python.

## Catatan
HOST `127.0.0.1` berarti server dan client dijalankan pada komputer yang sama (localhost).
PORT `5000` dipakai sebagai pintu komunikasi aplikasi.
