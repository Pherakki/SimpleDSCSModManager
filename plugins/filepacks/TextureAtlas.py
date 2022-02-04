import sys

from PyQt5 import QtCore

from CoreOperations.PluginLoaders.FilePacksPluginLoader import BaseFilepack

translate = QtCore.QCoreApplication.translate

class TextureAtlasFilepack(BaseFilepack):
    __slots__ = ('file_target', 'build_pipeline', 'hash')
    packgroup = "TextureAtlas"
    groups = ("texture_atlas",)
    
    def __init__(self, pack_target):
        super().__init__()
        self.file_target = None
        self.build_pipeline = None
        self.hash = None
        
    def add_file(self, file, build_pipeline):
        self.file_target = sys.intern(file)
        self.build_pipeline = build_pipeline
        
    def get_source_filenames(self):
        return tuple() # Will be the icon
    
    def get_dependencies(self):
        return None # Put in skel, geom, shaders
    
    @staticmethod
    def make_packname(file):
        return file

    @staticmethod
    def get_extraction_name():
        return translate("Filepacks::TextureAtlas", "texture atlases")
    
    @staticmethod
    def get_build_message():
        return translate("Filepacks::TextureAtlas", "Extending texture atlases")
    
    def get_build_pipelines(self):
        return (self.build_pipeline,)
    
    def set_build_pipelines(self, build_pipelines):
        self.build_pipeline = build_pipelines[0]
    
    def wipe_pipelines(self):
        self.build_pipeline = None
        
    def get_file_targets(self):
        return self.file_target
        
    def get_pack_targets(self):
        return self.file_target
        
    def set_file_targets(self, targets):
        self.file_target = targets[0]
        
    def set_pack_targets(self, targets):
        pass
        
    # Need something here to iterate over which files use the atlas?