import json
import os

from CoreOperations.PluginLoaders.RulesPluginLoader import get_rule_plugins
from Utils.MBE import mbetable_to_dict, dict_to_mbetable
from Utils.Settings import default_csv_encoding
from plugins.patchers import BasePatcher, UniversalDataPack

with open(os.path.join("config", "mberecord_idsizes.json"), 'r') as F:
    id_lengths = json.load(F)


class CSVDataPack(UniversalDataPack):
    __slots__ = ("csv_data", "id_len", "softcodes", "softcode_lookup", "encoding", "fill_value")
    

class CSVPatcher(BasePatcher):
    __slots__ = ("softcode_lookup", "filepack", "paths", "path_prefix", "post_action")
    group = "CSV"
    
    rules = get_rule_plugins("Basic", "CSV")
    
    # Need to insert the archive_pack, not the post_action...
    def __init__(self, filepack, paths, path_prefix, softcode_lookup, post_action=None):
        self.filepack = filepack
        self.paths = paths
        self.softcode_lookup = softcode_lookup
        self.path_prefix = path_prefix
        self.post_action = post_action
        
    def execute(self):
        cached_file = os.path.join(self.paths.patch_cache_loc, self.path_prefix, self.filepack.get_pack_targets()[0])
        try:
            # Copy all tables that don't need to be built
            csv_resource = os.path.join(self.paths.base_resources_loc, self.filepack.get_resource_targets()[0])
    
            file_target = self.filepack.get_file_targets()[0]
            pipeline = self.filepack.build_pipeline
            # Load the table to be patched into memory
            if os.path.exists(csv_resource):
                table_source = csv_resource
                id_len = id_lengths.get(os.path.join(self.filepack.get_resource_targets()[0], file_target), 1)
                header, working_table = mbetable_to_dict({}, table_source, id_len, None, None, encoding=default_csv_encoding)
            else:
                step_1 = pipeline[0]
                table_source = os.path.join(self.paths.mm_root, step_1.mod, step_1.src)
                id_len = id_lengths.get(os.path.join(self.filepack.get_resource_targets()[0], file_target), 1)
                header, working_table = mbetable_to_dict({}, table_source, id_len, None, None, encoding=default_csv_encoding)
                # In case there are any softcodes in the first table...
                working_table = {}
            
            os.makedirs(os.path.split(cached_file)[0], exist_ok=True)      
                               
            build_data = CSVDataPack()
            build_data.softcode_lookup = self.softcode_lookup
            build_data.cache_loc = os.path.join(self.paths.patch_cache_loc, self.path_prefix)
            build_data.archives_loc = self.paths.game_resources_loc
            build_data.target = file_target
            build_data.build_target = cached_file
            build_data.backups_loc = self.paths.backups_loc
                
            build_data.csv_data = working_table
            build_data.encoding = default_csv_encoding
            build_data.id_len = id_len
            build_data.fill_value = '0'
                
            # Now iterate over build steps
            id_len = id_lengths.get(file_target, 1)
            for build_step in pipeline:
                table_source = os.path.join(self.paths.mm_root, build_step.mod, build_step.src)
                
                build_data.source = table_source
                build_data.mod = build_step.mod
                build_data.source_file = build_step.src
                build_data.softcodes = build_step.softcodes
                build_data.rule_args = build_step.rule_args
                
                CSVPatcher.rules[build_step.rule](build_data)
            
    
            dict_to_mbetable(cached_file, header, build_data.csv_data, encoding=build_data.encoding)
            
            # Pack into the pack target
            self.filepack.wipe_pipelines()
    
            # Do any post actions, such as compressing the file
            if self.post_action is not None:
                self.post_action(cached_file, cached_file)
        except Exception as e:
            if os.path.exists(cached_file):
                os.remove(cached_file)
            raise e
