
import csv
import os
import matplotlib.pyplot as plt

os.makedirs('graphs', exist_ok=True)

with open('performance_results.csv') as f:
    reader = list(csv.DictReader(f))

clients = [int(r['clients']) for r in reader]
delay = [float(r['avg_delay_ms']) for r in reader]
throughput = [float(r['throughput_msgs_per_sec']) for r in reader]
broadcast = [int(r['broadcast_messages']) for r in reader]
private = [int(r['private_messages']) for r in reader]

# 1. Clients vs Average Delivery Time
plt.figure()
plt.plot(clients, delay, marker='o')
plt.xlabel('Number of Clients')
plt.ylabel('Average Delivery Time (ms)')
plt.title('Clients vs Average Delivery Time')
plt.grid(True)
plt.savefig('graphs/clients_vs_delay.png')
plt.close()

# 2. Clients vs Throughput
plt.figure()
plt.plot(clients, throughput, marker='o', color='green')
plt.xlabel('Number of Clients')
plt.ylabel('Throughput (msgs/sec)')
plt.title('Clients vs Throughput')
plt.grid(True)
plt.savefig('graphs/clients_vs_throughput.png')
plt.close()

# 3. Broadcast vs Private Messages
plt.figure()
x = range(len(clients))
plt.bar([i - 0.2 for i in x], broadcast, width=0.4, label='Broadcast')
plt.bar([i + 0.2 for i in x], private, width=0.4, label='Private')
plt.xticks(list(x), [f"{c} clients" for c in clients])
plt.ylabel('Number of Messages')
plt.title('Broadcast vs Private Messages')
plt.legend()
plt.savefig('graphs/message_type_distribution.png')
plt.close()

print("Graphs saved in graphs/ directory")