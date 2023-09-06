import os
import sys
import shutil

from PyQt5 import QtCore

from src.CoreOperations.ModBuildGraph import ModBuildGraphCreator
from src.CoreOperations.ModBuildGraph.graphHash import hashFilepack
from src.CoreOperations.ModInstallation.PipelineRunners import ArchivePipelineCollection
from src.CoreOperations.ModInstallation.VariableParser import parse_mod_variables, scan_variables_for_softcodes
from src.CoreOperations.PluginLoaders.FilePacksPluginLoader import get_filepack_plugins_dict
from src.Utils.JSONHandler import JSONHandler
from src.Utils.MBE import mbetable_to_dict, dict_to_mbetable
from libs.dscstools import DSCSTools

translate = QtCore.QCoreApplication.translate


def generate_step_message(cur_items, cur_total):
    return translate("ModInstall", "[Step {ratio}]").format(ratio=f"{cur_items}/{cur_total}")


def generate_prefixed_message(cur_items, cur_total, msg):
    return f">> {generate_step_message(cur_items, cur_total)} {msg}"


def format_exception(exception):
    return type(exception)(f"Error on line {sys.exc_info()[-1].tb_lineno} in file {__file__}:" + f" {exception}")


class BuildGraphRunner(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    # clean_up = QtCore.pyqtSignal()
    sendBuildGraphs = QtCore.pyqtSignal(dict)
    sendSoftcodes = QtCore.pyqtSignal(dict)
    raise_exception = QtCore.pyqtSignal(Exception)
    early_exit = QtCore.pyqtSignal()
    
    def __init__(self, ops, parent=None):
        super().__init__(None)
        self.ops = ops
        # self.finished.connect(lambda : self.clean_up.emit)
        # self.raise_exception.connect(lambda : self.clean_up.emit)
        self.substep = 0
        self.nsteps = 4
        
    def set_message_info(self, msg):
        self.pre_message = msg
        
    def init_signals(self, ui):
        self.log.connect(ui.log)
        self.updateLog.connect(ui.updateLog)
        
    @QtCore.pyqtSlot()
    def execute(self):
        try:
            # Get all mods to be installed
            active_mods = self.ops.profile_manager.get_active_mods()
            if not len(active_mods):
                self.log.emit(translate("ModInstall", "No mods selected, nothing to install. Use \'Restore Backups\' if you want to remove all mods."))
                self.early_exit.emit()
                return
            self.log.emit(translate("ModInstall", "Installing {count} mods...").format(count=len(active_mods)))
            for mod in active_mods:
                self.log.emit(f"> {mod.name}")
            self.log.emit(translate("ModInstall", "{curr_step_message} Generating build graph...").format(curr_step_message=self.pre_message))
            
            # Make the build pipeline for each file to be built across
            # all mods, also pull out all softcodes mentioned in the mods
            mod_build_graph_creator = ModBuildGraphCreator(self.ops)
            build_graphs, softcodes = mod_build_graph_creator.create_build_graph(active_mods, 
                                                                                 self.sendLog, 
                                                                                 self.sendUpdateLog)

            # Get the values of all softcodes mentioned in the mods to be installed
            softcode_lookup = {}
            self.ops.softcode_manager.load_softcode_data()
            # Get all hardcoded values that softcodes need to consider in the build graph, 
            # see if any conflict with cached softcodes
            self.get_blocking_hardcodes(build_graphs)
            
            # Evaluate all softcodes that should not have their evaluations
            # delayed
            varlist_calls = []
            variables_softcodes = []
            for mod in active_mods:
                variables_softcodes.append(scan_variables_for_softcodes(mod.path, self.ops.softcode_manager))
            for match in softcodes:
                for delay_item in ["VarLists"]:
                    if match.startswith(delay_item):
                        varlist_calls.append(match)
                    else:
                        softcode_lookup[match] = self.ops.softcode_manager.lookup_softcode(match)
            for mod_codes in variables_softcodes:
                for match in mod_codes: 
                    for delay_item in ["VarLists"]:
                        if match.startswith(delay_item):
                            varlist_calls.append(match)
                        else:
                            softcode_lookup[match] = self.ops.softcode_manager.lookup_softcode(match)
                        
                
            # Now put in the Variables
            for mod, mod_codes in zip(active_mods, variables_softcodes):
                parse_mod_variables(mod.path, self.ops.softcode_manager, softcode_lookup, mod_codes)

            # Execute the delayed VarList evaluations
            for match in varlist_calls:
                softcode_lookup[match] = self.ops.softcode_manager.lookup_softcode(match)
            # Now cull the graph depending on the hash of each pack target,
            # which requests are required, etc.
            self.process_graph(build_graphs, softcode_lookup)
            
            
            # Forward the culled graph and required softcodes to the next
            # stage in the install process
            self.sendBuildGraphs.emit(build_graphs)
            self.sendSoftcodes.emit(softcode_lookup)
            # Save any newly-generated softcode values to the cache
            self.ops.softcode_manager.dump_codes_to_json()
            self.ops.softcode_manager.unload_softcode_data()
            self.finished.emit()
        except Exception as e:
            self.raise_exception.emit(e)

    def get_blocking_hardcodes(self, build_graphs):
        pass
        # path = os.path.join("data", "shop_para.mbe", "shop.csv")
        
        # # Need to figure out how to find this path
        # pack_for_path = build_graphs["MDB1"]["DSDBP"].build_graph["MBE"][os.path.join("data", "shop_para.mbe")]
        
        # idx = pack_for_path.get_file_targets().index(path)
        # build_pipeline = pack_for_path.get_build_pipelines()[idx]["build_steps"]
        
        # # Here, need to get the values out of the file
        
        # for buildstep in build_pipeline:
        #     print(buildstep.src)
        
        # assert 0

    def process_graph(self, build_graphs, softcode_lookup):
        self.sendLog(translate("ModInstall", "Looking for cached mod files..."))
        
        # Create the cache index if it doesn't exist
        if not os.path.exists(self.ops.paths.patch_cache_index_loc):
            with open(self.ops.paths.patch_cache_index_loc, 'w') as F:
                F.write("{}")
                
        # Create the cache folder if it doesn't exist
        os.makedirs(self.ops.paths.patch_cache_loc, exist_ok=True)
        with JSONHandler(self.ops.paths.patch_cache_index_loc, f"Error reading '{self.ops.paths.patch_cache_index_loc}") as stream:
            cache_index = stream
            
        # Now prepare the process the build graph
        # Init some variables to count the number of packs in the build graph,
        # and the count how many are found in the cache
        n_found = 0
        n_total = 0
        # First just loop over the archive categories and archives...
        for archive_type, archives in list(build_graphs.items()):
            for archive, archive_obj in list(archives.items()):
                # Now we can actually inspect the filepacks we want to install...
                build_pipelines = archive_obj.build_graph
                for pack_type, packs in list(build_pipelines.items()):
                    ######################################
                    # Process each pack's build pipeline #
                    ######################################
                    
                    # 1. Start by iterating over each pack in each pack category
                    for pack_name, pack in list(packs.items()):
                        ###########################################
                        # Bake the softcode values into the packs #
                        ###########################################
                        # 1. This replaces filenames and data softcodes with values
                        pack.bake_softcodes(softcode_lookup)
                        
                        #################################
                        # Check is pack is in the cache #
                        #################################
                        # 1. Make a hash of the filepack
                        pack.hash = hashFilepack(self.ops.paths.mm_root, pack, softcode_lookup)
                        pack_is_in_cache = True
                        pack_targets = pack.get_pack_targets()
                        n_total += len(pack_targets)
                        
                        # 2. Check if each source file of the filepack is
                        # in the cache
                        for pack_target in pack_targets:
                            archive_pack_target = os.path.join(archive_obj.get_prefix(), pack_target)
                            if cache_index.get(archive_pack_target) != pack.hash or not os.path.isfile(os.path.join(self.ops.paths.patch_cache_loc, archive_pack_target)):
                                pack_is_in_cache = False
                                break
                            n_found += 1
                            
                        # 3. Cull the pack if all pack targets are in the cache
                        if pack_is_in_cache:
                            for pack_target in pack_targets:
                                archive_obj.cached_pack_targets.append(pack_target)
                            del packs[pack_name]
                            
                    # 2. Cull any groups with no packs
                    if not len(build_pipelines[pack_type]):
                        del build_pipelines[pack_type]
        self.sendUpdateLog(translate("ModInstall", "Looking for cached mod files... found {ratio} in cache.").format(ratio=f"[{n_found}/{n_total}]"))
       
       
    @QtCore.pyqtSlot(str) 
    def sendLog(self, msg):
        self.substep +=1
        self.log.emit(generate_prefixed_message(self.substep, self.nsteps, msg))
       
    @QtCore.pyqtSlot(str) 
    def sendUpdateLog(self, msg):
        self.updateLog.emit(generate_prefixed_message(self.substep, self.nsteps, msg))


class ResourceBootstrapper(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    clean_up = QtCore.pyqtSignal()
    raise_exception = QtCore.pyqtSignal(Exception)
    
    def __init__(self, threadpool, ops, parent=None):
        super().__init__(parent)
        self.threadpool = threadpool
        self.ops = ops
        self.build_graphs = None
        self.pre_message = None
        self.finished.connect(lambda : self.clean_up.emit)
        self.raise_exception.connect(lambda : self.clean_up.emit)
        
    def set_message_info(self, msg):
        self.pre_message = msg
        
    def init_signals(self, ui):
        self.log.connect(ui.log)
        self.updateLog.connect(ui.updateLog)
        
    @QtCore.pyqtSlot(dict)
    def receiveBuildGraphs(self, build_graphs):
        self.build_graphs = build_graphs
        
    @QtCore.pyqtSlot()
    def execute(self):
        try:
            self.log.emit(translate("ModInstall", "{curr_step_msg} Checking required resources...").format(curr_step_msg=self.pre_message))
            
            with JSONHandler(os.path.join(self.ops.paths.config_loc, "filelist.json"), "Error reading 'filelist.json'") as stream:
                resource_archives = stream
            
            required_resources = {}
            for archive_type, archives in self.build_graphs.items():
                for archive, archive_obj in archives.items():
                    archive_pipes = archive_obj.build_graph
                    for filepack_name, filepack_pipes in archive_pipes.items():
                        if filepack_name not in required_resources:
                            required_resources[filepack_name] = set()
                            
                        for filepack in filepack_pipes.values():
                            # First check if the requested resource already exists
                            # Remember, the file targets are a (resource, build_pipes) pair
                            filepack_targets = filepack.get_file_targets()
                            do_extract = any([not os.path.exists(os.path.join(self.ops.paths.base_resources_loc, target)) for target in filepack_targets])
                            
                            # Potential for a bug here with MBEs if one of the csvs is stupidly deleted from the resources...
                            if do_extract:
                                for target in filepack.get_source_filenames():
                                        required_resources[filepack_name].add(target)
            required_resources = {nm: list(val) for nm, val in required_resources.items()}
            filepacks = get_filepack_plugins_dict()
            
            file_extractors = []
            for filepack_name, resources in required_resources.items():
                filepack = filepacks[filepack_name]
                files_to_extract = []
                for resource in resources:
                    archive_to_pull_from = resource_archives.get(resource)
                    if archive_to_pull_from is not None:
                        files_to_extract.append((archive_to_pull_from, resource))
                if not len(files_to_extract):
                    continue
                fe = self.ops.dscstools.generateFilelistExtractor(self.threadpool, self.ops, files_to_extract, filepack=filepack, parent=self)
                fe.log.connect(self.log.emit)
                fe.updateLog.connect(self.updateLog.emit)
                file_extractors.append(fe)

            if len(file_extractors):
                self.updateLog.emit(translate("ModInstall", "{curr_step_message} Checking required resources... found missing resources.").format(curr_step_message=self.pre_message))
                for i, (fe, next_fe) in enumerate(zip(file_extractors, file_extractors[1:])):
                    fe.setLogInfo(i+1, len(file_extractors), 1)
                    fe.finished.connect(next_fe.execute)
                    fe.raise_exception.connect(self.raise_exception.emit)
                file_extractors[-1].finished.connect(self.finished.emit)
                file_extractors[-1].raise_exception.connect(self.raise_exception.emit)
                file_extractors[-1].setLogInfo(len(file_extractors), len(file_extractors), 1)
                file_extractors[0].execute()
            else:
                self.updateLog.emit(translate("ModInstall", "{curr_step_message} Checking required resources... no additional resources required.").format(curr_step_message=self.pre_message))
                self.finished.emit()
        except Exception as e:
            self.raise_exception.emit(e)
    
    
class BuildGraphExecutor(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    clean_up = QtCore.pyqtSignal()
    raise_exception = QtCore.pyqtSignal(Exception)
    
    def __init__(self, threadpool, ui, ops, parent=None):
        super().__init__(parent)
        self.threadpool = threadpool
        self.ui = ui
        self.ops = ops
        self.build_graphs = None
        self.softcodes = None
        self.cache_index = None
        self.pre_message = None
        self.finished.connect(self.clean_up.emit)
        self.raise_exception.connect(self.clean_up.emit)
    
    def set_message_info(self, msg):
        self.pre_message = msg
        
    @QtCore.pyqtSlot(dict)
    def receiveBuildGraphs(self, build_graphs):
        self.build_graphs = build_graphs
        
    @QtCore.pyqtSlot(dict)
    def receiveSoftcodes(self, softcodes):
        self.softcodes = softcodes
        
    @QtCore.pyqtSlot()
    def execute(self):
        try:
            self.ui.log(translate("ModInstall", "{curr_step_message} Creating modded assets...").format(curr_step_message=self.pre_message))

            archive_pipes = []
            for archive_type, archives in self.build_graphs.items():
                for archive_name, archive in archives.items():
                    # Make the cache location
                    os.makedirs(os.path.join(self.ops.paths.patch_cache_loc, archive_name), exist_ok=True)
                    if not len(archive.build_graph):
                        continue
                    # Softcodes get baked in here!
                    apcol = ArchivePipelineCollection(self.threadpool, self.ops, self.ui, archive, self.softcodes, parent=self)
                    apcol.log.connect(self.ui.log)
                    apcol.updateLog.connect(self.ui.updateLog)
                    apcol.raise_exception.connect(self.raise_exception)
                    archive_pipes.append(apcol)
                    
            n_pipes = len(archive_pipes)
            # Link the archive builders up to each other
            for i, (archive_pipe, next_archive_pipe) in enumerate(zip(archive_pipes, archive_pipes[1:])):
                def make_link(actor):
                    return lambda : actor.execute()
                archive_pipe.setLogInfo(i+1, n_pipes, 1)
                archive_pipe.finished.connect(make_link(next_archive_pipe))
                
            # Finalise and execute
            if len(archive_pipes):
                archive_pipes[-1].setLogInfo(n_pipes, n_pipes, 1)
                archive_pipes[-1].finished.connect(self.finished.emit)
                archive_pipes[0].execute()
            else:
                self.ui.updateLog(translate("ModInstall", "{curr_step_message} Creating modded assets... no files to build.").format(curr_step_message=self.pre_message))
                self.finished.emit()
        except Exception as e:
            self.raise_exception.emit(e)


# 1) Skip sort if data isn't in the build graph
# 2) Enumerate the sorts
# 3) Make it work for all MDB1 archives
# 4) Unify some sorters?
# 5) Do Item order, Digimon Market order
class DataSorter(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    raise_exception = QtCore.pyqtSignal(Exception)
    
    def __init__(self, ops, parent=None):
        super().__init__()
        self.ops = ops
        self.pre_message = None
        self.max_steps = 5
        
    def set_message_info(self, msg):
        self.pre_message = msg
        
    def init_signals(self, ui):
        self.log.connect(ui.log)
        self.updateLog.connect(ui.updateLog)
        
    @QtCore.pyqtSlot()
    def execute(self):
        self.log.emit(translate("ModInstall", "{curr_step_message} Sorting Game Database...").format(curr_step_message=self.pre_message))
        self.sort_field_guide(1)
        self.sort_voicelines(2)
        self.sort_items(4)
        self.sort_digimarket(5)
        self.finished.emit()
    
    def safe_remove_mbe(self, local_path):
        path = os.path.join(self.ops.paths.patch_build_loc, *local_path)
        if not os.path.exists(path):
            return
        stem, ext = os.path.splitext(path)
        if ext != ".mbe":
            self.raise_exception.emit(ValueError("Attempted to clean up MBE '{path}', but it was not an MBE".format(path=path)))
        files = os.listdir(path)
        if not all(os.path.splitext(f)[1] == ".csv" for f in files):
            self.raise_exception.emit(ValueError("Attempted to clean up MBE '{path}', but it did not only contain CSVs".format(path=path)))
        shutil.rmtree(path)
        
    
    ########################
    # FIELD GUIDE SORTING
    ########################
    def sort_field_guide(self, step_no):
        try:
            self.log.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Field Guide...").format(step_no=step_no, max_steps=self.max_steps))
            cache_loc = self.ops.paths.patch_cache_loc
            if os.path.exists(cache_table := os.path.join(cache_loc, "DSDBP", "data", "digimon_common_para.mbe")): 
                # Get the required data
                digimon_para_path = ["data", "digimon_common_para.mbe"]
                charname_path = ["text", "charname.mbe"]
                hdr, build_common_para_digimon = self.get_resource_table("DSDBP", digimon_para_path, "digimon.csv")
                _, build_charname = self.get_resource_table("DSDB", charname_path, "Sheet1.csv")

                # Now do the sorting
                to_sort = []
                for key, val in build_common_para_digimon.items():
                    if val[20] != '0':
                        to_sort.append(key)
                        
                to_sort = sorted(to_sort, key=lambda x: self.sortmode_compress_keygen(x, 
                                                                                      build_common_para_digimon,
                                                                                      build_charname))
                
                for i, key in enumerate(to_sort):
                    # Index 20 is the field guide ID
                    build_common_para_digimon[key][20] = i+1
   
                    
                # Save back to the cache
                build_table = os.path.join(self.ops.paths.patch_build_loc, "data", "digimon_common_para.mbe")
                dict_to_mbetable(os.path.join(build_table, "digimon.csv"), hdr, build_common_para_digimon)
                os.remove(cache_table)
                
                mbe_filepack = get_filepack_plugins_dict()["MBE"]
                cache_table_decomp = cache_table + ".decomp"
                mbe_filepack.pack(build_table, cache_table_decomp)
                DSCSTools.dobozCompress(cache_table_decomp, cache_table)
                os.remove(cache_table_decomp)
                self.safe_remove_mbe(digimon_para_path)
                self.safe_remove_mbe(charname_path)
                self.updateLog.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Field Guide... sort complete.").format(curr_step_message=self.pre_message, step_no=step_no, max_steps=self.max_steps))
            else:
                self.updateLog.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Field Guide... no edits required.").format(curr_step_message=self.pre_message, step_no=step_no, max_steps=self.max_steps))
        except Exception as e:
            self.raise_exception.emit(e)
            
    def get_resource_table(self, archive, table_path, subtable):
        mbe_filepack = get_filepack_plugins_dict()["MBE"]
            
        cache_loc = self.ops.paths.patch_cache_loc
        build_loc = self.ops.paths.patch_build_loc
        resource_loc = self.ops.paths.base_resources_loc
        working_loc = os.path.join(build_loc, "working")
        os.makedirs(working_loc, exist_ok=True)
        
            
        build_file = os.path.join(build_loc, *table_path)
        if os.path.exists(cached_file := os.path.join(cache_loc, "DSDBP", *table_path)):
            DSCSTools.dobozDecompress(cached_file, build_file)
            mbe_filepack.unpack(build_file, working_loc)
        elif os.path.exists(resource_file := os.path.join(resource_loc, *table_path)):
            shutil.copytree(resource_file, build_file)
        else:
            DSCSTools.extractMDB1File(os.path.join(self.ops.paths.game_resources_loc, f"{archive}.steam.mvgl"), build_loc, "/".join(table_path))
            mbe_filepack.unpack(build_file, working_loc)
        
        os.rmdir(working_loc)
        
        build_subtable = os.path.join(build_file, subtable)
        return mbetable_to_dict({}, build_subtable, 1, None, None)
    
    def name_getter(self, id_, charnames, lang):
        name_id = '1' + str(id_).rjust(3, '0')
        try:
            names = charnames[(name_id,)]
        except KeyError as e:
            raise KeyError(translate("ModInstall", "ID {name_id} is not defined in charnames; did you remember to enter a 4-character ID code?").format(name_id=name_id)) from e
        jp_name = names[0]
        lang_name = names[lang]
        return (jp_name, lang_name)
        
    def sortmode_compress_keygen(self, digi_id, build_common_para_digimon, build_charname):
        # Remember that digi_id is a tuple, despite having one element
        stage = build_common_para_digimon[digi_id][0]
        field_guide_id = build_common_para_digimon[digi_id][20]
        name = self.name_getter(digi_id[0], build_charname, 1)[1]
        return (int(field_guide_id), int(stage), name.encode('utf8'))
    
    def sortmode_sort_keygen(self, digi_id, build_common_para_digimon, build_charname):
        pass
    
    def gojuonjun_order(self):
        pass
    

    ########################
    # VOICELINES SORTING
    ########################
    def sort_voicelines(self, step_no):
        try:
            for table, game_name, step_add in [("battle_voice.mbe", "CS", 0), ("battle_voice_add.mbe", "HM", 1)]:
                self.log.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Battle Voices ({game_name})...").format(game_name=game_name, step_no=step_no+step_add, max_steps=self.max_steps))
                cache_loc = self.ops.paths.patch_cache_loc
                if os.path.exists(cache_table := os.path.join(cache_loc, "DSDBP", "data", table)): 
                    # Get the required data
                    voice_path = ["data", table]
                    hdr, build_voice_data = self.get_resource_table("DSDBP", voice_path, "voice.csv")
    
                    build_voice_data = {key: value for key, value in sorted(build_voice_data.items(), key=lambda x: x[0][0])}

                    # Save back to the cache
                    build_table = os.path.join(self.ops.paths.patch_build_loc, "data", table)
                    dict_to_mbetable(os.path.join(build_table, "voice.csv"), hdr, build_voice_data)
                    os.remove(cache_table)
                        
                    mbe_filepack = get_filepack_plugins_dict()["MBE"]
                    cache_table_decomp = cache_table + ".decomp"
                    mbe_filepack.pack(build_table, cache_table_decomp)
                    DSCSTools.dobozCompress(cache_table_decomp, cache_table)
                    os.remove(cache_table_decomp)
                    self.safe_remove_mbe(voice_path)
                    self.updateLog.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Battle Voices ({game_name})... sort complete.").format(game_name=game_name, step_no=step_no+step_add, max_steps=self.max_steps))
                else:
                    self.updateLog.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Battle Voices ({game_name})... no edits required.").format(game_name=game_name, step_no=step_no+step_add, max_steps=self.max_steps))

        except Exception as e:
            self.raise_exception.emit(e)
            
    #################
    # ITEMS SORTING #
    #################
    def sort_items(self, step_no):
        try:
            self.log.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Items...").format(step_no=step_no, max_steps=self.max_steps))
            cache_loc = self.ops.paths.patch_cache_loc
            if os.path.exists(cache_table := os.path.join(cache_loc, "DSDBP", "data", "item_para.mbe")): 
                # Get the required data
                item_path = ["data", "item_para.mbe"]
                item_name_path = ["text", "item_name.mbe"]
                hdr, build_common_para_digimon = self.get_resource_table("DSDBP", item_path, "table.csv")
                _, build_charname = self.get_resource_table("DSDB", item_name_path, "Sheet1.csv")

                # Now do the sorting
                to_sort = []
                for key, val in build_common_para_digimon.items():
                    to_sort.append(key)
                        
                to_sort = sorted(to_sort, key=lambda x: self.sortmode_compress_keygen_items(x, 
                                                                                      build_common_para_digimon,
                                                                                      build_charname))
                
                # Now that we have an order for the keys,
                # generate the sort order indices for them
                for i, key in enumerate(to_sort):
                    # Index 3 is the Item Sort Value
                    build_common_para_digimon[key][2] = i+1
   
                    
                # Save back to the cache
                build_table = os.path.join(self.ops.paths.patch_build_loc, "data", "item_para.mbe")
                dict_to_mbetable(os.path.join(build_table, "table.csv"), hdr, build_common_para_digimon)
                os.remove(cache_table)
                
                mbe_filepack = get_filepack_plugins_dict()["MBE"]
                cache_table_decomp = cache_table + ".decomp"
                mbe_filepack.pack(build_table, cache_table_decomp)
                DSCSTools.dobozCompress(cache_table_decomp, cache_table)
                os.remove(cache_table_decomp)
                self.safe_remove_mbe(item_path)
                self.safe_remove_mbe(item_name_path)
                self.updateLog.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Items... sort complete.").format(step_no=step_no, max_steps=self.max_steps))
            else:
                self.updateLog.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Items... no edits required.").format(step_no=step_no, max_steps=self.max_steps))
        except Exception as e:
            self.raise_exception.emit(e)
                    
    def sortmode_compress_keygen_items(self, item_id, build_item_para, build_item_name):
        # Remember that item_id is a tuple, despite having one element
        item_sort_id = build_item_para[item_id][2]
        name = build_item_name[item_id][2]
        return (int(item_sort_id), name.encode('utf8'))
                
    ######################
    # DIGIMARKET SORTING #
    ######################
    def sort_digimarket(self, step_no):
        try:
            self.log.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Digimon Market...").format(step_no=step_no, max_steps=self.max_steps))
            cache_loc = self.ops.paths.patch_cache_loc
            if os.path.exists(cache_table := os.path.join(cache_loc, "DSDBP", "data", "digimon_market_para.mbe")): 
                # Get the required data
                market_path = ["data", "digimon_market_para.mbe"]
                charname_path = ["text", "charname.mbe"]
                hdr, build_common_para_digimon = self.get_resource_table("DSDBP", market_path, "table.csv")
                _, build_charname = self.get_resource_table("DSDB", charname_path, "Sheet1.csv")

                # Now do the sorting
                to_sort = []
                for key, val in build_common_para_digimon.items():
                    to_sort.append(key)
                to_sort = sorted(to_sort, key=lambda x: self.sortmode_compress_keygen_digimarket(x, 
                                                                                      build_common_para_digimon,
                                                                                      build_charname))
                
                # Now that we have an order for the keys,
                # generate the sort order indices for them
                for i, key in enumerate(to_sort):
                    # Index 3 is the Item Sort Value
                    build_common_para_digimon[key][1] = i+1
   
                    
                # Save back to the cache
                build_table = os.path.join(self.ops.paths.patch_build_loc, "data", "digimon_market_para.mbe")
                dict_to_mbetable(os.path.join(build_table, "table.csv"), hdr, build_common_para_digimon)
                os.remove(cache_table)
                
                mbe_filepack = get_filepack_plugins_dict()["MBE"]
                cache_table_decomp = cache_table + ".decomp"
                mbe_filepack.pack(build_table, cache_table_decomp)
                DSCSTools.dobozCompress(cache_table_decomp, cache_table)
                os.remove(cache_table_decomp)
                self.safe_remove_mbe(market_path)
                self.safe_remove_mbe(charname_path)
                self.updateLog.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Digimon Market... sort complete.").format(step_no=step_no, max_steps=self.max_steps))
            else:
                self.updateLog.emit(translate("ModInstall", ">> [Step {step_no}/{max_steps}] Sorting Digimon Market... no edits required.").format(step_no=step_no, max_steps=self.max_steps))
        except Exception as e:
            self.raise_exception.emit(e)
                    
    def sortmode_compress_keygen_digimarket(self, item_id, build_item_para, build_item_name):
        # Remember that item_id is a tuple, despite having one element
        item_sort_id = build_item_para[item_id][1]
        digimon_id   = build_item_para[item_id][0]
        name = self.name_getter(digimon_id, build_item_name, 1)[1]
        return (int(item_sort_id), name.encode('utf8'))
    

class ArchiveBuilder(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    clean_up = QtCore.pyqtSignal()
    raise_exception = QtCore.pyqtSignal(Exception)
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
        
    def __init__(self, ops, parent=None):
        super().__init__()
        self.ops = ops
        self.build_graphs = None
        self.pre_message = None
        
    def set_message_info(self, msg):
        self.pre_message = msg
        
    def init_signals(self, ui):
        self.log.connect(ui.log)
        self.updateLog.connect(ui.updateLog)
        
    @QtCore.pyqtSlot(dict)
    def receiveBuildGraphs(self, build_graphs):
        self.build_graphs = build_graphs
        
    @QtCore.pyqtSlot()
    def execute(self):
        try:
            self.log.emit(translate("ModInstall", "{curr_step_message} Installing mod files...").format(curr_step_message=self.pre_message))
            n_items = 0
            for archive_t, archives in self.build_graphs.items():
                for archive_name, archive in archives.items():
                    n_items += 1
                    
            cur_item = 0
            for archive_t, archives in self.build_graphs.items():
                for archive_name, archive in archives.items():
                    cur_item += 1
                    archive.setLogs(lambda x: self.log.emit(generate_prefixed_message(cur_item, n_items, x)), 
                                    lambda x: self.updateLog.emit(generate_prefixed_message(cur_item, n_items, x)))
                    archive.pack()
            self.finished.emit()
        except Exception as e:
            self.raise_exception.emit(e)
       

class ModInstaller(QtCore.QObject):
    success = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    clean_up = QtCore.pyqtSignal()
    exiting = QtCore.pyqtSignal()
    raise_exception = QtCore.pyqtSignal(Exception)
    
    
    def __init__(self, ui, ops, threadpool, parent=None):
        super().__init__(parent)
        self.raise_exception.connect(parent.raise_exception.emit)
        self.ops = ops
        self.ui = ui
        self.thread = QtCore.QThread()
        self.threadpool = threadpool
        
        self.build_graph_runner = None
        self.resource_bootstrapper = None
        self.build_graph_executor = None
        self.data_sorter = None
        self.archive_builder = None
        
        
        # Link final step to the thread destructor
        self.success.connect(self.finished.emit)
        self.finished.connect(self.clean_up.emit)
        self.raise_exception.connect(self.clean_up.emit)
        self.clean_up.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.exiting.emit)
        self.exiting.connect(self.ui.enable_gui)
        
        self.success.connect(lambda: self.ui.log(translate("ModInstall", "Mods successfully installed.")))
        
    @QtCore.pyqtSlot()
    def install(self):
        try:
            self.ui.disable_gui()
            self.ui.log(translate("ModInstall", "[!] Preparing to install... [!]"))
            self.ops.profile_manager.save_profile()
            self.ops.mod_registry.update_mods()
            self.ops.profile_manager.save_profile()
            if os.path.isdir(self.ops.paths.patch_build_loc):
                shutil.rmtree(self.ops.paths.patch_build_loc)
            
            installer_steps = []
            
            # Step 1: Create Build graph
            self.build_graph_runner = BuildGraphRunner(self.ops, parent=self)
            self.build_graph_runner.moveToThread(self.thread)
            self.build_graph_runner.init_signals(self.ui)
            self.build_graph_runner.raise_exception.connect(self.raise_exception.emit)
            self.build_graph_runner.finished.connect(self.build_graph_runner.deleteLater)
            self.build_graph_runner.early_exit.connect(self.finished.emit)
            installer_steps.append(self.build_graph_runner)
            
            # Another step: resolve softcodes + other IDs?
            
            # Step 2: Bootstrap resources
            self.resource_bootstrapper = ResourceBootstrapper(self.threadpool, self.ops, parent=self)
            self.resource_bootstrapper.moveToThread(self.thread)
            self.resource_bootstrapper.init_signals(self.ui)
            self.resource_bootstrapper.raise_exception.connect(self.raise_exception.emit)
            self.resource_bootstrapper.finished.connect(self.resource_bootstrapper.deleteLater)
            installer_steps.append(self.resource_bootstrapper)
            
            # Step 3: Execute Build graph
            self.build_graph_executor = BuildGraphExecutor(self.threadpool, self.ui, self.ops, parent=self)
            self.build_graph_executor.raise_exception.connect(self.raise_exception.emit)
            installer_steps.append(self.build_graph_executor)
            
            # Optional step: Sort the field guide order
            self.data_sorter = DataSorter(self.ops, parent=self)
            self.data_sorter.moveToThread(self.thread)
            self.data_sorter.init_signals(self.ui)
            self.data_sorter.raise_exception.connect(self.raise_exception.emit)
            self.data_sorter.finished.connect(self.data_sorter.deleteLater)
            installer_steps.append(self.data_sorter)
            
            # Step 4: Build and install any archives and loose files
            self.archive_builder = ArchiveBuilder(self.ops, parent=self)
            self.archive_builder.moveToThread(self.thread)
            self.archive_builder.init_signals(self.ui)
            self.archive_builder.raise_exception.connect(self.raise_exception.emit)
            self.archive_builder.finished.connect(self.archive_builder.deleteLater)
            installer_steps.append(self.archive_builder)
            
            # Link it all up
            self.build_graph_runner.sendBuildGraphs.connect(self.resource_bootstrapper.receiveBuildGraphs)
            self.build_graph_runner.sendBuildGraphs.connect(self.build_graph_executor.receiveBuildGraphs)
            self.build_graph_runner.sendBuildGraphs.connect(self.archive_builder.receiveBuildGraphs)
            self.build_graph_runner.sendSoftcodes.connect(self.build_graph_executor.receiveSoftcodes)
            
            n_steps = len(installer_steps)
            self.thread.started.connect(installer_steps[0].execute)
            for i, (istep, next_istep) in enumerate(zip(installer_steps, installer_steps[1:])):
                istep.set_message_info(generate_step_message(i+1, n_steps))
                istep.finished.connect(next_istep.execute)
            
            # Link up final step
            last_istep = installer_steps[-1]
            last_istep.set_message_info(generate_step_message(n_steps, n_steps))
            last_istep.finished.connect(self.success.emit)
            
            # Green light! Go go go!
            self.ui.updateLog(translate("ModInstall", "[!] Starting mod installation... [!]"))
            self.thread.start()
        except Exception as e:
            self.raise_exception.emit(e)
