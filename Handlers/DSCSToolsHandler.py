import math
import os
import shutil
import subprocess
import urllib
import zipfile
import time
import subprocess

from tools.dscstools import DSCSTools
from UI.CustomWidgets import ProgressDialog
from Utils.MBE import mbe_batch_unpack
from .DSCSToolsArchiveWorker import DumpArchiveWorker, DumpArchiveWorkerThread
from .DSCSToolsMBEWorker import MBEWorker


def is_unpacked_mbe_table(path):
    return path[-3:] == 'mbe' and os.path.isdir(path)

def is_packed_mbe_table(path):
    return path[-3:] == 'mbe' and os.path.isfile(path)


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
            
    def dscstools_op(self, archive, origin, destination, operation, 
                     input_transform, output_transform, 
                     copy_required, remove_input):
        if copy_required:
            original_archive = os.path.join(origin, input_transform(archive))
            input_file = os.path.join(destination, input_transform(archive))
            shutil.copy2(original_archive, input_file)
        else:
            input_file = os.path.join(origin, input_transform(archive))
        
        output_file = os.path.join(destination, output_transform(archive))
        operation(input_file, output_file)

        if remove_input:
            os.remove(input_file)
        
    def decrypt_mvgl(self, archive, origin, destination, remove_input=False): 
        self.dscstools_op(archive, origin, destination, lambda inp, out: DSCSTools.crypt(inp, out), 
                     self.base_archive_name, self.decrypted_archive_name,
                     True, remove_input)
        
    def encrypt_mvgl(self, archive, origin, destination, remove_input=False):
        self.dscstools_op(archive, origin, destination, lambda inp, out: DSCSTools.crypt(inp, out),
                     self.decrypted_archive_name, self.base_archive_name,
                     False, remove_input)
        
    def unpack_mvgl(self, archive, origin, destination, remove_input=False):
        self.dscstools_op(archive, origin, destination, lambda inp, out: DSCSTools.extractMDB1(inp, out),
                     self.decrypted_archive_name, lambda x: x,
                     False, remove_input)
        
    def pack_mvgl(self, archive, origin, destination, remove_input=False):
        self.dscstools_op(archive, origin, destination,
                          lambda inp, out: DSCSTools.packMDB1(inp, out, DSCSTools.CompressMode.normal, False),
                     lambda x: x, self.decrypted_archive_name,
                     False, remove_input)
        
    def unpack_afs2(self, archive, origin, destination, remove_input=False):
        self.dscstools_op(archive, origin, destination, lambda inp, out: DSCSTools.extractAFS2(inp, out),
                     self.base_archive_name, lambda x: x,
                     False, remove_input)
        
    def pack_afs2(self, archive, origin, destination, remove_input=False):
        self.dscstools_op(archive, origin, destination, lambda inp, out: DSCSTools.packAFS2(inp, out),
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
        DSCSTools.extractMBE(origin_loc, destination_loc)
        
    def pack_mbe(self, mbe, origin, destination):
        origin_loc = os.path.join(origin, mbe)
        destination_loc = os.path.join(destination, mbe)
        DSCSTools.packMBE(origin_loc, destination_loc)
        
    def get_file_from_MDB1(self, archive, origin, destination, filepath):
        origin_loc = os.path.join(origin, archive)
        destination_loc = os.path.join(destination, archive)
        DSCSTools.extractMDB1File(origin_loc, destination_loc, filepath)
        
    ##########################
    # Multithreaded Patchers #
    ##########################
    def generate_archive_dumper(self, archive, origin, destination, threadpool, 
                                messageLog, updateMessageLog, lockGui, releaseGui):
        return DumpArchiveWorker(archive, origin, destination, threadpool, 
                                 messageLog, updateMessageLog, lockGui, releaseGui)
    
    def generate_mbe_extractor(self, origin, destination, threadpool, 
                               messageLog, updateMessageLog, lockGui, releaseGui):
        return MBEWorker(origin, destination, self.unpack_mbe, is_packed_mbe_table, threadpool, 
                         messageLog, updateMessageLog, lockGui, releaseGui)
    
    def generate_mbe_packer(self, origin, destination, threadpool, 
                               messageLog, updateMessageLog, lockGui, releaseGui):
        return MBEWorker(origin, destination, self.pack_mbe, is_unpacked_mbe_table, threadpool, 
                         messageLog, updateMessageLog, lockGui, releaseGui)
    
        