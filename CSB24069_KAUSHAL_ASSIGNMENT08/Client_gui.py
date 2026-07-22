import socket
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import json
import time
import sys

# TASK 4: Configuration Management
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    SERVER_IP = config.get('SERVER_IP', '10.0.0.1')
    SERVER_PORT = config.get('SERVER_PORT', 5000)
except Exception as e:
    messagebox.showerror("Config Error", "Could not load config.json. Using defaults.")
    SERVER_IP = "10.0.0.1"
    SERVER_PORT = 5000

client = None
username = ""
is_connected = False

# -----------------------------
# Login Window
# -----------------------------
login = tk.Tk()
login.title("Chat Login / Register")
login.geometry("350x300")
login.resizable(False, False)

tk.Label(login, text="Username", font=("Arial", 12)).pack(pady=(20, 5))
username_entry = tk.Entry(login, width=30)
username_entry.pack()

tk.Label(login, text="Password", font=("Arial", 12)).pack(pady=(10, 5))
password_entry = tk.Entry(login, width=30, show="*") 
password_entry.pack()

status_login = tk.Label(login, text="", fg="red")
status_login.pack(pady=5)

# -----------------------------
# Chat Window
# -----------------------------
chat = tk.Toplevel(login)
chat.title("Secure TCP Chat Application")
chat.geometry("800x500")
chat.withdraw()

left_frame = tk.Frame(chat)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

chat_area = ScrolledText(left_frame, wrap=tk.WORD, state='disabled', font=("Consolas", 10))
chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

bottom_frame = tk.Frame(left_frame)
bottom_frame.pack(fill=tk.X)

message_entry = tk.Entry(bottom_frame, font=("Arial", 11))
message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

send_button = tk.Button(bottom_frame, text="Send", width=10)
send_button.pack(side=tk.RIGHT, padx=5)

right_frame = tk.Frame(chat, width=180)
right_frame.pack(side=tk.RIGHT, fill=tk.Y)

tk.Label(right_frame, text="Online Users", font=("Arial", 12, "bold")).pack(pady=5)
users_list = tk.Listbox(right_frame)
users_list.pack(fill=tk.BOTH, expand=True, padx=5)

disconnect_button = tk.Button(right_frame, text="Disconnect", bg="red", fg="white", width=15)
disconnect_button.pack(pady=10)

status_label = tk.Label(right_frame, text="Disconnected", fg="red")
status_label.pack(pady=5)

# -----------------------------
# Helper Function
# -----------------------------
def append_message(msg):
    chat_area.config(state='normal')
    chat_area.insert(tk.END, msg + "\n")
    chat_area.config(state='disabled')
    chat_area.yview(tk.END)

# -----------------------------
# Receive Messages
# -----------------------------
def receive_messages():
    global is_connected
    while is_connected:
        try:
            message = client.recv(4096).decode()
            if not message:
                break

            for line in message.strip().split("\n"):
                if line.startswith("##USERS##:"):
                    users = line.replace("##USERS##:", "").split(",")
                    users_list.delete(0, tk.END)
                    for user in users:
                        if user.strip():
                            users_list.insert(tk.END, user.strip())
                else:
                    append_message(line)
        except Exception as e:
            if is_connected:
                # TASK 1 & 2: Meaningful error message upon automatic disconnection detection
                append_message("\n[SYSTEM] Connection lost with the server.")
                status_label.config(text="Disconnected", fg="red")
                is_connected = False
            break

# -----------------------------
# Send Message
# -----------------------------
def send_message():
    msg = message_entry.get().strip()
    if msg == "" or not is_connected:
        return
    try:
        client.send(msg.encode())
        if not msg.startswith("/"):
            append_message(f"[You]: {msg}")
        elif msg.startswith("/msg"):
            append_message(msg)
        message_entry.delete(0, tk.END)
    except:
        messagebox.showerror("Error", "Unable to send message. Server might be down.")

# -----------------------------
# Graceful Shutdown & Disconnect
# -----------------------------
def disconnect():
    global is_connected
    is_connected = False
    try:
        if client:
            client.send("/quit".encode())
            client.close()
    except:
        pass

def on_closing():
    # TASK 2: Graceful Shutdown handling on the client side
    disconnect()
    try:
        chat.destroy()
        login.destroy()
    except:
        pass
    sys.exit(0)

login.protocol("WM_DELETE_WINDOW", on_closing)
chat.protocol("WM_DELETE_WINDOW", on_closing)

def start_receive_thread():
    thread = threading.Thread(target=receive_messages, daemon=True)
    thread.start()

# -----------------------------
# Authentication & Reconnection
# -----------------------------
def perform_auth(action):
    global client
    global username
    global is_connected

    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if not username or not password:
        messagebox.showerror("Error", "Username and password cannot be empty.")
        return

    # TASK 2: Automatic Reconnection mechanism
    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5.0) # TASK 2: Timeout Handling
            client.connect((SERVER_IP, SERVER_PORT))
            client.settimeout(None) 
            
            auth_msg = f"{action}|{username}|{password}"
            client.send(auth_msg.encode())

            response = client.recv(1024).decode().strip()

            if response.startswith("SUCCESS"):
                if action == "LOGIN":
                    is_connected = True
                    status_label.config(text="Connected", fg="green")
                    login.withdraw()
                    chat.deiconify()
                    append_message(f"Connected as {username}")
                    start_receive_thread()
                else:
                    messagebox.showinfo("Success", "Registration successful! You can now log in.")
                    client.close()
            else:
                error_msg = response.split("|")[1] if "|" in response else "Unknown Error"
                # TASK 1: Display meaningful error messages
                messagebox.showerror("Authentication Failed", error_msg)
                client.close()
            return

        except socket.timeout:
            messagebox.showwarning("Timeout", f"Connection timed out. Retrying... ({attempt+1}/{max_retries})")
            time.sleep(1)
        except Exception as e:
            if attempt == max_retries - 1:
                messagebox.showerror("Connection Error", f"Failed to connect after {max_retries} attempts.\nError: {str(e)}")
            time.sleep(1)

def manual_disconnect():
    disconnect()
    chat.withdraw()
    login.deiconify()
    password_entry.delete(0, tk.END)

# -----------------------------
# Bind Buttons
# -----------------------------
login_button = tk.Button(login, text="Login", width=15, command=lambda: perform_auth("LOGIN"))
login_button.pack(pady=(15, 5))

register_button = tk.Button(login, text="Register", width=15, command=lambda: perform_auth("REGISTER"))
register_button.pack(pady=5)

send_button.config(command=send_message)
disconnect_button.config(command=manual_disconnect)
message_entry.bind("<Return>", lambda event: send_message())

# -----------------------------
# Main Loop
# -----------------------------
if __name__ == "__main__":
    login.mainloop()