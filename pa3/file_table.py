import threading

class FileTableManager:
    def __init__(self):
        # Maps peer_id (string) to a list of filenames (strings)
        self.peer_files = {}
        self.lock = threading.Lock()

    def update_peer_files(self, peer_id, file_list):
        """
        Called when we receive a FILE_LIST message from a peer.
        Replaces their old list of files with the new list.
        """
        with self.lock:
            self.peer_files[peer_id] = file_list

    def remove_peer(self, peer_id):
        """
        Called when a peer disconnects. 
        Removes them completely from the table.
        """
        with self.lock:
            if peer_id in self.peer_files:
                self.peer_files.pop(peer_id)

    def get_all_available_files(self):
        """
        Returns a dictionary of all peers and their files.
        """

        with self.lock:
            return dict(self.peer_files)