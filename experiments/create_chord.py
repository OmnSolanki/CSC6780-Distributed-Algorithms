import os
import sys
import time
import socket
import random
from chord import *

def create_chord_ring(nnodes, stabilize_time=8):
    print(f"Creating Chord network with {nnodes} nodes...")

    # Create random ports (avoid collisions)
    ports_list = [random.randrange(10000, 60000) for _ in range(nnodes)]
    address_list = [Address('127.0.0.1', port) for port in ports_list]
    address_list = sorted(set(address_list))  # remove duplicates

    locals_list = []

    for i, address in enumerate(address_list):
        if len(locals_list) == 0:
            local = Local(address)
        else:
            remote = locals_list[random.randrange(len(locals_list))].address_
            local = Local(address, remote)
        local.start()
        locals_list.append(local)
        print(f"Node {i+1}/{len(address_list)} started at {address}")
        time.sleep(0.3)  # small delay for stability

    print(f"Stabilizing network for {stabilize_time} seconds...")
    time.sleep(stabilize_time)

    print("Network stabilized. Returning peer list.")
    return locals_list


def shutdown_chord_ring(locals_list):
    print("Shutting down all nodes...")
    for peer in locals_list:
        try:
            peer.shutdown()
        except Exception:
            pass
    print("All nodes shut down.")


if __name__ == "__main__":
    nnodes = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    peers = create_chord_ring(nnodes)
    print(f"Ring created with {nnodes} nodes.")
    time.sleep(2)
    shutdown_chord_ring(peers)
    print("🏁 Experiment setup complete.")
