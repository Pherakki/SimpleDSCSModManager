import json
import os
import shutil

from PyQt5 import QtCore 

from ModFiles.Indexing import generate_mod_index
from ModFiles.PatchGenMultithreaded import generate_patch_mt
from Utils.Path import splitpath
from Utils.FiletypesPluginLoader import get_filetype_plugins
from Utils.PatchersPluginLoader import get_patcher_plugins
from Utils.RulesPluginLoader import get_rule_plugins
from Utils.Multithreading import PoolChain
from ModFiles.Hashing import hash_file_install_orders, sort_hashes, add_cache_to_index, cull_index
            
class InstallModsWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    
    def __init__(self, output_loc, resources_loc, game_resources_loc,  backups_loc,
                 profile_handler, dscstools_handler, script_handler, threadpool, thread, parent=None):
        super().__init__()
        self.output_loc = output_loc
        self.resources_loc = resources_loc
        self.game_resources_loc = game_resources_loc
        self.backups_loc = backups_loc
        self.profile_handler = profile_handler
        self.dscstools_handler = dscstools_handler
        self.script_handler = script_handler
        self.threadpool = threadpool
        
        self.lockGuiFunc = None
        self.releaseGuiFunc = None
        self.messageLogFunc = None
        self.updateMessageLogFunc = None
        
        self.mod_indexer = None
        self.thread = thread
        self.patch_installer = None
        self.thread2 = QtCore.QThread()
        self.resource_bootstrapper = None
        
        self.indices = None
        self.all_used_archives = None
        
    def run(self):
        try:
            self.lockGuiFunc()
            self.messageLogFunc("Preparing to patch mods together...")
            
            # 1. Clean up any pre-existing patch files
            patch_dir = os.path.relpath(os.path.join(self.output_loc, 'patch'))
            if os.path.exists(patch_dir):
                shutil.rmtree(patch_dir)
            
            # 2. Define a function to set up the signals on any single-threaded operations
            def hook_signals(pool_obj, thread):
                # Setup and life cycle signals
                pool_obj.moveToThread(thread)
                thread.started.connect(pool_obj.run)
                pool_obj.finished.connect(thread.quit)
                pool_obj.finished.connect(pool_obj.deleteLater)
                thread.finished.connect(thread.deleteLater)
                
                # GUI signals
                pool_obj.messageLog.connect(self.messageLogFunc)
                pool_obj.updateMessageLog.connect(self.updateMessageLogFunc)
                pool_obj.lockGui.connect(self.lockGuiFunc)
                pool_obj.releaseGui.connect(self.releaseGuiFunc)   
                
            # 3. Create an object to detect which files are in the mods, figure out which archives
            #    they should be put into, read which rules should be applied to each file in the
            #    mod to combine it into the patch, etc.
            self.mod_indexer = ModsIndexer(self.output_loc, self.profile_handler)
            hook_signals(self.mod_indexer, self.thread)
            
            # 4. Create an object to get any files the mods depends on from game archives
            # The resource bootstrapper is not generalised and will crash if the MBE or script plugins are removed
            # This NEEDS to be changed
            self.resource_bootstrapper = multithreaded_bootstrap_index_resources(None, self.game_resources_loc, 
                                                                                 self.resources_loc, self.backups_loc,
                                                                                 self.dscstools_handler, self.script_handler,
                                                                                 self.threadpool,
                                                                                 self.messageLogFunc, self.updateMessageLogFunc,
                                                                                 self.lockGuiFunc, self.releaseGuiFunc)
             
            # 5. Create an object to patch all the mods together into their respective archives
            #    using the given rules
            rules = get_rule_plugins()
            patchers = get_patcher_plugins()
            self.patch_builder = generate_patch_mt(rules, patchers,
                                                   patch_dir, self.resources_loc, self.threadpool, 
                                                   self.lockGuiFunc, self.releaseGuiFunc,
                                                   self.messageLogFunc, self.updateMessageLogFunc)
                
            # 6. Create an object to pack any MBE tables into MBE archives, and to compile any
            #    Squirrel files
            self.file_packer = PackerGenerator(patch_dir, self.dscstools_handler, self.script_handler, 
                                                    self.threadpool,
                                                    self.messageLogFunc, self.updateMessageLogFunc,
                                                    self.lockGuiFunc, self.releaseGuiFunc)

            # 7. Create an object to update the mod manager's file cache, pack the archives, and then install them
            self.patch_installer = FinaliseInstallation(patch_dir, self.output_loc, self.resources_loc,
                                                        self.game_resources_loc, self.backups_loc, self.dscstools_handler)
            hook_signals(self.patch_installer, self.thread2)
            
            # 8. Make a function to pass the mod index/metadata/target archive to other objects
            def relay_indices_and_cache(indices, cache, archives, all_used_archives):
                self.resource_bootstrapper.indices = indices
                self.patch_builder.indices = indices
                self.patch_builder.archives = archives
                self.patch_builder.all_used_archives = all_used_archives
                self.file_packer.all_used_archives = all_used_archives
                self.patch_installer.cached_files = cache
                self.patch_installer.all_used_archives = all_used_archives
                           
            self.mod_indexer.emitIndicesAndCache.connect(relay_indices_and_cache)
            
            # 9. Link up the installer objects such that they kick off the next object in a chain
            #    Don't forget that e.g. thread2.start() starts off patch_installer, so we can hook
            #    the finished() signal of patch_installer
            self.mod_indexer.continue_execution.connect(self.resource_bootstrapper.run)
            self.resource_bootstrapper.finished.connect(self.patch_builder.run)
            self.patch_builder.finished.connect(self.file_packer.run)
            self.file_packer.finished.connect(lambda: self.thread2.start())
            self.patch_installer.finished.connect(self.finished.emit)

            # 10. Green light! Go go go!
            self.thread.start()

        except Exception as e:
            self.messageLogFunc(f"The following error occured when trying to install modlist: {e}")
            raise e
        

