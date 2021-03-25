import math
import os
import shutil
import subprocess
import urllib
import zipfile
import time

from .CustomWidgets import ProgressDialog


class DSCSToolsHandler:
    def __init__(self, game_location, dscstools_location):
        self.game_location = game_location
        self.dscstools_location = dscstools_location
        self.dscstools_folder = os.path.join(*os.path.split(dscstools_location)[:-1])
        self.dscstools_url = r"https://github.com/SydMontague/DSCSTools/releases/latest"
        
    ####################
    # Helper Functions #
    ####################
    def base_archive_name(self, archive):
        return  f"{archive}.steam.mvgl"
    
    def decrypted_archive_name(self, archive):
        return  f"{archive}_decrypted"
    
    ############################
    # DSCSTools Call Functions #
    ############################
    def mvgl_op(self, archive, origin, destination, operation, 
                input_transform, output_transform, 
                copy_required, remove_input):
        if copy_required:
            original_archive = os.path.join(origin, input_transform(archive))
            input_file = os.path.join(destination, input_transform(archive))
            shutil.copy2(original_archive, input_file)
        else:
            input_file = os.path.join(origin, input_transform(archive))
        
        output_file = os.path.join(destination, output_transform(archive))
            
        subprocess.call([self.dscstools_location, f'--{operation}', input_file, output_file],
                        creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.dscstools_folder)

        if remove_input:
            os.remove(input_file)
        
    def decrypt_mvgl(self, archive, origin, destination, remove_input=False): 
        self.mvgl_op(archive, origin, destination, "crypt", 
                     self.base_archive_name, self.decrypted_archive_name,
                     True, remove_input)
        
    def encrypt_mvgl(self, archive, origin, destination, remove_input=False):
        self.mvgl_op(archive, origin, destination, "crypt", 
                     self.decrypted_archive_name, self.base_archive_name,
                     False, remove_input)
        
    def unpack_mvgl(self, archive, origin, destination, remove_input=False):
        self.mvgl_op(archive, origin, destination, "extract", 
                     self.decrypted_archive_name, lambda x: x,
                     False, remove_input)
        
    def pack_mvgl(self, archive, origin, destination, remove_input=False):
        self.mvgl_op(archive, origin, destination, "pack", 
                     lambda x: x, self.decrypted_archive_name,
                     False, remove_input)
        
    def unpack_afs2(self, archive, origin, destination, remove_input=False):
        self.mvgl_op(archive, origin, destination, "afs2extract", 
                     self.base_archive_name, lambda x: x,
                     False, remove_input)
        
    def pack_afs2(self, archive, origin, destination, remove_input=False):
        self.mvgl_op(archive, origin, destination, "afs2pack", 
                     lambda x: x, self.base_archive_name, 
                     False, remove_input)
        
    def dump_mvgl(self, archive, origin, destination):
        self.decrypt_mvgl(archive, origin, destination, remove_input=True)
        self.unpack_mvgl(archive, destination, destination, remove_input=True)
        
    def unpack_mbe(self, mbe, origin, destination):
        origin_loc = os.path.join(origin, mbe)
        destination_loc = destination
        subprocess.call([self.dscstools_location, '--mbeextract', origin_loc, destination_loc], creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.dscstools_folder)

    def pack_mbe(self, mbe, origin, destination):
        origin_loc = os.path.join(origin, mbe)
        destination_loc = os.path.join(destination, mbe)
        subprocess.call([self.dscstools_location, '--mbepack', origin_loc, destination_loc], creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.dscstools_folder)
        
    ################################
    # DSCSTools Download Functions #
    ################################
    def get_dscstools_tag(self):
        if self.dscstools_url[:19] != r"https://github.com/":
            raise ValueError("Download URL is not on GitHub.")
        url = urllib.request.urlopen(self.dscstools_url).geturl()
        return url.split('/')[-1]
        
    def get_dscstools_download_url(self):
        tag = self.get_dscstools_tag()
        return rf"https://github.com/SydMontague/DSCSTools/releases/download/{tag}/DSCSTools_win64.zip", tag
        
    def deploy_dscstools(self, path):
        containing_folder = os.path.join(*os.path.split(path)[:-1])
        for iter_item in os.listdir(containing_folder):
            item = os.path.join(containing_folder, iter_item)
            if os.path.isfile(item):
                os.remove(item)
            elif os.path.isdir(item):
                shutil.rmtree(item)
            else:
                raise Exception("Encountered neither a file nor directory:", item)
        progdiag = ProgressDialog("Downloading DSCSTools")
        progdiag.show()
        try:
            url, tag = self.get_dscstools_download_url()
            with urllib.request.urlopen(url) as req, open(path, 'ab') as f:
                chunk_size = 1024 * 256
                total_size = int(req.info()['Content-Length'])

                chunk = None
                total_read = 0
                num_packets = int(math.ceil(chunk_size / total_size))
                packet_number = 1
                #I think this should request 256kB packets?!
                while chunk != b'':
                    progdiag.update_progbar(f"Downloading packet {packet_number}/{num_packets}", chunk_size / total_size)
                    chunk = req.read(chunk_size)
                    f.write(chunk)
                    total_read += len(chunk)
                    packet_number += 1
                    
            with zipfile.ZipFile(path, 'r') as f:
                progdiag.update_progbar("Extracting zip...", 1)
                f.extractall(containing_folder)
        finally:
            progdiag.close()
            
        return tag
    
    def install_dscstools(self):
        pass
    
    def update_dscstools(self):
        pass
    
    def check_for_new_dscstools_version(self):
        pass
