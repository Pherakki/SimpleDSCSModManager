import json
import os
import shutil

from CoreOperations.PluginLoaders.RulesPluginLoader import get_rule_plugins
from Utils.MBE import mbetable_to_dict, dict_to_mbetable

with open(os.path.join("config", "mberecord_idsizes.json"), 'r') as F:
    id_lengths = json.load(F)

rules = get_rule_plugins()

class MBEPatcher:
    __slots__ = ("softcode_lookup", "filepack", "paths", "path_prefix", "post_action")
    group = "MBE"
    
    # Need to insert the archive_pack, not the post_action...
    def __init__(self, filepack, paths, path_prefix, softcode_lookup, post_action=None):
        self.filepack = filepack
        self.paths = paths
        self.path_prefix = path_prefix
        self.post_action = post_action
        self.softcode_lookup = softcode_lookup
        
    def execute(self):
        file_targets = set(self.filepack.get_file_targets())
        source_tables = set()
        
        # Copy all tables that don't need to be built
        mbe_resource = os.path.join(self.paths.base_resources_loc, self.filepack.get_resource_targets()[0])
        # dst needs to have the archive name inserted
        dst = os.path.join(self.paths.patch_build_loc, self.filepack.get_resource_targets()[0])
        
        os.makedirs(dst, exist_ok=True)
        if os.path.isdir(mbe_resource):
            for file in os.listdir(mbe_resource):
                source_tables.add(os.path.join(self.filepack.get_resource_targets()[0], file))
                if os.path.join(self.filepack.get_resource_targets()[0], file) not in file_targets:
                    table_path = os.path.join(mbe_resource, file)
                    file_dst = os.path.join(dst, file)
                    shutil.copy2(table_path, file_dst)
                
        # Iterate over targets; build each target
        for file_target, pipeline in zip(self.filepack.get_file_targets(), self.filepack.build_pipelines):
            
            id_len = id_lengths.get(file_target.replace(os.sep, "/"), 1)
            # Load the table to be patched into memory
            if file_target in source_tables:
                table_source = os.path.join(self.paths.base_resources_loc, file_target)
                header, working_table = mbetable_to_dict({}, table_source, id_len, None, None)
            else:
                step_1 = pipeline[0]
                table_source = os.path.join(self.paths.mm_root, step_1.mod, step_1.src)
                header, working_table = mbetable_to_dict({}, table_source, id_len, None, None)
                # In case there are any softcodes in the first table...
                working_table = {}
            
            # Now iterate over build steps
            for build_step in pipeline:
                table_source = os.path.join(self.paths.mm_root, build_step.mod, build_step.src)
                rules[build_step.rule](working_table, table_source, id_len, build_step.softcodes, self.softcode_lookup)
                
            abs_filepath = os.path.join(dst, os.path.split(file_target)[1])
            dict_to_mbetable(abs_filepath, header, working_table)
        
        # Pack into the pack target
        cached_file = os.path.join(self.paths.patch_cache_loc, self.path_prefix, self.filepack.get_pack_targets()[0])
        os.makedirs(os.path.split(cached_file)[0], exist_ok=True)
        self.filepack.pack(dst, cached_file)
        self.filepack.set_build_pipelines(None)

        # Do any post actions, such as compressing the file
        if self.post_action is not None:
            self.post_action(cached_file, cached_file)
            
