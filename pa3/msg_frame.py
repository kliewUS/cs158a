import struct
"""
    Prepends all messages with 4 byte int, represeting exact byte length of JSON payload.
"""
def send_msg(sock, payload):
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
"""
def recv_msg(sock):
    raw_len = recv_bytes(sock, 4)
    msg_len = struct.unpack('>I', raw_len)[0]
    return recv_bytes(sock, msg_len)