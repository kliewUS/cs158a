import socket
import threading
import json
import time
import uuid
from typing import Callable, Dict
from msg_frame import send_msg, recv_msg

UDP_PORT = 54321

class p2p_node:
    def __init__(self, tcp_port, on_message_received: Callable, on_peer_disconnected: Callable):
        self.id = str(uuid.uuid4())
        self.tcp_port = tcp_port
        self.on_message_received = on_message_received
        self.on_peer_disconnected = on_peer_disconnected
        self.peer_sockets: Dict[str, socket.socket] = {}
        self.lock = threading.Lock()
        self.running = False 

    def start(self):
        self.running = True 

        self.server = threading.Thread(target=self.tcp_server, daemon=True)
        self.server.start()

        self.listener = threading.Thread(target=self.udp_listener, daemon=True)
        self.listener.start()

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
                        self.connect_to_peer(addr[0], tcp_port)
            except socket.timeout:
                break
            except Exception:
                break

        udp_socket.close()


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
                    # udp_socket.sendto(json.dumps(ack_msg).encode(), (addr[0], UDP_PORT))
            except Exception:
                if not self.running: 
                    break

        udp_socket.close()
            
    def tcp_server(self):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind(("", self.tcp_port))
        tcp_socket.listen(5)
        print(f"Listening for connections at port: {self.tcp_port}")

        while self.running:
            try:
                conn, addr = tcp_socket.accept()
                peer_key = f"{addr[0]}:{addr[1]}"
                print(peer_key)

                with self.lock:
                    self.peer_sockets[peer_key] = conn

                client_thread = threading.Thread(target=self.peer_receiver, args=(conn, peer_key), daemon=True)
                client_thread.start()
            except Exception as e:
                if not self.running: 
                    break

        tcp_socket.close()

    def connect_to_peer(self, ip, port):
        peer_key = f"{ip}:{port}"
        print(f"Peer Key: {peer_key}")

        with self.lock:
            if peer_key in self.peer_sockets:
                return False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))

            with self.lock:
                self.peer_sockets[peer_key] = sock

            client_conn_thread = threading.Thread(target=self.peer_receiver, args=(sock, peer_key), daemon=True)
            client_conn_thread.start()

        except Exception as e:
            print(f"Failed to connect to {peer_key}: {e}")

    def send_message(self, peer_key, msg_dict):
        with self.lock:
            sock = self.peer_sockets.get(peer_key)

        if not sock:
            return False

        try:
            data = json.dumps(msg_dict).encode()
            send_msg(sock, data)
            return True
        except Exception:
            self.handle_disconnect(peer_key)
            return False

    def peer_receiver(self, sock, peer_key):
        while self.running:
            try:
                payload = recv_msg(sock)
                msg_dict = json.loads(payload.decode())
                self.on_message_received(peer_key, msg_dict)
            except (ConnectionError, OSError):
                self.handle_disconnect(peer_key)
                break
            except Exception as e:
                print(f"Failed to parse message from {peer_key}: {e}")

    def handle_disconnect(self, peer_key):
        with self.lock:
            sock = self.peer_sockets.pop(peer_key, None)

            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
            self.on_peer_disconnected(peer_key)

    def stop(self):
        self.running = False
        with self.lock:
            for sock in self.peer_sockets.values():
                sock.close()
        self.peer_sockets.clear()
            