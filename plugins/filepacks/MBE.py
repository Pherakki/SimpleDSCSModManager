import os
import shutil
import sys

from PyQt5 import QtCore

from CoreOperations.PluginLoaders.FilePacksPluginLoader import BaseFilepack
from sdmmlib.dscstools import DSCSTools

translate = QtCore.QCoreApplication.translate


class MBEFilepack(BaseFilepack):
    __slots__ = ('file_targets', 'pack_target', 'build_pipelines', 'hash')
    packgroup = "MBE"
    groups = ("mbe",)
    
    def __init__(self, pack_target):
        super().__init__()
        self.file_targets = []
        self.build_pipelines = []
        self.pack_target = sys.intern(pack_target)
        self.hash = None
        
    def add_file(self, file, build_pipeline):
        self.file_targets.append(sys.intern(file))
        self.build_pipelines.append(build_pipeline)
        
    def get_source_filenames(self):
        return (self.pack_target,)
    
    def get_resource_targets(self):
        return (self.pack_target,)
        
    
    @staticmethod
    def make_packname(file):
        return os.path.split(file)[0]

    @staticmethod
    def unpack(file, working_directory):
        assert os.path.isfile(file), translate("Filepacks::MBE", "Input path {file} is not a file!").format(file=file)
        # The output folder will have the same name as the input MBE...
        # so get the output location from the input MBE filepath
        # First point of order is to move the input MBE to the working dir
        destination_loc, filename = os.path.split(file)

        DSCSTools.extractMBE(file, working_directory)
        
        working_path = os.path.join(working_directory, filename)
        os.remove(file)
        os.rename(working_path, file)
    
    @staticmethod
    def pack(mbe_path, destination_directory):
        # Make a bunch of careful checks to make sure we're not going to accidentally
        # wipe somebody's hard drive if mbe_path is a bad value
        assert mbe_path[-4:] == '.mbe', translate("Filepacks::MBE", "Attempted to pack a non-mbe path.")
        assert os.path.isdir(mbe_path), translate("Filepacks::MBE", "Error packing MBE: \'{mbe_path}\' is not a directory.").format(mbe_path=mbe_path)
        assert all((os.path.splitext(path)[1] == '.csv' for path in os.listdir(mbe_path))), translate("Filepacks::MBE", "Not all files in {mbe_path} are .csv files.").format(mbe_path=mbe_path)
        DSCSTools.packMBE(mbe_path, destination_directory)
        shutil.rmtree(mbe_path)
    
    @staticmethod
    def get_extraction_name():
        return translate("Filepacks::MBE", "MBEs")
    
    @staticmethod
    def get_build_message():
        return translate("Filepacks::MBE", "Building MBE tables")

    def get_build_pipelines(self):
        return self.build_pipelines

    def set_build_pipelines(self, build_pipelines):
        self.build_pipelines = build_pipelines
        
    def get_file_targets(self):
        return self.file_targets
        
    def set_file_targets(self, targets):
        self.file_targets = targets
        
    def get_pack_targets(self):
        return (self.pack_target,)
        
    def set_pack_targets(self, targets):
        self.pack_target = targets[0]
        
    def wipe_pipelines(self):
        self.build_pipelines = None