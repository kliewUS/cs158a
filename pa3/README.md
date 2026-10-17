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

# Execution examples



