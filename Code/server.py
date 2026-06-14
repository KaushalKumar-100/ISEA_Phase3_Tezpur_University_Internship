import socket

SERVER_IP = "10.0.0.1"
PORT = 5000
TOTAL_MESSAGES = 10

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((SERVER_IP, PORT))

print("Server started...")
print(f"Listening on {SERVER_IP}:{PORT}")

received_seq = set()

unique_messages = 0
duplicates = 0

while unique_messages < TOTAL_MESSAGES:

    data, client_addr = server.recvfrom(1024)
    packet = data.decode()

    print(f"\nReceived: {packet}")

    try:
        seq, message = packet.split("|", 1)
        seq = int(seq)

    except:
        print("Invalid packet format")
        continue

    if seq in received_seq:
        duplicates += 1
        print(f"Duplicate message detected: SEQ {seq}")

    else:
        received_seq.add(seq)
        unique_messages += 1
        print(f"New message: {message}")

    ack = f"ACK|{seq}"
    server.sendto(ack.encode(), client_addr)

    print(f"Sent {ack}")


print("\n===== SERVER OUTPUT =====")
print(f"TOTAL_UNIQUE_MESSAGES_RECEIVED={unique_messages}")
print(f"TOTAL_DUPLICATES_DETECTED={duplicates}")
print("STATUS=SUCCESS")

server.close()