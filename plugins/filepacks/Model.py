import os
import sys

from PyQt5 import QtCore

from CoreOperations.PluginLoaders.FilePacksPluginLoader import BaseFilepack

translate = QtCore.QCoreApplication.translate


class ModelFilepack(BaseFilepack):
    __slots__ = ('file_targets', 'build_pipelines', 'hash')
    filepack = "Model"
    
    def __init__(self, pack_targets):
        super().__init__()
        self.file_targets = {}
        self.build_pipelines = {}
        self.hash = None
        self.pack_targets = {}
        
               
    def get_source_filenames(self):
        model_filename = None
        for ext in ["name", "skel", "geom"]:
            if ext in self.file_targets:
                model_filename = os.path.splitext(self.file_targets[ext])[0]
                break
        if model_filename is None:
            return tuple()
        else:
            return [os.path.extsep.join((model_filename, ext)) for ext in 
                    ["name", "skel", "geom", "anim"]]
            
        return (self.pack_target,)
    
    def get_resource_targets(self):
        model_filename = None
        for ext in ["name", "skel", "geom"]:
            if ext in self.file_targets:
                model_filename = os.path.splitext(self.file_targets[ext])
                break
        if model_filename is None:
            return tuple()
        else:
            return [os.path.extsep.join((model_filename, ext)) for ext in 
                    ["name", "skel", "geom", "anim"]]
        
    
    def add_file(self, file, build_pipeline):
        extension = os.path.splitext(file)[1].lstrip(os.path.extsep)
        
        if extension == "anim":
            if extension not in self.file_targets:
                self.file_targets[extension] = []
                self.build_pipelines[extension] = []
                self.pack_targets[extension] = []
            self.file_targets[extension].append(sys.intern(file))
            self.build_pipelines[extension].append(build_pipeline)
            self.pack_targets[extension].append(sys.intern(file))
        else:
            self.file_targets[extension] = sys.intern(file)
            self.build_pipelines[extension] = build_pipeline
            self.pack_targets[extension] = sys.intern(file)
            
    
    @staticmethod
    def make_packname(file):
        filename, ext = os.path.splitext(file)
        return filename
    
    @staticmethod
    def get_build_message():
        return translate("Filepacks::3DModels", "Building Model files")
    
    @staticmethod
    def get_extraction_name():
        return translate("Filepacks::3DModels", "Model files")

    def get_build_pipelines(self):
        res = []
        for name, val in self.build_pipelines.items():
            if name == "anim":
                res.extend(val)
            else:
                res.append(val)
        return res
    
    def set_build_pipelines(self, build_pipelines):
        build_pipelines = iter(build_pipelines)
        for name, val in self.build_pipelines.items():
            if name == "anim":
                for i in range(len(val)):
                    val[i] = next(build_pipelines)
            else:
                self.build_pipelines[name] = next(build_pipelines)
        
    def get_file_targets(self):
        res = []
        for name, val in self.file_targets.items():
            if name == "anim":
                res.extend(val)
            else:
                res.append(val)
        return res
        
    def get_pack_targets(self):
        res = []
        for name, val in self.pack_targets.items():
            if name == "anim":
                res.extend(val)
            else:
                res.append(val)
        return res
    
    def set_file_targets(self, targets):
        targets = iter(targets)
        for name, val in self.file_targets.items():
            if name == "anim":
                for i in range(len(val)):
                    val[i] = next(targets)
            else:
                self.file_targets[name] = next(targets)
        
    def set_pack_targets(self, targets):
        targets = iter(targets)
        for name, val in self.pack_targets.items():
            if name == "anim":
                for i in range(len(val)):
                    val[i] = next(targets)
            else:
                self.pack_targets[name] = next(targets)
    
    def wipe_pipelines(self):
        self.build_pipelines = None
        
    @staticmethod
    def get_data_structure(out_struct):
        res = []
        for val in out_struct.values():
            if type(val) == list:
                res.extend(val)
            else:
                res.append(val)
        return res

    @staticmethod        
    def set_data_structure(self, in_struct, out_struct):
        in_struct = iter(in_struct)
        for name, val in out_struct.items():
            if type(val) == list:
                for i in range(len(val)):
                    val[i] = next(in_struct)
            else:
                out_struct[name] = next(in_struct)
