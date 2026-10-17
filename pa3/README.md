# Contributions

- Khai Yuan Liew - UDP broadcast listener, TCP server and client connector, socket connection management, handling peer disconnects, and demo setup.
- Daniel Nguyen - File management (Peer and file table management), file operations (scan shared files, Base64 encoding/decoding), and logging (file sent/received, peer table additions and removals) 
- Ivan Rivera - JSON seralization and desearlization, messaging delimiting, message format (message builders and handlers), and file list timer

# Message Format

## Message Fields
- ID - Id of the node in UUID.
- TYPE - Type of message recorded [ PEER_REQ | PEER_ACK | IDENT | FILE_LIST | DATA_REQ | FILE_DATA ]
- TARGET_PORT - Target peer TCP port to connect to. (PEER_ACK only)
- FILE_LIST_FIELD - List of available files from the node's connected peer(s). (FILE_LIST only)
- FILE_NAME - Name of the file requested. (DATA_REQ only)
- FILE_CONTENT - Contents of the file requested in a Base64 string. (FILE_DATA only)
- STATUS - Download status of the file requested. If an error occurred, then insert the error message into the message. [ OK | ERROR ]
- ERROR_MESSAGE - Error message if the download of the file requested failed. 

## Message Types
- PEER_REQ - {ID: str, TYPE: str} - Logs sender's id/address for the peers to identify and acknowledge the sender's connection request.
- PEER_ACK: {ID: str, TYPE: str, TARGET_PORT: int} - Logs sender's id/address and target TCP port for the peer to identify and connect to the target peer's port.
- IDENT: {ID: str, TYPE: str}
- FILE_LIST: {ID: str, TYPE: str, FILE_LIST_FIELD: list} - Logs peer's available file list is sent immediately upon connecting and then every 10 secs afterwards by default.
- DATA_REQ: {ID: str, TYPE: str, FILE_NAME: str} - Logs sender's id/address and the file name requested to the target peer that has the file requested.
- FILE_DATA: {ID: str, TYPE: str, FILE_NAME: str, STATUS: str, FILE_CONTENT: str} - Logs sender's id/address, the requested file name, the requested file content (if download is successful), and the download status.

## Message Boundaries and File Content Encoding
All messages are prepended with a 4 byte int before sending the message, which represents the exact byte length of the JSON payload. 
When read by the receiving peer, the first 4 bytes are unpacked to determine the message length and then the entire message is buffered as bytes.

Up to max of 48 MB can be stored in one message as Base64 inflates files size by 33%. If the message payload is oversized, then we will reject sending that message.

File content is encoded as a Base64 string to handle file transmission as the protocol only designed to handle text content not binary data.

# Local Instructions
To run p2p nodes, simply go to the pa3 directory and run the python demo agent file in each of the five terminals. 
```bash
cd pa3
python demo.py --port <port_number> --dir <file_dir>
```

# Inital Node Shared Files:
- Node 1 starts with test.txt
- Node 2 starts with alice.txt
- Node 3 starts with bob.txt
- Node 4 starts with cat.jpg
- Node 5 starts with charlie.txt


# Execution examples
### 3rd - 5th terminal executions examples are similar to the first two terminals, simply increment the port and node number by 1 per terminal when starting the nodes.

## 1st terminal:
```bash
python demo.py --port 6001 --dir node1
Listening for connections at port: 6001
Node 390d2571-6ca4-4214-80cd-e0eb428528ca sent message: {'id': '390d2571-6ca4-4214-80cd-e0eb428528ca', 'type': 'PEER_REQ'}
Node 390d2571-6ca4-4214-80cd-e0eb428528ca received message: {'id': '390d2571-6ca4-4214-80cd-e0eb428528ca', 'type': 'PEER_REQ'}
Node 390d2571-6ca4-4214-80cd-e0eb428528ca ignores self-broadcast.
2026-10-17 12:25:26.308290 SENT: [Type: PEER_REQ] | Peer: broadcast:54321
> Node 390d2571-6ca4-4214-80cd-e0eb428528ca received message: {'id': '9b26cb4c-2635-4295-89d7-57077306c758', 'type': 'PEER_REQ'}
2026-10-17 12:25:27.840971 RECEIVED: [Type: PEER_REQ] | Peer: 10.0.0.175:49843
Node 390d2571-6ca4-4214-80cd-e0eb428528ca received Message Type: PEER_REQ and sending it to 10.0.0.175 with tcp_port: 6001
2026-10-17 12:25:27.841163 SENT: [Type: PEER_ACK] | Peer: 10.0.0.175:49843
2026-10-17 12:25:27.841965 RECEIVED: [Type: IDENT] | Peer: 10.0.0.175:61277
2026-10-17 12:25:27.842087 PEER ADDED: 10.0.0.175:61277
2026-10-17 12:25:27.842497 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61277
2026-10-17 12:25:27.842659 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61277
get alice.txt
2026-10-17 12:25:31.396369 SENT: [Type: DATA_REQ] | Peer: 10.0.0.175:61277
> 2026-10-17 12:25:31.397939 RECEIVED: [Type: FILE_DATA] | Peer: 10.0.0.175:61277
Successfully downloaded alice.txt
2026-10-17 12:25:35.809906 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61277
2026-10-17 12:25:37.341631 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61277
peers
9b26cb4c-2635-4295-89d7-57077306c758 : 10.0.0.175:61277
> 2026-10-17 12:25:45.814009 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61277
2026-10-17 12:25:47.344765 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61277
files
9b26cb4c-2635-4295-89d7-57077306c758: ['alice.txt']
> 2026-10-17 12:25:55.816150 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61277
2026-10-17 12:25:57.351508 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61277
quit
```

## 2nd terminal:
```bash
python demo.py --port 6002 --dir node2
Listening for connections at port: 6002
Node 9b26cb4c-2635-4295-89d7-57077306c758 sent message: {'id': '9b26cb4c-2635-4295-89d7-57077306c758', 'type': 'PEER_REQ'}
Node 9b26cb4c-2635-4295-89d7-57077306c758 received message: {'id': '9b26cb4c-2635-4295-89d7-57077306c758', 'type': 'PEER_REQ'}
Node 9b26cb4c-2635-4295-89d7-57077306c758 ignores self-broadcast.
2026-10-17 12:25:27.840619 SENT: [Type: PEER_REQ] | Peer: broadcast:54321
2026-10-17 12:25:27.841290 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node 9b26cb4c-2635-4295-89d7-57077306c758 received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6001
2026-10-17 12:25:27.841862 SENT: [Type: IDENT] | Peer: 10.0.0.175:6001
2026-10-17 12:25:27.841949 PEER ADDED: 10.0.0.175:6001
2026-10-17 12:25:27.842335 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:25:27.842689 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
> 2026-10-17 12:25:31.396603 RECEIVED: [Type: DATA_REQ] | Peer: 10.0.0.175:6001
2026-10-17 12:25:31.397787 SENT: [Type: FILE_DATA] | Peer: 10.0.0.175:6001
2026-10-17 12:25:35.810241 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:25:37.341311 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:25:45.814335 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:25:47.344530 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:25:55.816515 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:25:57.351239 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:26:02.696960 PEER REMOVED: 10.0.0.175:6001
quit
```

