import os
import shutil
import sys
import subprocess

from PyQt5 import QtCore

from src.CoreOperations.PluginLoaders.FilePacksPluginLoader import BaseFilepack
from libs.nutcracker import NutCracker
from libs.squirrel import sq

translate = QtCore.QCoreApplication.translate


class Script(BaseFilepack):
    __slots__ = ('file_target', 'pack_target', 'build_pipeline', 'hash')
    filepack = "Script"
    
    def __init__(self, pack_target):
        super().__init__()
        self.file_target = None
        self.build_pipeline = None
        self.pack_target = sys.intern(os.path.splitext(pack_target)[0] + ".nut")
        self.hash = None
        
    def add_file(self, file, build_pipeline):
        self.file_target = sys.intern(file)
        self.build_pipeline = build_pipeline
        
    def get_source_filenames(self):
        return (os.path.splitext(self.file_target)[0] + ".nut",)
    
    def get_resource_targets(self):
        return (self.file_target,)
    
    @staticmethod
    def make_packname(file):
        return file

    @staticmethod
    def unpack(file, working_directory):
        dest_file = os.path.splitext(file)[0] + ".txt"
        NutCracker.decompile(file, dest_file)
        os.remove(file)
    
    @staticmethod
    def pack(script_file, destination_file):
        sq.compile(script_file, destination_file)
        os.remove(script_file)
    
    @staticmethod
    def get_build_message():
        return translate("Filepacks::Scripts", "Building Squirrel source files")
    
    @staticmethod
    def get_extraction_name():
        return translate("Filepacks::Scripts", "scripts")

    def get_build_pipelines(self):
        return (self.build_pipeline,)
    
    def set_build_pipelines(self, build_pipelines):
        self.build_pipeline = build_pipelines[0]
        
    def get_file_targets(self):
        return (self.file_target,)
        
    def get_pack_targets(self):
        return (self.pack_target,)
    
    def set_file_targets(self, targets):
        self.file_target = targets[0]
        
    def set_pack_targets(self, targets):
        self.pack_target = targets[0]
    
    def wipe_pipelines(self):
        self.build_pipeline = None