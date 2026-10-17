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
- Node 1 starts with test.txt and danny.txt
- Node 2 starts with alice.txt
- Node 3 starts with bob.txt
- Node 4 starts with cat.jpg
- Node 5 starts with charlie.txt


# Execution examples

## 1st terminal:
```bash
python demo.py --port 6001 --dir node1
Listening for connections at port: 6001
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e sent message: {'id': 'c3ef21f5-3804-4193-b1d6-9a0c03ee678e', 'type': 'PEER_REQ'}
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e received message: {'id': 'c3ef21f5-3804-4193-b1d6-9a0c03ee678e', 'type': 'PEER_REQ'}
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e ignores self-broadcast.
2026-10-17 12:52:33.038283 SENT: [Type: PEER_REQ] | Peer: broadcast:54321
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e received message: {'id': '8c28247b-1210-41b7-a3aa-0db16e535138', 'type': 'PEER_REQ'}
2026-10-17 12:52:38.423564 RECEIVED: [Type: PEER_REQ] | Peer: 10.0.0.175:55920
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e received Message Type: PEER_REQ and sending it to 10.0.0.175 with tcp_port: 6001
2026-10-17 12:52:38.423766 SENT: [Type: PEER_ACK] | Peer: 10.0.0.175:55920
2026-10-17 12:52:38.424700 RECEIVED: [Type: IDENT] | Peer: 10.0.0.175:61412
2026-10-17 12:52:38.424819 PEER ADDED: 10.0.0.175:61412
2026-10-17 12:52:38.425152 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
2026-10-17 12:52:38.425264 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e received message: {'id': '0cbd1885-744f-49b9-bcda-53fe0c9c79de', 'type': 'PEER_REQ'}
2026-10-17 12:52:42.500944 RECEIVED: [Type: PEER_REQ] | Peer: 10.0.0.175:52438
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e received Message Type: PEER_REQ and sending it to 10.0.0.175 with tcp_port: 6001
2026-10-17 12:52:42.501892 SENT: [Type: PEER_ACK] | Peer: 10.0.0.175:52438
2026-10-17 12:52:42.506224 RECEIVED: [Type: IDENT] | Peer: 10.0.0.175:61417
2026-10-17 12:52:42.506745 PEER ADDED: 10.0.0.175:61417
2026-10-17 12:52:42.508283 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
2026-10-17 12:52:42.509013 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
2026-10-17 12:52:42.538204 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
2026-10-17 12:52:42.538408 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e received message: {'id': '92c36753-75c9-461d-9377-3f607e0c52ad', 'type': 'PEER_REQ'}
2026-10-17 12:52:47.529102 RECEIVED: [Type: PEER_REQ] | Peer: 10.0.0.175:63343
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e received Message Type: PEER_REQ and sending it to 10.0.0.175 with tcp_port: 6001
2026-10-17 12:52:47.529301 SENT: [Type: PEER_ACK] | Peer: 10.0.0.175:63343
2026-10-17 12:52:47.532396 RECEIVED: [Type: IDENT] | Peer: 10.0.0.175:61422
2026-10-17 12:52:47.532467 PEER ADDED: 10.0.0.175:61422
2026-10-17 12:52:47.532687 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61422
2026-10-17 12:52:47.532808 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61422
2026-10-17 12:52:47.924253 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e received message: {'id': 'ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e', 'type': 'PEER_REQ'}
2026-10-17 12:52:51.053038 RECEIVED: [Type: PEER_REQ] | Peer: 10.0.0.175:58072
Node c3ef21f5-3804-4193-b1d6-9a0c03ee678e received Message Type: PEER_REQ and sending it to 10.0.0.175 with tcp_port: 6001
2026-10-17 12:52:51.053319 SENT: [Type: PEER_ACK] | Peer: 10.0.0.175:58072
2026-10-17 12:52:51.060630 RECEIVED: [Type: IDENT] | Peer: 10.0.0.175:61427
2026-10-17 12:52:51.061065 PEER ADDED: 10.0.0.175:61427
2026-10-17 12:52:51.061846 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61427
2026-10-17 12:52:51.062962 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61427
2026-10-17 12:52:52.000437 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
2026-10-17 12:52:52.539423 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
2026-10-17 12:52:52.539750 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
2026-10-17 12:52:52.539859 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61422
2026-10-17 12:52:52.539943 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61427
2026-10-17 12:52:57.030740 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61422
2026-10-17 12:52:57.927908 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
get cat.jpg
2026-10-17 12:53:00.553700 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61427
2026-10-17 12:53:02.008728 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
2026-10-17 12:53:02.172789 SENT: [Type: DATA_REQ] | Peer: 10.0.0.175:61422
2026-10-17 12:53:02.174881 RECEIVED: [Type: FILE_DATA] | Peer: 10.0.0.175:61422
Successfully downloaded cat.jpg
2026-10-17 12:53:02.545552 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
2026-10-17 12:53:02.545883 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
2026-10-17 12:53:02.546402 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61422
2026-10-17 12:53:02.546486 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61427
files
8c28247b-1210-41b7-a3aa-0db16e535138 - (10.0.0.175:61412): ['alice.txt']
0cbd1885-744f-49b9-bcda-53fe0c9c79de - (10.0.0.175:61417): ['bob.txt']
92c36753-75c9-461d-9377-3f607e0c52ad - (10.0.0.175:61422): ['cat.jpg']
ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e - (10.0.0.175:61427): ['charlie.txt']
2026-10-17 12:53:07.034945 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61422
2026-10-17 12:53:07.935780 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
2026-10-17 12:53:10.560894 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61427
2026-10-17 12:53:12.017463 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
2026-10-17 12:53:12.550365 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
2026-10-17 12:53:12.550697 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
2026-10-17 12:53:12.550825 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61422
2026-10-17 12:53:12.550925 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61427
2026-10-17 12:53:17.043890 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61422
2026-10-17 12:53:17.943712 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
peers
8c28247b-1210-41b7-a3aa-0db16e535138 - (10.0.0.175:61412)
0cbd1885-744f-49b9-bcda-53fe0c9c79de - (10.0.0.175:61417)
92c36753-75c9-461d-9377-3f607e0c52ad - (10.0.0.175:61422)
ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e - (10.0.0.175:61427)
2026-10-17 12:53:20.568720 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61427
2026-10-17 12:53:22.025060 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
2026-10-17 12:53:22.556592 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61412
2026-10-17 12:53:22.556977 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61417
2026-10-17 12:53:22.557610 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61422
2026-10-17 12:53:22.557726 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61427
quit
```

