import json
from typing import Callable, Dict

"""
    Defines the message format shared by every node in the group.
    All messages are JSON objects carrying an "id" (sender UUID) and a "type".
    This module only converts between dicts and bytes; it never touches sockets.
    TCP framing (length prefix) is handled separately in msg_frame.py.
"""

# Message types
PEER_REQ = "PEER_REQ"
PEER_ACK = "PEER_ACK"
IDENT = "IDENT"
FILE_LIST = "FILE_LIST"
DATA_REQ = "DATA_REQ"
FILE_DATA = "FILE_DATA"

# FILE_DATA status values
STATUS_OK = "OK"
STATUS_ERROR = "ERROR"

# Field names
ID = "id"
TYPE = "type"
TARGET_PORT = "targetPort"
FILE_LIST_FIELD = "fileList"
FILE_NAME = "fileName"
FILE_CONTENT = "fileContent"
STATUS = "status"
ERROR_MESSAGE = "errorMessage"

# Fields every message of a given type must carry, along with their expected type.
REQUIRED_FIELDS = {
    PEER_REQ: {ID: str, TYPE: str},
    PEER_ACK: {ID: str, TYPE: str, TARGET_PORT: int},
    IDENT: {ID: str, TYPE: str},
    FILE_LIST: {ID: str, TYPE: str, FILE_LIST_FIELD: list},
    DATA_REQ: {ID: str, TYPE: str, FILE_NAME: str},
    FILE_DATA: {ID: str, TYPE: str, FILE_NAME: str, STATUS: str},
}


class MessageError(Exception):
    """
        Raised when received bytes are not a valid message.
    """
    pass


"""
    Message builders. Use these instead of writing message dicts by hand.
"""
def make_peer_req(node_id):
    return {ID: node_id, TYPE: PEER_REQ}

def make_peer_ack(node_id, tcp_port):
    return {ID: node_id, TYPE: PEER_ACK, TARGET_PORT: tcp_port}

def make_ident(node_id):
    return {ID: node_id, TYPE: IDENT}

def make_file_list(node_id, file_names):
    return {ID: node_id, TYPE: FILE_LIST, FILE_LIST_FIELD: list(file_names)}

def make_data_req(node_id, file_name):
    return {ID: node_id, TYPE: DATA_REQ, FILE_NAME: file_name}

"""
    file_content is the file's bytes already encoded as base64 text (done by the file manager).
"""
def make_file_data(node_id, file_name, file_content):
    return {ID: node_id, TYPE: FILE_DATA, FILE_NAME: file_name, STATUS: STATUS_OK, FILE_CONTENT: file_content}

"""
    Sent in place of file data when the requested file cannot be served.
"""
def make_file_error(node_id, file_name, error_message):
    return {ID: node_id, TYPE: FILE_DATA, FILE_NAME: file_name, STATUS: STATUS_ERROR, ERROR_MESSAGE: error_message}


"""
    Serializes a message dict into UTF-8 JSON bytes.
"""
def encode(msg):
    return json.dumps(msg).encode("utf-8")

"""
    Parses bytes into a message dict and validates it.
    Raises MessageError if the bytes are not valid JSON or the message is malformed.
"""
def decode(data):
    try:
        msg = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise MessageError(f"Invalid JSON: {e}")

    validate(msg)
    return msg

"""
    Checks that msg has a known type and every field that type requires.
    FILE_DATA additionally needs fileContent when OK, or errorMessage when ERROR.
"""
def validate(msg):
    if not isinstance(msg, dict):
        raise MessageError("Message is not a JSON object")

    msg_type = msg.get(TYPE)
    if msg_type not in REQUIRED_FIELDS:
        raise MessageError(f"Unknown message type: {msg_type}")

    for field, field_type in REQUIRED_FIELDS[msg_type].items():
        if field not in msg:
            raise MessageError(f"{msg_type} missing field: {field}")
        # bool is a subclass of int, so reject it explicitly for targetPort.
        if not isinstance(msg[field], field_type) or isinstance(msg[field], bool):
            raise MessageError(f"{msg_type} field {field} must be {field_type.__name__}")

    if msg_type == FILE_LIST and not all(isinstance(name, str) for name in msg[FILE_LIST_FIELD]):
        raise MessageError("FILE_LIST fileList must contain only strings")

    if msg_type == FILE_DATA:
        status = msg[STATUS]
        if status == STATUS_OK and not isinstance(msg.get(FILE_CONTENT), str):
            raise MessageError("FILE_DATA with OK status missing fileContent")
        if status == STATUS_ERROR and not isinstance(msg.get(ERROR_MESSAGE), str):
            raise MessageError("FILE_DATA with ERROR status missing errorMessage")
        if status not in (STATUS_OK, STATUS_ERROR):
            raise MessageError(f"FILE_DATA has unknown status: {status}")


class MessageRouter:
    """
        Routes each received message to the handler registered for its type.
        handlers - Maps message type to a function taking (peer_id, msg).
        on_unhandled - Called for messages with no registered handler.
    """
    def __init__(self, on_unhandled: Callable = None):
        self.handlers: Dict[str, Callable] = {}
        self.on_unhandled = on_unhandled

    """
        Registers handler(peer_id, msg) for the given message type.
    """
    def register(self, msg_type, handler):
        if msg_type not in REQUIRED_FIELDS:
            raise ValueError(f"Unknown message type: {msg_type}")
        self.handlers[msg_type] = handler

    """
        Calls the handler for msg's type. Can be passed directly as a node's on_message_received.
    """
    def dispatch(self, peer_id, msg):
        handler = self.handlers.get(msg.get(TYPE))
        if handler:
            handler(peer_id, msg)
        elif self.on_unhandled:
            self.on_unhandled(peer_id, msg)
