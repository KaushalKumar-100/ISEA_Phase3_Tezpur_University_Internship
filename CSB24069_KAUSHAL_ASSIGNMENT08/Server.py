import socket
import threading
import csv
import os
import hashlib
import time
import re
import json
import sys
import signal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# TASK 4: Configuration Management
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("[ERROR] config.json not found. Please create it.")
    sys.exit(1)

HOST = '0.0.0.0'
PORT = config.get('SERVER_PORT', 5000)
HISTORY_FILE = 'chat_history.csv'
USERS_FILE = 'users.csv'
SEC_LOG_FILE = 'security_log.txt'

MAX_MSG_SIZE = config.get('MAX_MSG_SIZE', 1024)
MAX_FAILURES = config.get('MAX_FAILURES', 5)
BLOCK_TIME = config.get('BLOCK_TIME', 60)
SESSION_TIMEOUT = config.get('SESSION_TIMEOUT', 300.0)
MAX_WORKERS = config.get('MAX_WORKERS', 20)

clients = {}          # username -> {conn, ip, port, login_time, status}
clients_lock = threading.Lock()

stats = {'messages_processed': 0, 'broadcast_messages': 0, 'private_messages': 0}
stats_lock = threading.Lock()

failed_attempts = {}  # ip -> count
blocked_ips = {}      # ip -> unblock_timestamp

def init_files():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'sender', 'receiver', 'message_type', 'message'])
            
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'password_hash'])

def secure_log(event):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {event}\n"
    with open(SEC_LOG_FILE, 'a') as f:
        f.write(log_entry)
    print(f"[SECURITY] {event}")

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

def update_online_users():
    users = ",".join(get_user_list())
    broadcast(f"##USERS##:{users}")