## 2nd terminal:
```bash
python demo.py --port 6002 --dir node2
Listening for connections at port: 6002
Node 8c28247b-1210-41b7-a3aa-0db16e535138 sent message: {'id': '8c28247b-1210-41b7-a3aa-0db16e535138', 'type': 'PEER_REQ'}
Node 8c28247b-1210-41b7-a3aa-0db16e535138 received message: {'id': '8c28247b-1210-41b7-a3aa-0db16e535138', 'type': 'PEER_REQ'}
Node 8c28247b-1210-41b7-a3aa-0db16e535138 ignores self-broadcast.
2026-10-17 12:52:38.423291 SENT: [Type: PEER_REQ] | Peer: broadcast:54321
2026-10-17 12:52:38.423916 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node 8c28247b-1210-41b7-a3aa-0db16e535138 received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6001
2026-10-17 12:52:38.424611 SENT: [Type: IDENT] | Peer: 10.0.0.175:6001
2026-10-17 12:52:38.424693 PEER ADDED: 10.0.0.175:6001
2026-10-17 12:52:38.425096 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:52:38.425222 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
Node 8c28247b-1210-41b7-a3aa-0db16e535138 received message: {'id': '0cbd1885-744f-49b9-bcda-53fe0c9c79de', 'type': 'PEER_REQ'}
2026-10-17 12:52:42.500936 RECEIVED: [Type: PEER_REQ] | Peer: 10.0.0.175:52438
Node 8c28247b-1210-41b7-a3aa-0db16e535138 received Message Type: PEER_REQ and sending it to 10.0.0.175 with tcp_port: 6002
2026-10-17 12:52:42.501893 SENT: [Type: PEER_ACK] | Peer: 10.0.0.175:52438
2026-10-17 12:52:42.503128 RECEIVED: [Type: IDENT] | Peer: 10.0.0.175:61416
2026-10-17 12:52:42.503386 PEER ADDED: 10.0.0.175:61416
2026-10-17 12:52:42.504331 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61416
2026-10-17 12:52:42.504646 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61416
2026-10-17 12:52:42.538325 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
...
2026-10-17 12:53:10.560163 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61425
2026-10-17 12:53:12.016423 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61416
2026-10-17 12:53:12.550584 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:53:17.043178 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61421
2026-10-17 12:53:17.943381 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:53:17.944617 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61416
2026-10-17 12:53:17.945462 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61421
2026-10-17 12:53:17.946281 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61425
2026-10-17 12:53:20.567240 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61425
2026-10-17 12:53:22.024254 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61416
2026-10-17 12:53:22.556755 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:53:23.778525 PEER REMOVED: 10.0.0.175:6001
quit
```
## 3rd terminal:
```bash
python demo.py --port 6003 --dir node3
Listening for connections at port: 6003
Node 0cbd1885-744f-49b9-bcda-53fe0c9c79de sent message: {'id': '0cbd1885-744f-49b9-bcda-53fe0c9c79de', 'type': 'PEER_REQ'}
Node 0cbd1885-744f-49b9-bcda-53fe0c9c79de received message: {'id': '0cbd1885-744f-49b9-bcda-53fe0c9c79de', 'type': 'PEER_REQ'}
Node 0cbd1885-744f-49b9-bcda-53fe0c9c79de ignores self-broadcast.
2026-10-17 12:52:42.500542 SENT: [Type: PEER_REQ] | Peer: broadcast:54321
2026-10-17 12:52:42.502088 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node 0cbd1885-744f-49b9-bcda-53fe0c9c79de received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6002
2026-10-17 12:52:42.502937 SENT: [Type: IDENT] | Peer: 10.0.0.175:6002
2026-10-17 12:52:42.503388 PEER ADDED: 10.0.0.175:6002
2026-10-17 12:52:42.504331 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:52:42.504649 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:52:42.504885 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node 0cbd1885-744f-49b9-bcda-53fe0c9c79de received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6001
2026-10-17 12:52:42.506062 SENT: [Type: IDENT] | Peer: 10.0.0.175:6001
2026-10-17 12:52:42.506744 PEER ADDED: 10.0.0.175:6001
2026-10-17 12:52:42.508391 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:52:42.508773 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:52:42.538557 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
Node 0cbd1885-744f-49b9-bcda-53fe0c9c79de received message: {'id': '92c36753-75c9-461d-9377-3f607e0c52ad', 'type': 'PEER_REQ'}
2026-10-17 12:52:47.529012 RECEIVED: [Type: PEER_REQ] | Peer: 10.0.0.175:63343
Node 0cbd1885-744f-49b9-bcda-53fe0c9c79de received Message Type: PEER_REQ and sending it to 10.0.0.175 with tcp_port: 6003
2026-10-17 12:52:47.529257 SENT: [Type: PEER_ACK] | Peer: 10.0.0.175:63343
2026-10-17 12:52:47.530342 RECEIVED: [Type: IDENT] | Peer: 10.0.0.175:61420
2026-10-17 12:52:47.530431 PEER ADDED: 10.0.0.175:61420
2026-10-17 12:52:47.530741 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61420
2026-10-17 12:52:47.530837 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61420
2026-10-17 12:52:47.925501 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
...
2026-10-17 12:53:12.551005 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:53:17.042301 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61420
2026-10-17 12:53:17.944752 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:53:20.569351 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61428
2026-10-17 12:53:22.024071 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:53:22.024824 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:53:22.025389 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61420
2026-10-17 12:53:22.026054 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61428
2026-10-17 12:53:22.557135 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:53:23.778544 PEER REMOVED: 10.0.0.175:6001
2026-10-17 12:53:26.374696 PEER REMOVED: 10.0.0.175:6002
2026-10-17 12:53:27.046039 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61420
quit
```

