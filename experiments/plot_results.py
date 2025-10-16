import json
import matplotlib.pyplot as plt
import numpy as np
import os

# === Helper: Load JSON safely ===
def load_results(filename):
    if not os.path.exists(filename):
        print(f"⚠️ File not found: {filename}")
        return None
    with open(filename) as f:
        return json.load(f)

# === Load all result sets ===
baseline = load_results("results_baseline.json")
delay = load_results("results_delay.json")
churn_base = load_results("results_churn_baseline.json")
churn_delay = load_results("results_churn_delay.json")

if not any([baseline, delay, churn_base, churn_delay]):
    raise FileNotFoundError("No results files found. Run experiments.py first.")

# === Function to extract arrays ===
def extract_metrics(results):
    nodes = [r["nodes"] for r in results]
    latency = [r["avg_latency_sec"] for r in results]
    stdev = [r["stdev_latency_sec"] for r in results]
    throughput = [r["throughput_ops_per_sec"] for r in results]
    success_rate = [r["success_rate"] * 100 for r in results]
    return nodes, latency, stdev, throughput, success_rate

# === Function to extract churn metrics ===
def extract_churn_metrics(results):
    churn = [r["failure_probability"] * 100 for r in results]
    latency = [r["avg_latency_sec"] for r in results]
    p95 = [r.get("p95_latency_sec", None) for r in results]
    success = [r["success_rate"] * 100 for r in results]
    return churn, latency, p95, success

# === Extract baseline/delay ===
nodes_base, lat_base, std_base, thr_base, succ_base = extract_metrics(baseline) if baseline else ([], [], [], [], [])
nodes_delay, lat_delay, std_delay, thr_delay, succ_delay = extract_metrics(delay) if delay else ([], [], [], [], [])

# === Plot 1: Latency Comparison ===
plt.figure(figsize=(8, 5))
if baseline:
    plt.errorbar(nodes_base, lat_base, yerr=std_base, fmt='-o', color='royalblue',
                 ecolor='lightgray', elinewidth=2, capsize=5, label='Baseline')
if delay:
    plt.errorbar(nodes_delay, lat_delay, yerr=std_delay, fmt='-s', color='crimson',
                 ecolor='pink', elinewidth=2, capsize=5, label='With Delay')

