import socket
import threading
import time
import json
import sys

# Load Configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    SERVER_IP = config.get('SERVER_IP', '10.0.0.1')
    SERVER_PORT = config.get('SERVER_PORT', 5000)
except Exception as e:
    print("[ERROR] Could not load config.json. Make sure it exists.")
    sys.exit(1)

def simulate_client(client_id, num_messages=10):
    """Simulates a single headless client connecting and sending messages."""
    username = f"bot_user_{client_id}"
    password = "password123"
    
    # Step 1: Register (Fails silently if user already exists, which is fine)
    try:
        reg_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        reg_sock.connect((SERVER_IP, SERVER_PORT))
        reg_sock.send(f"REGISTER|{username}|{password}".encode())
        reg_sock.recv(1024)
        reg_sock.close()
    except Exception:
        pass
        
    time.sleep(0.5) # Brief pause before login
    
    # Step 2: Login and Send Messages
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, SERVER_PORT))
        s.send(f"LOGIN|{username}|{password}".encode())
        
        response = s.recv(1024).decode()
        if not response.startswith("SUCCESS"):
            print(f"[{username}] Login failed: {response.strip()}")
            s.close()
            return
            
        # Clear out the initial history/welcome messages from the buffer
        s.settimeout(1.0)
        try:
            while True:
                s.recv(4096)
        except socket.timeout:
            pass 
        s.settimeout(None)
        
        # Step 3: Send exactly `num_messages` messages
        for i in range(num_messages):
            msg = f"Automated test message {i+1} from {username}"
            s.send(msg.encode())
            
            # Wait for server acknowledgment or broadcast to ensure sync
            s.recv(1024) 
            time.sleep(0.1) # 100ms delay to simulate natural pacing and prevent buffer overflow
            
        # Step 4: Disconnect
        s.send("/quit".encode())
        s.close()
        print(f"[✓] {username} successfully completed {num_messages} messages.")
        
    except Exception as e:
        print(f"[X] Error in {username}: {e}")

def run_experiment(num_clients):
    """Runs a batch of concurrent clients."""
    print(f"\n{'='*50}")
    print(f"🚀 STARTING EXPERIMENT: {num_clients} CONCURRENT CLIENTS")
    print(f"{'='*50}")
    
    threads = []
    start_time = time.time()
    
    # Spawn threads for concurrent execution
    for i in range(num_clients):
        t = threading.Thread(target=simulate_client, args=(i, 10))
        threads.append(t)
        t.start()
        
    # Wait for all clients to finish
    for t in threads:
        t.join()
        
    duration = time.time() - start_time
    total_messages = num_clients * 10
    throughput = total_messages / duration
    
    print(f"\n📊 RESULTS FOR {num_clients} CLIENTS:")
    print(f"Time Taken: {duration:.2f} seconds")
    print(f"Throughput: {throughput:.2f} messages/second")
    print(f"Average Delay per message: {(duration/total_messages)*1000:.2f} ms")

if __name__ == "__main__":
    # Test using 5, 8, and 10 concurrent clients
    experiment_sizes = [5, 8, 10]
    
    for size in experiment_sizes:
        run_experiment(size)
        print("\nCooling down for 3 seconds before next batch...")
        time.sleep(3)
        
    print("\n✅ All automated experiments completed!")