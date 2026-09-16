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
