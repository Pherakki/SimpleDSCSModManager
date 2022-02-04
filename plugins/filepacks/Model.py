import os
import sys

from PyQt5 import QtCore

from CoreOperations.PluginLoaders.FilePacksPluginLoader import BaseFilepack

translate = QtCore.QCoreApplication.translate

class ModelFilepack(BaseFilepack):
    __slots__ = ('file_targets', 'build_pipelines', 'hash')
    packgroup = "Model"
    groups = ("geom", "skel")
    
    def __init__(self, pack_target):
        super().__init__()
        self.file_targets = []
        self.build_pipelines = []
        self.hash = None
        
    def add_file(self, file, build_pipeline):
        self.file_targets.append(sys.intern(file))
        self.build_pipelines.append(build_pipeline)
        
    def get_file_targets(self):
        return self.file_targets
        
    def get_pack_targets(self):
        return self.file_targets
        
    def get_dependencies(self):
        return None # Put in skel, geom, shaders
    
    @staticmethod
    def make_packname(file):
        return os.path.splitext(file)[0]

    @staticmethod
    def get_build_message():
        return translate("Filepacks::3DModels", "Building model files")
    
    def get_build_pipelines(self):
        return self.build_pipelines
    
    def set_build_pipelines(self, build_pipelines):
        self.build_pipelines = build_pipelines
        
    def set_file_targets(self, targets):
        self.file_targets = targets
        
    def set_pack_targets(self, targets):
        pass
        