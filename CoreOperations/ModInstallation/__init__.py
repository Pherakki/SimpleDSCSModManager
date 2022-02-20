import json
import os
import shutil

from PyQt5 import QtCore

from CoreOperations.ModBuildGraph import ModBuildGraphCreator
from CoreOperations.ModBuildGraph.graphHash import hashFilepack
from CoreOperations.ModInstallation.PipelineRunners import ArchivePipelineCollection
from CoreOperations.PluginLoaders.FilePacksPluginLoader import get_filepack_plugins_dict
from sdmmlib.dscstools import DSCSTools
from Utils.MBE import mbetable_to_dict, dict_to_mbetable

translate = QtCore.QCoreApplication.translate

def generate_step_message(cur_items, cur_total):
    return translate("ModInstall", "[Step {ratio}]").format(ratio=f"{cur_items}/{cur_total}")
   
def generate_prefixed_message(cur_items, cur_total, msg):
    return f">> {generate_step_message(cur_items, cur_total)} {msg}"
    
class BuildGraphRunner(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    # clean_up = QtCore.pyqtSignal()
    sendBuildGraphs = QtCore.pyqtSignal(dict)
    sendSoftcodes = QtCore.pyqtSignal(dict)
    raise_exception = QtCore.pyqtSignal(Exception)
    
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
            active_mods = self.ops.profile_manager.get_active_mods()
            self.log.emit(translate("ModInstall", "Installing {count} mods...").format(count=len(active_mods)))
            for mod in active_mods:
                self.log.emit(f"> {mod.name}")
            self.log.emit(translate("ModInstall", "{curr_step_message} Generating build graph...").format(curr_step_message=self.pre_message))
            # Make all the build pipelines...
            mod_build_graph_creator = ModBuildGraphCreator(self.ops)
            build_graphs, softcodes = mod_build_graph_creator.create_build_graph(active_mods, 
                                                                                 self.sendLog, 
                                                                                 self.sendUpdateLog)

            softcode_lookup = {}
            for category in softcodes:
                softcode_lookup[category] = {}
                for key in softcodes[category]:
                    softcode_lookup[category][key] = self.ops.softcode_manager.get_softcode(category, key)
            self.process_graph(build_graphs, softcode_lookup)
            
            # Now cull the graph depending on the hash of each pack target...
            self.ops.softcode_manager.dump_cached_softcodes()
            # assert 0
            self.sendBuildGraphs.emit(build_graphs)
            self.sendSoftcodes.emit(softcode_lookup)
            self.finished.emit()
        except Exception as e:
            self.raise_exception.emit(e)

    def process_graph(self, build_graphs, softcode_lookup):
        self.sendLog(translate("ModInstall", "Looking for cached mod files..."))
        if not os.path.exists(self.ops.paths.patch_cache_index_loc):
            with open(self.ops.paths.patch_cache_index_loc, 'w') as F:
                F.write("{}")
        os.makedirs(self.ops.paths.patch_cache_loc, exist_ok=True)
        with open(self.ops.paths.patch_cache_index_loc, 'r') as F:
            cache_index = json.load(F)
        n_found = 0
        n_total = 0
        # First just loop over the archive categories and archives...
        for archive_type, archives in list(build_graphs.items()):
            for archive, archive_obj in list(archives.items()):
                # Now we can actually inspect the filepacks we want to install...
                build_pipelines = archive_obj.build_graph
                for pack_type, packs in list(build_pipelines.items()):
                    for pack_name, pack in list(packs.items()):
                        # Substitute softcode names in the packs
                        pack.link_softcodes(softcode_lookup)
                        # Hash pack
                        pack.hash = hashFilepack(self.ops.paths.mm_root, pack)
                        pack_is_in_cache = True
                        pack_targets = pack.get_pack_targets()
                        n_total += len(pack_targets)
                        for pack_target in pack_targets:
                            archive_pack_target = os.path.join(archive_obj.get_prefix(), pack_target)
                            if cache_index.get(archive_pack_target) != pack.hash or not os.path.isfile(os.path.join(self.ops.paths.patch_cache_loc, archive_pack_target)):
                                pack_is_in_cache = False
                                break
                            n_found += 1
                        # Cull the pack if all pack targets are in the cache...
                        if pack_is_in_cache:
                            for pack_target in pack_targets:
                                archive_obj.cached_pack_targets.append(pack_target)
                            del packs[pack_name]
                    # Cull any groups with no packs
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
            
            with open(os.path.join(self.ops.paths.config_loc, "filelist.json")) as F:
                resource_archives = json.load(F)
            
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

class FieldGuideSorter(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    raise_exception = QtCore.pyqtSignal(Exception)
    
    def __init__(self, ops, parent=None):
        super().__init__()
        self.ops = ops
        self.pre_message = None
        
    def set_message_info(self, msg):
        self.pre_message = msg
        
    def init_signals(self, ui):
        self.log.connect(ui.log)
        self.updateLog.connect(ui.updateLog)
        
    @QtCore.pyqtSlot()
    def execute(self):
        try:
            self.log.emit(translate("ModInstall", "{curr_step_message} Sorting Field Guide...").format(curr_step_message=self.pre_message))
            cache_loc = self.ops.paths.patch_cache_loc
            if os.path.exists(cache_table := os.path.join(cache_loc, "DSDBP", "data", "digimon_common_para.mbe")): 
                # Get the required data
                hdr, build_common_para_digimon = self.get_resource_table("DSDBP", ["data", "digimon_common_para.mbe"], "digimon.csv")
                _, build_charname = self.get_resource_table("DSDB", ["text", "charname.mbe"], "Sheet1.csv")

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
                self.updateLog.emit(translate("ModInstall", "{curr_step_message} Sorting Field Guide... sort complete.").format(curr_step_message=self.pre_message))
            else:
                self.updateLog.emit(translate("ModInstall", "{curr_step_message} Sorting Field Guide... no edits required.").format(curr_step_message=self.pre_message))
                
            self.finished.emit()
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
            DSCSTools.extractMDB1File(os.path.join((self.ops.paths.game_resources_loc, f"{archive}.steam.mvgl"), build_loc, "/".join(*table_path)))
        
        os.rmdir(working_loc)
        
        build_subtable = os.path.join(build_file, subtable)
        return mbetable_to_dict({}, build_subtable, 1, None, None)
    
    def name_getter(self, id_, charnames, lang):
        name_id = '1' + str(id_).rjust(3, '0')
        names = charnames[(name_id,)]
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
        self.archive_builder = None
        
        
        # Link final step to the thread destructor
        self.finished.connect(self.clean_up.emit)
        self.raise_exception.connect(self.clean_up.emit)
        self.clean_up.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.exiting.emit)
        self.exiting.connect(self.ui.enable_gui)
        
        self.finished.connect(lambda: self.ui.log(translate("ModInstall", "Mods successfully installed.")))
        
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
            self.field_guide_sorter = FieldGuideSorter(self.ops, parent=self)
            self.field_guide_sorter.moveToThread(self.thread)
            self.field_guide_sorter.init_signals(self.ui)
            self.field_guide_sorter.raise_exception.connect(self.raise_exception.emit)
            self.field_guide_sorter.finished.connect(self.field_guide_sorter.deleteLater)
            installer_steps.append(self.field_guide_sorter)
            
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
            last_istep.finished.connect(self.finished.emit)
            
            # Green light! Go go go!
            self.ui.updateLog(translate("ModInstall", "[!] Starting mod installation... [!]"))
            self.thread.start()
        except Exception as e:
            self.raise_exception.emit(e)
        
        
