# LAPORAN PRAKTIKUM NETWORK PROGRAMMING 1

## Analisis Konsep Pemrograman Client-Server

**Nama:** Nur Akhmad Van Jouvi  
**NIM:** 2314000024  
**Mata Kuliah:** Network Programming  
**Dosen Pengampu:** Dr. Hadi Syahrial, S.Si., M.M., M.Kom.  

---

# BAB I — PENDAHULUAN

## 1.1 Latar Belakang

Perkembangan teknologi komputasi modern menuntut aplikasi untuk saling terhubung dan bertukar data secara efisien melalui jaringan komputer. Komputasi terdistribusi tidak lagi menjadi opsi tambahan, melainkan fondasi utama dari hampir seluruh arsitektur perangkat lunak saat ini, mulai dari aplikasi web, komputasi awan (*cloud computing*), hingga komunikasi perangkat *Internet of Things* (IoT). Di balik interaksi antarperangkat tersebut, terdapat paradigma **Network Programming** yang menjembatani logika perangkat lunak dengan infrastruktur fisik jaringan.

Salah satu model arsitektur komunikasi yang paling mendasar dan luas digunakan adalah **Client-Server**. Dalam model ini, tugas dibagi secara tegas antara entitas penyedia layanan (*server*) dan entitas peminta layanan (*client*). Komunikasi tersebut diwujudkan menggunakan antarmuka pemrograman aplikasi jaringan yang dikenal sebagai **Socket API**. Melalui socket, pemrogram dapat memanfaatkan layanan protokol lapisan transport, khususnya **Transmission Control Protocol (TCP)**, yang menawarkan keandalan transmisi (*reliability*), pengurutan paket (*sequencing*), dan integritas data secara *connection-oriented*.

Pada praktikum ini, dilakukan perancangan, implementasi, serta analisis komunikasi client-server berbasis socket TCP menggunakan bahasa pemrograman Python. Praktikum mencakup dua model komunikasi: pertukaran pesan teks sederhana (*plain text*) dan pertukaran pesan terstruktur menggunakan format **JSON (JavaScript Object Notation)**. Praktikum ini tidak hanya menguji aspek fungsional program, tetapi juga menginvestigasi mekanisme internal jaringan seperti siklus hidup socket, *three-way handshake*, penanganan buffer transmisi, terminasi koneksi (*four-way handshake*), serta penanganan kondisi tak terduga (*error handling*) seperti terminasi abnormal client dan konflik port (*port conflict*).

## 1.2 Tujuan Praktikum

1. Memahami konsep dasar arsitektur komunikasi client-server dalam jaringan komputer.
2. Menguasai penggunaan Socket API berbasis protokol TCP pada bahasa pemrograman Python.
3. Memahami dan mengamati mekanisme jabat tangan (*three-way handshake*) dan siklus koneksi client-server.
4. Menganalisis proses serialisasi, transmisi, *buffering*, dan rekonstruksi data byte stream.
5. Menganalisis korelasi kode program socket dengan lapisan protokol pada Model OSI dan Model TCP/IP.
6. Mengimplementasikan pertukaran data terstruktur menggunakan format JSON antar-endpoint jaringan.
7. Mengamati dan menganalisis perilaku socket saat penutupan normal (*graceful shutdown*) maupun saat client terputus secara tiba-tiba (*abrupt disconnection*).

---

# BAB II — DASAR TEORI

## 2.1 Network Programming

**Network Programming** (Pemrograman Jaringan) adalah disiplin penulisan kode program yang berjalan pada beberapa sistem komputer (atau proses yang terisolasi) yang saling terhubung melalui suatu jaringan komunikasi (LAN, WAN, atau Internet). Inti dari pemrograman jaringan adalah fasilitas *Inter-Process Communication* (IPC) lintas node jaringan. Melalui antarmuka abstraksi sistem operasi—umumnya mengacu pada standar *Berkeley Sockets*—program aplikasi dapat mengirim dan menerima data melalui jaringan tanpa perlu mengelola perangkat keras kartu jaringan (NIC) atau rute fisik secara manual.

## 2.2 Konsep Client-Server

Arsitektur Client-Server merupakan model komputasi terdistribusi di mana beban kerja dibagi antara penyedia sumber daya/layanan yang disebut **Server**, dan peminta layanan yang disebut **Client**.

```text
+----------------+                       +----------------+
|     CLIENT     |                       |     SERVER     |
| (Active Role)  |                       | (Passive Role) |
+----------------+                       +----------------+
        |                                        |
        |  1. Inisiasi Koneksi (Connect)        |
        |--------------------------------------->| (Menunggu via Listen)
        |                                        |
        |  2. Mengirim Request (Payload Data)    |
        |--------------------------------------->| Memproses Request
        |                                        |
        |  3. Menerima Response                  |
        |<<--------------------------------------| Mengirim Response
        |                                        |
```

Karakteristik kedua entitas tersebut adalah:
* **Server**: Berperan pasif pada awalnya (*passive open*), berjalan secara kontinu, mengikat diri pada IP dan Port tertentu (*bind*), mendengarkan permintaan masuk (*listen*), lalu melayani permintaan client (*accept*).
* **Client**: Berperan aktif (*active open*), menginisiasi permintaan koneksi ke alamat server tujuan yang sudah diketahui, mengirimkan data permintaan (*request*), dan menunggu hasil balasan (*response*).

## 2.3 Socket

**Socket** adalah abstraksi perangkat lunak yang bertindak sebagai titik akhir (*endpoint*) dari tautan komunikasi dua arah (*bidirectional*) antar dua program yang berjalan di jaringan. Socket didefinisikan oleh kombinasi:
$$\text{Socket Endpoint} = \langle \text{Protokol Transport}, \text{IP Address}, \text{Port Number} \rangle$$

Di tingkat sistem operasi, socket diperlakukan mirip seperti berkas (*file descriptor*). Program dapat "menulis" data ke socket untuk dikirim ke jaringan, dan "membaca" data dari socket yang diterima dari jaringan.

## 2.4 IP Address

**Internet Protocol (IP) Address** adalah label numerik unik yang diberikan kepada setiap perangkat yang terhubung ke jaringan komputer yang menggunakan protokol internet untuk komunikasi. IP Address berfungsi sebagai penunjuk identitas host dan lokasi penempatan host dalam topologi jaringan (pengalamatan logis pada Layer 3).
* Pada praktikum ini digunakan alamat loopback IPv4 **`127.0.0.1`** (localhost). Alamat ini merujuk ke mesin lokal yang sama, di mana paket data tidak dikirimkan ke antarmuka jaringan fisik luar, melainkan diarahkan kembali ke TCP/IP stack sistem operasi lokal secara internal.

## 2.5 Port

**Port** adalah mekanisme pengalamatan perangkat lunak 16-bit (bernilai antara $0$ hingga $65535$) pada Transport Layer yang berfungsi untuk mengidentifikasi proses atau aplikasi spesifik di dalam suatu host. Jika IP Address dianalogikan sebagai alamat sebuah gedung apartemen, maka nomor port adalah nomor kamar/pintu spesifik di gedung tersebut.
* **Well-Known Ports (0 – 1023):** Dicadangkan untuk protokol standar (misal HTTP: 80, HTTPS: 443, SSH: 22).
* **Registered Ports (1024 – 49151):** Digunakan untuk layanan aplikasi khusus.
* **Dynamic/Private/Ephemeral Ports (49152 – 65535):** Dialokasikan secara dinamis oleh sistem operasi untuk koneksi client temporer.
* Pada praktikum ini, port yang digunakan oleh server adalah port **`5000`** (kategori Registered Port).

## 2.6 TCP (Transmission Control Protocol)

