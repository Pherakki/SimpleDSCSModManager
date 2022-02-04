import inspect
import os

from CoreOperations.PluginLoaders.PluginLoad import load_sorted_plugins_in
from CoreOperations.PluginLoaders.RulesPluginLoader import get_rule_plugins

rules = get_rule_plugins()

def get_patcher_plugins():
    plugin_dir = os.path.join('plugins', 'patchers')
    
    return [patcher for patcher in [*load_sorted_plugins_in(plugin_dir, inspect.isclass), UncategorisedPatcher]]


def get_patcher_plugins_dict():
    return {patcher.group: patcher for patcher in get_patcher_plugins()}

class UncategorisedPatcher:
    __slots__ = ("softcode_lookup", "filepack", "paths", "path_prefix", "post_action")
    group = "Uncategorised"
    
    def __init__(self, filepack, paths, path_prefix, softcode_lookup, post_action=None):
        self.filepack = filepack
        self.paths = paths
        self.softcode_lookup = softcode_lookup
        self.path_prefix = path_prefix
        self.post_action = post_action
        
    def execute(self):
        build_pipeline = self.filepack.build_pipeline
        
        cached_file = os.path.join(self.paths.patch_cache_loc, self.path_prefix, self.filepack.get_pack_targets()[0])
        os.makedirs(os.path.split(cached_file)[0], exist_ok=True)
        for build_step in build_pipeline:
            mod_source_file = os.path.join(self.paths.mm_root, build_step.mod, build_step.src)
            rules[build_step.rule](mod_source_file, cached_file)
        self.filepack.wipe_pipelines()
        
        if self.post_action is not None:
            self.post_action(cached_file, cached_file)