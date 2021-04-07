import math
import os
import shutil
import subprocess
import urllib
import zipfile
import time

from UI.CustomWidgets import ProgressDialog
from Utils.MBE import mbe_batch_unpack


class DSCSToolsHandler:
    def __init__(self, game_location, dscstools_location):
        self.game_location = game_location
        self.dscstools_location = dscstools_location
        self.dscstools_folder = os.path.join(*os.path.split(dscstools_location)[:-1])
        
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
        
    def full_dump_mdb1(self, archive, origin, destination, messageLog, updateMessageLog):
        self.dump_mvgl(archive, origin, destination)
        mbe_batch_unpack(os.path.join(destination, archive), self, messageLog.emit, updateMessageLog.emit)
    
    def full_dump_afs2(self, archive, origin, destination, messageLog, updateMessageLog):
        self.unpack_afs2(archive, origin, destination)
            
    def unpack_mbe(self, mbe, origin, destination):
        origin_loc = os.path.join(origin, mbe)
        destination_loc = destination
        subprocess.call([self.dscstools_location, '--mbeextract', origin_loc, destination_loc], creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.dscstools_folder)

    def pack_mbe(self, mbe, origin, destination):
        origin_loc = os.path.join(origin, mbe)
        destination_loc = os.path.join(destination, mbe)
        subprocess.call([self.dscstools_location, '--mbepack', origin_loc, destination_loc], creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.dscstools_folder)
    
    def install_dscstools(self):
        pass
    
    def update_dscstools(self):
        pass
    
    def check_for_new_dscstools_version(self):
        pass
