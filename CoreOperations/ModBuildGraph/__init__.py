import array
import json
import os
import sys

from PyQt5 import QtCore

from CoreOperations.ModBuildGraph.graphHash import hashFilepack
from CoreOperations.PluginLoaders.FiletypesPluginLoader import get_filetype_plugins
from CoreOperations.PluginLoaders.ArchivesPluginLoader import get_archivetype_plugins_dict
from CoreOperations.PluginLoaders.FilePacksPluginLoader import get_filepack_plugins, get_filetype_to_filepack_plugins_map
from Utils.Path import calc_has_dir_changed_info


translate = QtCore.QCoreApplication.translate

class BuildStep:
    __slots__ = ('mod', 'src', 'rule', 'rule_args', 'softcodes')
    
    def __init__(self, mod, src, rule, softcodes, *rule_args):
        self.mod = mod
        self.src = src
        self.rule = rule
        self.rule_args = rule_args
        self.softcodes = softcodes
        
def make_interned_buildstep(dct):
    if 'mod' in dct:
        softcodes = dct.get('softcodes', {})
        return BuildStep(sys.intern(dct['mod']),
                         sys.intern(dct['src']),
                         sys.intern(dct['rule']),
                         {
                             sys.intern(match): tuple(offsets)
                             for match, offsets in softcodes.items()
                         } if len(softcodes) else None,
                         *dct.get('rule_args', []))
    else:
        return dct

def get_interned_mod_index(path):
    with open(os.path.join(path, "INDEX.json"), 'r') as F:
        return json.load(F, object_hook=make_interned_buildstep)

    
    
def categorise_build_targets(build_graphs, ops, log, updateLog):
    filetypes = get_targettable_filetypes()
    filepacks = get_filepack_plugins_dict()
    rules = get_rule_plugins()

    log(translate("BuildGraph", "Categorising install graph pipelines..."))

    total_pipes = 0
    for archive_type in build_graphs:
        for archive in build_graphs[archive_type]:
            total_pipes += len(build_graphs[archive_type][archive].build_graph)
            
    total = 0
    for archive_type in build_graphs:
        for archive in build_graphs[archive_type]:
            archive_build_graph = build_graphs[archive_type][archive].build_graph
            retval = {filepack: {} for filepack in filepacks}
            
            # Collect file targets into filepacks
            for target in list(archive_build_graph.keys()):
                total += 1
                group = 'Uncategorised'
                for filetype in filetypes:
                    if filetype.checkIfMatch(*os.path.split(target)):
                        group = filetype.filepack
                        break
                    
                # Remove any build steps that require pre-existing data that
                # doesn't exist
                archive_build_graph[target]["build_steps"] = trim_dead_nodes(archive_build_graph[target]["build_steps"], rules)
                # If that means no build steps are left, don't build that target
                if not len(archive_build_graph[target]["build_steps"]):
                    continue
            
                pack = filepacks[group]
                packgroup = pack.filepack
                filepack_name = sys.intern(pack.make_packname(target))
                
                if filepack_name not in retval[packgroup]:
                    retval[packgroup][filepack_name] = pack(filepack_name)
                retval[packgroup][filepack_name].add_file(target, archive_build_graph.pop(target))
            # Cull any unused plugin types; hash pipes
            for packgroup in list(retval.keys()):
                if not len(retval[packgroup]):
                    del retval[packgroup]
                # else:
                #     for pack in retval[packgroup].values():
                #         pack.hash = hashFilepack(ops.paths.mm_root, pack)
                        
            # Replace build graph with filepack version
            build_graphs[archive_type][archive].build_graph = retval
    updateLog(translate("BuildGraph", "Categorising install graph pipelines... Done. ") + f"[{total}/{total_pipes}]")
    return build_graphs


class ModBuildGraphCreator:
    def __init__(self, ops):
        self.ops = ops
        
    def regenerate_missing_mod_indices(self, active_mods, log, updateLog):
        missing_mods = []
        for i, mod in enumerate(active_mods):
            modpath = mod.path
            if not os.path.exists(os.path.join(modpath, "INDEX.json")):
                missing_mods.append(mod)
        
        n_missing_mods = len(missing_mods)
        if n_missing_mods:
            log(translate("BuildGraph::Debug", "---mod index message slot---"))
        else:
            log(translate("BuildGraph", "Located all mod indices."))
        for i, mod in enumerate(missing_mods):
            modpath = mod.path
            updateLog(translate("BuildGraph", "Creating missing mod indices... ") + f"[{i+1}/{n_missing_mods}] [{mod.name}]")
            self.ops.mod_registry.save_index(modpath, self.ops.mod_registry.index_mod(modpath))
        if n_missing_mods:
            updateLog(translate("BuildGraph", "Creating missing mod indices... Done. ") + f"[{i+1}/{n_missing_mods}]")
            
    def regenerate_index_if_out_of_date(self, index, path, updateLog, msg):

        if latest_edit_time != index["last_edit_time"]:
        latest_edit_time, contents_hash = calc_has_dir_changed_info(os.path.relpath(os.path.join(path, "modfiles")))
            updateLog(translate("BuildGraph", "{msg} [Regenerating index...]").format(msg=msg))
            self.ops.mod_registry.save_index(path, self.ops.mod_registry.index_mod(path))
            return get_interned_mod_index(path)
        else:
            return index
            
    def create_build_graph(self, active_mods, log, updateLog):
        archive_type_classes = get_archivetype_plugins_dict()
        self.regenerate_missing_mod_indices(active_mods, log, updateLog)
        build_graphs = {}
        mod_softcodes = []
        log(translate("BuildGraph::Debug", "---build graph message slot---"))
        n = len(active_mods)
        for i, mod in enumerate(active_mods):
            # Get the index
            index = get_interned_mod_index(mod.path)
            msg = translate("BuildGraph", "Building install graph nodes... ") + f"[{i+1}/{n}] [{mod.name}]"
            index = self.regenerate_index_if_out_of_date(index, mod.path, updateLog, msg)
            updateLog(msg)
            
            # Handle contents data
            index_data = index["data"]
            for archive_type in index_data:
                if archive_type not in build_graphs:
                    build_graphs[archive_type] = {}
                archive_type_build_graph = build_graphs[archive_type]
                archive_type_cls = archive_type_classes[archive_type]
                for archive in index_data[archive_type]:
                    if archive not in archive_type_build_graph:
                        archive_type_build_graph[archive] = archive_type_cls(archive, self.ops)
                        
                    archive_build_graph = archive_type_build_graph[archive].build_graph
                    for target, target_data in index_data[archive_type][archive].items():
                        build_steps = target_data["build_steps"]
                        sys.intern(target)
                        if target not in archive_build_graph:
                            archive_build_graph[target] = {'build_steps': []}
                            if 'softcodes' in target_data:
                                archive_build_graph[target]['softcodes'] = target_data['softcodes']
    
                        archive_build_graph[target]['build_steps'].extend(build_steps)
            
            # Handle softcodes
            softcode_data = index["softcodes"]
            # for category, keys in softcode_data.items():
            #     if category not in mod_softcodes:
            #         mod_softcodes[category] = []
            mod_softcodes.extend(softcode_data)
                
        updateLog(translate("BuildGraph", "Building install graph nodes... Done. ") + f"[{i+1}/{n}]")
        return categorise_build_targets(build_graphs, self.ops, log, updateLog), mod_softcodes
