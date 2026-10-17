import os
import base64
import shutil

class FileManager:
    def __init__(self, shared_dir="shared", downloads_dir="downloads"):
        self.shared_dir = shared_dir
        self.downloads_dir = downloads_dir

        os.makedirs(self.shared_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)

    def scan_shared(self):
        """
        Looks inside the shared directory.
        Returns a list of filenames (strings) currently available to share.
        """
        shared_file_path = os.path.join(os.getcwd(), self.shared_dir)
        return os.listdir(shared_file_path)

    def read_and_encode(self, filename):
        """
        First, checks if a file was provided. If not, this means a path was provided, so ignore it.
        Reads a file from the shared directory and converts it to Base64 text.
        Returns the Base64 string, or None if the file doesn't exist.
        """
        name = os.path.basename(filename)

        if name != filename or not name:
            return None

        file_path = os.path.join(os.getcwd(), self.shared_dir, filename)

        try:
            with open(file_path, "rb") as image_file:
                base64_bytes = base64.b64encode(image_file.read())
                base64_string = base64_bytes.decode("utf-8")
        except OSError:
            return None
        
        return base64_string
    
    def decode_and_save(self, filename, base64_string):
        """
        First, checks if a file was provided. If not, this means a path was provided, so ignore it.
        Decodes base64 string back into bytes and saves into the download folder.
        Then copies the file into the node's shared folder.
        """
        name = os.path.basename(filename)

        if name != filename or not name:
            return None

        download_path = os.path.join(os.getcwd(), self.downloads_dir, filename)
        shared_path = os.path.join(os.getcwd(), self.shared_dir, filename)

        file_bytes = base64.b64decode(base64_string)

        with open(download_path, "wb") as file:
            file.write(file_bytes)

        tmp = os.path.join(self.shared_dir, "." + name + ".part")
        shutil.copy(download_path, tmp)
        
        os.replace(tmp, shared_path) 