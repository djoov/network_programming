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
