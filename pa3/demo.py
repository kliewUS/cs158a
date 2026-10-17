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

def reg_handlers(router, node, fm, ftm):

    def on_file_list(peer_id, msg):
        ftm.update_peer_files(peer_id, msg[FILE_LIST_FIELD])

    def on_data_req(peer_id, msg):
        name = msg[FILE_NAME]
        content = fm.read_and_encode(name)
        if content is None:
            node.send_message(peer_id, make_file_error(node.id, name, "File not found"))
        else:
            node.send_message(peer_id, make_file_data(node.id, name, content))

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
    parser = argparse.ArgumentParser(description='setup node')
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--dir', default='.')

    args = parser.parse_args()

    fm = FileManager(shared_dir=os.path.join(args.dir, "shared"), downloads_dir=os.path.join(args.dir, "downloads"))
    logger = Logger(log_file_path=os.path.join(args.dir, "log.txt"))
    ftm = FileTableManager()
    router = MessageRouter()
    node = p2p_node(args.port, on_message_received=router.dispatch, on_peer_disconnected=ftm.remove_peer, logger=logger, get_file_list=fm.scan_shared)

    reg_handlers(router, node, fm, ftm)
    node.start()
    time.sleep(0.5)
    node.broadcast_peer_req()

    while True:
        try: 
            cmd = input("> ").split()

            if not cmd:
                continue

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
            elif cmd[0] == "peers":
                for pid in node.peer_list.keys():
                    print(f"{pid}")
            elif cmd[0] == "files":
                for pid, files in ftm.get_all_available_files().items():
                    print(f"{pid}: {files}")
            elif cmd[0] == "quit":
                node.stop()
                break
            else:
                print("Commands: peers, files, get <filename>, quit")
        except KeyboardInterrupt:
            node.stop()
            break