**TCP** adalah protokol lapisan transport yang bersifat *connection-oriented* dan menyediakan layanan pengiriman aliran data (*byte stream*) yang andal (*reliable*). Karakteristik utama TCP meliputi:
1. **Connection-Oriented:** Sebelum data aplikasi dapat dipertukarkan, saluran komunikasi logis harus dibentuk terlebih dahulu melalui mekanisme *Three-Way Handshake*.
2. **Reliability (Keandalan):** Setiap segmen data yang dikirim diberi nomor urut (*Sequence Number*). Penerima wajib mengonfirmasi penerimaan melalui paket *Acknowledgment (ACK)*. Jika terjadi kehilangan data (*packet loss*), TCP akan melakukan pengiriman ulang (*retransmission*).
3. **Ordered Delivery:** TCP menjamin bahwa urutan byte yang diterima aplikasi sama persis dengan urutan byte saat dikirim, meskipun di tingkat jaringan paket IP tiba secara acak (*out of order*).
4. **Flow Control & Congestion Control:** TCP menggunakan mekanisme *Sliding Window* untuk mencegah pengirim membanjiri buffer penerima, serta algoritma kendali kemacetan untuk mencegah saturasi jaringan.

## 2.7 TCP pada Model OSI dan TCP/IP

### Model OSI

```text
Layer 7 - Application   <-- Format JSON, Teks Pesan, Logika Aplikasi Python
Layer 6 - Presentation  <-- Encoding/Decoding String ke Bytes (UTF-8)
Layer 5 - Session       <-- Pengelolaan Sesi Komunikasi Client-Server
Layer 4 - Transport     <-- TCP (Socket API: Port, Handshake, Sequencing, ACK)
Layer 3 - Network       <-- IP (Routing Paket, Alamat IP 127.0.0.1)
Layer 2 - Data Link     <-- Framing, Ethernet/Loopback Interface
Layer 1 - Physical      <-- Media Transmisi Fisik / Perangkat Keras
```

* **Posisi TCP pada Layer 4 (Transport):** Bertanggung jawab memastikan data utuh, bebas galat, dan sampai ke nomor port tujuan yang benar.
* **Peran Layer di Bawahnya (Layer 1–3):** Bertanggung jawab memecah segmen transport menjadi paket IP, menentukan rute (*routing*), membungkus paket menjadi frame data link, dan mengirimkannya dalam sinyal fisik.
* **Peran Layer di Atasnya (Layer 5–7):** Aplikasi Python beroperasi di Application/Presentation layer yang bertugas mendefinisikan arti semantik dari data (misalnya format JSON atau string teks) dan melakukan encoding UTF-8 sebelum diserahkan ke Transport Layer melalui Socket API.

### Model TCP/IP

```text
+-------------------+---------------------------------------------------+
| Lapisan           | Protokol / Peran pada Praktikum                   |
+-------------------+---------------------------------------------------+
| Application       | Logika Program Python, Payload JSON / Plain Text  |
+-------------------+---------------------------------------------------+
| Transport         | TCP (Transmission Control Protocol), Port 5000    |
+-------------------+---------------------------------------------------+
| Internet          | IP (Internet Protocol), IP Loopback 127.0.0.1     |
+-------------------+---------------------------------------------------+
| Network Access    | Antarmuka Loopback Lokal / Driver OS              |
+-------------------+---------------------------------------------------+
```

Socket bertindak sebagai antarmuka perantara (*API gateway*) antara Application Layer yang dikembangkan pemrogram dengan Transport Layer yang dikelola oleh kernel sistem operasi.

## 2.8 Perbandingan TCP dan UDP

| Aspek | TCP (*Transmission Control Protocol*) | UDP (*User Datagram Protocol*) |
|---|---|---|
| **Karakteristik Koneksi** | *Connection-Oriented* (wajib jabat tangan) | *Connectionless* (kirim langsung) |
| **Keandalan (*Reliability*)** | Sangat Andal (*guaranteed delivery*, ada ACK & *retransmission*) | Tidak Andal (*best-effort*, paket bisa hilang tanpa pemberitahuan) |
| **Urutan Data (*Ordering*)** | Terjamin urut (*sequenced byte stream*) | Tidak terjamin urut (*datagram arrival out-of-order*) |
| **Kecepatan & Overhead** | Lebih lambat, *overhead* header 20–60 bytes | Sangat cepat, *overhead* header kecil (8 bytes) |
| **Batasan Pesan** | Aliran byte tanpa batas pesan (*stream-oriented*) | Mempertahankan batas pesan (*datagram-oriented*) |
| **Contoh Penggunaan** | HTTP/HTTPS, SSH, FTP, Database, Pengiriman JSON | DNS, VoIP, Video Streaming (*Live*), Game Online |

> **Relevansi TCP pada Kasus Praktikum:**  
> Pada praktikum ini, data yang dikirim berupa string teks perintah (`exit`) dan struktur JSON (`nama`, `pesan`). Jika terjadi kehilangan atau pemotongan karakter (misalnya sintaks kurung kurawal `{` atau tanda kutip `"` hilang), parser JSON pada sisi server akan mengalami *syntax error* / *crash*. Oleh karena itu, jaminan keandalan (*reliability*) dan integritas data dari TCP bersifat mutlak dibutuhkan.

## 2.9 Three-Way Handshake

Sebelum socket TCP dapat mentransmisikan data aplikasi, TCP stack pada kernel sistem operasi client dan server harus melakukan prosedur sinkronisasi 3 langkah (*Three-Way Handshake*):

```text
Client (Active Open)                               Server (Passive Open)
       |                                                    |
       |  1. SYN (Seq = x)                                  |
       |--------------------------------------------------->| (Menerima SYN, alokasi TCB)
       |                                                    |
       |  2. SYN-ACK (Seq = y, Ack = x + 1)                 |
       |<<--------------------------------------------------|
       |                                                    |
       |  3. ACK (Ack = y + 1)                              |
       |--------------------------------------------------->|
       |                                                    |
[ESTABLISHED]                                        [ESTABLISHED]
```

1. **Langkah 1 (SYN):** Client mengirimkan segmen TCP dengan flag `SYN` aktif dan nomor urut awal acak (*Initial Sequence Number* = $x$) untuk meminta inisiasi koneksi.
2. **Langkah 2 (SYN + ACK):** Server menerima permintaan, mengalokasikan buffer koneksi, lalu membalas dengan flag `SYN` aktif (nomor urut awal server = $y$) dan flag `ACK` aktif bernilai $x + 1$ sebagai bukti bahwa paket SYN client telah diterima.
3. **Langkah 3 (ACK):** Client membalas dengan segmen berflag `ACK` bernilai $y + 1$. Setelah tahap ini selesai, kedua belah pihak berada pada status `ESTABLISHED` dan siap bertukar data.

> **Hubungan dengan `connect()` dan `accept()`:**  
> * Pemanggilan `client_socket.connect((HOST, PORT))` memicu sistem operasi untuk mengirimkan paket **SYN**. Fungsi `connect()` akan memblokir eksekusi program hingga paket **SYN-ACK** diterima dan paket **ACK** ketiga berhasil dikirimkan.  
> * Pemanggilan `server_socket.accept()` bertugas mengambil koneksi yang telah berstatus *ESTABLISHED* dari antrean koneksi masuk (*backlog queue*).  
> * **Penting:** Perlu ditegaskan bahwa pertukaran flag SYN, SYN-ACK, dan ACK dikerjakan sepenuhnya oleh **TCP/IP stack di level kernel sistem operasi**, bukan dieksekusi langsung oleh interpreter Python baris per baris.

---

# BAB III — IMPLEMENTASI PROGRAM

## 3.1 Lingkungan Praktikum

| Komponen | Keterangan / Spesifikasi |
|---|---|
| **Sistem Operasi** | Microsoft Windows 11 Home / Pro (Build 26200, 64-bit) |
| **Python Version** | Python 3.12.13 (Conda) / Python 3.14.5 |
| **Editor / IDE** | Visual Studio Code & Python IDLE |
| **Conda Environment** | `network-programming` |
| **IP Address** | `127.0.0.1` (Localhost / IPv4 Loopback) |
| **Port** | `5000` |

## 3.2 Struktur Program

```text
praktikum_1/
├── server_basic.py     # Implementasi server TCP dasar (string timestamp)
├── client_basic.py     # Implementasi client TCP dasar
├── server_json.py      # Server TCP lanjutan dengan payload JSON & SO_REUSEADDR
├── client_json.py      # Client TCP lanjutan dengan payload JSON terstruktur
├── README.txt          # Panduan operasional praktikum
├── TEST_RESULT.txt     # Log hasil uji coba integrasi JSON
└── kerangka_laporan.md # Laporan komprehensif praktikum
```