def print_stats():
    with stats_lock:
        s = dict(stats)
    print(f"[STATS] Connected: {len(get_user_list())} | Processed: {s['messages_processed']} | Broadcast: {s['broadcast_messages']} | Private: {s['private_messages']}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, ip):
    if not re.match(r"^[a-zA-Z0-9_]{3,16}$", username):
        return False, "Invalid username. Use 3-16 alphanumeric chars."
    if len(password) < 4:
        return False, "Password too short (minimum 4 characters)."

    with open(USERS_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username:
                return False, "Username already exists."

    pwd_hash = hash_password(password)
    with open(USERS_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([username, pwd_hash])
        
    secure_log(f"New user registered: {username} from IP {ip}")
    return True, "Registration successful."

def authenticate_user(username, password, ip):
    if ip in blocked_ips and time.time() < blocked_ips[ip]:
        remaining = int(blocked_ips[ip] - time.time())
        secure_log(f"Blocked login attempt from {ip} (User: {username}) - {remaining}s left")
        return False, f"Too many failed attempts. Try again in {remaining}s."

    if not re.match(r"^[a-zA-Z0-9_]{3,16}$", username) or not password:
        return False, "Invalid username or empty password."

    authenticated = False
    
    with open(USERS_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username:
                if row['password_hash'] == hash_password(password):
                    authenticated = True
                break

    if authenticated:
        with clients_lock:
            if username in clients:
                secure_log(f"Duplicate login attempt for {username} from {ip}")
                return False, "User is already logged in."
        
        failed_attempts[ip] = 0
        if ip in blocked_ips:
            del blocked_ips[ip]
            
        secure_log(f"Successful login for {username} from {ip}")
        return True, "Login successful."
    else:
        attempts = failed_attempts.get(ip, 0) + 1
        failed_attempts[ip] = attempts
        secure_log(f"Failed login ({attempts}/{MAX_FAILURES}) for {username} from {ip}")
        
        if attempts >= MAX_FAILURES:
            blocked_ips[ip] = time.time() + BLOCK_TIME
            secure_log(f"IP {ip} temporarily blocked for {BLOCK_TIME}s")
            return False, f"Account locked. Try again in {BLOCK_TIME}s."
            
        return False, "Invalid username or password."

def handle_client(conn, addr):
    ip, port = addr
    username = None
    conn.settimeout(60.0)

    try:
        auth_data = conn.recv(1024).decode().strip()
        if not auth_data:
            conn.close()
            return
            
        parts = auth_data.split('|', 2)
        if len(parts) != 3:
            conn.sendall(b"ERROR|Invalid payload format.\n")
            conn.close()
            return
            
        action, user, pwd = parts
        
        if action == "REGISTER":
            success, msg = register_user(user, pwd, ip)
            conn.sendall(f"{'SUCCESS' if success else 'ERROR'}|{msg}\n".encode())
            conn.close() 
            return
        elif action == "LOGIN":
            success, msg = authenticate_user(user, pwd, ip)
            if not success:
                conn.sendall(f"ERROR|{msg}\n".encode())
                conn.close()
                return
            conn.sendall(b"SUCCESS|Authenticated.\n")
            username = user
        else:
            conn.sendall(b"ERROR|Unknown command.\n")
            conn.close()
            return

        with clients_lock:
            clients[username] = {
                'conn': conn,
                'ip': ip,
                'port': port,
                'login_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'online'
            }

        conn.settimeout(SESSION_TIMEOUT)
        secure_log(f"Session started: {username} ({ip}:{port})")

        log_message('SERVER', 'ALL', 'system', f"{username} joined the chat")
        broadcast(f"*** {username} has joined the chat ***", exclude=username)
        print_stats()
        update_online_users()

        history = get_last_messages(username, 5)
        if history:
            conn.sendall(b"--- Your last 5 messages ---\n")
            for row in history:
                conn.sendall(f"[{row['timestamp']}] {row['message']}\n".encode())
            conn.sendall(b"----------------------------\n")

        while True:
            try:
                data = conn.recv(8192) 
                if not data:
                    break
                
                if len(data) > MAX_MSG_SIZE:
                    conn.sendall(b"System Error: Message size exceeds 1024 bytes. Ignored.\n")
                    continue
                    
                msg = data.decode().strip()
                if not msg:
                    continue

                conn.settimeout(SESSION_TIMEOUT)

                if msg == '/quit':
                    secure_log(f"User {username} logged out normally.")
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
                elif msg.startswith('/'):
                    conn.sendall(b"System Error: Unsupported command.\n")
                else:
                    log_message(username, 'ALL', 'broadcast', msg)
                    broadcast(f"[{username}]: {msg}", exclude=username)
                    conn.sendall(b"[OK]\n") 
                    
            except socket.timeout:
                secure_log(f"Session timeout for {username} due to inactivity.")
                conn.sendall(b"System: Disconnected due to inactivity (5 mins).\n")
                break

    except (ConnectionResetError, BrokenPipeError) as e:
        # TASK 1: Connection Management - Detect disconnects automatically
        secure_log(f"Unexpected disconnect from {ip}:{port} ({e})")
    finally:
        # TASK 1: Release resources correctly
        if username:
            with clients_lock:
                if username in clients:
                    del clients[username]
            secure_log(f"Session ended: {username}")
            log_message('SERVER', 'ALL', 'system', f"{username} left the chat")
            broadcast(f"*** {username} has left the chat ***")
            update_online_users()
            print_stats()
            
        conn.close()

# TASK 2: Graceful Shutdown
def signal_handler(sig, frame):
    print("\n[SERVER] Initiating graceful shutdown...")
    secure_log("Server shut down gracefully by admin.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    init_files()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(MAX_WORKERS)
        print(f"Secure Chat Server listening on {HOST}:{PORT}")
        
        # TASK 3: Scalability Enhancement - Using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while True:
                conn, addr = server.accept()
                executor.submit(handle_client, conn, addr)
                
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        server.close()

if __name__ == '__main__':
    main()