import sys

from PyQt5 import QtCore

from CoreOperations.PluginLoaders.FilePacksPluginLoader import BaseFilepack

translate = QtCore.QCoreApplication.translate

class MBEFilepack(BaseFilepack):
    __slots__ = ('file_target', 'pack_target', 'build_pipeline', 'hash')
    filepack = "CSV"
    
    def __init__(self, pack_target):
        super().__init__()
        self.file_target = None
        self.build_pipeline = None
        self.pack_target = sys.intern(pack_target)
        self.hash = None
        
    def add_file(self, file, build_pipeline):
        self.file_target = sys.intern(file)
        self.build_pipeline = build_pipeline
        
    def get_source_filenames(self):
        return (self.pack_target,)
    
    def get_resource_targets(self):
        return (self.pack_target,)
        
    
    @staticmethod
    def make_packname(file):
        return file

    @staticmethod
    def unpack(file, working_directory):
        pass
    
    @staticmethod
    def pack(mbe_path, destination_directory):
        pass
    
    @staticmethod
    def get_extraction_name():
        return "CSVs"
    
    @staticmethod
    def get_build_message():
        return translate("Filepacks::CSV", "Building CSV files")

    def get_build_pipelines(self):
        return (self.build_pipeline,)

    def set_build_pipelines(self, build_pipelines):
        self.build_pipeline = build_pipelines[0]
        
    def get_file_targets(self):
        return (self.file_target,)
    
    def set_file_targets(self, targets):
        self.file_target = targets[0]
        
    def get_pack_targets(self):
        return (self.pack_target,)
    
    def set_pack_targets(self, targets):
        self.pack_target = targets[0]

    def wipe_pipelines(self):
        self.build_pipeline = None