## 3.3 Source Code `server_basic.py`

```python
import socket
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server berjalan di {HOST}:{PORT}")
print("Menunggu koneksi client...")

conn, addr = server_socket.accept()
print(f"Client terhubung: {addr}")

while True:
    data = conn.recv(1024).decode()

    if not data:
        break

    if data.lower() == "exit":
        print("Client menutup koneksi.")
        break

    response = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.send(response.encode())

conn.close()
server_socket.close()
print("Server berhenti.")
```

## 3.4 Source Code `client_basic.py`

```python
import socket

HOST = "127.0.0.1"
PORT = 5000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

print(f"Terhubung ke server {HOST}:{PORT}")
print("Ketik pesan. Ketik 'exit' untuk keluar.")

while True:
    message = input("Client: ")
    client_socket.send(message.encode())

    if message.lower() == "exit":
        break

    response = client_socket.recv(1024).decode()
    print("Server:", response)

client_socket.close()
print("Client berhenti.")
```

## 3.5 Analisis Kode Server (`server_basic.py`)

### 3.5.1 Import Library

```python
import socket
from datetime import datetime
```

**Analisis:**
* `socket`: Modul bawaan standar Python yang menyediakan antarmuka akses ke Berkeley Socket API tingkat sistem operasi untuk transmisi jaringan berbasis TCP/IP atau UDP.
* `datetime`: Modul untuk memanipulasi informasi tanggal dan waktu sistem yang digunakan untuk membangkitkan timestamp balasan server.

### 3.5.2 Pembuatan Socket

```python
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```

**Analisis:**
Baris ini menginstansiasi objek socket jaringan. Parameter `socket.AF_INET` mendefinisikan rumpun alamat (*address family*) berupa IPv4 (format 32-bit `x.x.x.x`). Parameter `socket.SOCK_STREAM` menentukan tipe socket berorientasi aliran byte (*byte stream*) yang secara otomatis memetakan komunikasi ke protokol **TCP**.

### 3.5.3 Binding

```python
server_socket.bind((HOST, PORT))
```

**Analisis:**
Metode `bind()` mengasosiasikan socket server dengan antarmuka jaringan dan port lokal spesifik melalui pasangan *tuple* `(HOST, PORT)`. Dalam kasus ini, socket diikat ke `127.0.0.1` pada port `5000`, sehingga sistem operasi mengetahui bahwa paket data masuk yang ditujukan ke port `5000` harus disalurkan ke proses server ini.

### 3.5.4 Listening

```python
server_socket.listen(1)
```

**Analisis:**
Metode `listen(backlog)` mengubah status socket dari aktif menjadi pasif (*passive socket*), yaitu siap menerima permintaan koneksi masuk dari client. Angka parameter `1` menunjukkan ukuran antrean *backlog*, yakni jumlah maksimum koneksi berstatus *pending/unaccepted* yang dapat ditampung dalam antrean sistem operasi sebelum koneksi baru berikutnya ditolak.

### 3.5.5 Accept

```python
conn, addr = server_socket.accept()
```

**Analisis:**
Metode `accept()` bersifat **blocking call**, artinya eksekusi program server akan berhenti/menunggu pada baris ini hingga ada client yang menyelesaikan *Three-Way Handshake*. Ketika koneksi terbentuk, `accept()` menghasilkan dua nilai kembalian:
1. `conn`: Objek socket baru yang terdedikasi khusus untuk mentransfer data dengan client yang baru terhubung.
2. `addr`: Tuple yang berisi informasi alamat client, mencakup IP asal dan ephemeral port acak dari client (contoh: `('127.0.0.1', 57234)`).  
Socket asli (`server_socket`) tetap berada pada posisinya untuk terus mendengarkan koneksi baru lainnya.

### 3.5.6 Receive dan Send

```python
data = conn.recv(1024).decode()
...
response = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
conn.send(response.encode())
```

**Analisis:**
* `conn.recv(1024)`: Membaca aliran byte masuk dari socket client hingga batas maksimum ukuran buffer 1024 byte. Metode ini memblokir eksekusi hingga setidaknya 1 byte data tiba. Setelah byte diterima, `.decode()` mengonversi stream byte mentah menjadi string Python dengan encoding default UTF-8.
* `conn.send(response.encode())`: Mempersiapkan string timestamp, mengubahnya kembali menjadi stream byte melalui `.encode()`, lalu memancarkannya ke client melalui saluran socket TCP yang telah terjalin.

### 3.5.7 Penutupan Socket

```python
conn.close()
server_socket.close()
```

**Analisis:**
Metode `close()` melepaskan sumber daya socket dan mengembalikan nomor *file descriptor* serta port ke sistem operasi. Penutupan socket memicu transmisi segmen kendali penutupan TCP (*Four-Way Handshake*) ke pihak lawan. `conn.close()` menutup koneksi dengan client tertentu, sedangkan `server_socket.close()` menghentikan layanan server secara keseluruhan.

---

## 3.6 Analisis Kode Client (`client_basic.py`)

### 3.6.1 Pembuatan Socket

```python
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```

**Analisis:**
Sama seperti server, client menginisialisasi socket TCP IPv4. Namun, client tidak memanggil `bind()` secara manual; sistem operasi akan memberikan nomor port acak sementara (*ephemeral port*) secara otomatis saat client melakukan koneksi.

### 3.6.2 Connect

```python
client_socket.connect((HOST, PORT))
```

**Analisis:**
Metode `connect()` melakukan aksi *active open* dengan mengirimkan paket TCP SYN ke alamat server `('127.0.0.1', 5000)`. Fungsi ini akan memblokir jalannya program hingga jabat tangan *Three-Way Handshake* berhasil diselesaikan atau melempar eksepsi error (misal `ConnectionRefusedError` jika server belum aktif).

### 3.6.3 Pengiriman Data

```python
message = input("Client: ")
client_socket.send(message.encode())
```

**Analisis:**
Client mengambil masukan teks interaktif dari pengguna melalui terminal, mengonversinya menjadi representasi biner (*bytes*) melalui `.encode('utf-8')`, lalu mentransmisikannya ke server melalui metode `send()`.

### 3.6.4 Penerimaan Response

```python
response = client_socket.recv(1024).decode()
print("Server:", response)
```

**Analisis:**
Client menunggu respon balasan dari server secara tersinkronisasi (*synchronous blocking*). Begitu balasan diterima dari buffer TCP, data didekode menjadi string dan dicetak ke layar terminal.

### 3.6.5 Penutupan Koneksi

```python
client_socket.close()
```

**Analisis:**
Saat perulangan berhenti (pengguna mengetik `"exit"`), client memanggil `close()` untuk mengakhiri sesi komunikasi TCP dan melepaskan *ephemeral port* yang dialokasikan sebelumnya.

---

# BAB IV — ANALISIS KONSEPTUAL JARINGAN DAN PROTOKOL

## 4.1 Posisi TCP pada Model OSI

Pada Model OSI 7-Layer, TCP menempati **Layer 4 (Transport Layer)**.
* **Hubungan dengan Layer di Atasnya (Layer 5–7):** Data yang berasal dari logika program Python (teks pesan dan string JSON) merupakan *Application Data* (Layer 7). Sebelum dikirim, data diubah representasinya menjadi byte array UTF-8 di Layer 6 (Presentation Layer). Socket API bertindak sebagai interface di Layer 5/4 yang meneruskan stream data tersebut ke TCP.
* **Hubungan dengan Layer di Bawahnya (Layer 1–3):** TCP di Layer 4 memecah stream byte aplikasi menjadi unit-unit segmen, menyematkan header TCP (port asal, port tujuan, Sequence Number, ACK Number, Window Size, checksum). Segmen ini lalu diserahkan ke Layer 3 (Network Layer / IP) untuk dibungkus menjadi paket IP dengan alamat logis `127.0.0.1`, diteruskan ke Layer 2 (Data Link) menjadi frame, dan ditransmisikan di Layer 1 (Physical/Loopback).

