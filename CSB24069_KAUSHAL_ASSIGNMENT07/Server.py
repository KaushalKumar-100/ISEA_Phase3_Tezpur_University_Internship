import socket
import threading
import csv
import os
import hashlib
import time
import re
from datetime import datetime

HOST = '0.0.0.0'
PORT = 5000
HISTORY_FILE = 'chat_history.csv'
USERS_FILE = 'users.csv'             # Database for user credentials
SEC_LOG_FILE = 'security_log.txt'    # File for Secure Logging

MAX_MSG_SIZE = 1024       # Task 4: Limit message size to prevent buffer overflow
MAX_FAILURES = 5          # Task 5: Max failed login attempts
BLOCK_TIME = 60           # Task 5: Penalty block time in seconds
SESSION_TIMEOUT = 300.0   # Task 6: Idle session timeout (5 minutes)

clients = {}          # username -> {conn, ip, port, login_time, status}
clients_lock = threading.Lock()

stats = {'messages_processed': 0, 'broadcast_messages': 0, 'private_messages': 0}
stats_lock = threading.Lock()

# IP tracking for Failed Login Protection
failed_attempts = {}  # ip -> count
blocked_ips = {}      # ip -> unblock_timestamp

def init_files():
    """Initialize necessary CSV files if they don't exist."""
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'sender', 'receiver', 'message_type', 'message'])
            
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'password_hash'])

def secure_log(event):
    """TASK 6: Secure logging mechanism without storing passwords"""
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

# ----------------------------------
# SECURITY FUNCTIONS
# ----------------------------------

def hash_password(password):
    """TASK 2: Secure Password Storage via SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, ip):
    """Handles User Registration and Validations"""
    # TASK 4: Input Validation
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
    """Handles Login Verification, Rate Limiting, and Duplicates"""
    # TASK 5: Failed Login Protection
    if ip in blocked_ips and time.time() < blocked_ips[ip]:
        remaining = int(blocked_ips[ip] - time.time())
        secure_log(f"Blocked login attempt from {ip} (User: {username}) - {remaining}s left")
        return False, f"Too many failed attempts. Try again in {remaining}s."

    # TASK 4: Input Validation
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
        # TASK 3: Duplicate Login Prevention
        with clients_lock:
            if username in clients:
                secure_log(f"Duplicate login attempt for {username} from {ip}")
                return False, "User is already logged in."
        
        # Reset failed attempts on success
        failed_attempts[ip] = 0
        if ip in blocked_ips:
            del blocked_ips[ip]
            
        secure_log(f"Successful login for {username} from {ip}")
        return True, "Login successful."
    else:
        # Increment failed attempts
        attempts = failed_attempts.get(ip, 0) + 1
        failed_attempts[ip] = attempts
        secure_log(f"Failed login ({attempts}/{MAX_FAILURES}) for {username} from {ip}")
        
        if attempts >= MAX_FAILURES:
            blocked_ips[ip] = time.time() + BLOCK_TIME
            secure_log(f"IP {ip} temporarily blocked for {BLOCK_TIME}s")
            return False, f"Account locked. Try again in {BLOCK_TIME}s."
            
        return False, "Invalid username or password."

# ----------------------------------
# CLIENT HANDLER
# ----------------------------------

def handle_client(conn, addr):
    ip, port = addr
    username = None
    # Short timeout for authentication phase
    conn.settimeout(60.0)

    try:
        # Wait for authentication payload: ACTION|username|password
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
            conn.close() # Close so client can navigate to login
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

        # Add to Active Sessions
        with clients_lock:
            clients[username] = {
                'conn': conn,
                'ip': ip,
                'port': port,
                'login_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'online'
            }

        # TASK 6: Set Session Inactivity Timeout
        conn.settimeout(SESSION_TIMEOUT)
        secure_log(f"Session started: {username} ({ip}:{port})")

        log_message('SERVER', 'ALL', 'system', f"{username} joined the chat")
        broadcast(f"*** {username} has joined the chat ***", exclude=username)
        print_stats()
        update_online_users()

        # History Feature
        history = get_last_messages(username, 5)
        if history:
            conn.sendall(b"--- Your last 5 messages ---\n")
            for row in history:
                conn.sendall(f"[{row['timestamp']}] {row['message']}\n".encode())
            conn.sendall(b"----------------------------\n")

        # Message Loop
        while True:
            try:
                data = conn.recv(8192) # Listen up to 8KB to check bounds
                if not data:
                    break
                
                # TASK 4: Reject Oversized Messages
                if len(data) > MAX_MSG_SIZE:
                    conn.sendall(b"System Error: Message size exceeds 1024 bytes. Ignored.\n")
                    continue
                    
                msg = data.decode().strip()
                if not msg:
                    continue

                # Reset inactivity timer since user is active
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
                    # TASK 4: Unsupported command validation
                    conn.sendall(b"System Error: Unsupported command.\n")
                else:
                    log_message(username, 'ALL', 'broadcast', msg)
                    broadcast(f"[{username}]: {msg}", exclude=username)
                    conn.sendall(b"[OK]\n") 
                    
            except socket.timeout:
                # TASK 6: Session Inactivity Timeout
                secure_log(f"Session timeout for {username} due to inactivity.")
                conn.sendall(b"System: Disconnected due to inactivity (5 mins).\n")
                break

    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
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

def main():
    init_files()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(20)
    print(f"Secure Chat Server listening on {HOST}:{PORT}")
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