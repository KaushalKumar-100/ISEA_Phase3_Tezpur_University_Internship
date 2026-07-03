import socket
import threading
import csv
import os
from datetime import datetime

HOST = '0.0.0.0'
PORT = 5000
HISTORY_FILE = 'chat_history.csv'

clients = {}          # username -> {conn, ip, port, login_time, status}
clients_lock = threading.Lock()

stats = {'messages_processed': 0, 'broadcast_messages': 0, 'private_messages': 0}
stats_lock = threading.Lock()


def init_history_file():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'sender', 'receiver', 'message_type', 'message'])


def log_message(sender, receiver, msg_type, message):
    with open(HISTORY_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          sender, receiver, msg_type, message])
    with stats_lock:
        stats['messages_processed'] += 1
        if msg_type == 'broadcast':
            stats['broadcast_messages'] += 1
        elif msg_type == 'private':
            stats['private_messages'] += 1


def get_last_messages(username, n=5):
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r', newline='') as f:
        reader = list(csv.DictReader(f))
    user_msgs = [row for row in reader if row['sender'] == username]
    return user_msgs[-n:]


def broadcast(message, exclude=None):
    with clients_lock:
        dead = []
        for user, info in clients.items():
            if user != exclude:
                try:
                    info['conn'].sendall((message + '\n').encode())
                except OSError:
                    dead.append(user)
        for u in dead:
            del clients[u]


def send_private(sender, receiver, message):
    with clients_lock:
        if receiver not in clients:
            return False
        try:
            clients[receiver]['conn'].sendall(f"[PM from {sender}]: {message}\n".encode())
            return True
        except OSError:
            return False


def get_user_list():
    with clients_lock:
        return list(clients.keys())


def print_stats():
    with stats_lock:
        s = dict(stats)
    print(f"[STATS] Connected: {len(get_user_list())} | "
          f"Processed: {s['messages_processed']} | "
          f"Broadcast: {s['broadcast_messages']} | "
          f"Private: {s['private_messages']}")


def handle_client(conn, addr):
    username = None
    try:
        conn.sendall(b"Enter username: ")
        raw = conn.recv(1024)
        if not raw:
            conn.close()
            return
        username = raw.decode().strip()
        if not username:
            conn.close()
            return

        with clients_lock:
            if username in clients:
                conn.sendall(b"Username already taken. Disconnecting.\n")
                conn.close()
                return
            clients[username] = {
                'conn': conn,
                'ip': addr[0],
                'port': addr[1],
                'login_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'online'
            }

        print(f"[JOIN] {username} connected from {addr[0]}:{addr[1]}")
        log_message('SERVER', 'ALL', 'system', f"{username} joined the chat")
        broadcast(f"*** {username} has joined the chat ***", exclude=username)
        print_stats()

        # Reconnect history feature
        history = get_last_messages(username, 5)
        if history:
            conn.sendall(b"--- Your last 5 messages ---\n")
            for row in history:
                conn.sendall(f"[{row['timestamp']}] {row['message']}\n".encode())
            conn.sendall(b"----------------------------\n")

        while True:
            data = conn.recv(4096)
            if not data:
                break
            msg = data.decode().strip()
            if not msg:
                continue

            if msg == '/quit':
                break

            elif msg == '/list':
                users = get_user_list()
                conn.sendall(f"Online users ({len(users)}): {', '.join(users)}\n".encode())

            elif msg == '/stats':
                with stats_lock:
                    s = dict(stats)
                s['connected_users'] = len(get_user_list())
                conn.sendall(f"Stats: {s}\n".encode())

            elif msg.startswith('/msg '):
                parts = msg.split(' ', 2)
                if len(parts) < 3:
                    conn.sendall(b"Usage: /msg <username> <message>\n")
                    continue
                target, pm = parts[1], parts[2]
                if target not in get_user_list():
                    conn.sendall(f"Error: user '{target}' not found or offline.\n".encode())
                    continue
                ok = send_private(username, target, pm)
                if ok:
                    log_message(username, target, 'private', pm)
                    conn.sendall(f"[PM to {target}]: {pm}\n".encode())
                else:
                    conn.sendall(f"Error: could not deliver message to {target}.\n".encode())

            else:
                log_message(username, 'ALL', 'broadcast', msg)
                broadcast(f"[{username}]: {msg}", exclude=username)
                conn.sendall(b"[OK]\n")  # ack so sender's own delay can be measured

    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        if username:
            with clients_lock:
                if username in clients:
                    del clients[username]
            print(f"[LEAVE] {username} disconnected")
            log_message('SERVER', 'ALL', 'system', f"{username} left the chat")
            broadcast(f"*** {username} has left the chat ***")
            print_stats()
        conn.close()


def main():
    init_history_file()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(20)
    print(f"Chat server listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        server.close()


if __name__ == '__main__':
    main()