
import socket
import threading
import datetime
import os
import csv
import time

HOST = '0.0.0.0'
PORT = 5000

clients = {}

message_count = 0
delivery_times = []
start_time = time.time()


def get_timestamp():
    return datetime.datetime.now().strftime("%H:%M:%S")


# Create CSV file
with open("performance_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "clients",
        "total_messages",
        "avg_delivery_time_ms",
        "throughput_msgs_per_sec"
    ])


def update_performance():

    runtime = time.time() - start_time

    if len(delivery_times) > 0:
        avg_delivery = (
            sum(delivery_times) /
            len(delivery_times)
        )
    else:
        avg_delivery = 0

    if runtime > 0:
        throughput = (
            message_count / runtime
        )
    else:
        throughput = 0

    with open(
        "performance_results.csv",
        "w",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "clients",
            "total_messages",
            "avg_delivery_time_ms",
            "throughput_msgs_per_sec"
        ])

        writer.writerow([
            len(clients),
            message_count,
            round(avg_delivery, 3),
            round(throughput, 3)
        ])


def log_server_event(
    event,
    username,
    client_ip
):

    log_entry = (
        f"{get_timestamp()},"
        f"{event},"
        f"{username},"
        f"{client_ip}\n"
    )

    print(log_entry.strip())

    with open(
        "server_log.txt",
        "a"
    ) as f:

        f.write(log_entry)


def log_chat_message(
    username,
    message
):

    log_entry = (
        f"{get_timestamp()},"
        f"{username},"
        f"{message}\n"
    )

    with open(
        "chat_log.txt",
        "a"
    ) as f:

        f.write(log_entry)


def broadcast(
    message,
    sender_socket=None
):

    start = time.time()

    for client_socket in list(clients.keys()):

        if client_socket != sender_socket:

            try:

                client_socket.send(
                    message.encode(
                        'utf-8'
                    )
                )

            except:

                client_socket.close()

                remove_client(
                    client_socket
                )

    end = time.time()

    delivery_times.append(
        (end - start) * 1000
    )


def remove_client(
    client_socket
):

    if client_socket in clients:

        username = clients[
            client_socket
        ]

        try:

            client_ip = (
                client_socket
                .getpeername()[0]
            )

        except:

            client_ip = "Unknown"

        log_server_event(
            "DISCONNECTED",
            username,
            client_ip
        )

        del clients[
            client_socket
        ]

        update_performance()


def handle_client(
    client_socket,
    client_address
):

    global message_count

    try:

        username = (
            client_socket
            .recv(1024)
            .decode('utf-8')
        )

        clients[
            client_socket
        ] = username

        log_server_event(
            "CONNECTED",
            username,
            client_address[0]
        )

        update_performance()

        while True:

            message = (
                client_socket
                .recv(1024)
                .decode('utf-8')
            )

            if not message:
                break

            client_socket.send(
                "ACK".encode(
                    'utf-8'
                )
            )

            message_count += 1

            formatted_message = (
                f"[{username}] "
                f"{message}"
            )

            print(
                "Received:",
                formatted_message
            )

            log_chat_message(
                username,
                message
            )

            broadcast(
                formatted_message,
                client_socket
            )

            update_performance()

    except Exception as e:

        print(
            "Client Error:",
            e
        )

    finally:

        remove_client(
            client_socket
        )

        client_socket.close()


def start_server():

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.bind(
        (HOST, PORT)
    )

    server.listen(5)

    print(
        f"Server started on "
        f"{HOST}:{PORT}"
    )

    if not os.path.exists(
        "chat_log.txt"
    ):
        open(
            "chat_log.txt",
            "w"
        ).close()

    while True:

        client_socket, \
        client_address = (
            server.accept()
        )

        thread = threading.Thread(
            target=handle_client,
            args=(
                client_socket,
                client_address
            )
        )

        thread.start()


if __name__ == "__main__":
    start_server()





