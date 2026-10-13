import sys
import time
from p2p_node import p2p_node
from messages import FILE_LIST, FILE_LIST_FIELD, TYPE

# Tests the FILE_LIST timer: an immediate send on new connections, periodic sends, and quick shutdown.
# Peers are connected directly with connect_to_peer so timing does not depend on UDP discovery.

STARTING_TCP_PORT = 60001
PRINT_LINE = "-" * 50

failures = []

def check(condition, description):
    print(("PASS: " if condition else "FAIL: ") + description)
    if not condition:
        failures.append(description)

"""
    Creates a node whose shared files are read from files[idx], and records every FILE_LIST it receives.
    Returns the node and its list of received (peer_id, fileList) pairs.
"""
def make_node(idx, files, interval):
    received = []

    def on_msg(peer_id, msg):
        if msg[TYPE] == FILE_LIST:
            received.append((peer_id, msg[FILE_LIST_FIELD]))

    node = p2p_node(tcp_port=STARTING_TCP_PORT + idx, on_message_received=on_msg, on_peer_disconnected=lambda peer_id: None,
                    get_file_list=lambda: list(files[idx]), file_list_interval=interval)
    return node, received

"""
    Returns the file lists received from peer_id, in order.
"""
def lists_from(received, peer_id):
    return [file_list for sender, file_list in received if sender == peer_id]

"""
    With a long interval the timer never fires, so any FILE_LIST received must be the immediate send.
"""
def test_immediate_send():
    print("Immediate FILE_LIST on new connection" + "\n" + PRINT_LINE)
    files = {0: ["a.txt"], 1: ["b.txt"]}
    node_a, recv_a = make_node(0, files, interval=100)
    node_b, recv_b = make_node(1, files, interval=100)
    node_a.start()
    node_b.start()
    time.sleep(0.5)

    node_a.connect_to_peer(node_b.id, "127.0.0.1", node_b.tcp_port)
    time.sleep(0.5)

    check(lists_from(recv_b, node_a.id) == [["a.txt"]], "Server side received client's file list immediately")
    check(lists_from(recv_a, node_b.id) == [["b.txt"]], "Client side received server's file list immediately")

    start_time = time.time()
    node_a.stop()
    node_b.stop()
    elapsed = time.time() - start_time
    check(elapsed < 3, f"stop() did not wait out the 100s interval (took {elapsed:.1f}s for 2 nodes)")

"""
    With a 1s interval, every peer should receive repeated file lists, and changes should appear on the next tick.
"""
def test_periodic_send():
    print("\n" + "Periodic FILE_LIST every interval" + "\n" + PRINT_LINE)
    files = {0: ["a.txt"], 1: ["b.txt"], 2: ["c.txt"]}
    nodes, recvs = zip(*(make_node(i, files, interval=1) for i in range(3)))
    for node in nodes:
        node.start()
    time.sleep(0.5)

    # Form a full mesh.
    for i in range(3):
        for j in range(i + 1, 3):
            nodes[i].connect_to_peer(nodes[j].id, "127.0.0.1", nodes[j].tcp_port)

    time.sleep(3.5)

    # 1 immediate send + about 3 timer ticks.
    for i in range(3):
        for j in range(3):
            if i != j:
                count = len(lists_from(recvs[i], nodes[j].id))
                check(count >= 3, f"Node {i + 1} received {count} file lists from Node {j + 1} (expected >= 3)")

    files[0].append("new.txt")
    time.sleep(1.5)

    latest = lists_from(recvs[1], nodes[0].id)[-1]
    check(latest == ["a.txt", "new.txt"], f"Updated file list sent on next tick (got {latest})")

    for node in nodes:
        node.stop()

if __name__ == "__main__":
    test_immediate_send()
    test_periodic_send()

    print("\n" + PRINT_LINE)
    if failures:
        print(f"{len(failures)} check(s) failed")
        sys.exit(1)
    print("All checks passed")
