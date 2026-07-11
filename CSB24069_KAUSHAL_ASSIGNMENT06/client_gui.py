import socket
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

SERVER_IP = "10.0.0.1"      # Change if needed
SERVER_PORT = 5000

client = None
username = ""

# -----------------------------
# Login Window
# -----------------------------
login = tk.Tk()
login.title("Chat Login")
login.geometry("350x200")
login.resizable(False, False)

tk.Label(login, text="Username", font=("Arial", 12)).pack(pady=10)

username_entry = tk.Entry(login, width=30)
username_entry.pack()

status_login = tk.Label(login, text="", fg="red")
status_login.pack(pady=5)


# -----------------------------
# Chat Window
# -----------------------------
chat = tk.Toplevel(login)
chat.title("TCP Chat Application")
chat.geometry("800x500")
chat.protocol("WM_DELETE_WINDOW", lambda: None)
chat.withdraw()

# -----------------------------
# Left Frame
# -----------------------------
left_frame = tk.Frame(chat)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

chat_area = ScrolledText(
    left_frame,
    wrap=tk.WORD,
    state='disabled',
    font=("Consolas", 10)
)

chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

bottom_frame = tk.Frame(left_frame)
bottom_frame.pack(fill=tk.X)

message_entry = tk.Entry(bottom_frame, font=("Arial", 11))
message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

send_button = tk.Button(
    bottom_frame,
    text="Send",
    width=10
)
send_button.pack(side=tk.RIGHT, padx=5)

# -----------------------------
# Right Frame
# -----------------------------
right_frame = tk.Frame(chat, width=180)
right_frame.pack(side=tk.RIGHT, fill=tk.Y)

tk.Label(
    right_frame,
    text="Online Users",
    font=("Arial", 12, "bold")
).pack(pady=5)

users_list = tk.Listbox(right_frame)
users_list.pack(fill=tk.BOTH, expand=True, padx=5)

disconnect_button = tk.Button(
    right_frame,
    text="Disconnect",
    bg="red",
    fg="white",
    width=15
)

disconnect_button.pack(pady=10)

status_label = tk.Label(
    right_frame,
    text="Disconnected",
    fg="red"
)

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
# Connect Function
# -----------------------------
def connect_server():
    global client
    global username

    username = username_entry.get().strip()

    if username == "":
        messagebox.showerror("Error", "Username cannot be empty")
        return

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, SERVER_PORT))

        # Receive "Enter username:"
        client.recv(1024)

        client.send(username.encode())

        status_label.config(
            text="Connected",
            fg="green"
        )

        login.withdraw()
        chat.deiconify()

        append_message(f"Connected as {username}")

        # Receive thread will start here
        # (Added in Part 2)

    except Exception as e:
        messagebox.showerror(
            "Connection Error",
            str(e)
        )


connect_button = tk.Button(
    login,
    text="Connect",
    width=15,
    command=connect_server
)

connect_button.pack(pady=15)

# -----------------------------
# Receive Messages
# -----------------------------
def receive_messages():
    while True:
        try:
            message = client.recv(4096).decode()

            if not message:
                break

            for line in message.strip().split("\n"):

                # Online users update
                if line.startswith("##USERS##:"):
                    users = line.replace("##USERS##:", "").split(",")

                    users_list.delete(0, tk.END)

                    for user in users:
                        if user.strip():
                            users_list.insert(tk.END, user.strip())

                else:
                    append_message(line)

        except:
            append_message("Disconnected from server.")
            break


# -----------------------------
# Send Message
# -----------------------------
def send_message():

    msg = message_entry.get().strip()

    if msg == "":
        return

    try:
        client.send(msg.encode())

        # Show sender's own broadcast
        if not msg.startswith("/"):
            append_message(f"[You]: {msg}")

        elif msg.startswith("/msg"):
            append_message(msg)

        message_entry.delete(0, tk.END)

    except:
        messagebox.showerror(
            "Error",
            "Unable to send message."
        )


# -----------------------------
# Disconnect
# -----------------------------
def disconnect():

    try:
        client.send("/quit".encode())
        client.close()
    except:
        pass

    chat.destroy()
    login.destroy()


# -----------------------------
# Start Receive Thread
# -----------------------------
def start_receive_thread():

    thread = threading.Thread(
        target=receive_messages,
        daemon=True
    )

    thread.start()


# -----------------------------
# Connect Server (Updated)
# Replace the old connect_server()
# with this one.
# -----------------------------
def connect_server():

    global client
    global username

    username = username_entry.get().strip()

    if username == "":
        messagebox.showerror(
            "Error",
            "Username cannot be empty."
        )
        return

    try:

        client = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        client.connect(
            (SERVER_IP, SERVER_PORT)
        )

        # Receive:
        # Enter username:
        client.recv(1024)

        client.send(username.encode())

        status_label.config(
            text="Connected",
            fg="green"
        )

        login.withdraw()

        chat.deiconify()

        append_message(
            f"Connected as {username}"
        )

        start_receive_thread()

    except Exception as e:

        messagebox.showerror(
            "Connection Error",
            str(e)
        )


# -----------------------------
# Bind Buttons
# -----------------------------
send_button.config(
    command=send_message
)

disconnect_button.config(
    command=disconnect
)

message_entry.bind(
    "<Return>",
    lambda event: send_message()
)

connect_button.config(
    command=connect_server
)


# -----------------------------
# Main Loop
# -----------------------------
login.mainloop()