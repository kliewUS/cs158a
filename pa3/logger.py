from datetime import datetime
import threading

class Logger():
    """
    log_file_path - Path to save log file.
    echo_stdout - Toggle to print to terminal or not.
    lock - lock - Acquires lock for the node using the logger.
    """
    def __init__(self, log_file_path="log.txt", echo_stdout=True):
        self.log_file_path = log_file_path
        self.echo_stdout = echo_stdout
        self.lock = threading.Lock()

    def _write_log(self, text):
        """
        Helper method to format the timestamp, write to the file, 
        and print to the terminal if echo_stdout is True.
        """
        with self.lock: 
            timestamp = str(datetime.now())
            log_entry = timestamp + " " + text

            with open(self.log_file_path, "a") as file:
                file.write(log_entry + "\n")
            
            if self.echo_stdout:
                print(log_entry)

    def log_message(self, direction, peer_id, msg_type):
        """
        Logs a sent or received message.
        'direction' should be a string like "SENT" or "RECEIVED".
        """
        log_text = f"{direction}: [Type: {msg_type}] | Peer: {peer_id}"
        self._write_log(log_text)

    def log_peer_event(self, action, peer_id):
        """
        Logs when a peer is added or removed.
        'action' should be a string like "CONNECTED" or "DISCONNECTED".
        """
        log_text = f"PEER {action}: {peer_id}"
        self._write_log(log_text)