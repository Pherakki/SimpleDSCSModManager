import os
import shutil

from PyQt5 import QtCore

from src.Utils.Path import splitpath
from src.CoreOperations.PluginLoaders.RulesPluginLoader import get_rule_plugins
from plugins.patchers import BasePatcher, UniversalDataPack


class ScriptDataPack(UniversalDataPack):
    __slots__ = ("source_code", "softcodes", "softcode_lookup")

class ScriptPatcher(BasePatcher):
    __slots__ = ("softcode", "softcode_lookup", "filepack", "paths", "path_prefix", "post_action")
    group = "Script"
    
    rules = get_rule_plugins("Basic", "Script")
    
    def __init__(self, filepack, paths, path_prefix, softcode_lookup, post_action=None):
        self.filepack = filepack
        self.paths = paths
        self.softcode_lookup = softcode_lookup
        self.path_prefix = path_prefix
        self.post_action = post_action
        
    def execute(self):
        cached_file = os.path.join(self.paths.patch_cache_loc, self.path_prefix, self.filepack.get_pack_targets()[0])
        try:
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
                
            os.makedirs(os.path.split(cached_file)[0], exist_ok=True)
            
            # Make rule args
            build_data = ScriptDataPack()
            build_data.target = file_target
            build_data.build_target = cached_file
            build_data.cache_loc = os.path.join(self.paths.patch_cache_loc, self.path_prefix)
            build_data.archives_loc = self.paths.game_resources_loc
            build_data.source_code = source_code
            build_data.softcode_lookup = self.softcode_lookup
            build_data.backups_loc = self.paths.backups_loc
                
            # Now iterate over build steps
            for build_step in pipeline:
                mod_source_file = os.path.join(self.paths.mm_root, build_step.mod, build_step.src)
                
                build_data.source = mod_source_file
                build_data.mod = build_step.mod
                build_data.source_file = build_step.src
                build_data.rule_args = build_step.rule_args
                build_data.softcodes = build_step.softcodes
                
                build_data.source_code = ScriptPatcher.rules[build_step.rule](build_data)
            
            os.makedirs(os.path.split(dst)[0], exist_ok=True)
            with open(dst, 'w') as F:
                F.write(build_data.source_code)
            self.filepack.wipe_pipelines()
            
            # Pack into the pack target
            self.filepack.pack(dst, cached_file)
    
            if self.post_action is not None:
                self.post_action(cached_file, cached_file)
        except Exception as e:
            if os.path.exists(cached_file):
                os.remove(cached_file)
            raise e
