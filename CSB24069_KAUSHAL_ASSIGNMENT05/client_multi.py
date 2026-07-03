import socket
import threading
import sys
import time


def receive_messages(sock):
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("\n[Disconnected from server]")
                break
            print(data.decode(), end='')
        except OSError:
            break


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 client.py <server_ip> <port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    port = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, port))

    prompt = sock.recv(1024).decode()
    print(prompt, end='')
    username = input()
    sock.sendall(username.encode())

    t = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    t.start()

    time.sleep(0.3)
    print("Connected. Commands: /msg <user> <message>, /list, /stats, /quit")

    try:
        while True:
            msg = input()
            if not msg:
                continue
            sock.sendall(msg.encode())
            if msg == '/quit':
                break
    except (KeyboardInterrupt, EOFError):
        try:
            sock.sendall(b'/quit')
        except OSError:
            pass
    finally:
        sock.close()


if __name__ == '__main__':
    main()