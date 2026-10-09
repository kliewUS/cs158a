import time

from p2p_node import p2p_node

# This is a placeholder. Meant to ensure nodes are communicating with each other, disconnecting gracefully. 
# Feel free to remove or modify this once messaging and/or file mgment is implemented.

node1_recv = []
node2_recv = []

def on_node1_msg(peer_key, msg):
    print(f"[Node 1 Callaback]: Received from {peer_key}: {msg}")
    node1_recv.append((peer_key, msg))

def on_node2_msg(peer_key, msg):
    print(f"[Node 2 Callaback]: Received from {peer_key}: {msg}")
    node2_recv.append((peer_key, msg))    

def on_disconnect(peer_key):
    print(f"[Disconnect Callback]: Peer disconnected: {peer_key}")

def run_test():
    print("Starting Broadcasting test")

    node1 = p2p_node(tcp_port=60001, on_message_received=on_node1_msg, on_peer_disconnected=on_disconnect)
    node2 = p2p_node(tcp_port=60002, on_message_received=on_node2_msg, on_peer_disconnected=on_disconnect)

    node1.start()
    node2.start()
    print("Node 1 (60001) and Node 2 (60002) started.")

    node1.broadcast_peer_req()
    time.sleep(2)

    print(f"Node 1 Connected Peers: {list(node1.peer_sockets.keys())}")
    print(f"Node 2 Connected Peers: {list(node2.peer_sockets.keys())}")

    if not node1.peer_sockets:
        print("Test failed: Node 1 failed to connect to Node 2 via TCP.")
        node1.stop()
        node2.stop()
        return

    peer_key_node2 = list(node1.peer_sockets.keys())[0]

    print("Test Message Delivery")
    test_payload = {
        "type": "FILE_LIST",
        "fileContent": "Hello world from Node 1"
    }

    success = node1.send_message(peer_key_node2, test_payload)
    print(f"Send status: {success}")
    time.sleep(1)

    if len(node2_recv) and node2_recv[0][1]["fileContent"] == "Hello world from Node 1":
        print("Test passed: Message delivered and framed correctly!")
    else:
        print("Test failed: Message was not received properly.")

    print("Test shutdown and disconnection.")
    node2.stop()
    time.sleep(1)

    node1.stop()
    print("Test concluded")

if __name__ == "__main__":
    run_test()