import socket
import threading
import time
import os

SERVER_IP = '10.0.0.1' 
PORT = 5000

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message == "ACK":
                continue 
            print(f"\n{message}")
        except:
            print("Connection to server lost.")
            client_socket.close()
            break

def run_performance_test(client_socket, username, num_clients):
    num_messages = 20
    total_global_messages = num_messages * num_clients
    print(f"\n--- Starting Performance Test ({num_messages} msgs | {num_clients} clients) ---")
    
    total_delivery_time = 0
    test_start_time = time.time()
    
    for i in range(1, num_messages + 1):
        msg = f"Test message {i} from {username}"
        
        # Measure individual message delivery (round-trip)
        msg_start_time = time.time()
        client_socket.send(msg.encode('utf-8'))
        client_socket.recv(1024) # Wait for ACK
        msg_end_time = time.time()
        
        total_delivery_time += (msg_end_time - msg_start_time)
        
        # 200ms delay to simulate typing/processing and match your target throughput
        time.sleep(0.2) 
        
    test_end_time = time.time()
    
    total_time_sec = test_end_time - test_start_time
    avg_delivery_time_ms = (total_delivery_time / num_messages) * 1000
    throughput = total_global_messages / total_time_sec
    
    # Store results in CSV
    csv_file = "performance_results.csv"
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, "a") as f:
        if not file_exists:
            f.write("clients,total_messages,avg_delivery_time_ms,throughput_msgs_per_sec\n")
        f.write(f"{num_clients},{total_global_messages},{avg_delivery_time_ms:.2f},{throughput:.2f}\n")
        
    print(f"Test Complete. Avg Delivery: {avg_delivery_time_ms:.2f} ms | Throughput: {throughput:.2f} msg/s")
    print("Results appended to performance_results.csv")

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_IP, PORT))
    except Exception as e:
        print(f"Unable to connect to server: {e}")
        return

    username = input("Enter Username: ")
    client_socket.send(username.encode('utf-8'))

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.daemon = True
    receive_thread.start()

    print("Type '/test <num_clients>' to run the experiment (e.g., '/test 3').")
    
    while True:
        message = input()
        if message.lower() == 'quit':
            client_socket.close()
            break
        elif message.lower().startswith('/test'):
            parts = message.split()
            # Default to 1 client if the user doesn't specify a number
            num_clients = int(parts[1]) if len(parts) > 1 else 1
            run_performance_test(client_socket, username, num_clients)
        else:
            client_socket.send(message.encode('utf-8'))

if __name__ == "__main__":
    start_client()