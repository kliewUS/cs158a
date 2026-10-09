import socket
import threading
import json
import time
import uuid
from typing import Callable, Dict
from msg_frame import send_msg, recv_msg

UDP_PORT = 54321 # Set default UDP port for all nodes to listen to.

class p2p_node:
    """
        uuid - UUID of the current node.
        tcp_port - Current node's tcp port for client nodes to connect to.
        peer_list = List of peer_ids to connect.
        lock - Acquires lock for this node
        running - Tracks if node is running or not.
        on_message_received (May not be needed or could be replaced) - Calls function upon message received. 
        on_peer_disconnected (May not be needed or could be replaced) - Calls function upon peer disconnection.
    """    
    def __init__(self, tcp_port, on_message_received: Callable, on_peer_disconnected: Callable):
        self.id = str(uuid.uuid4())
        self.tcp_port = tcp_port
        self.on_message_received = on_message_received
        self.on_peer_disconnected = on_peer_disconnected
        self.peer_list: Dict[str, socket.socket] = {} 
        self.lock = threading.Lock()
        self.running = False 

    """
        Starts up the TCP server and UDP Listener.
    """
    def start(self):
        self.running = True 

        self.server = threading.Thread(target=self.tcp_server, daemon=True)
        self.server.start()

        self.listener = threading.Thread(target=self.udp_listener, daemon=True)
        self.listener.start()

    """
        Broadcast Peer Request
    """
    def broadcast_peer_req(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.settimeout(1.5)

        msg = {
            "id": self.id,
            "type": "PEER_REQ"
        }

        print(f"Node {self.id} sent message: {msg}") 

        data = json.dumps(msg).encode()
        udp_socket.sendto(data, ('<broadcast>', UDP_PORT))

        # Might want to check this. This feels very hacky.
        start_time = time.time()
        while time.time() - start_time < 1.5:
            try:
                ack_data, addr = udp_socket.recvfrom(4096)
                ack_msg = json.loads(ack_data.decode())

                if ack_msg.get("type") == "PEER_ACK":
                    tcp_port = ack_msg.get("tcp_port")
                    print(f"Node {self.id} received Message Type: {ack_msg.get('type')} and connecting to {addr[0]} with tcp_port: {self.tcp_port}")
                    print(f"TCP Port to connect: {tcp_port}")
                    if tcp_port:
                        self.connect_to_peer(ack_msg.get('id'), addr[0], tcp_port)
            except (socket.timeout, Exception):
                break

        udp_socket.close()

    """
        Estalishes UDP listener that listens at port 54321
        Will ignore its own broadcasts if the id is the same.
        If peer request is received, then send back ack message with tcp_port for client node to connect to.
        UDP listener stays online for the entire lifetime of the node.
    """
    def udp_listener(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_socket.bind(("", UDP_PORT))

        while self.running:
            try:
                data, addr = udp_socket.recvfrom(4096)
                msg = json.loads(data.decode())
                print(f"Node {self.id} received message: {msg}")

                if msg.get("id") == self.id:
                    print(f"Node {self.id} ignores self-broadcast.")
                    continue

                if msg.get("type") == "PEER_REQ":
                    ack_msg = {
                        "id": self.id,
                        "type": "PEER_ACK",
                        "tcp_port": self.tcp_port
                    }
                    print(f"Node {self.id} received Message Type: {msg.get('type')} and sending it to {addr[0]} with tcp_port: {self.tcp_port}")
                    udp_socket.sendto(json.dumps(ack_msg).encode(), addr)
            except Exception:
                if not self.running: 
                    break

        udp_socket.close()

    """
        Establishes TCP server at specified port.
        If message IDENT is received, then retrieve id.
        Close the connection if the id is already in peer list.

    """
    def tcp_server(self):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind(("", self.tcp_port))
        tcp_socket.listen(5)
        print(f"Listening for connections at port: {self.tcp_port}")

        while self.running:
            try:
                conn, addr = tcp_socket.accept()

                payload = recv_msg(conn)
                msg = json.loads(payload.decode())

                if msg.get("type") == "IDENT":
                    peer_id = msg.get("id")

                    if not peer_id or peer_id == self.id or peer_id in self.peer_list:
                        conn.close()
                        continue # Kinda hacky. Will need to take a look later. Could possibly replace an existing connection.

                    with self.lock:
                        self.peer_list[peer_id] = conn

                    client_thread = threading.Thread(target=self.peer_receiver, args=(conn, peer_id), daemon=True)
                    client_thread.start()
            except Exception:
                if not self.running: 
                    break

        tcp_socket.close()

    """
        Connects to peer node with target ip and port.
        Also sends IDENT message to allow target node to store into its peer list.
        Also creates a new client thread to prevent blocking.
    """
    def connect_to_peer(self, peer_id, ip, port):
        if peer_id == self.id:
            return False

        with self.lock:
            if peer_id in self.peer_list:
                return False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))

            msg = {"type": "IDENT", "id": self.id}
            send_msg(sock, json.dumps(msg).encode())

            with self.lock:
                self.peer_list[peer_id] = sock

            client_conn_thread = threading.Thread(target=self.peer_receiver, args=(sock, peer_id), daemon=True)
            client_conn_thread.start()

        except Exception as e:
            print(f"Failed to connect to {peer_id}: {e}")

    """
        Get peer_id and sends message to specified peer_id.
    """
    def send_message(self, peer_id, msg_dict):
        with self.lock:
            sock = self.peer_list.get(peer_id)

        if not sock:
            return False

        try:
            data = json.dumps(msg_dict).encode()
            send_msg(sock, data)
            return True
        except Exception:
            self.handle_disconnect(peer_id)
            return False

    """
        Handles and parses message received from peers.
    """
    def peer_receiver(self, sock, peer_id):
        while self.running:
            try:
                payload = recv_msg(sock)
                msg_dict = json.loads(payload.decode())
                self.on_message_received(peer_id, msg_dict)
            except (ConnectionError, OSError):
                self.handle_disconnect(peer_id)
                break
            except Exception as e:
                print(f"Failed to parse message from {peer_id}: {e}")

    """
        Pops peer_id from list of peer sockets it is connected to.
        Closes the specified peer_id socket.
    """
    def handle_disconnect(self, peer_id):
        with self.lock:
            sock = self.peer_list.pop(peer_id, None)
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
            self.on_peer_disconnected(peer_id)

    """
        Handles closing the connection of this node.
    """
    def stop(self):
        self.running = False
        with self.lock:
            for sock in self.peer_list.values():
                sock.close()
        self.peer_list.clear()
            