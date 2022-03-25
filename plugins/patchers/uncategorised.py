import os
from CoreOperations.PluginLoaders.RulesPluginLoader import get_rule_plugins
from plugins.patchers import BasePatcher, UniversalDataPack



class UncategorisedPatcher(BasePatcher):
    __slots__ = ("softcode_lookup", "filepack", "paths", "path_prefix", "post_action")
    group = "Uncategorised"
    
    rules = get_rule_plugins("Basic")
    
    def __init__(self, filepack, paths, path_prefix, softcode_lookup, post_action=None):
        self.filepack = filepack
        self.paths = paths
        self.softcode_lookup = softcode_lookup
        self.path_prefix = path_prefix
        self.post_action = post_action
        
    def execute(self):
        target = self.filepack.get_pack_targets()[0]
        cached_file = os.path.join(self.paths.patch_cache_loc, self.path_prefix, target)
        try:
            build_pipeline = self.filepack.build_pipeline
            
            
            os.makedirs(os.path.split(cached_file)[0], exist_ok=True)
            
            build_data = UniversalDataPack()
            build_data.target = target
            build_data.build_target = cached_file
            build_data.cache_loc = os.path.join(self.paths.patch_cache_loc, self.path_prefix)
            build_data.archives_loc = self.paths.game_resources_loc
            build_data.backups_loc = self.paths.backups_loc
            
            for build_step in build_pipeline:
                build_data.source = os.path.join(self.paths.mm_root, build_step.mod, build_step.src)
                build_data.mod = build_step.mod
                build_data.source_file = build_step.src
                build_data.rule_args = build_step.rule_args
                
                self.rules[build_step.rule](build_data)
            self.filepack.wipe_pipelines()
            
            if self.post_action is not None:
                self.post_action(cached_file, cached_file)
        except Exception as e:
            if os.path.exists(cached_file):
                os.remove(cached_file)
            raise e