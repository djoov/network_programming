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