plt.title("Chord DHT: Average Lookup Latency vs Number of Nodes", fontsize=13, weight='bold')
plt.xlabel("Number of Nodes", fontsize=12)
plt.ylabel("Average Latency (seconds)", fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig("latency_comparison.png", dpi=300)
print("Saved latency_comparison.png")

# === Plot 2: Throughput Comparison ===
plt.figure(figsize=(8, 5))
if baseline:
    plt.plot(nodes_base, thr_base, marker='o', color='forestgreen', linewidth=2, label='Baseline')
if delay:
    plt.plot(nodes_delay, thr_delay, marker='s', color='darkorange', linewidth=2, label='With Delay')

plt.title("Chord DHT: Throughput vs Number of Nodes", fontsize=13, weight='bold')
plt.xlabel("Number of Nodes", fontsize=12)
plt.ylabel("Throughput (operations per second)", fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig("throughput_comparison.png", dpi=300)
print("Saved throughput_comparison.png")

# === Plot 3: Success Rate Comparison ===
plt.figure(figsize=(8, 5))
width = 2.5
if baseline and delay and len(nodes_base) == len(nodes_delay):
    x = np.arange(len(nodes_base))
    plt.bar(x - 0.15, succ_base, width=0.3, label='Baseline', color='steelblue', alpha=0.8)
    plt.bar(x + 0.15, succ_delay, width=0.3, label='With Delay', color='tomato', alpha=0.8)
    plt.xticks(x, nodes_base)
else:
    if baseline:
        plt.bar(nodes_base, succ_base, color='steelblue', alpha=0.8, label='Baseline')
    if delay:
        plt.bar(nodes_delay, succ_delay, color='tomato', alpha=0.8, label='With Delay')

plt.title("Chord DHT: Success Rate vs Number of Nodes", fontsize=13, weight='bold')
plt.xlabel("Number of Nodes", fontsize=12)
plt.ylabel("Success Rate (%)", fontsize=12)
plt.legend()
plt.ylim(0, 110)
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig("success_rate_comparison.png", dpi=300)
print("Saved success_rate_comparison.png")

# === Plot 4: Trade-off — Latency vs Throughput ===
plt.figure(figsize=(8, 5))
if baseline:
    plt.scatter(lat_base, thr_base, color='royalblue', s=80, label='Baseline')
    for i, n in enumerate(nodes_base):
        plt.text(lat_base[i] + 0.0003, thr_base[i] + 0.1, f"{n} nodes", fontsize=8)
if delay:
    plt.scatter(lat_delay, thr_delay, color='crimson', s=80, marker='s', label='With Delay')
    for i, n in enumerate(nodes_delay):
        plt.text(lat_delay[i] + 0.0003, thr_delay[i] - 0.2, f"{n} nodes", fontsize=8)

plt.title("Chord DHT: Trade-off Between Latency and Throughput", fontsize=13, weight='bold')
plt.xlabel("Average Latency (seconds)", fontsize=12)
plt.ylabel("Throughput (operations per second)", fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig("tradeoff_latency_throughput.png", dpi=300)
print("Saved tradeoff_latency_throughput.png")

# === Plot 5: Churn Sensitivity (if available) ===
if churn_base or churn_delay:
    plt.figure(figsize=(8, 5))
    if churn_base:
        churns, lat, p95, succ = extract_churn_metrics(churn_base)
        plt.errorbar(churns, lat, yerr=None, fmt='-o', color='dodgerblue', label='Baseline')
    if churn_delay:
        churns_d, lat_d, p95_d, succ_d = extract_churn_metrics(churn_delay)
        plt.errorbar(churns_d, lat_d, yerr=None, fmt='-s', color='firebrick', label='With Delay')
    plt.title("Chord DHT: Average Latency vs Failure Probability (Churn)", fontsize=13, weight='bold')
    plt.xlabel("Failure Probability (%)", fontsize=12)
    plt.ylabel("Average Latency (seconds)", fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig("churn_latency_comparison.png", dpi=300)
    print("Saved churn_latency_comparison.png")

    # Success rate under churn
    plt.figure(figsize=(8, 5))
    if churn_base:
        plt.plot(churns, succ, marker='o', color='mediumblue', linewidth=2, label='Baseline')
    if churn_delay:
        plt.plot(churns_d, succ_d, marker='s', color='orangered', linewidth=2, label='With Delay')
    plt.title("Chord DHT: Success Rate vs Failure Probability (Churn)", fontsize=13, weight='bold')
    plt.xlabel("Failure Probability (%)", fontsize=12)
    plt.ylabel("Success Rate (%)", fontsize=12)
    plt.ylim(0, 110)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig("churn_success_comparison.png", dpi=300)
    print("Saved churn_success_comparison.png")

# === Summary ===
print("\n=== Summary ===")
if baseline:
    print(f"Baseline → Avg Latency: {np.mean(lat_base)*1000:.2f} ms | Avg Throughput: {np.mean(thr_base):.2f} ops/s | Avg Success: {np.mean(succ_base):.1f}%")
if delay:
    print(f"With Delay → Avg Latency: {np.mean(lat_delay)*1000:.2f} ms | Avg Throughput: {np.mean(thr_delay):.2f} ops/s | Avg Success: {np.mean(succ_delay):.1f}%")
if churn_base:
    churns, lat, p95, succ = extract_churn_metrics(churn_base)
    print(f"Churn (Baseline) → Avg Latency: {np.mean(lat)*1000:.2f} ms | Avg Success: {np.mean(succ):.1f}%")
if churn_delay:
    churns_d, lat_d, p95_d, succ_d = extract_churn_metrics(churn_delay)
    print(f"Churn (With Delay) → Avg Latency: {np.mean(lat_d)*1000:.2f} ms | Avg Success: {np.mean(succ_d):.1f}%")
