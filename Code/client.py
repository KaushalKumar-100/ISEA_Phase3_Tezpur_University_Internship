import socket
import time

SERVER_IP = "10.0.0.1"
PORT = 5000

TOTAL_MESSAGES = 10

# Roll number 69 -> last digit 9 -> timeout 1.5 sec
TIMEOUT = 1.5

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set timeout for waiting ACK
client.settimeout(TIMEOUT)

packets_sent = 0
retransmissions = 0

start_time = time.time()


for seq in range(1, TOTAL_MESSAGES + 1):

    message = f"{seq}|Message {seq} from h2"

    while True:

        try:
            # Send packet
            client.sendto(message.encode(), (SERVER_IP, PORT))
            packets_sent += 1

            print(f"Sent: {message}")

            # Wait for ACK
            ack, address = client.recvfrom(1024)

            ack = ack.decode()

            print(f"Received: {ack}")

            # Check ACK sequence
            if ack == f"ACK|{seq}":
                print(f"Packet {seq} successful\n")
                break

            else:
                print("Wrong ACK received. Sending again.")
                retransmissions += 1


        except socket.timeout:
            retransmissions += 1
            print(f"Timeout for SEQ {seq}. Retransmitting...\n")


end_time = time.time()

transfer_time = end_time - start_time


print("\n===== CLIENT OUTPUT =====")

print(f"TOTAL_MESSAGES={TOTAL_MESSAGES}")
print("LOSS_PERCENT=__")
print(f"TIMEOUT={TIMEOUT}")
print(f"TOTAL_PACKETS_SENT={packets_sent}")
print(f"TOTAL_RETRANSMISSIONS={retransmissions}")
print(f"TRANSFER_TIME_SECONDS={transfer_time:.4f}")
print("STATUS=SUCCESS")


client.close()