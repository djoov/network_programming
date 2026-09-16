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
