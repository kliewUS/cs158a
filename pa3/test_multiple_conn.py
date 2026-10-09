import time
from p2p_node import p2p_node

# This is a temporary test. Meant to ensure mutliple nodes are communicating and disconnecting with each other.
# Feel free to remove or modify this once messaging and/or file mgment is implemented.

NUM_NODES = 5
STARTING_TCP_PORT = 60001

recv_msg = {i: [] for i in range(NUM_NODES)}

def msg_callback(idx):
    def callback(peer_key, msg):
        print(f"[Node {idx + 1} Callback]: Received from {peer_key}: {msg}")
        recv_msg[idx].append((peer_key, msg))
    return callback

def disconnect_callback(idx):
    def on_disconnect(peer_key):
        print(f"[Node {idx + 1} Disconnect Callback]: Peer disconnected: {peer_key}")
    return on_disconnect

def run_multi_node_test():
    print(f"Starting {NUM_NODES}-node network test")
    nodes = []

    for i in range(NUM_NODES):
        port = STARTING_TCP_PORT + i
        node = p2p_node(tcp_port=port, on_message_received=msg_callback(i), on_peer_disconnected=disconnect_callback(i))
        nodes.append(node)
        node.start()
        print(f"Node {i + 1} (ID: {node.id}) started on TCP port {port}")

    time.sleep(1)

    print("Node 1 broadcasts PEER_REQ to find peers...")
    nodes[0].broadcast_peer_req()

    time.sleep(2)

    for i, node in enumerate(nodes):
        print(f"Node {i + 1} (Port: {node.tcp_port}): {len(node.peer_list)} connected peers(s)")

    node1_peers = len(nodes[0].peer_list)
    if node1_peers == NUM_NODES - 1:
        print(f"Node 1 discovered and connected to all {NUM_NODES - 1} peers")
    else:
        print(f"Failed: Expected Node 1 to have {NUM_NODES - 1} peers, got {node1_peers}")

    print("Node 1 sending message to all connected peers.")
    test_payload = {
        "type": "FILE_LIST",
        "fileContent": "Hello from Node 1 to all my peers!"
    }

    for peer_id in list(nodes[0].peer_list.keys()):
        nodes[0].send_message(peer_id, test_payload)

    time.sleep(1)

    all_recv = all(len(recv_msg[i]) > 0 for i in range(1, NUM_NODES))
    if all_recv:
        print("All 4 nodes received message from Node 1!")
    else:
        print("Failed: One or more nodes failed to receive the message.")

    print("Triggering broadcasts from remaining nodes to form full network")
    for i in range(1, NUM_NODES):
        nodes[i].broadcast_peer_req()

    time.sleep(2)

    print("Total connected peers: ")
    for i, node in enumerate(nodes):
        peer_count = len(node.peer_list)
        print(f"Node {i + 1} (Port {node.tcp_port}): {peer_count} connected peer(s)")

    print("Stopping all nodes")
    for node in nodes:
        node.stop()

if __name__ == "__main__":
    run_multi_node_test()