class ModsIndexer(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    continue_execution = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    updateMessageLog = QtCore.pyqtSignal(str)
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()
    emitIndicesAndCache = QtCore.pyqtSignal(list, dict, list, list)
    
    def __init__(self, output_loc, profile_handler):
        super().__init__()
        self.output_loc = output_loc
        self.profile_handler = profile_handler
    
    def run(self):
        try:
            filetypes = get_filetype_plugins()
            self.messageLog.emit("Indexing mods...")
            indices = []
            mod_archives = []
            for mod in self.profile_handler.get_active_mods():
                # Yes, this is really messy and needs a refactor
                modfiles_path = os.path.relpath(os.path.join(mod.path, "modfiles"))
                metadata_path = os.path.relpath(os.path.join(mod.path, "METADATA.json"))
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as F:
                        metadata = json.load(F)
                else:
                    metadata = {}
                    
                base_archive = metadata.get("DefaultArchive", "DSDBP")
                rules = metadata.get("Rules", {})
                rules = {key.replace('/', os.sep): value for key, value in rules.items()}
                archives = metadata.get("Archives", {})
                archives = {key.replace('/', os.sep): value for key, value in archives.items()}
                    
                index = generate_mod_index(modfiles_path, rules, filetypes)
                indices.append(index)
                
                archive_data = {}
                for index_data in index.values():
                    for key in index_data.keys():
                        archive_data[key] = archives.get(key, base_archive)
                        
                mod_archives.append(archive_data)
                

                
            self.messageLog.emit(f"Indexed ({len(indices)}) active mods.")
            if len(indices) == 0:
                raise Exception("No mods activated.")
            
            self.messageLog.emit("Indexing mods...")
            mod_hashes = hash_file_install_orders(indices)
            modcache_location = os.path.join(self.output_loc, "modcache.json")
            if os.path.exists(modcache_location):
                with open(modcache_location, 'r') as F:
                    cached_hashes = json.load(F)
                    shared_hashes = sort_hashes(mod_hashes, cached_hashes)
                    shared_hashes = add_cache_to_index(indices, mod_archives, shared_hashes)
                    cull_index(indices[:-1], shared_hashes)
                    all_hashes = {**cached_hashes, **mod_hashes}
            else:
                all_hashes = {}

            all_used_archives = set()
            for archive_data in mod_archives:
                all_used_archives.update(set(archive_data.values()))
            all_used_archives = sorted(list(all_used_archives))

            self.emitIndicesAndCache.emit(indices, all_hashes, mod_archives, all_used_archives)
            self.continue_execution.emit()
        except Exception as e:
            self.messageLog.emit(f"The following exception occured when indexing mods: {e}")
        finally:
            self.releaseGui.emit()
            self.finished.emit()


class PackerGenerator(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    
    def __init__(self, patch_dir, dscstools_handler, script_handler, threadpool,
                 messageLogFunc, updateMessageLogFunc, lockGuiFunc, releaseGuiFunc):
        super().__init__()
        self.patch_dir = patch_dir
        self.dscstools_handler= dscstools_handler
        self.script_handler = script_handler
        self.threadpool = threadpool
        self.messageLogFunc = messageLogFunc
        self.updateMessageLogFunc = updateMessageLogFunc
        self.lockGuiFunc = lockGuiFunc
        self.releaseGuiFunc = releaseGuiFunc
        self.workers = []
        
        self.all_used_archives = None
        self.runner = None
    
    def run(self):
        try:
            self.lockGuiFunc()
            for archive in self.all_used_archives:
                # Pack the resources              
                gmp = self.dscstools_handler.generate_mbe_packer
                datmbe_worker = gmp(os.path.join(self.patch_dir, archive, 'data'), 
                                    os.path.join(self.patch_dir, archive, 'data'),
                                    self.threadpool,
                                    self.messageLogFunc, self.updateMessageLogFunc, 
                                    self.lockGuiFunc, self.releaseGuiFunc)
                msgmbe_worker = gmp(os.path.join(self.patch_dir, archive, 'message'), 
                                    os.path.join(self.patch_dir, archive, 'message'), 
                                    self.threadpool,
                                    self.messageLogFunc, self.updateMessageLogFunc, 
                                    self.lockGuiFunc, self.releaseGuiFunc)
                texmbe_worker = gmp(os.path.join(self.patch_dir, archive, 'text'), 
                                    os.path.join(self.patch_dir, archive, 'text'),
                                    self.threadpool,
                                    self.messageLogFunc, self.updateMessageLogFunc, 
                                    self.lockGuiFunc, self.releaseGuiFunc)
                gsc = self.script_handler.generate_script_compiler
                script_worker = gsc(os.path.abspath(os.path.join(self.patch_dir, archive, 'script64')), 
                                    os.path.abspath(os.path.join(self.patch_dir, archive, 'script64')),
                                    self.threadpool,
                                    self.lockGuiFunc, self.releaseGuiFunc,
                                    self.messageLogFunc, self.updateMessageLogFunc,
                                    remove_input=True)
                
                self.workers.append(datmbe_worker)
                self.workers.append(msgmbe_worker)
                self.workers.append(texmbe_worker)
                self.workers.append(script_worker)
            
            self.runner = PoolChain(*self.workers)
            self.runner.finished.connect(self.finished.emit)
            self.runner.run()
        except Exception as e:
            self.messageLogFunc.emit(f"The following exception occured when packing mod files: {e}")
        finally:
            self.releaseGuiFunc()
            # self.finished.emit()
            
            
    
            
class FinaliseInstallation(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    updateMessageLog = QtCore.pyqtSignal(str)
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()

    def __init__(self, patch_dir, output_loc, resources_loc, game_resources_loc, backups_loc, dscstools_handler):
        super().__init__()
        self.patch_dir = patch_dir
        self.output_loc = output_loc
        self.resources_loc = resources_loc
        self.game_resources_loc = game_resources_loc
        self.backups_loc = backups_loc
        
        self.shared_cache = None
        self.cached_files = None
        self.cache_dir = os.path.join(os.path.split(patch_dir)[0], "cache", "modfiles")
        self.cache_record_filepath = os.path.join(os.path.split(patch_dir)[0], "modcache.json")

        self.dscstools_handler = dscstools_handler
        
        self.all_used_archives = None

    def run(self):
        try:
            self.lockGui.emit()
            
            def adapted_mvgl_pack(archive, origin, destination, remove_input):
                self.dscstools_handler.pack_mvgl_plain(os.path.join(origin, archive),
                                                       os.path.join(destination, archive + ".steam.mvgl"),
                                                       remove_input=remove_input)
            def adapted_mvgl_unpack(archive, origin, destination, remove_input):
                self.dscstools_handler.pack_mvgl_plain(os.path.join(origin, archive),
                                                       os.path.join(destination, archive),
                                                       remove_input=remove_input)
            
            packers = {'DSDB': adapted_mvgl_pack,
                       'DSDBA': adapted_mvgl_pack,
                       'DSDBS': adapted_mvgl_pack,
                       'DSDBSP': adapted_mvgl_pack,
                       'DSDBP': adapted_mvgl_pack,
                       'DSDBse': adapted_mvgl_pack,
                       'DSDBPse': adapted_mvgl_pack,
                       'DSDBbgm': self.dscstools_handler.pack_afs2,
                       'DSDBPDSEbgm': self.dscstools_handler.pack_afs2,
                       'DSDBvo': self.dscstools_handler.pack_afs2,
                       'DSDBPvo': self.dscstools_handler.pack_afs2,
                       'DSDBPvous': self.dscstools_handler.pack_afs2}
            
            unpackers = {'DSDB': adapted_mvgl_unpack,
                       'DSDBA': adapted_mvgl_unpack,
                       'DSDBS': adapted_mvgl_unpack,
                       'DSDBSP': adapted_mvgl_unpack,
                       'DSDBP': adapted_mvgl_unpack,
                       'DSDBse': adapted_mvgl_unpack,
                       'DSDBPse': adapted_mvgl_unpack,
                       'DSDBbgm': self.dscstools_handler.unpack_afs2,
                       'DSDBPDSEbgm': self.dscstools_handler.unpack_afs2,
                       'DSDBvo': self.dscstools_handler.unpack_afs2,
                       'DSDBPvo': self.dscstools_handler.unpack_afs2,
                       'DSDBPvous': self.dscstools_handler.unpack_afs2}
            
            categories = {'data': 'DSDBP',
                          'sfx': 'DSDBPse',
                          'bgm': 'DSDBbgm',
                          'vo': 'DSDBPvous'}
            
            self.messageLog.emit("Updating cache...")
            # Replace this with only copying updated files...
            for archive in self.all_used_archives:
                shutil.copytree(os.path.join(self.patch_dir, archive), self.cache_dir, dirs_exist_ok=True)
                with open(self.cache_record_filepath, 'w') as F:
                    json.dump(self.cached_files, F, indent=4)
            
            self.messageLog.emit("Generating patched MVGL archive (this may take a few minutes)...")

            for archive in self.all_used_archives:            
                dsdbp_resource_loc = os.path.join(self.resources_loc, archive)
                unpacked_archive_loc = os.path.join(self.output_loc, archive)
                patch_loc = os.path.join(self.patch_dir, archive)
                if not os.path.exists(dsdbp_resource_loc):
                    self.messageLog.emit(f"Base {archive} archive not found, generating...")
                    origin = backup_ifdef(archive, self.game_resources_loc, self.backups_loc)
                    unpackers[archive](archive, origin, self.resources_loc)
                
                shutil.copytree(dsdbp_resource_loc, unpacked_archive_loc)
                shutil.copytree(patch_loc, unpacked_archive_loc, dirs_exist_ok=True)
                packers[archive](archive, self.output_loc, self.output_loc, remove_input=False)
                shutil.rmtree(unpacked_archive_loc)

            self.messageLog.emit("Installing patched archive...")
            # Now here's the important bit
            create_backups(self.game_resources_loc, self.backups_loc, self.messageLog.emit)
            for archive in self.all_used_archives:
                shutil.move(os.path.join(self.output_loc, f'{archive}.steam.mvgl'), 
                            os.path.join(self.game_resources_loc, f'{archive}.steam.mvgl'))
            
            self.messageLog.emit("Mods successfully installed.")
        except Exception as e:
            self.messageLog.emit(f"The following error occured when trying to install modlist: {e}")
        finally:
            self.releaseGui.emit()
            self.finished.emit()

    
def create_backups(game_resources_loc, backups_loc, logfunc):
    backup_filepath = os.path.join(backups_loc, 'DSDBP.steam.mvgl')
    if not os.path.exists(backup_filepath):
        logfunc("Creating backup...")
        os.mkdir(os.path.split(backup_filepath)[0])
        shutil.copy2(os.path.join(game_resources_loc, 'DSDBP.steam.mvgl'), backup_filepath)

      
def backup_ifdef(archive, game_resources_loc, backups_loc):
    backup_filepath = os.path.join(backups_loc, f'{archive}.steam.mvgl')
    if not os.path.exists(backup_filepath):
        return game_resources_loc
    else:
        return backups_loc
                            
            
class multithreaded_bootstrap_index_resources(QtCore.QObject):
    """Needs to be generalised to any number or kind of resource gathering...
    no idea how to implement that sensibly yet though"""
    finished = QtCore.pyqtSignal()
    
    def __init__(self, indices, game_resources_loc, resources_loc, backups_loc,
                 dscstools_handler, script_handler, threadpool,
                 messageLog, updateMessageLog,
                 lockGui, releaseGui):
        super().__init__()
        
        self.indices = indices
        self.game_resources_loc = game_resources_loc
        self.resources_loc = resources_loc
        self.backups_loc = backups_loc
        self.dscstools_handler = dscstools_handler
        self.script_handler = script_handler
        self.threadpool = threadpool
        self.messageLog = messageLog
        self.updateMessageLog = updateMessageLog
        self.lockGui = lockGui
        self.releaseGui = releaseGui
        
        self.mbe_dump = None
        self.script_dump = None
        
    def run(self):
        indices = self.indices
        game_resources_loc = self.game_resources_loc
        resources_loc = self.resources_loc
        backups_loc = self.backups_loc
        dscstools_handler = self.dscstools_handler
        script_handler = self.script_handler
        threadpool = self.threadpool
        messageLog = self.messageLog
        updateMessageLog = self.updateMessageLog
        lockGui = self.lockGui
        releaseGui = self.releaseGui
        
        gfd = dscstools_handler.generate_file_dumper
            
        missing_scripts = []
        missing_mbes = []
        for index in indices:
            if 'script_src' in index:
                for script in index['script_src'].keys():
                    internal_path = os.path.join(*splitpath(script)[3:])
                    if not os.path.exists(os.path.join(resources_loc, 'base_scripts', internal_path)):
                        missing_scripts.append(internal_path)
            if 'mbe' in index:
                for mbe in index['mbe'].keys():
                    internal_path = os.path.join(*splitpath(mbe)[3:])
                    if not os.path.exists(os.path.join(resources_loc, 'base_mbes', internal_path)):
                        missing_mbes.append(internal_path)
                    
        with open(os.path.join("config", "filelist.json"), 'r') as F:
            filelist = json.load(F)
            
        archive_origins = {archive: backup_ifdef(archive, game_resources_loc, backups_loc)
                           for archive in ['DSDB', 'DSDBA', 'DSDBS', 'DSDBSP', 'DSDBP']}
        # Strip out the individual tables and get the packed MBE archives they belong to
        missing_mbes = sorted(list(set([os.path.split(mbe_path)[0] for mbe_path in missing_mbes])))
        nmbes = len(missing_mbes)
        if nmbes:
            messageLog(f"Fetching {nmbes} missing mbes...")
            missing_mbe_paths = {mbe_path: os.path.join(archive_origins[filelist[mbe_path]], filelist[mbe_path] + '.steam.mvgl') for mbe_path in missing_mbes}
            os.makedirs(os.path.join(resources_loc, 'base_mbes', 'data'), exist_ok=True)
            os.makedirs(os.path.join(resources_loc, 'base_mbes', 'message'), exist_ok=True)
            os.makedirs(os.path.join(resources_loc, 'base_mbes', 'text'), exist_ok=True)
            self.mbe_dump = gfd(missing_mbe_paths, os.path.join(resources_loc, 'base_mbes'), 
                                threadpool, messageLog, updateMessageLog, lockGui, releaseGui)
        
        nscripts = len(missing_scripts)
        if nscripts:
            messageLog(f"Fetching {nscripts} missing scripts...")
            missing_scripts = [script[:-3] + 'nut' for script in missing_scripts]
            missing_script_paths = {script_path: os.path.join(archive_origins[filelist[script_path]], filelist[script_path] + '.steam.mvgl') for script_path in missing_scripts}
            os.makedirs(os.path.join(resources_loc, 'base_scripts', 'script64'), exist_ok=True)
            self.script_dump = gfd(missing_script_paths, os.path.join(resources_loc, 'base_scripts'), 
                                   threadpool, messageLog, updateMessageLog, lockGui, releaseGui)

        gme = self.dscstools_handler.generate_mbe_extractor
        self.mbe_ex_data = gme(os.path.join(resources_loc, 'base_mbes', 'data'), os.path.join(resources_loc, 'base_mbes', 'data'), 
                     threadpool, messageLog, updateMessageLog, lockGui, releaseGui)
        self.mbe_ex_msg = gme(os.path.join(resources_loc, 'base_mbes', 'message'), os.path.join(resources_loc, 'base_mbes', 'message'), 
                     threadpool, messageLog, updateMessageLog, lockGui, releaseGui)
        self.mbe_ex_txt = gme(os.path.join(resources_loc, 'base_mbes', 'text'), os.path.join(resources_loc, 'base_mbes', 'text'), 
                     threadpool, messageLog, updateMessageLog, lockGui, releaseGui)
        gsd = self.script_handler.generate_script_decompiler
        self.scr_ex = gsd(os.path.join(resources_loc, 'base_scripts', 'script64'), os.path.join(resources_loc, 'base_scripts', 'script64'), 
                     threadpool, lockGui, releaseGui, messageLog, updateMessageLog,
                     remove_input=True)      
        
        if self.mbe_dump is not None:
            self.mbe_dump.finished.connect(self.mbe_ex_data.run)
            if self.script_dump is not None:
                self.mbe_ex_data.finished.connect(self.mbe_ex_msg.run)
                self.mbe_ex_msg.finished.connect(self.mbe_ex_txt.run)
                self.mbe_ex_txt.finished.connect(self.script_dump.run)
                self.script_dump.finished.connect(self.scr_ex.run)
                self.scr_ex.finished.connect(self.finished.emit)
            else:
                self.mbe_ex_data.finished.connect(self.mbe_ex_msg.run)
                self.mbe_ex_msg.finished.connect(self.mbe_ex_txt.run)
                self.mbe_ex_txt.finished.connect(self.finished.emit)
            self.mbe_dump.run()
        elif self.script_dump is not None:
            self.script_dump.finished.connect(self.scr_ex.run)
            self.scr_ex.finished.connect(self.finished.emit)
            self.script_dump.run()
        else:
            self.finished.emit()
        