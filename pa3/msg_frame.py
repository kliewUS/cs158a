import struct

def send_msg(sock, payload):
    len_prefix = struct.pack('>I', len(payload))
    sock.sendall(len_prefix + payload)

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

def recv_msg(sock):
    raw_len = recv_bytes(sock, 4)
    msg_len = struct.unpack('>I', raw_len)[0]
    return recv_bytes(sock, msg_len)