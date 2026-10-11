import struct

# Largest payload allowed in one message (64 MiB). Base64 inflates files by ~4/3, so this fits files up to ~48 MiB.
MAX_MSG_SIZE = 64 * 1024 * 1024

"""
    Prepends all messages with 4 byte int, represeting exact byte length of JSON payload.
    Raises ValueError if the payload is larger than MAX_MSG_SIZE, since the receiver would reject it.
"""
def send_msg(sock, payload):
    if len(payload) > MAX_MSG_SIZE:
        raise ValueError(f"Message of {len(payload)} bytes exceeds limit of {MAX_MSG_SIZE} bytes")
    len_prefix = struct.pack('>I', len(payload))
    sock.sendall(len_prefix + payload)

"""
    First reads first 4 bytes to get message length.
    Then loops through recv until the entire message in bytes are in the buffer.
"""
def recv_bytes(sock, num_bytes):
    buffer = bytearray()
    while len(buffer) < num_bytes:
        try:
            data = sock.recv(num_bytes - len(buffer))
            if not data:
                raise ConnectionError("Peer closed connection")
            buffer.extend(data)
        except ConnectionResetError as e:
            raise ConnectionError("Peer connection unexpectedly reset")
    return bytes(buffer)

"""
    Reads first 4 bytes and unpacks it to determine message length.
    Then calls recv_bytes to buffer the entire message in bytes.
    A length over MAX_MSG_SIZE means the stream is corrupt (or the peer is misbehaving).
    The next message boundary can no longer be found, so it is treated as a disconnection.
"""
def recv_msg(sock):
    raw_len = recv_bytes(sock, 4)
    msg_len = struct.unpack('>I', raw_len)[0]
    if msg_len > MAX_MSG_SIZE:
        raise ConnectionError(f"Message length {msg_len} exceeds limit of {MAX_MSG_SIZE} bytes")
    return recv_bytes(sock, msg_len)