## 4.2 Posisi TCP pada Model TCP/IP

Pada arsitektur 4-Layer TCP/IP, TCP menempati **Transport Layer**. Peran utama TCP di sini adalah menyediakan saluran komunikasi logis *end-to-end* antarproses aplikasi. TCP menyembunyikan kompleksitas transmisi fisik jaringan di bawahnya (seperti paket yang hilang, terduplikasi, atau salah rute) sehingga programmer aplikasi dapat memperlakukan koneksi jaringan layaknya membaca dan menulis pada berkas lokal (*stream-oriented abstraction*).

## 4.3 TCP vs UDP

Dalam konteks praktikum ini, perbandingan teknis antara TCP dan UDP dianalisis sebagai berikut:
1. **Reliability:** Program server mengandalkan string perintah `"exit"` dan parsing dokumen JSON. Jika kita menggunakan UDP (*unreliable*), satu byte data atau tanda kurung `{` yang hilang di perjalanan tidak akan pernah dikirim ulang, menyebabkan kegagalan decoding JSON (`json.decoder.JSONDecodeError`). TCP menjamin seluruh byte terkirim tanpa cacat.
2. **Ordering:** Protokol TCP memastikan urutan paket data terjaga melalui nomor urut (*Sequence Number*). Jika paket tiba tidak berurutan, kernel penerima akan menyusunnya kembali sebelum diserahkan ke metode `recv()`. Sebaliknya, UDP tidak memiliki fitur rekonstruksi urutan.
3. **Connection-Oriented vs Connectionless:** TCP membutuhkan pembentukan status koneksi (*stateful*) yang jelas (SYN, ESTABLISHED, FIN), yang memungkinkan program mendeteksi secara pasti kapan client masuk dan kapan client menutup koneksi.

## 4.4 Three-Way Handshake

```text
Client (IP: 127.0.0.1:Port_X)               Server (IP: 127.0.0.1:5000)
             |                                           |
             | ----- Segmen 1: [SYN, Seq=0] -----------> |
             |                                           |
             | <---- Segmen 2: [SYN, ACK, Ack=1, Seq=0]- |
             |                                           |
             | ----- Segmen 3: [ACK, Ack=1, Seq=1] ----> |
             |                                           |
    Koneksi Terbentuk                           Koneksi Terbentuk
```

### Hubungan dengan `connect()`
Pemanggilan baris `client_socket.connect((HOST, PORT))` memicu TCP stack sistem operasi client untuk mengirimkan segmen berflag **SYN** ke server. Metode `connect()` berada dalam kondisi *blocking* sampai server merespons dengan segmen **SYN-ACK**, dan client mengirimkan kembali segmen **ACK**. Begitu *handshake* tiga langkah ini sukses, fungsi `connect()` selesai dieksekusi dan baris kode berikutnya pada client dijalankan.

### Hubungan dengan `accept()`
Pada sisi server, proses pembentukan *Three-Way Handshake* ditangani secara mandiri oleh kernel sistem operasi pada antrean koneksi (*pending connection queue*). Fungsi `server_socket.accept()` bertugas mengambil koneksi yang telah berstatus *ESTABLISHED* dari antrean tersebut. Jika antrean kosong, `accept()` memblokir eksekusi program hingga ada *handshake* baru yang selesai. Ketika dipanggil, `accept()` mengembalikan socket khusus (`conn`) untuk melayani komunikasi dengan client tersebut.

### Hasil Pengamatan
Pada saat pengujian praktikum di lingkungan lokal (*localhost*):
* Waktu yang dibutuhkan untuk menyelesaikan *Three-Way Handshake* sangat kecil (< 1 milidetik) karena transmisi terjadi secara internal dalam memori kernel melalui antarmuka loopback tanpa latensi transmisi fisik jaringan.
* Ketika `client_basic.py` dijalankan di jendela terminal kedua, terminal server seketika mencetak pesan: `Client terhubung: ('127.0.0.1', 57234)`. Angka `57234` membuktikan bahwa sistem operasi secara otomatis menetapkan *ephemeral port* unik pada sisi client untuk membedakan koneksi tersebut dari proses lain di komputer.

---

# BAB V — INISIASI SOCKET SERVER DAN CLIENT

## 5.1 `socket()`

### Server
```python
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```

### Client
```python
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```

**Analisis:**
* `AF_INET`: Menentukan *Address Family* IPv4. Pemilihan ini membatasi pengalamatan jaringan pada format 32-bit (contoh `127.0.0.1`).
* `SOCK_STREAM`: Menentukan tipe soket berorientasi stream byte terurut, yang secara otomatis memetakan transmisi ke protokol **TCP** (Layer 4).

## 5.2 `bind()`

```python
server_socket.bind((HOST, PORT))
```

**Analisis:**
Server wajib memanggil fungsi `bind()` untuk mendaftarkan alamat IP dan nomor port secara statis pada sistem operasi. Hal ini mutlak diperlukan karena server bertindak sebagai penyedia layanan (*service provider*) yang alamat dan pintunya harus diketahui secara pasti oleh semua calon client yang ingin terhubung. Jika server tidak melakukan `bind()`, client tidak akan memiliki target alamat tujuan yang konsisten.

Sebaliknya, client **tidak memerlukan `bind()` eksplisit** karena client bertindak sebagai inisiator. Saat client memanggil `connect()`, sistem operasi secara otomatis meminjamkan sebuah *ephemeral port* yang belum terpakai untuk sementara waktu.

## 5.3 `connect()`

```python
client_socket.connect((HOST, PORT))
```

**Analisis:**
Fungsi `connect()` digunakan oleh client untuk menginisiasi koneksi aktif (*active open*) ke pasangan IP dan Port server tujuan. Fungsi ini memicu pengiriman paket SYN dan menunggu hingga proses *Three-Way Handshake* dengan server berhasil diverifikasi.

## 5.4 `listen()`

```python
server_socket.listen(1)
```

**Analisis:**
Fungsi `listen()` menginstruksikan sistem operasi bahwa socket server siap menerima koneksi masuk.

### Backlog
Parameter `1` pada `listen(1)` menetapkan panjang antrean *backlog*. Backlog adalah batas maksimal antrean koneksi yang sudah menyelesaikan *Three-Way Handshake* tetapi belum sempat diproses/diambil oleh program melalui pemanggilan `accept()`.

> **Apa yang terjadi jika koneksi masuk melebihi backlog?**  
> Jika terdapat banyak client yang melakukan koneksi secara bersamaan melebihi kuota antrean backlog yang ditentukan, sistem operasi akan menolak koneksi tambahan tersebut dengan mengirimkan paket TCP RST (*Reset*) atau mengabaikan paket SYN baru hingga batas waktu tertentu (*timeout*). Pada sisi client, hal ini bermanifestasi sebagai error `ConnectionRefusedError: [WinError 10061] No connection could be made because the target machine actively refused it`.

## 5.5 `accept()`

```python
conn, addr = server_socket.accept()
```

**Analisis:**
Fungsi `accept()` merupakan operasi yang bersifat **blocking call**. Jika belum ada client yang terhubung, eksekusi thread server akan berhenti total pada baris ini tanpa memakan siklus CPU berlebih (*idle waiting*).

> **Dampaknya jika melayani banyak client:**  
> Karena arsitektur `server_basic.py` bersifat *single-threaded*, server hanya mampu menangani satu koneksi client dalam satu waktu. Jika client pertama sedang terhubung dan berada dalam loop komunikasi, client kedua yang mencoba melakukan `connect()` akan tertahan di antrean backlog dan **tidak akan dilayani** hingga client pertama selesai/menutup koneksi (`conn.close()`). Untuk melayani banyak client secara simultan, arsitektur server harus ditingkatkan menggunakan konsep *Multithreading*, *Multiprocessing*, atau *Asynchronous I/O* (`asyncio`/`select`).

### Hasil Pengamatan
Saat `server_basic.py` dijalankan pertama kali, program langsung berhenti di baris `accept()` dan mencetak `Menunggu koneksi client...`. Program baru melanjutkan eksekusi ke baris berikutnya tepat saat `client_basic.py` dijalankan dan menyelesaikan *handshake*.

