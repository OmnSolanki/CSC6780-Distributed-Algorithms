import subprocess
import time
import statistics
import json
import signal
import random
import os
import argparse
import math

# === Experiment Parameters ===
NUM_NODES = [5, 10, 15, 20, 25]
LOOKUPS_PER_NODE = 10
STABILIZATION_DELAY = 5
NETWORK_DELAY_RANGE = (0.005, 0.03)   # artificial delay between messages
FAILURE_PROBABILITY = 0.15            # default failure probability
CHURN_LEVELS = [0.0, 0.10, 0.20, 0.30]  # for churn experiment


# === Utility: Inject or remove artificial delay ===
def inject_network_delay():
    """Inject a small artificial delay into ../core/network.py for realism."""
    network_path = "../core/network.py"

    with open(network_path, "r") as f:
        content = f.read()

    if "# ADDED_DELAY_FLAG" not in content:
        content = content.replace(
            "s.sendall(str(msg) + \"\\r\\n\")",
            f"import time, random  # ADDED_DELAY_FLAG\n"
            f"time.sleep(random.uniform({NETWORK_DELAY_RANGE[0]}, {NETWORK_DELAY_RANGE[1]}))\n"
            "s.sendall(str(msg) + \"\\r\\n\")"
        )
        with open(network_path, "w") as f:
            f.write(content)
        print(f"Injected simulated network delay between {NETWORK_DELAY_RANGE[0]}–{NETWORK_DELAY_RANGE[1]} seconds.")
    else:
        print("Network delay already injected. Skipping reinjection.")


def remove_network_delay():
    """Remove previously injected artificial delay from ../core/network.py."""
    network_path = "../core/network.py"
    with open(network_path, "r") as f:
        content = f.read()

    if "# ADDED_DELAY_FLAG" in content:
        lines = content.splitlines()
        clean_lines = [
            line for line in lines
            if "# ADDED_DELAY_FLAG" not in line and "time.sleep(random.uniform" not in line
        ]
        cleaned_content = "\n".join(clean_lines)
        with open(network_path, "w") as f:
            f.write(cleaned_content)
        print("Removed injected network delay.")
    else:
        print("No artificial delay found — network.py already clean.")


def p95(values):
    """Compute 95th percentile latency."""
    if not values:
        return None
    s = sorted(values)
    k = int(math.ceil(0.95 * len(s))) - 1
    k = max(0, min(k, len(s)-1))
    return s[k]


# === Core experiment ===
def run_experiment(n):
    """Run one experiment with n nodes and current FAILURE_PROBABILITY."""
    print(f"\n=== Running experiment with {n} nodes (fail_prob={FAILURE_PROBABILITY}) ===")
    start_time = time.time()

    process = subprocess.Popen(
        ["python3", "create_chord.py", str(n)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    print("Waiting for network to stabilize...")
    time.sleep(STABILIZATION_DELAY)

    lookup_times = []
    successes = 0
    failures = 0

    for i in range(LOOKUPS_PER_NODE):
        t0 = time.time()
        target_port = 10000 + (i % n)

        # Random node failure simulation
        if random.random() < FAILURE_PROBABILITY:
            print(f"Simulating node failure at port {target_port}")
            try:
                os.system(f"kill -9 $(lsof -ti tcp:{target_port}) 2>/dev/null")
                failures += 1
                time.sleep(0.5)
            except Exception:
                pass
            continue

        try:
            subprocess.run(
                ["python3", "query_chord.py", str(target_port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15
            )
            successes += 1
            latency = time.time() - t0
            lookup_times.append(latency)
            print(f"Lookup {i+1} done ({latency:.3f}s)")
        except subprocess.TimeoutExpired:
            print(f"Lookup {i+1} timed out.")
            failures += 1
            continue

    # Compute metrics
    avg_latency = statistics.mean(lookup_times) if lookup_times else None
    stdev_latency = statistics.stdev(lookup_times) if len(lookup_times) > 1 else 0
    p95_latency = p95(lookup_times) if lookup_times else None
    throughput = successes / sum(lookup_times) if lookup_times else 0
    total_time = time.time() - start_time

    # Shutdown network
    process.send_signal(signal.SIGTERM)
    process.wait(timeout=5)

    print(f"Done → latency={avg_latency:.3f}s ±{stdev_latency:.3f}, p95={p95_latency:.3f}, throughput={throughput:.2f} ops/s")

    return {
        "nodes": n,
        "failure_probability": FAILURE_PROBABILITY,
        "avg_latency_sec": round(avg_latency, 4) if avg_latency else None,
        "p95_latency_sec": round(p95_latency, 4) if p95_latency else None,
        "stdev_latency_sec": round(stdev_latency, 4),
        "throughput_ops_per_sec": round(throughput, 3),
        "success_rate": round(successes / LOOKUPS_PER_NODE, 2),
        "failures": failures,
        "total_runtime_sec": round(total_time, 2)
    }


# === New: Churn Sweep Experiment ===
def run_churn_sweep(n, delay=False):
    """Sweep across multiple failure probabilities to measure churn sensitivity."""
    global FAILURE_PROBABILITY
    label = "delay" if delay else "baseline"
    results = []

    if delay:
        inject_network_delay()
    else:
        remove_network_delay()

    print(f"\n=== Running Churn Sensitivity Sweep ({label}) ===")
    for fp in CHURN_LEVELS:
        FAILURE_PROBABILITY = fp
        results.append(run_experiment(n))

    filename = f"results_churn_{label}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved churn sweep results to {filename}")
    return results


# === Main ===
def main():
    parser = argparse.ArgumentParser(description="Run Chord DHT experiments with optional network delay.")
    parser.add_argument("--delay", action="store_true", help="Enable artificial network delay.")
    parser.add_argument("--churn", action="store_true", help="Run churn sensitivity sweep instead of full scale test.")
    args = parser.parse_args()

    if args.churn:
        # Fixed node count for churn test
        n = 20
        run_churn_sweep(n, delay=args.delay)
        return

    # Normal baseline/delay tests
    if args.delay:
        inject_network_delay()
        mode = "With Delay"
    else:
        remove_network_delay()
        mode = "Baseline (No Delay)"

    print(f"\nStarting experiments: {mode}\n")
    results = []
    for n in NUM_NODES:
        results.append(run_experiment(n))

    filename = "results_delay.json" if args.delay else "results_baseline.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {filename}")


if __name__ == "__main__":
    main()