## 4th terminal:
```bash
python demo.py --port 6004 --dir node4
Listening for connections at port: 6004
Node 92c36753-75c9-461d-9377-3f607e0c52ad sent message: {'id': '92c36753-75c9-461d-9377-3f607e0c52ad', 'type': 'PEER_REQ'}
Node 92c36753-75c9-461d-9377-3f607e0c52ad received message: {'id': '92c36753-75c9-461d-9377-3f607e0c52ad', 'type': 'PEER_REQ'}
Node 92c36753-75c9-461d-9377-3f607e0c52ad ignores self-broadcast.
2026-10-17 12:52:47.528694 SENT: [Type: PEER_REQ] | Peer: broadcast:54321
2026-10-17 12:52:47.529402 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node 92c36753-75c9-461d-9377-3f607e0c52ad received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6003
2026-10-17 12:52:47.530263 SENT: [Type: IDENT] | Peer: 10.0.0.175:6003
2026-10-17 12:52:47.530337 PEER ADDED: 10.0.0.175:6003
2026-10-17 12:52:47.530660 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6003
2026-10-17 12:52:47.530746 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node 92c36753-75c9-461d-9377-3f607e0c52ad received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6002
2026-10-17 12:52:47.530857 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6003
2026-10-17 12:52:47.531347 SENT: [Type: IDENT] | Peer: 10.0.0.175:6002
2026-10-17 12:52:47.531431 PEER ADDED: 10.0.0.175:6002
2026-10-17 12:52:47.531672 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:52:47.531748 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node 92c36753-75c9-461d-9377-3f607e0c52ad received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6001
2026-10-17 12:52:47.531899 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:52:47.532314 SENT: [Type: IDENT] | Peer: 10.0.0.175:6001
2026-10-17 12:52:47.532372 PEER ADDED: 10.0.0.175:6001
2026-10-17 12:52:47.532623 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:52:47.532797 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:52:47.925912 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
Node 92c36753-75c9-461d-9377-3f607e0c52ad received message: {'id': 'ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e', 'type': 'PEER_REQ'}
2026-10-17 12:52:51.052311 RECEIVED: [Type: PEER_REQ] | Peer: 10.0.0.175:58072
Node 92c36753-75c9-461d-9377-3f607e0c52ad received Message Type: PEER_REQ and sending it to 10.0.0.175 with tcp_port: 6004
2026-10-17 12:52:51.052999 SENT: [Type: PEER_ACK] | Peer: 10.0.0.175:58072
2026-10-17 12:52:51.057043 RECEIVED: [Type: IDENT] | Peer: 10.0.0.175:61426
2026-10-17 12:52:51.057268 PEER ADDED: 10.0.0.175:61426
2026-10-17 12:52:51.058817 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61426
2026-10-17 12:52:51.059124 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61426
2026-10-17 12:52:52.001082 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6003
2026-10-17 12:52:52.539975 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:52:57.029369 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6003
2026-10-17 12:52:57.030103 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:52:57.030557 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:52:57.030864 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61426
2026-10-17 12:52:57.929255 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:53:00.553077 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61426
2026-10-17 12:53:02.009856 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6003
2026-10-17 12:53:02.172950 RECEIVED: [Type: DATA_REQ] | Peer: 10.0.0.175:6001
2026-10-17 12:53:02.174622 SENT: [Type: FILE_DATA] | Peer: 10.0.0.175:6001
2026-10-17 12:53:02.546569 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
...
2026-10-17 12:53:23.778647 PEER REMOVED: 10.0.0.175:6001
2026-10-17 12:53:26.374859 PEER REMOVED: 10.0.0.175:6002
2026-10-17 12:53:27.045685 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6003
2026-10-17 12:53:27.047078 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:61426
2026-10-17 12:53:29.395198 PEER REMOVED: 10.0.0.175:6003
2026-10-17 12:53:30.575428 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:61426
quit
```