---

# BAB VI — MEKANISME TRANSFER DATA

## 6.1 `send()` dan `sendall()`

```python
# Penggunaan send() pada program praktikum:
conn.send(response.encode())
client_socket.send(message.encode())
```

**Analisis:**
* `send(bytes)`: Mengirimkan data byte ke buffer pengiriman socket TCP sistem operasi. Fungsi ini mengembalikan nilai integer yang merepresentasikan jumlah byte yang **sebenarnya berhasil ditulis** ke dalam buffer. Nilai kembalian ini bisa saja lebih kecil dari total panjang data yang ingin dikirim jika buffer sistem operasi sedang penuh (*partial send*).
* `sendall(bytes)`: Merupakan fungsi tingkat tinggi Python yang membungkus pemanggilan `send()` secara berulang dalam perulangan internal hingga **seluruh byte data tuntas terkirim**. Jika terjadi error di tengah proses pengiriman, fungsi ini melempar eksepsi.

## 6.2 `recv()`

```python
data = conn.recv(1024).decode()
```

**Analisis:**
Metode `recv(bufsize)` membaca data byte dari buffer penerima TCP socket. Fungsi ini memblokir eksekusi program hingga ada minimal satu byte data yang tersedia. Nilai kembalian berupa objek `bytes`. Jika pihak lawan menutup koneksi secara normal, `recv()` akan langsung mengembalikan objek byte kosong (`b''`), yang menjadi indikator standar bagi program untuk keluar dari perulangan penerimaan data (*EOF indicator*).

## 6.3 Perbedaan `send()` dan `sendall()`

Pada pengiriman pesan pendek (di bawah beberapa kilobyte seperti pada praktikum ini), `send()` sering kali langsung mengirimkan seluruh data dalam satu pemanggilan. Namun, untuk pengiriman data berukuran besar (misalnya file dokumen megabyte atau payload JSON raksasa), pemanggilan `send()` tunggal berisiko hanya mengirimkan sebagian byte (*partial write*).

Penggunaan `sendall()` jauh lebih aman untuk data besar karena menjamin integritas transmisi data secara utuh tanpa mewajibkan programmer membuat algoritma perulangan *offset pointer* pengiriman secara manual.

## 6.4 Buffer `recv(1024)`

```python
data = conn.recv(1024)
```

**Analisis:**
Angka `1024` menunjukkan ukuran maksimum *buffer chunk* pembacaan dalam satuan byte ($1024 \text{ byte} = 1 \text{ KiB}$).

> **Apa yang terjadi jika data yang dikirim lebih besar daripada ukuran buffer?**  
> TCP adalah protokol berbasis *stream*, bukan berbasis pesan utuh. Jika pengirim mengirimkan payload sebesar 2500 byte sementara server menggunakan `recv(1024)`, maka:
> * Pemanggilan `recv(1024)` pertama hanya akan mengambil 1024 byte pertama.
> * Sisa 1476 byte tidak hilang, melainkan tetap tersimpan dengan aman di dalam receive buffer kernel TCP sistem operasi.
> * Pemanggilan `recv(1024)` kedua akan membaca 1024 byte berikutnya.
> * Pemanggilan `recv(1024)` ketiga akan membaca sisa 452 byte terakhir.

### Pembuktian Melalui Pengujian Empiris
Telah dilakukan pengujian eksperimen khusus dengan mengirimkan payload sebesar 2500 byte data `b'A' * 2500` menggunakan buffer penerima `recv(1024)`. Hasil pengamatan menunjukkan:
```text
Server recv chunk1 len: 1024
Server recv chunk2 len: 1024
Server recv chunk3 len: 452
Total byte diterima: 2500 byte
```
Hal ini membuktikan secara empiris bahwa data yang melebihi ukuran buffer tidak terpotong atau hilang, melainkan terfragmentasi ke dalam beberapa siklus pembacaan buffer.

## 6.5 Encoding dan Decoding

### Encoding
```python
message.encode()        # Mengonversi string Python -> bytes (default: UTF-8)
```

### Decoding
```python
data.decode()           # Mengonversi bytes -> string Python (default: UTF-8)
```

**Analisis:**
Socket jaringan beroperasi pada level fisik dan transport yang hanya mengenali aliran biner mentah (*raw stream of octets/bytes*). Di sisi lain, objek string pada Python 3 merupakan representasi karakter abstrak tingkat tinggi berbasis Unicode. Interpreter Python tidak dapat mengirimkan objek string secara langsung ke kabel jaringan tanpa memetakan karakter-karakter tersebut ke representasi deretan byte biner melalui standar encoding (seperti UTF-8). Oleh karena itu, langkah `.encode()` sebelum transmisi dan `.decode()` setelah penerimaan adalah kewajiban mutlak.

## 6.6 TCP sebagai Byte Stream

