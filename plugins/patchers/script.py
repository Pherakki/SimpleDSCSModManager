import os
import shutil

from PyQt5 import QtCore

from Utils.Path import splitpath
from CoreOperations.PluginLoaders.RulesPluginLoader import get_rule_plugins

rules = get_rule_plugins()

class ScriptPatcher:
    __slots__ = ("softcode_lookup", "filepack", "paths", "path_prefix", "post_action")
    group = "Script"
    
    def __init__(self, filepack, paths, path_prefix, softcode_lookup, post_action=None):
        self.filepack = filepack
        self.paths = paths
        self.softcode_lookup = softcode_lookup
        self.path_prefix = path_prefix
        self.post_action = post_action
        
    def execute(self):
        file_target = self.filepack.get_file_targets()[0]
        
        script_resource = os.path.join(self.paths.base_resources_loc, self.filepack.get_resource_targets()[0])
        dst = os.path.join(self.paths.patch_build_loc, file_target)
        
        pipeline = self.filepack.build_pipeline
        # Load the table to be patched into memory
        if os.path.exists(script_resource):
            with open(script_resource, 'r') as F:
                source_code = F.read()
        else:
            source_code = ""
            
        # Now iterate over build steps
        for build_step in pipeline:
            mod_source_file = os.path.join(self.paths.mm_root, build_step.mod, build_step.src)
            source_code = rules[build_step.rule](source_code, mod_source_file)
        
        os.makedirs(os.path.split(dst)[0], exist_ok=True)
        with open(dst, 'w') as F:
            F.write(source_code)
        self.filepack.wipe_pipelines()
        
        # Pack into the pack target
        cached_file = os.path.join(self.paths.patch_cache_loc, self.path_prefix, self.filepack.get_pack_targets()[0])
        os.makedirs(os.path.split(cached_file)[0], exist_ok=True)
        self.filepack.pack(dst, cached_file)

        if self.post_action is not None:
            self.post_action(cached_file, cached_file)
