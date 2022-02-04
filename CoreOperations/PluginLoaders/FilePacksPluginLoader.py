import inspect
import os
import sys

from PyQt5 import QtCore

from CoreOperations.PluginLoaders.PluginLoad import load_sorted_plugins_in
from CoreOperations.ModRegistry.Softcoding import search_string_for_softcodes
from Utils.Softcodes import replace_softcodes

translate = QtCore.QCoreApplication.translate

def get_filepack_plugins():
    plugin_dir = os.path.join('plugins', 'filepacks')
    return [*load_sorted_plugins_in(plugin_dir, lambda x: issubclass(x, BaseFilepack) if inspect.isclass(x) else False), UnhandledFilepack]

def get_filepack_plugins_dict():
    return {plugin.packgroup: plugin for plugin in get_filepack_plugins()}

def get_filetype_to_filepack_plugins_map():
    out = {}
    for plugin in get_filepack_plugins():
        out.update({group: plugin for group in plugin.groups})
    return out

    
class BaseFilepack:
    """
    Base class for the basic elements iterated over in the build graph.
    Each "filepack" represents a collection of one or more file targets that 
    must be collected together for some purpose, such as packing or 
    dependencies.
    The individual file targets in the filepack are intended to be patched 
    individually; the collection is used for determining the source files, 
    pack targets, and pack dependencies.
    
    There are five main categories of file referred to by a filepack:
        a) "Pack Targets":       These are the names of the modded asset files 
                                 that are installed to the game assets.
        b) "Source Targets":     These are the names of vanilla game assets
                                 required to *build* the modded assets.
        c) "Dependency Targets": These are the names of vanilla game assets
                                 required to make the modded assets work inside
                                 the game, but not necessary for building.
                                 E.g. Shaders for model files.
        d) "Resource Targets":   The names of unpacked "Source Targets" stored
                                 by the mod manager in its "resources" folder.
        e) "File Targets":       An intermediate step between the "Resource 
                                 Targets" and the "Pack Targets". These are
                                 the files that are directly patched in order
                                 to build the pack targets. For example, the
                                 individual CSV tables of an MBE must be
                                 individually edited before rebuilding them
                                 into the MBE file to be installed.
                                 
    There is usually considerable overlap between these definitions for
    individual filepacks, but many filepacks make distinctions between
    at least some of them.
    """
    
    
    def add_file(self, file, build_pipeline):
        """
        Add a new file target to the pack
        """
        raise NotImplementedError()
        
    def get_source_filenames(self):
        """
        Get the list of game asset files required to build the pack targets
        """
        return tuple()
        
    def get_file_targets(self):
        """
        Get the list of intermediate files that will be edited in order to
        build the pack targets
        """
        raise NotImplementedError()
        
    def get_resource_targets(self):
        """
        Get the list of unpacked game asset files required to build the pack 
        targets
        """
        return tuple()
        
    def get_pack_targets(self):
        """
        Get the list of filenames that will be installed to the game assets
        """
        raise NotImplementedError()
        
    def get_dependencies(self):
        """
        List any files that should be included alongside this one if they are
        not built by any mods
        """
        return tuple()
    
    @staticmethod
    def make_packname(file):
        """
        Given an input file target, figure out what the pack target(s) should be
        """
        raise NotImplementedError()

    @staticmethod
    def unpack(file, working_directory):
        """
        Generates the "file targets" from the "source filenames"
        """
        pass
    
    @staticmethod
    def pack(file, working_directory):
        """
        Generates the "pack targets" from the "file targets"
        """
        pass
    
    @staticmethod
    def get_extraction_name():
        raise NotImplementedError()
        
    @staticmethod
    def get_build_message():
        """
        Used by the BuildGraphExecutor pipeline runners to message the log
        """
        raise NotImplementedError()
        
    def get_build_pipelines(self):
        raise NotImplementedError()
        
    def set_build_pipelines(self, obj):
        raise NotImplementedError()
        

    def link_softcodes(self, softcodes):
        new_targets = []
        new_pipes = []
        for file_target, build_pipeline in zip(self.get_file_targets(), self.get_build_pipelines()):
            if 'softcodes' in build_pipeline:
                file_codes = {}
                for cat in build_pipeline['softcodes']:
                    for key in build_pipeline['softcodes'][cat]:
                        file_codes[(cat, key)] = build_pipeline['softcodes'][cat][key]
                file_target = replace_softcodes(file_target.encode('utf8'), file_codes, softcodes).decode('utf8')
            new_targets.append(sys.intern(file_target))
            new_pipes.append(build_pipeline["build_steps"])
        
        new_pack_targets = []
        for pack_target in self.get_pack_targets():
            pack_softcodes = {}
            for match in search_string_for_softcodes(pack_target):
                code_cat, code_key = match.groups((1, 2))
                code_cat = code_cat
                code_key = code_key
                code_offset = match.start() - 1
                code_catkey = (code_cat, code_key)
                if code_catkey not in pack_softcodes:
                    pack_softcodes[code_catkey] = []
                pack_softcodes[code_catkey].append(code_offset)
            pack_target = replace_softcodes(pack_target.encode('utf8'), pack_softcodes, softcodes).decode('utf8')
            new_pack_targets.append(sys.intern(pack_target))
        
        self.set_file_targets(new_targets)
        self.set_build_pipelines(new_pipes)
        self.set_pack_targets(new_pack_targets)

class UnhandledFilepack(BaseFilepack):
    __slots__ = ('target', 'pack_target', 'build_pipeline', "hash")
    packgroup = "Uncategorised"
    groups = ("other",)
    
    def __init__(self, pack_name):
        super().__init__()
        self.target = None
        self.build_pipeline = None
        self.pack_target = sys.intern(pack_name)
        self.hash = None
        
    def add_file(self, file, build_pipeline):
        self.target = sys.intern(file)
        self.build_pipeline = build_pipeline
        
    @staticmethod
    def make_packname(file):
        return file
    
    @staticmethod
    def get_build_message():
        return translate("Filepacks::Unhandled", "Building miscellaneous files")
    
    def get_build_pipelines(self):
        return (self.build_pipeline,)
    
    def set_build_pipelines(self, build_pipelines):
        self.build_pipeline = build_pipelines[0]
        
    def get_file_targets(self):
        return (self.target,)
    
    def set_file_targets(self, targets):
        self.target = targets[0]
        
    def get_pack_targets(self):
        return (self.pack_target,)
    
    def set_pack_targets(self, targets):
        self.pack_target = targets[0]
        
    def wipe_pipelines(self):
        self.build_pipeline = None