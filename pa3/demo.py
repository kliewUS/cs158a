import argparse
import os
import time
from file_table import FileTableManager
from file_manager import FileManager
from logger import Logger
from messages import (MessageRouter, 
                      FILE_LIST, DATA_REQ, FILE_DATA, 
                      FILE_LIST_FIELD, FILE_NAME, FILE_CONTENT, STATUS, STATUS_OK, ERROR_MESSAGE,
                      make_file_data, make_file_error, make_data_req
                      )
from p2p_node import p2p_node


"""
    Registers handlers using MessageRouter to route receiver message to the designated handler.
"""
def reg_handlers(router, node, fm, ftm):

    """
        Handler method to update the target peer's files
    """
    def on_file_list(peer_id, msg):
        ftm.update_peer_files(peer_id, msg[FILE_LIST_FIELD])

    """
        Handler method to handle data requests
        If file is not found, return an error.
        Otherwise, send a message to retrieve the requested file and send it to the requesting peer(s).
    """
    def on_data_req(peer_id, msg):
        name = msg[FILE_NAME]
        content = fm.read_and_encode(name)
        if content is None:
            node.send_message(peer_id, make_file_error(node.id, name, "File not found"))
        else:
            node.send_message(peer_id, make_file_data(node.id, name, content))

    """
        Handler method to handle FILE_DATA messages.
        If file already exists, do nothing.
        If the download fails, print the error message.
        Otherwise, decode the base64 string and save it to the downloads folder and copy it to the shared folder when download is done.
    """
    def on_file_data(peer_id, msg):
        name = msg[FILE_NAME]
        if msg[STATUS] != STATUS_OK:
            print(f"Download of {name} failed: {msg[ERROR_MESSAGE]}")
            return
        if name in fm.scan_shared():
            return
        fm.decode_and_save(name, msg[FILE_CONTENT])
        print(f"Successfully downloaded {name}")

    router.register(FILE_LIST, on_file_list)
    router.register(DATA_REQ, on_data_req)
    router.register(FILE_DATA, on_file_data)


if __name__ == "__main__":
    # Setup terminal arguments
    parser = argparse.ArgumentParser(description='setup node')
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--dir', default='.')

    args = parser.parse_args()

    # Setup node configuration
    fm = FileManager(shared_dir=os.path.join(args.dir, "shared"), downloads_dir=os.path.join(args.dir, "downloads"))
    logger = Logger(log_file_path=os.path.join(args.dir, "log.txt"))
    ftm = FileTableManager()
    router = MessageRouter()
    node = p2p_node(args.port, on_message_received=router.dispatch, on_peer_disconnected=ftm.remove_peer, logger=logger, get_file_list=fm.scan_shared)

    # Register handlers
    reg_handlers(router, node, fm, ftm)

    # Start up the node and broadcast peer requests.
    node.start()
    time.sleep(0.5)
    node.broadcast_peer_req()

    while True:
        try: 
            cmd = input("> ").split()

            # Ignore empty input.
            if not cmd:
                continue

            # Get the requested file from peers.
            # If we already have the file, keep the current file and do nothing.
            # Otherwise, check all peers to see if any nodes in the network have the requested file.
            # If a peer has a requested file, then send a data request messages to the target peer.
            # Otherwise, print a failure message in the terminal, stating no node has that requested file.
            if cmd[0] == "get" and len(cmd) == 2:
                name = cmd[1]
                if name in fm.scan_shared():
                    print(f"Already have {name}")
                else:
                    owner = next((pid for pid, files in ftm.get_all_available_files().items() if name in files), None)
                    if owner is None:
                        print(f"No peer has {name}")
                    else:
                        node.send_message(owner, make_data_req(node.id, name))
            
            # Returns a list of connected peers as UUIDs.
            elif cmd[0] == "peers":
                for pid in node.peer_list.keys():
                    print(f"{pid}")
            # Returns a list of available files from each connected peer.
            elif cmd[0] == "files":
                for pid, files in ftm.get_all_available_files().items():
                    print(f"{pid}: {files}")
            # Terminates the node.
            elif cmd[0] == "quit":
                node.stop()
                break
            # Prints out list of available commands if invalid command was given.
            else:
                print("Commands: peers, files, get <filename>, quit")
        # Handle program interruptions from the user. Also, terminates the node.
        except KeyboardInterrupt:
            node.stop()
            break

