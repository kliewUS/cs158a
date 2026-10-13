import socket
import threading
import time
import uuid
from typing import Callable, Dict
from msg_frame import send_msg, recv_msg
from messages import (
    MessageError, encode, decode,
    make_peer_req, make_peer_ack, make_ident, make_file_list,
    TYPE, ID, TARGET_PORT, PEER_REQ, PEER_ACK, IDENT
)

UDP_PORT = 54321 # Set default UDP port for all nodes to listen to.
FILE_LIST_INTERVAL = 10 # Seconds between periodic FILE_LIST sends to every peer.

class p2p_node:
    """
        uuid - UUID of the current node.
        tcp_port - Current node's tcp port for client nodes to connect to.
        peer_list = List of peer_ids to connect.
        lock - Acquires lock for this node
        running - Tracks if node is running or not.
        on_message_received (May not be needed or could be replaced) - Calls function upon message received. 
        on_peer_disconnected (May not be needed or could be replaced) - Calls function upon peer disconnection.
        get_file_list - Returns the filenames this node shares (e.g. FileManager.scan_shared).
        file_list_interval - Seconds between periodic FILE_LIST sends.
        send_locks - One lock per peer socket, so messages from different threads are never interleaved.
        stop_event - Set by stop() to wake the file list timer immediately.
    """    
    def __init__(self, tcp_port, on_message_received: Callable, on_peer_disconnected: Callable,
                 get_file_list: Callable = lambda: [], file_list_interval=FILE_LIST_INTERVAL):
        self.id = str(uuid.uuid4())
        self.tcp_port = tcp_port
        self.on_message_received = on_message_received
        self.on_peer_disconnected = on_peer_disconnected
        self.get_file_list = get_file_list
        self.file_list_interval = file_list_interval
        self.peer_list: Dict[str, socket.socket] = {} 
        self.send_locks: Dict[socket.socket, threading.Lock] = {}
        self.lock = threading.Lock()
        self.running = False 
        self.stop_event = threading.Event()

    """
        Starts up the TCP server, UDP Listener, and file list timer.
    """
    def start(self):
        self.running = True 
        self.stop_event.clear()

        self.server = threading.Thread(target=self.tcp_server, daemon=True)
        self.server.start()

        self.listener = threading.Thread(target=self.udp_listener, daemon=True)
        self.listener.start()

        self.file_list_timer_thread = threading.Thread(target=self.file_list_timer, daemon=True)
        self.file_list_timer_thread.start()

    """
        Broadcast Peer Request
            Sends peer request into udp socket
            checks for replies (1.5s)
    """
    def broadcast_peer_req(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.settimeout(1.5)

        msg = make_peer_req(self.id)

        print(f"Node {self.id} sent message: {msg}") 

        udp_socket.sendto(encode(msg), ('<broadcast>', UDP_PORT))

        start_time = time.time()
        while time.time() - start_time < 1.5:
            try:
                ack_data, addr = udp_socket.recvfrom(4096)
                ack_msg = decode(ack_data)

                if ack_msg[TYPE] == PEER_ACK:
                    tcp_port = ack_msg[TARGET_PORT]
                    print(f"Node {self.id} received Message Type: {ack_msg[TYPE]} and connecting to {addr[0]} with tcp_port: {tcp_port}")
                    self.connect_to_peer(ack_msg[ID], addr[0], tcp_port)
            except MessageError as e:
                # Ignore a malformed reply and keep waiting for valid ACKs.
                print(f"Node {self.id} ignored invalid UDP message from {addr[0]}: {e}")
            except Exception:
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
        udp_socket.settimeout(1.0)

        while self.running:
            try:
                data, addr = udp_socket.recvfrom(4096)
            except socket.timeout: # Re-check self.running
                continue
            except OSError:
                break

            # If we received PEER_REQ, send the back the tcp_port for the peer to connect to.
            # Ignores all self-broadcasts.
            try:
                msg = decode(data)
                print(f"Node {self.id} received message: {msg}")

                if msg[ID] == self.id:
                    print(f"Node {self.id} ignores self-broadcast.")
                    continue

                if msg[TYPE] == PEER_REQ:
                    ack_msg = make_peer_ack(self.id, self.tcp_port)
                    print(f"Node {self.id} received Message Type: {msg[TYPE]} and sending it to {addr[0]} with tcp_port: {self.tcp_port}")
                    udp_socket.sendto(encode(ack_msg), addr)
            except MessageError as e:
                print(f"Node {self.id} ignored invalid UDP message from {addr[0]}: {e}")
            except Exception as e:
                print(f"Node {self.id} encountered a UDP Listener error: {e}")

        udp_socket.close()

    """
        Establishes TCP server at specified port.
        The first message on each accepted connection must be IDENT, which carries the peer's id.
        Close the connection if the first message is not IDENT, or the id is already in peer list.
    """
    def tcp_server(self):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind(("", self.tcp_port))
        tcp_socket.listen(5)
        tcp_socket.settimeout(1.0)
        print(f"Listening for connections at port: {self.tcp_port}")

        while self.running:
            try:
                conn, addr = tcp_socket.accept()
            except socket.timeout: # Re-check self.running
                continue 
            except OSError:
                break     

            try:
                msg = decode(recv_msg(conn))
            except (MessageError, ConnectionError, OSError) as e:
                print(f"Node {self.id} rejected connection from {addr[0]}: {e}")
                conn.close()
                continue                

            if msg[TYPE] != IDENT:
                print(f"Node {self.id} rejected connection from {addr[0]}: expected IDENT, got {msg[TYPE]}")
                conn.close()
                continue

            peer_id = msg[ID]

            #If peer does not exist or we somehow connected to ourselves, close the connection.
            if not peer_id or peer_id == self.id:
                conn.close()
                continue

            with self.lock:
                # Check if peer is already in the node's peer list.
                if peer_id in self.peer_list:
                    dup = True
                else:
                    self.peer_list[peer_id] = conn
                    dup = False

            # Close the uneeded connection.
            if dup:
                conn.close()
                continue

            # Otherwise, start up the peer_receiver method.
            client_thread = threading.Thread(target=self.peer_receiver, args=(conn, peer_id), daemon=True)
            client_thread.start()    

            # Send our file list to the new peer right away instead of waiting for the next timer tick.
            self.send_file_list(peer_id)

        tcp_socket.close()

    """
        Connects to peer node with target ip and port.
        Also sends IDENT message to allow target node to store into its peer list.
        Also creates a new client thread to prevent blocking.
    """
    def connect_to_peer(self, peer_id, ip, port):
        # Do not connect to itself.
        if peer_id == self.id:
            return False

        with self.lock:
            # If peer is in the node's list, don't connect.
            if peer_id in self.peer_list:
                return False

        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            send_msg(sock, encode(make_ident(self.id)))
        except Exception as e:
            print(f"Failed to connect to {peer_id}: {e}")

            # Closes stale socket.
            if sock:
                sock.close()
            return False

        with self.lock:
            # If somehow the peer that is already in a node's peer list connects, close the connection.
            if peer_id in self.peer_list:
                sock.close()
                return False
            # Otherwise, add the peer to the node's socket list and start up the peer_receiver method.
            self.peer_list[peer_id] = sock

        client_conn_thread = threading.Thread(target=self.peer_receiver, args=(sock, peer_id), daemon=True)
        client_conn_thread.start()

        # Send our file list to the new peer right away instead of waiting for the next timer tick.
        self.send_file_list(peer_id)
        return True

    """
        Get peer_id and sends message to specified peer_id.
        Returns False if the message could not be sent.
    """
    def send_message(self, peer_id, msg_dict):
        with self.lock:
            sock = self.peer_list.get(peer_id)
            if not sock:
                return False
            send_lock = self.send_locks.setdefault(sock, threading.Lock())

        try:
            # Only one thread may write to a socket at a time, or two messages' bytes could interleave.
            with send_lock:
                send_msg(sock, encode(msg_dict))
            return True
        except ValueError as e:
            # Message too large to send. The connection itself is fine, so keep the peer.
            print(f"Failed to send message to {peer_id}: {e}")
            return False
        except Exception:
            self.handle_disconnect(peer_id, sock)
            return False

    """
        Sends this node's current file list to one peer.
        Used right after a new connection is established.
    """
    def send_file_list(self, peer_id):
        try:
            file_names = self.get_file_list()
        except Exception as e:
            print(f"Node {self.id} could not get file list: {e}")
            return False

        return self.send_message(peer_id, make_file_list(self.id, file_names))

    """
        Sends this node's current file list to every connected peer.
        The file list is read once and the same message is sent to all peers.
    """
    def broadcast_file_list(self):
        try:
            file_names = self.get_file_list()
        except Exception as e:
            print(f"Node {self.id} could not get file list: {e}")
            return

        msg = make_file_list(self.id, file_names)

        # Copy the peer ids so peers connecting or disconnecting during the loop don't affect it.
        with self.lock:
            peer_ids = list(self.peer_list.keys())

        for peer_id in peer_ids:
            self.send_message(peer_id, msg)

    """
        Sends the file list to every peer every file_list_interval seconds until stop() is called.
        stop_event.wait returns early when stop() sets the event, so shutdown does not wait out the interval.
    """
    def file_list_timer(self):
        while not self.stop_event.wait(self.file_list_interval):
            self.broadcast_file_list()

    """
        Handles and parses message received from peers.
        Invalid messages are skipped; the connection stays open.
    """
    def peer_receiver(self, sock, peer_id):
        while self.running:
            try:
                msg_dict = decode(recv_msg(sock))
                self.on_message_received(peer_id, msg_dict)
            except (ConnectionError, OSError):
                if self.running:
                    self.handle_disconnect(peer_id, sock)
                break
            except MessageError as e:
                print(f"Ignored invalid message from {peer_id}: {e}")
            except Exception as e:
                print(f"Failed to parse message from {peer_id}: {e}")

    """
        Deletes peer_id from list of peer sockets it is connected to and then closes the specified peer_id socket.
    """
    def handle_disconnect(self, peer_id, sock):
        with self.lock:
            if self.peer_list.get(peer_id) is not sock:
                return
            del self.peer_list[peer_id]
            self.send_locks.pop(sock, None)
        try:
            sock.close()
        except Exception:
            pass

        self.on_peer_disconnected(peer_id)

    """
        Handles closing the connection of this node.
        Clears the peer list and close all of this node's connections.
    """
    def stop(self):
        self.running = False
        self.stop_event.set()
        with self.lock:
            socks = list(self.peer_list.values())
            self.peer_list.clear()
            self.send_locks.clear()

        for sock in socks:
            sock.close()

        self.server.join(timeout=2) # Waits for listener threads to exit.
        self.listener.join(timeout=2)
        self.file_list_timer_thread.join(timeout=2)
            