## 5th terminal:
```bash
python demo.py --port 6005 --dir node5
Listening for connections at port: 6005
Node ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e sent message: {'id': 'ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e', 'type': 'PEER_REQ'}
Node ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e received message: {'id': 'ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e', 'type': 'PEER_REQ'}
Node ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e ignores self-broadcast.
2026-10-17 12:52:51.051992 SENT: [Type: PEER_REQ] | Peer: broadcast:54321
2026-10-17 12:52:51.053573 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6002
2026-10-17 12:52:51.054383 SENT: [Type: IDENT] | Peer: 10.0.0.175:6002
2026-10-17 12:52:51.054695 PEER ADDED: 10.0.0.175:6002
2026-10-17 12:52:51.055522 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:52:51.055844 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:52:51.056068 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6004
2026-10-17 12:52:51.056933 SENT: [Type: IDENT] | Peer: 10.0.0.175:6004
2026-10-17 12:52:51.057287 PEER ADDED: 10.0.0.175:6004
2026-10-17 12:52:51.058810 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6004
2026-10-17 12:52:51.059114 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6004
2026-10-17 12:52:51.059411 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6001
2026-10-17 12:52:51.060546 SENT: [Type: IDENT] | Peer: 10.0.0.175:6001
2026-10-17 12:52:51.060903 PEER ADDED: 10.0.0.175:6001
2026-10-17 12:52:51.061846 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:52:51.062928 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:52:51.063748 RECEIVED: [Type: PEER_ACK] | Peer: 10.0.0.175:54321
Node ef5a9c07-0fcb-4bd9-a1cf-3e5bad75881e received Message Type: PEER_ACK and connecting to 10.0.0.175 with tcp_port: 6003
2026-10-17 12:52:51.064875 SENT: [Type: IDENT] | Peer: 10.0.0.175:6003
2026-10-17 12:52:51.065126 PEER ADDED: 10.0.0.175:6003
2026-10-17 12:52:51.065558 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6003
2026-10-17 12:52:51.065720 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6003
2026-10-17 12:52:52.001254 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6003
2026-10-17 12:52:52.540074 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:52:57.031107 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6004
2026-10-17 12:52:57.929682 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:53:00.552004 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6002
2026-10-17 12:53:00.552879 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6004
2026-10-17 12:53:00.553518 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6001
2026-10-17 12:53:00.554066 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6003
...
2026-10-17 12:53:23.778777 PEER REMOVED: 10.0.0.175:6001
2026-10-17 12:53:26.375000 PEER REMOVED: 10.0.0.175:6002
2026-10-17 12:53:27.047328 RECEIVED: [Type: FILE_LIST] | Peer: 10.0.0.175:6004
2026-10-17 12:53:29.395409 PEER REMOVED: 10.0.0.175:6003
2026-10-17 12:53:30.575263 SENT: [Type: FILE_LIST] | Peer: 10.0.0.175:6004
2026-10-17 12:53:32.097263 PEER REMOVED: 10.0.0.175:6004
quit
```