import socket
from datetime import datetime

HOST = "10.0.0.1"  # Server h1 IP
PORT = 5000


def write_log(client_ip, msg_id, received_size):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open("server_log.txt", "a") as file:
        file.write(
            f"{timestamp},{client_ip},{msg_id},{received_size},ACK_SENT\n"
        )


def start_server():
    # Create TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind IP and port
    server_socket.bind((HOST, PORT))

    # Start listening
    server_socket.listen(5)

    print(f"Server is listening on {HOST}:{PORT}")

    while True:
        # Accept client connection
        conn, address = server_socket.accept()

        print(f"\nConnected by {address[0]}")

        while True:
            # Receive data
            data = conn.recv(2048)

            # If client closes connection
            if not data:
                print("Client disconnected")
                break

            message = data.decode()

            parts = message.split("|", 2)

            if len(parts) != 3:
                print("Invalid message format")
                continue

            msg_id = parts[0]
            msg_size = parts[1]
            msg_data = parts[2]

            received_size = len(msg_data)

            print(f"Received message ID: {msg_id}, Size: {received_size} bytes")

            # Create ACK
            ack = f"ACK|{msg_id}|{received_size}"

            # Send ACK to client
            conn.sendall(ack.encode())

            print("Sent:", ack)

            # Save log
            write_log(address[0], msg_id, received_size)

        conn.close()


if __name__ == "__main__":
    start_server()