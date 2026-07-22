import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Create the graphs/ directory if it doesn't exist (Required by Task 5)
output_dir = 'graphs'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Helper function to generate dummy data if the CSV doesn't exist yet
def create_dummy_csv(filename):
    data = {
        'Clients': [5, 5, 8, 8, 10, 10],
        'State': ['Before', 'After', 'Before', 'After', 'Before', 'After'],
        'Throughput_msgs_per_sec': [45.2, 58.4, 60.1, 85.3, 65.5, 98.7],
        'Delay_ms': [15.2, 8.4, 25.4, 12.1, 45.3, 15.6],
        'CPU_Usage_Percent': [12.5, 8.2, 18.4, 10.5, 28.9, 14.2],
        'Memory_Usage_MB': [45.0, 46.5, 55.2, 48.1, 75.8, 52.3]
    }
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Created sample {filename} for testing.")

csv_file = 'performance_results.csv'

# Check if CSV exists, if not, create a dummy one for demonstration
if not os.path.exists(csv_file):
    create_dummy_csv(csv_file)

# Read the data
try:
    df = pd.read_csv(csv_file)
except Exception as e:
    print(f"Error reading {csv_file}: {e}")
    exit(1)

# Ensure data is sorted for consistent plotting
df = df.sort_values(by=['Clients', 'State'], ascending=[True, False])

# Separate data into 'Before' and 'After'
before_data = df[df['State'] == 'Before'].set_index('Clients')
after_data = df[df['State'] == 'After'].set_index('Clients')

clients = before_data.index.tolist()
x = np.arange(len(clients))  # the label locations
width = 0.35  # the width of the bars

# Dictionary mapping dataframe column names to graph titles and Y-axis labels
metrics = {
    'Throughput_msgs_per_sec': ('Throughput Comparison', 'Messages per Second'),
    'Delay_ms': ('Network Delay Comparison', 'Delay (ms)'),
    'CPU_Usage_Percent': ('CPU Usage Comparison', 'CPU Usage (%)'),
    'Memory_Usage_MB': ('Memory Usage Comparison', 'Memory Usage (MB)')
}

# Generate and save a graph for each metric
for column, (title, ylabel) in metrics.items():
    if column not in df.columns:
        print(f"Warning: Column '{column}' not found in CSV. Skipping.")
        continue

    fig, ax = plt.subplots(figsize=(8, 5))
    
    rects1 = ax.bar(x - width/2, before_data[column], width, label='Before Optimization', color='#d9534f')
    rects2 = ax.bar(x + width/2, after_data[column], width, label='After Optimization', color='#5cb85c')

    # Add text for labels, title and custom x-axis tick labels, etc.
    ax.set_xlabel('Number of Concurrent Clients')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(clients)
    ax.legend()

    # Add values on top of the bars for better readability
    ax.bar_label(rects1, padding=3, fmt='%.1f')
    ax.bar_label(rects2, padding=3, fmt='%.1f')

    fig.tight_layout()

    # Save the figure in the graphs directory
    filename = f"{output_dir}/{column.split('_')[0].lower()}_comparison.png"
    plt.savefig(filename, dpi=300)
    print(f"Saved graph: {filename}")
    
    plt.close()

print("\nAll graphs generated successfully! You can find them in the 'graphs/' folder.")