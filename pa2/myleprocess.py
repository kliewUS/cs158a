import time
import uuid
import json
import socket
import threading
import sys

class Message:
    """
        uuid - UUID of the current node.
        flag - Two states: 0 - node still looking for leader, 1 - node knows the leader.
    """
    def __init__(self, uuid, flag):
        self.uuid = uuid
        self.flag = flag

    """
        Serializes json to str via json.dumps.
        Returns the JSON message as a string.
    """
    def json_to_str(self):
        return json.dumps({"uuid": str(self.uuid), "flag": self.flag})

    """
        Deserializes json to a python object via json.loads.
        Returns a new Message containing the UUID and the flag.
    """
    @classmethod
    def str_to_json(cls, json_str):
        data = json.loads(json_str)
        return cls(data["uuid"], data["flag"])

class Node:
    """
        node_uuid - UUID of current process, generated upon initialization.
        state - Two states: 0 - node still looking for leader, 1 - node knows the leader.
        current_highest_id - The highest UUID found by the node so far.
        leader_id - UUID of leader process
        client_sock - Socket where process is connected to based on client_ip and client_port from client_addr
        log_file - Log file where processes store all logs.
        server_addr - IP address and port where the process's server will start up.
        client_addr - IP address and port where the process's client will connect to.
    """
    def __init__(self, config_file, node_id):
        self.node_uuid = uuid.uuid4()
        self.state = 0
        self.current_highest_id = None
        self.leader_id = None
        self.client_sock = None
        self.log_file = f"log{node_id}.txt" 

        # Reads the config file line by line.
        with open(config_file, "r") as f: 
            lines = []
            for line in f:
                if line.strip():
                    lines.append(line.strip())

        # Gets the total number of lines. One line per node.
        total_nodes = len(lines)

        # Index is 0-index, so -1 on node_id for server_idx. 
        # client_idx will get the next idx after server_idx
        server_idx = node_id - 1
        client_idx = node_id % total_nodes

        # Splits both server and client ips and ports into tuples. Then sets as the server address and client addresses.
        server_ip, server_port = lines[server_idx].split(",")
        client_ip, client_port = lines[client_idx].split(",")

        self.server_addr = (server_ip, int(server_port))
        self.client_addr = (client_ip, int(client_port))

    """
        Writes entry to log file specified in the node.
    """
    def write_log(self, entry):
        print(entry)
        with open(self.log_file, "a") as f:
            f.write(entry + "\n")

    """
        If sender node is connected to the receiver node's socket, send a message to the left edge (receiver node) and write the send operation to the sender node's log file.
    """
    def send_msg_client(self, msg):
        if self.client_sock:
            self.client_sock.sendall(msg.json_to_str().encode())
            self.write_log(f"Sent: uuid={msg.uuid}, flag={msg.flag}")

    """
        Check message UUID and node's UUID.
        Set uuid_comp depending if the message UUID is greater, equal to, or less than the current node's UUID.
        Then log that the message was received with the message UUID, message flag, the UUID comparsion result, and the current state.
        Returns UUID comparsion result.
    """
    def check_log_uuid(self, msg):
        if uuid.UUID(msg.uuid) > self.node_uuid:
            uuid_comp = "greater"
            self.current_highest_id = uuid.UUID(msg.uuid)
        elif uuid.UUID(msg.uuid) < self.node_uuid:
            uuid_comp = "less"
        else:
            uuid_comp = "same"

        log_entry = f"Received: uuid={msg.uuid}, flag={msg.flag}, {uuid_comp}, {self.state}"

        if self.state == 1:
            log_entry += f", leader={self.leader_id}"
        self.write_log(log_entry)

        return uuid_comp

    """
        First checks message UUID and node's UUID and then checks the message flag.
        If message flag is 0, 
            Depending on the current UUID comparsion result:
            If UUID comparsion result returns greater, forward the message to the left edge (receiver node).
            If UUID comparsion result return less, log the message, stating that message has been ignored.
            If UUID comparsion result return same, make the current process a leader and forward a message to the left edge (receiver node), stating that it is now the leader.
        If message flag is 1,
            For both sub-cases, print a message with the leader's UUID.
            If the message UUID is different from current UUID, then set the state to 1 and the leader_id to the leader's UUID, stating it has found the leader
            and forward the message to the left edge (receiver node).
            Otherwise, just stop sending messages.
    """
    def process_msg(self, msg):
        uuid_comp = self.check_log_uuid(msg)

        if msg.flag == 0:
            if uuid_comp == "greater":
                self.send_msg_client(msg)
            elif uuid_comp == "less":
                self.write_log(f"Ignored message with uuid={msg.uuid}")
            elif uuid_comp == "same":
                self.state = 1
                self.leader_id = self.node_uuid
                self.write_log(f"Leader is decided to {self.leader_id}.")
                self.send_msg_client(Message(self.node_uuid, flag=1))
        elif msg.flag == 1:
            # Termination condition. All nodes have been notified of the leader and have stopped sending messages as a result.
            if uuid.UUID(msg.uuid) == self.node_uuid:
                self.write_log(f"Leader is {self.leader_id}.")
                pass
            else:
                self.state = 1
                self.leader_id = msg.uuid
                self.write_log(f"Leader is {self.leader_id}.")
                self.send_msg_client(msg)

    """
        Start up TCP server and continous listen for any client connections.
        Once a client connection has been accepted, deserialze all incoming messages and process them.
        If client connection has been closed, shut the node of this server.

        Note that we are not using the with keyword on the server and client sockets.
        That because we don't want to automatically close the connection if we are finished or when we get an error.
    """
    def server(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(self.server_addr)
        server_sock.listen(1)

        conn, addr = server_sock.accept()
        with conn:
            while True:
                data = conn.recv(1024)

                if not data:
                    print(f"Empty byte object received. Client with {addr} has disconnected.\n")
                    break

                msg = Message.str_to_json(data.decode())
                self.process_msg(msg)                

            print(f"Client socket has closed. [Node with ID: {self.node_uuid}] shutting down.") 
                     

    """
        Waits for 2 seconds and then the node attempts to connect to target IP and port. 
        Or in the case of the demo, the node will only attempt to connect once Enter is pressed.
        If the node is unable to connect, it will close the stale socket and try again after 1 second.
        If the node has not received any messages, then send a message to the left edge with this node's id.
        If the node has received messages, use the current highest id found by this node and send a message to the left edge with that id.
    """
    def client(self):
        time.sleep(2) # Comment out for in-class demo.
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # input("Press Enter when everyone is ready.\n") # Uncomment out for in-class demo.
                sock.connect(self.client_addr)
                self.client_sock = sock
                break
            except socket.error:
                sock.close()
                time.sleep(1)

        if self.current_highest_id:       
            self.send_msg_client(Message(self.current_highest_id, flag=0)) 
        else:
            self.send_msg_client(Message(self.node_uuid, flag=0))


    """
        Starts up node process with a server thread.
        The node will only try to connect to client once a client has connected to this node's server.
        If user requests to shut off the node, print a message and shut down the node. 
    """
    def startup(self):
        self.write_log(f"Process started with ID: {self.node_uuid}")
        try:
            # Create a server thread, so that it does not prevent the node from connecting to anyone.
            server = threading.Thread(target=self.server, daemon=True)
            server.start()

            # Make the connection to the left edge (Receiver Node)
            self.client()

            # Maintain the connection until the user's shut down the server of this node. Or the nodes have been disconnected from the left edge.
            server.join()
        except KeyboardInterrupt:
            print(f"\n[Node with ID: {self.node_uuid}] shutting down.")     

if __name__ == "__main__":
    # Specify a node id. Otherwise, defaults to 1.
    node_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    node = Node("./config.txt", node_id)
    node.startup()