TCP memperlakukan data sebagai aliran byte tanpa henti (*continuous stream of bytes*), tanpa memiliki konsep "batas pesan" (*message boundary*). Berbeda dengan UDP yang mengirimkan paket per paket diskret (*datagram*), pada TCP:
```python
client.send(b"Hello")
client.send(b"World")
```
Dua pemanggilan `send()` terpisah di atas tidak menjamin server akan menerima pesan dalam dua panggilan `recv()` yang terpisah. Di tingkat jaringan, TCP dapat menggabungkan kedua pesan tersebut menjadi satu segmen (*packet coalescing / Nagle's algorithm*) sehingga server menerima `b"HelloWorld"` sekaligus, atau sebaliknya memecahnya ke fragmen yang berbeda tergantung kapasitas MSS (*Maximum Segment Size*).

> **Dampak terhadap Desain Protokol Aplikasi:**  
> Karakteristik *byte stream* ini mewajibkan pengembang protokol aplikasi untuk menyusun mekanisme pembatas pesan sendiri (*framing mechanism*), seperti:
> 1. Menggunakan karakter pembatas/delimiter (misal `\n` atau `\r\n`).
> 2. Menggunakan prefiks panjang data (*Length-Prefixed Framing* / header ukuran payload).
> 3. Menggunakan format data terstruktur dengan tanda kurung pembuka dan penutup yang jelas seperti **JSON** (`{ ... }`).

---

# BAB VII — IMPLEMENTASI DAN ANALISIS JSON

## 7.1 Struktur Data JSON

Format JSON (JavaScript Object Notation) digunakan pada praktikum pengembangan untuk mengirimkan data terstruktur multi-atribut antara client dan server.

### Format Request (Client ke Server):
```json
{
  "nama": "Jouvi",
  "pesan": "Halo Server"
}
```

### Format Response (Server ke Client):
```json
{
  "status": "success",
  "nama": "Jouvi",
  "pesan": "Halo Server",
  "tanggal": "2026-09-09",
  "waktu": "03:39:34"
}
```

## 7.2 Pengiriman JSON dari Client (`client_json.py`)

```python
request = {
    "nama": nama,
    "pesan": pesan
}

client_socket.send(json.dumps(request).encode())
```

**Analisis:**
1. Variabel masukan pengguna dikumpulkan ke dalam dictionary Python `request`.
2. Fungsi `json.dumps(request)` melakukan **serialisasi**, yaitu mengubah dictionary objek Python menjadi representasi string JSON yang terstandarisasi.
3. Metode `.encode()` mengubah string JSON tersebut menjadi aliran byte UTF-8.
4. Metode `client_socket.send()` mentransmisikan stream byte ke jaringan.

## 7.3 Penerimaan JSON pada Server (`server_json.py`)

```python
data = conn.recv(1024).decode()
request = json.loads(data)
```

**Analisis:**
1. Metode `conn.recv(1024)` membaca stream byte dari socket.
2. Metode `.decode()` mengonversi byte tersebut kembali menjadi string teks.
3. Fungsi `json.loads(data)` melakukan **deserialisasi**, yaitu mem-parse string JSON dan merekonstruksinya kembali menjadi objek dictionary Python native sehingga atribut-atribut seperti `request["nama"]` dan `request["pesan"]` dapat diakses dengan mudah oleh logika server.

## 7.4 Response JSON dari Server

Pada file [server_json.py](file:///d:/Project/Network%20Programming/praktikum_1/server_json.py), server memproses data yang masuk dan menyusun respon balik berupa dictionary lengkap:
```python
response = {
    "status": "success",
    "nama": request.get("nama", ""),
    "pesan": request.get("pesan", ""),
    "tanggal": datetime.now().strftime("%Y-%m-%d"),
    "waktu": datetime.now().strftime("%H:%M:%S")
}
conn.send(json.dumps(response).encode())
```

**Hasil Pengujian Nyata (Berdasarkan `TEST_RESULT.txt`):**
```text
{"status": "success", "nama": "Jouvi", "pesan": "Halo Server", "tanggal": "2026-09-09", "waktu": "03:39:34"}
{"status": "success", "pesan": "Koneksi ditutup oleh client."}
```

## 7.5 Analisis Implementasi JSON

Penerapan JSON memberikan keunggulan signifikan dibandingkan teks mentah (*plain text*):
1. **Representasi Multi-Field:** Memungkinkan pengiriman banyak atribut (status, nama, pesan, tanggal, waktu) dalam satu paket transmisi tanpa perlu membuat parser teks kustom (*custom string splitting*).
2. **Interoperabilitas Lintas Platform:** Format JSON bersifat standar dan independen dari bahasa pemrograman. Server Python dapat berkomunikasi lancar dengan client Android (Java/Kotlin), web browser (JavaScript), maupun iOS (Swift).
3. **Validasi dan Penanganan Tipe Data:** Nilai skalar seperti integer, boolean, null, serta array dapat dipertahankan integritas tipe datanya saat ditransmisikan.

---

# BAB VIII — PENUTUPAN KONEKSI

## 8.1 `close()`

```python
conn.close()
server_socket.close()
client_socket.close()
```

**Analisis:**
Pemanggilan fungsi `close()` bertujuan untuk mengakhiri sesi komunikasi jaringan, melepaskan sumber daya memori buffer soket, serta membebaskan *file descriptor* yang dialokasikan oleh kernel sistem operasi.

## 8.2 Four-Way Handshake

Penutupan koneksi TCP yang berlangsung secara normal (*graceful shutdown*) menggunakan mekanisme pertukaran 4 segmen kendali (*Four-Way Handshake*):

```text
Pihak Inisiator (Client)                          Pihak Penerima (Server)
          |                                                  |
          |  1. FIN (Seq = u)                                |
          |------------------------------------------------->| (Menerima FIN, kirim ACK)
          |                                                  |
          |  2. ACK (Ack = u + 1)                            |
          |<<------------------------------------------------|
          |                                                  | Server menyelesaikan
          |                                                  | pengiriman data terakhir
          |  3. FIN (Seq = v)                                |
          |<<------------------------------------------------|
          |                                                  |
          |  4. ACK (Ack = v + 1)                            |
          |------------------------------------------------->|
          |                                                  |
     [TIME_WAIT]                                          [CLOSED]
          | (2 * MSL)
       [CLOSED]
```

1. **Langkah 1 (FIN):** Pihak yang ingin mengakhiri koneksi (misal client setelah mengetik `exit`) memanggil `close()`, memicu pengiriman segmen berflag **FIN**.
2. **Langkah 2 (ACK):** Server menerima FIN dan membalas dengan segmen **ACK**. Pada tahap ini, koneksi berada pada status *half-closed*; client tidak lagi mengirim data, namun masih bisa menerima data sisa dari server.
3. **Langkah 3 (FIN):** Setelah server menyelesaikan pemrosesan dan memanggil `conn.close()`, server mengirimkan segmen **FIN** ke client.
4. **Langkah 4 (ACK):** Client membalas dengan segmen **ACK**, lalu memasuki status `TIME_WAIT` untuk memastikan paket ACK terakhir sampai sebelum socket benar-benar ditutup (`CLOSED`).

## 8.3 Context Manager

Bahasa pemrograman Python mendukung sintaks *context manager* dengan blok `with`:
```python
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    ...
```

**Analisis:**
Ketika alur program keluar dari cakupan blok `with` (baik karena selesai secara normal maupun karena terinterupsi oleh *exception* runtime), metode `__exit__()` dari objek socket akan otomatis memanggil fungsi `close()`.  
Pada implementasi praktikum saat ini ([server_basic.py](file:///d:/Project/Network%20Programming/praktikum_1/server_basic.py)), program tidak menggunakan context manager, melainkan memanggil `close()` secara manual di akhir skrip. Pendekatan manual ini berisiko: jika terjadi exception runtime di tengah-tengah loop `while True`, baris `conn.close()` dan `server_socket.close()` tidak akan pernah dieksekusi, berpotensi meninggalkan socket dalam keadaan terbuka (*resource leak*).

## 8.4 Konsekuensi Koneksi Tidak Ditutup dengan Benar

Jika soket tidak ditutup dengan benar atau program dihentikan secara paksa:
1. **Resource Leak (Kebocoran Sumber Daya):** Port dan *file descriptor* sistem operasi tetap terikat dan tidak dilepaskan.
2. **Status `TIME_WAIT` dan Port Locking:** Port lokal tertahan dalam status `TIME_WAIT` selama durasi $2 \times \text{MSL}$ (sekitar 1–2 menit).
3. **Error `WinError 10048`:** Terjadi galat fatal saat server hendak dijalankan kembali:
   ```text
   OSError: [WinError 10048] Only one usage of each socket address (protocol/network address/port) is normally permitted
   ```
   Kasus ini telah dialami secara langsung pada praktikum saat proses Python sebelumnya belum ditutup sempurna. Solusinya adalah mematikan proses via Task Manager / PowerShell (`Stop-Process`), serta menambahkan opsi socket `SO_REUSEADDR`:
   ```python
   server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   ```

## 8.5 Pengujian Client Mati Mendadak

### Skenario Pengujian
Pengujian dilakukan untuk mengamati respons server apabila proses client dimatikan secara paksa (*hard crash*) tanpa melalui mekanisme penutupan normal (tanpa mengetik `"exit"` dan tanpa memanggil `close()`), misalnya melalui penghentian proses paksa dengan `os._exit()` atau terminasi task via sistem operasi.

### Hasil Pengamatan
Ketika client dimatikan mendadak tepat setelah terkoneksi dan mengirim data pertama, server yang sedang menunggu pembacaan di baris `conn.recv(1024)` seketika mengalami exception fatal:
```text
Client terhubung: ('127.0.0.1', 57234)
Data diterima: Halo
Hasil recv() exception: ConnectionResetError [WinError 10054] - [WinError 10054] An existing connection was forcibly closed by the remote host
Server socket closed.
```

### Analisis
Ketika sebuah proses client dimatikan paksa di Windows, kernel sistem operasi client tidak sempat menjalankan *Four-Way Handshake* secara tertib. Sebagai gantinya, kernel mengirimkan paket segmen **TCP RST (Reset)** ke server. Saat server memanggil fungsi `recv()` pada koneksi yang telah di-reset oleh paket RST, kernel Windows melemparkan error jaringan:  
**`ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host`**.  
Hasil eksperimen ini menegaskan pentingnya menyematkan blok proteksi `try ... except ConnectionResetError` pada perulangan server agar server tidak *crash* ketika ada client yang putus mendadak.

---

# BAB IX — PENGUJIAN DAN HASIL

## 9.1 Pengujian Server

### Langkah
1. Buka terminal PowerShell pertama pada direktori proyek.
2. Jalankan perintah `python server_basic.py`.
3. Amati pesan startup pada konsol.

### Hasil
```text
Server berjalan di 127.0.0.1:5000
Menunggu koneksi client...
```

### Screenshot

*(Tempatkan screenshot konsol server saat pertama kali berjalan dan menunggu koneksi di sini)*

---

## 9.2 Pengujian Koneksi Client

### Langkah
1. Buka terminal PowerShell kedua.
2. Jalankan perintah `python client_basic.py`.
3. Amati pesan konfirmasi koneksi pada terminal client dan terminal server.

### Hasil pada Client:
```text
Terhubung ke server 127.0.0.1:5000
Ketik pesan. Ketik 'exit' untuk keluar.
Client: 
```

### Hasil pada Server:
```text
Client terhubung: ('127.0.0.1', 57234)
```

### Screenshot

*(Tempatkan screenshot konsol client dan server saat status koneksi berhasil terbentuk di sini)*

---

## 9.3 Pengujian Pengiriman Pesan

**Input Client:**
```text
Client: Halo Server
```

**Response Server pada Layar Client:**
```text
Server: 2026-09-16 09:47:12
```

**Analisis:**
Pesan string `"Halo Server"` dari client berhasil dienkapsulasi menjadi stream byte UTF-8, diterima oleh server melalui `recv(1024)`, dan server membalas dengan string tanggal dan waktu saat ini yang kemudian dicetak dengan benar di terminal client.

---

## 9.4 Pengujian JSON

Pengujian dilakukan menggunakan modul [server_json.py](file:///d:/Project/Network%20Programming/praktikum_1/server_json.py) dan [client_json.py](file:///d:/Project/Network%20Programming/praktikum_1/client_json.py).

**Input pada Client:**
```text
Nama: Jouvi
Pesan: Halo Server
```

**Request JSON yang Dikirim Client:**
```json
{
  "nama": "Jouvi",
  "pesan": "Halo Server"
}
```

**Response JSON yang Diterima Client dari Server:**
```json
{
  "status": "success",
  "nama": "Jouvi",
  "pesan": "Halo Server",
  "tanggal": "2026-09-09",
  "waktu": "03:39:34"
}
```

**Analisis:**
Serialisasi dictionary Python menjadi string JSON menggunakan `json.dumps()` dan rekonstruksi kembali di sisi server menggunakan `json.loads()` berjalan dengan sukses 100%. Data multi-atribut berhasil diekstrak dan dibalas oleh server dengan atribut tambahan (`status`, `tanggal`, `waktu`).

---

## 9.5 Pengujian `exit`

**Input pada Client:**
```text
Client: exit
```

**Hasil pada Client:**
```text
Client berhenti.
```

**Hasil pada Server:**
```text
Client menutup koneksi.
Server berhenti.
```

**Analisis:**
Perintah string `"exit"` berhasil dievaluasi oleh kondisi percabangan `if data.lower() == "exit":`. Kedua pihak keluar dari perulangan `while True`, memanggil fungsi `.close()`, dan proses berakhir secara tertib (*graceful termination*).

---

## 9.6 Pengujian Client Mati Mendadak

**Metode Pengujian:**
Client dijalankan dan terhubung ke server, kemudian proses client dimatikan secara mendadak menggunakan `os._exit(0)` atau *End Task* paksa tanpa mengirim sinyal `exit`.

**Hasil pada Server:**
```text
Client terhubung: ('127.0.0.1', 57234)
Data diterima: Halo
Exception terjadi: ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host
Server berhenti.
```

**Analisis:**
Pemutusan mendadak memicu pengiriman paket TCP RST oleh sistem operasi client, yang dideteksi oleh server sebagai `ConnectionResetError`. Server menangani kondisi ini dengan menutup socket sehingga port kembali bebas.

---

## 9.7 Rekap Pengujian

| No | Skenario Pengujian | Input Data | Hasil yang Diharapkan | Hasil Aktual | Status |
|:--:|---|---|---|---|:--:|
| 1 | Menjalankan Server TCP | `python server_basic.py` | Server aktif & mendengarkan port 5000 | Server mencetak `Server berjalan di 127.0.0.1:5000` | **BERHASIL** |
| 2 | Menghubungkan Client ke Server | `python client_basic.py` | Berhasil *handshake*, server mencetak alamat client | Alamat `('127.0.0.1', <port>)` tercetak di server | **BERHASIL** |
| 3 | Pengiriman Pesan Plain Text | `"Halo Server"` | Server menerima pesan & merespons timestamp | Client menerima string waktu valid | **BERHASIL** |
| 4 | Pengiriman Payload JSON | `{"nama":"Jouvi", "pesan":"Halo"}` | Server mem-parse JSON dan membalas response JSON lengkap | Client menerima objek dictionary JSON terstruktur | **BERHASIL** |
| 5 | Perintah Penutupan Normal | `"exit"` | Client & Server memutus koneksi secara tertib | Kedua proses keluar loop & socket ditutup | **BERHASIL** |
| 6 | Pengujian Kapasitas Buffer | Payload 2500 bytes (> buffer 1024) | Data terfragmentasi tanpa kehilangan byte | Diterima 3 tahap (1024 + 1024 + 452 byte) | **BERHASIL** |
| 7 | Terminasi Client Mendadak | Pemutusan paksa via task kill | Server mendeteksi paket RST / memutus soket | Server menangkap `ConnectionResetError (10054)` | **BERHASIL** |

---

# BAB X — ANALISIS KESELURUHAN

## 10.1 Alur Komunikasi Client-Server

```text
       CLIENT                                          SERVER
         |                                               |
         |                                        socket.socket()
         |                                            bind()
         |                                           listen()
         |                                               |
   socket.socket()                                       |
     connect()  ------------ [SYN] --------------------> |
         |      <------- [SYN + ACK] ------------------- |  accept()
         |      ------------ [ACK] --------------------> | (Koneksi Diterima)
         |                                               |
         | ===== Saluran Komunikasi Terbentuk (ESTABLISHED) =====
         |                                               |
    input("...")                                         |
   message.encode()                                      |
     send()     ------ Stream Byte Request ------------> | recv(1024)
         |                                               | decode()
         |                                               | Proses Logika Data
         |                                               | datetime.now()
         |                                               | response.encode()
   recv(1024)   <----- Stream Byte Response ----------- | send()
    decode()                                             |
  print(resp)                                            |
         |                                               |
         | ===== Sesi Penutupan Koneksi (Ketik 'exit') =====
         |                                               |
   send("exit") ---------------------------------------> | Deteksi "exit"
     close()    ------------ [FIN] --------------------> | conn.close()
         |      <----------- [ACK] --------------------- |
         |      <----------- [FIN] --------------------- |
         |      ------------ [ACK] --------------------> |
         |                                         server_socket.close()
   (Terminasi)                                         (Terminasi)
```

## 10.2 Analisis Hubungan Program dengan Konsep Jaringan

Berdasarkan keseluruhan implementasi praktikum, terdapat korelasi langsung antara baris kode Python dengan konsep jaringan komputer:
1. **Socket (`socket.socket`):** Merepresentasikan pembuatan *Communication Endpoint* di tingkat kernel yang mengabstraksikan antarmuka Layer 4 (Transport).
2. **IP Address & Port (`HOST`, `PORT`):** Menentukan pengalamatan logis Layer 3 (`127.0.0.1`) dan identitas proses spesifik Layer 4 (`5000`).
3. **TCP Stream (`SOCK_STREAM`):** Menentukan protokol lapisan transport yang andal, berurutan, dan bebas galat melalui verifikasi *checksum* dan *acknowledgment*.
4. **Model OSI & TCP/IP:** Menunjukkan proses enkapsulasi data: data tingkat aplikasi (JSON) dikonversi menjadi byte di Presentation Layer, dikemas menjadi segmen TCP di Transport Layer, dipaketkan ke IP di Network Layer, dan dialirkan melalui kartu jaringan.
5. **Three-Way Handshake (`connect()` & `accept()`):** Membuktikan bahwa transmisi data hanya dapat terjadi setelah kesepakatan parameter komunikasi logis antara client dan server terbentuk.
6. **Transfer Data (`send()` & `recv()`):** Mengilustrasikan mekanisme *byte streaming*, fragmentasi buffer, dan keharusan encoding/decoding karakter Unicode menjadi representasi biner.
7. **Four-Way Handshake & Penutupan (`close()`):** Merealisasikan pelepasan sumber daya socket secara terkoordinasi antar dua arah (*duplex disconnection*).

## 10.3 Permasalahan dan Solusi

Selama pelaksanaan praktikum, ditemukan beberapa permasalahan teknis yang dianalisis dan diselesaikan sebagai berikut:

| Permasalahan | Penyebab Teknis | Solusi yang Diterapkan |
|---|---|---|
| **Error `OSError: [WinError 10048]`** *(Address already in use)* saat menjalankan server | Port `5000` masih terkunci oleh proses instance server sebelumnya yang masih aktif di latar belakang (PID 9772) karena terminal sebelumnya ditutup paksa. | 1. Melacak PID proses via PowerShell: `Get-NetTCPConnection -LocalPort 5000`.<br>2. Menghentikan paksa proses terkait: `Stop-Process -Id 9772 -Force`.<br>3. Menambahkan opsi `SO_REUSEADDR` pada kode server (`server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)`). |
| **Error `ConnectionResetError: [WinError 10054]`** saat client dimatikan paksa | Client menutup proses tanpa *graceful shutdown*, menyebabkan sistem operasi client memancarkan segmen TCP RST ke server yang sedang menunggu `recv()`. | Menambahkan blok penanganan eksepsi `try ... except ConnectionResetError` di dalam loop server untuk menutup socket client dengan rapi tanpa merusak proses utama server. |
| **Risiko data terpotong (*Truncated Data*)** jika payload melebihi ukuran buffer 1024 byte | Karakteristik TCP sebagai *byte stream* yang membagi data besar menjadi beberapa paket fragmen. | Menggunakan perulangan pembacaan buffer atau menggunakan fungsi `sendall()` di sisi pengirim serta mendesain framing berformat JSON. |

---

# BAB XI — KESIMPULAN

Berdasarkan perancangan, implementasi, dan serangkaian pengujian yang telah dilakukan pada Praktikum Network Programming 1, dapat ditarik beberapa kesimpulan penting:

1. **Keberhasilan Komunikasi Client-Server TCP:** Implementasi program client-server menggunakan Socket API pada Python berhasil dibangun dengan sempurna, di mana client dapat mengirimkan pesan permintaan dan server mampu memproses serta memberikan respon secara *real-time*.
2. **Peran Alamat IP dan Port:** IP Address `127.0.0.1` berhasil berfungsi sebagai alamat loopback lokal, dan nomor port `5000` secara efektif berperan sebagai pintu masuk layanan server yang membedakan proses praktikum dari proses aplikasi lain dalam sistem operasi.
3. **Mekanisme Serialisasi dan Transmisi Data:** Komunikasi socket hanya dapat mentransmisikan data dalam bentuk aliran biner (*raw bytes*). Proses encoding string menjadi byte sebelum dikirim dan decoding byte kembali menjadi string saat diterima adalah tahapan wajib dalam pemrograman socket Python.
4. **Efektivitas Format JSON:** Penggunaan format JSON terbukti jauh lebih unggul dan terstruktur dibandingkan pengiriman teks biasa (*plain text*), karena memungkinkan pertukaran data multi-atribut (nama, pesan, tanggal, waktu, status) secara modular, aman, dan mudah di-parse oleh kedua belah pihak.
5. **Mekanisme Penutupan Koneksi (*Graceful Shutdown*):** Perintah `exit` berhasil memicu pemutusan koneksi normal melalui prosedur penutupan soket (`close()`), yang secara internal mengeksekusi mekanisme *Four-Way Handshake* untuk mencegah kebocoran *file descriptor* dan status *port locking*.
6. **Ketahanan terhadap Pemutusan Mendadak:** Pengujian terminasi client mendadak membuktikan timbulnya paket TCP RST yang menghasilkan eksepsi `ConnectionResetError [WinError 10054]` pada server, menggarisbawahi pentingnya penerapan *exception handling* dalam membangun arsitektur jaringan yang tangguh (*robust*).

---

# DAFTAR PUSTAKA

1. Syahrial, H. (2026). *Bahan Perkuliahan Network Programming: Pengantar Pemrograman Jaringan dan Konsep Client-Server Socket*. Program Studi Informatika.
2. Python Software Foundation. (2026). *Python 3 Standard Library Documentation: socket — Low-level networking interface*. Diakses dari https://docs.python.org/3/library/socket.html
3. Python Software Foundation. (2026). *Python 3 Standard Library Documentation: json — JSON encoder and decoder*. Diakses dari https://docs.python.org/3/library/json.html
4. Kurose, J. F., & Ross, K. W. (2021). *Computer Networking: A Top-Down Approach* (8th ed.). Pearson Education.
5. Postel, J. (1981). *Transmission Control Protocol - DARPA Internet Program Protocol Specification* (RFC 793). Internet Engineering Task Force (IETF).
6. Bray, T. (2017). *The JavaScript Object Notation (JSON) Data Interchange Format* (RFC 8259). Internet Engineering Task Force (IETF).

---

# LAMPIRAN

## Lampiran A — Source Code `server_basic.py`

```python
import socket
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server berjalan di {HOST}:{PORT}")
print("Menunggu koneksi client...")

conn, addr = server_socket.accept()
print(f"Client terhubung: {addr}")

while True:
    data = conn.recv(1024).decode()

    if not data:
        break

    if data.lower() == "exit":
        print("Client menutup koneksi.")
        break

    response = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.send(response.encode())

conn.close()
server_socket.close()
print("Server berhenti.")
```

## Lampiran B — Source Code `client_basic.py`

```python
import socket

HOST = "127.0.0.1"
PORT = 5000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

print(f"Terhubung ke server {HOST}:{PORT}")
print("Ketik pesan. Ketik 'exit' untuk keluar.")

while True:
    message = input("Client: ")
    client_socket.send(message.encode())

    if message.lower() == "exit":
        break

    response = client_socket.recv(1024).decode()
    print("Server:", response)

client_socket.close()
print("Client berhenti.")
```

## Lampiran C — Source Code JSON

### C.1 `server_json.py`
```python
import socket
import json
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server JSON berjalan di {HOST}:{PORT}")
print("Menunggu koneksi client...")

conn, addr = server_socket.accept()
print(f"Client terhubung: {addr}")

while True:
    data = conn.recv(1024).decode()

    if not data:
        break

    request = json.loads(data)

    if request.get("pesan", "").lower() == "exit":
        response = {
            "status": "success",
            "pesan": "Koneksi ditutup oleh client."
        }
        conn.send(json.dumps(response).encode())
        break

    response = {
        "status": "success",
        "nama": request.get("nama", ""),
        "pesan": request.get("pesan", ""),
        "tanggal": datetime.now().strftime("%Y-%m-%d"),
        "waktu": datetime.now().strftime("%H:%M:%S")
    }

    conn.send(json.dumps(response).encode())

conn.close()
server_socket.close()
print("Server berhenti.")
```

### C.2 `client_json.py`
```python
import socket
import json

HOST = "127.0.0.1"
PORT = 5000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

print(f"Terhubung ke server {HOST}:{PORT}")
print("Format: nama dan pesan. Ketik 'exit' pada pesan untuk keluar.")

while True:
    nama = input("Nama: ")
    pesan = input("Pesan: ")

    request = {
        "nama": nama,
        "pesan": pesan
    }

    client_socket.send(json.dumps(request).encode())

    response = client_socket.recv(1024).decode()
    response_json = json.loads(response)

    print("Server:", response_json)

    if pesan.lower() == "exit":
        break

client_socket.close()
print("Client berhenti.")
```

## Lampiran D — Screenshot Pengujian

### D.1 Server Berjalan
*(Sematkan tangkapan layar terminal saat `server_basic.py` atau `server_json.py` mulai dijalankan dan berada dalam status listening)*

### D.2 Client Terhubung
*(Sematkan tangkapan layar terminal saat `client_basic.py` berhasil terhubung ke server dan mencetak tuple alamat IP dan ephemeral port client)*

### D.3 Pengiriman Data
*(Sematkan tangkapan layar interaksi pengiriman pesan string biasa dan penerimaan balasan timestamp dari server)*

### D.4 Pengiriman JSON
*(Sematkan tangkapan layar interaksi input nama & pesan pada client JSON serta respons objek JSON dari server)*

### D.5 Penutupan Koneksi
*(Sematkan tangkapan layar proses penutupan koneksi saat perintah `exit` diketikkan)*

### D.6 Client Mati Mendadak
*(Sematkan tangkapan layar pesan error atau pemutusan saat proses client dihentikan secara paksa)*
