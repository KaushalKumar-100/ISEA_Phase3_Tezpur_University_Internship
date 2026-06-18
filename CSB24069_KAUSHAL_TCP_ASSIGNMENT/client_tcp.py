import socket
import time
import csv

SERVER_IP = "10.0.0.1"
PORT = 5000

MESSAGE_SIZES = [128, 512, 1024]
TOTAL_MESSAGES = 10

ROLL_NO = "CSB24069"
NAME = "Kaushal Kumar"

result_rows = []
message_logs = []


def create_message(msg_id, size):
    data = "A" * size
    return f"{msg_id}|{size}|{data}"


def send_message(sock, msg_id, size, mode):
    message = create_message(msg_id, size)

    start_time = time.time()

    sock.sendall(message.encode())

    ack = sock.recv(1024).decode()

    end_time = time.time()

    response_time = end_time - start_time

    print(f"{mode}: Sent message {msg_id}, Received -> {ack}")

    return response_time


def persistent_mode(size):
    total_time = 0
    total_bytes = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, PORT))

    for i in range(1, TOTAL_MESSAGES + 1):
        response_time = send_message(
            sock, i, size, "persistent"
        )

        total_time += response_time
        total_bytes += size

        message_logs.append([
            ROLL_NO,
            NAME,
            "persistent",
            size,
            i,
            response_time
        ])

    sock.close()

    average_response = total_time / TOTAL_MESSAGES
    throughput = total_bytes / total_time

    result_rows.append([
        ROLL_NO,
        NAME,
        "persistent",
        5,
        50,
        size,
        TOTAL_MESSAGES,
        average_response,
        throughput,
        "SUCCESS"
    ])


def new_connection_mode(size):
    total_time = 0
    total_bytes = 0

    for i in range(1, TOTAL_MESSAGES + 1):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, PORT))

        response_time = send_message(
            sock, i, size, "new_connection"
        )

        sock.close()

        total_time += response_time
        total_bytes += size

        message_logs.append([
            ROLL_NO,
            NAME,
            "new_connection",
            size,
            i,
            response_time
        ])

    average_response = total_time / TOTAL_MESSAGES
    throughput = total_bytes / total_time

    result_rows.append([
        ROLL_NO,
        NAME,
        "new_connection",
        5,
        50,
        size,
        TOTAL_MESSAGES,
        average_response,
        throughput,
        "SUCCESS"
    ])


def save_result_table():

    with open("result_table.csv", "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "roll_no",
            "name",
            "mode",
            "bandwidth_mbps",
            "delay_ms",
            "message_size_bytes",
            "total_messages",
            "average_response_time_seconds",
            "throughput_bytes_per_second",
            "status"
        ])

        writer.writerows(result_rows)


def save_message_log():

    with open(
        "message_response_log.csv",
        "w",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "roll_no",
            "name",
            "mode",
            "message_size_bytes",
            "message_number",
            "response_time_seconds"
        ])

        writer.writerows(message_logs)


def main():

    print("Starting TCP Performance Experiment\n")

    for size in MESSAGE_SIZES:

        print(f"\nTesting {size} bytes")

        persistent_mode(size)

        new_connection_mode(size)

    save_result_table()

    save_message_log()

    print("\nExperiment completed.")
    print("CSV files generated successfully.")


if __name__ == "__main__":
    main()