import os
import shutil
import struct

from CoreOperations.PluginLoaders.RulesPluginLoader import get_rule_plugins
from plugins.patchers import BasePatcher, UniversalDataPack
from sdmmlib.dscs_model_tools.FileInterfaces.NameInterface import NameInterface
from sdmmlib.dscs_model_tools.FileInterfaces.SkelInterface import SkelInterface
from sdmmlib.dscs_model_tools.FileInterfaces.GeomInterface import GeomInterface
from sdmmlib.dscs_model_tools.FileInterfaces.AnimInterface import AnimInterface
#from sdmmlib.dscs_model_tools.FileInterfaces.PhysInterface import PhysInterface 

class ModelFileDataPack(UniversalDataPack):
    __slots__ = ("softcodes", "softcode_lookup", "data", "bone_indices")
    
    def __init__(self, datapack):
        self.data = None
        for key, value in datapack.items():
            setattr(self, key, value)
        

def name_data_fetcher(datapack, filepath):
    ni = NameInterface.from_file(filepath)
    datapack["bone_indices"] = {name: idx for idx, name in enumerate(ni.bone_names)}
    
interfaces = {"name": NameInterface, "geom": GeomInterface, "skel": SkelInterface, "anim": AnimInterface}
data_fetchers = {"name": name_data_fetcher}    

class ModelPatcher(BasePatcher):
    __slots__ = ("softcode_lookup", "filepack", "paths", "path_prefix", "post_action")
    group = "Model"
    
    rules = get_rule_plugins("Basic", "Model")
    
    def __init__(self, filepack, paths, path_prefix, softcode_lookup, post_action=None):
        self.filepack = filepack
        self.paths = paths
        self.softcode_lookup = softcode_lookup
        self.path_prefix = path_prefix
        self.post_action = post_action
        
    def execute(self):
        build_pipelines = self.filepack.build_pipelines
        targets = self.filepack.pack_targets
        fetched_data = {}
        
        ###########################################
        # Copy the model files from the resources #
        ###########################################
        for ext in ["name", "skel", "geom"]:
            if ext in targets:
                target = targets[ext]
                cached_file = os.path.join(self.paths.patch_cache_loc, self.path_prefix, target)
                resource_file = os.path.join(self.paths.base_resources_loc, target)
                if os.path.exists(resource_file):
                    shutil.copy2(resource_file, cached_file)
                
        if "anim" in targets:
            target = targets["anim"][0]
            cached_file = os.path.join(self.paths.patch_cache_loc, self.path_prefix, target)
            resource_file = os.path.join(self.paths.base_resources_loc, target)
            if os.path.exists(resource_file):
                shutil.copy2(resource_file, cached_file)
        
        ########################
        # Now build everything #
        ########################
        if 'name' in build_pipelines:
            self.build_generic("name", targets["name"], build_pipelines["name"], fetched_data)
            
        for target, build_pipeline in zip(targets.get("anim", []), build_pipelines.get("anim", [])):
            if "skel" in build_pipelines:
                first_step = build_pipelines["skel"][0]
                src = os.path.join(first_step.mod, first_step.src)
                resource_file = os.path.join(self.paths.base_resources_loc, os.path.extsep.join((os.path.splitext(target)[0], "skel")))
                if os.path.splitext(src)[1] == ".skel":
                    use_src = src
                elif os.path.exists(resource_file):
                    use_src = resource_file
                else:
                    raise ValueError(f"Tried to init animations from {src}, but it wasn't a skel file. Include the skel file if you want to mdledit animations.")
                with open(use_src, "rb") as F:
                    F.seek(0x10)
                    num_bones       = struct.unpack('H', F.read(2))[0]
                    F.seek(0x12)
                    num_uv_channels = struct.unpack('H', F.read(2))[0]
            else:
                num_uv_channels = None
                num_bones = None

            isBase = os.path.splitext(os.path.split(use_src)[1])[0] == os.path.splitext(target)[0] if num_bones is not None else False

            self.build_generic("anim", target, build_pipeline, fetched_data, num_uv_channels, num_bones, isBase=isBase)
            
        if 'skel' in build_pipelines:
            self.build_generic("skel", targets["skel"], build_pipelines["skel"], fetched_data)
        if 'geom' in build_pipelines:
            self.build_generic("geom", targets["geom"], build_pipelines["geom"], fetched_data, "PC")
        #if 'phys' in build_pipelines:
        #    self.build_generic("phys", targets["phys"], build_pipelines["phys"], fetched_data)

        self.filepack.build_pipelines = None

    def build_generic(self, ext, target, build_pipelines, fetched_data, *args, **kwargs):
        cached_file = os.path.join(self.paths.patch_cache_loc, self.path_prefix, target)
        try:
            build_data = ModelFileDataPack(fetched_data)
            self.assign_basic_pack_data(build_data, target)
            
            for build_step in build_pipelines:
                self.assign_basic_step_pack_data(build_data, build_step)   
                
                rule = ModelPatcher.rules[build_step.rule]
                self.handle_interface(build_data, getattr(rule, "requires_open_file", False), ext, *args, **kwargs)
                rule(build_data)
    
            # Close the file if it's open
            self.handle_interface(build_data, False, ext, *args, **kwargs)
            if ext in data_fetchers:
                data_fetchers[ext](fetched_data, cached_file)
            if self.post_action is not None:
                self.post_action(cached_file, cached_file)
        except Exception as e:
            if os.path.exists(cached_file):
                os.remove(cached_file)
            raise e
            
    def assign_basic_pack_data(self, build_data, target):
        cached_file = os.path.join(self.paths.patch_cache_loc, self.path_prefix, target)

        build_data.softcode_lookup = self.softcode_lookup
        build_data.target = target
        build_data.build_target = cached_file
        build_data.cache_loc = os.path.join(self.paths.patch_cache_loc, self.path_prefix)
        build_data.archives_loc = self.paths.game_resources_loc
        build_data.backups_loc = self.paths.backups_loc
        
    def assign_basic_step_pack_data(self, build_data, build_step):
        build_data.source = os.path.join(self.paths.mm_root, build_step.mod, build_step.src)
        build_data.mod = build_step.mod
        build_data.source_file = build_step.src
        build_data.rule_args = build_step.rule_args
        build_data.softcodes = build_step.softcodes
    
    def handle_interface(self, build_data, needs_open, ext, *args, **kwargs):
        if build_data.data is None and needs_open:
            build_data.data = interfaces[ext].from_file(build_data.build_target, *args)
        elif not build_data.data is None and not needs_open:
            build_data.data.to_file(build_data.build_target, *args, **kwargs)
            build_data.data = None
        