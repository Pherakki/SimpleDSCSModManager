import json
import os
import shutil

from PyQt5 import QtCore 

from Subprocesses.ModInstallation.Hashing import hash_file_install_orders, sort_hashes, add_cache_to_index, cull_index
from Subprocesses.ModInstallation.Indexing import generate_mod_index
from Subprocesses.ModInstallation.PatchGenMultithreaded import generate_patch_mt
from Subprocesses.ModInstallation.Softcoding import search_string_for_softcodes, construct_softcode_links
from Utils.FiletypesPluginLoader import get_filetype_plugins
from Utils.Multithreading import PoolChain
from Utils.PatchersPluginLoader import get_patcher_plugins
from Utils.Path import splitpath
from Utils.RulesPluginLoader import get_rule_plugins
            
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
            keep_items = ["modcache.json", "cache"]
            for path in os.listdir(self.output_loc):
                if path in keep_items:
                    continue
                item_dir = os.path.relpath(os.path.join(self.output_loc, path))
                if os.path.isdir(item_dir):
                    shutil.rmtree(item_dir)
                elif os.path.isfile(item_dir):
                    os.remove(item_dir)
                else:
                    self.messageLogFunc(f"WARNING: Could not remove item \"{item_dir}\", was neither a file nor a directory.")
            
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
            
            # 6. Create an object to parse the final patch for softcodes, and convert them to
            #    hardcodes
            self.softcode_linker = SoftcodeLinker(patch_dir, self.messageLogFunc, self.updateMessageLogFunc, self.lockGuiFunc, self.releaseGuiFunc)
            
            # 7. Create an object to pack any MBE tables into MBE archives, and to compile any
            #    Squirrel files
            self.file_packer = PackerGenerator(patch_dir, self.dscstools_handler, self.script_handler, 
                                                    self.threadpool,
                                                    self.messageLogFunc, self.updateMessageLogFunc,
                                                    self.lockGuiFunc, self.releaseGuiFunc)

            # 8. Create an object to update the mod manager's file cache, pack the archives, and then install them
            self.patch_installer = FinaliseInstallation(patch_dir, self.output_loc, self.resources_loc,
                                                        self.game_resources_loc, self.backups_loc, self.dscstools_handler)
            hook_signals(self.patch_installer, self.thread2)
            
            # 9. Make a function to pass the mod index/metadata/target archive to other objects
            def relay_indices_and_cache(indices, cache, archives, all_used_archives):
                self.resource_bootstrapper.indices = indices
                self.patch_builder.indices = indices
                self.patch_builder.archives = archives
                self.patch_builder.all_used_archives = all_used_archives
                self.file_packer.all_used_archives = all_used_archives
                self.patch_installer.cached_files = cache
                self.patch_installer.all_used_archives = all_used_archives
                           
            self.mod_indexer.emitIndicesAndCache.connect(relay_indices_and_cache)
            
            # 10. Link up the installer objects such that they kick off the next object in a chain
            #     Don't forget that e.g. thread2.start() starts off patch_installer, so we can hook
            #     the finished() signal of patch_installer
            self.mod_indexer.continue_execution.connect(self.resource_bootstrapper.run)
            self.resource_bootstrapper.finished.connect(self.patch_builder.run)
            self.patch_builder.finished.connect(self.file_packer.run)
            # self.patch_builder.finished.connect(self.softcode_linker.run)
            # self.softcode_linker.finished.connect(self.file_packer.run)
            self.file_packer.finished.connect(self.thread2.start)
            self.patch_installer.finished.connect(self.finished.emit)

            # 11. Green light! Go go go!
            self.thread.start()

        except Exception as e:
            self.messageLogFunc(f"The following error occured when trying to install modlist: {e}")
            self.releaseGuiFunc()

class IndexException(Exception):
    def __init__(self, base_msg, mod_name):
        super().__init__(self)
        self.base_msg = base_msg
        self.mod_name = mod_name
        
    def __str__(self):
        return f"{self.mod_name}: {self.base_msg}"


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
    
    def index(self, mod, filetypes):
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

        
        archive_data = {}
        for index_data in index.values():
            for key in index_data.keys():
                archive_data[key] = archives.get(key, base_archive)
        return archive_data, index
                
    
    def run(self):
        try:
            filetypes = get_filetype_plugins()
            self.messageLog.emit("Indexing mods...")
            indices = []
            mod_archives = []
            for mod in self.profile_handler.get_active_mods():
                try:
                    archive_data, index = self.index(mod, filetypes)
                    mod_archives.append(archive_data)
                    indices.append(index)
                except Exception as e:
                    raise IndexException(e.__str__(), mod.name) from e
                
            self.messageLog.emit(f"Indexed ({len(indices)}) active mods.")
            if len(indices) == 0:
                raise Exception("No mods activated.")
            
            self.messageLog.emit("Checking cache...")
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
                all_hashes = {**mod_hashes}

            all_used_archives = set()
            for archive_data in mod_archives:
                all_used_archives.update(set(archive_data.values()))
            all_used_archives = sorted(list(all_used_archives))

            self.emitIndicesAndCache.emit(indices, all_hashes, mod_archives, all_used_archives)
            self.continue_execution.emit()
        except Exception as e:
            self.messageLog.emit(f"The following exception occured when indexing mods: {e}")
            self.releaseGui.emit()
        finally:
            self.finished.emit()
            
class SoftcodeLinker(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self, patch_dir, messageLogFunc, updateMessageLog, lockGuiFunc, releaseGuiFunc):
        super().__init__()
        self.patch_dir = patch_dir
        self.messageLogFunc = messageLogFunc
        self.updateMessageLog = updateMessageLog
        self.lockGuiFunc = lockGuiFunc
        self.releaseGuiFunc = releaseGuiFunc
    
    def run(self):
        try:
            self.lockGuiFunc()
            # Find all files that contribute to the softcode library
            self.messageLogFunc("Indexing patch...")
            softcodable_filetypes = [filetype for filetype in get_filetype_plugins() if getattr(filetype, "enable_softcodes", False)]
            patch_index = generate_mod_index(self.patch_dir, {}, softcodable_filetypes)
            
            # Now find all the softcodes
            # Should run this bit in parallel...
            self.messageLogFunc("Finding softcodes...")
            softcodes = set()
            files_to_update = []
            i = 0
            n_files = sum([len(modfiles) for modfiles in patch_index.values()])
            if len(n_files):
                self.messageLogFunc("")
            for modfiles in patch_index.values():
                for modfile in modfiles:
                    with open(modfile, 'r', encoding="utf-8") as F:
                        i += 1
                        self.updateMessageLog(f"Searching file {i}/{n_files}...")
                        new_codes = search_string_for_softcodes(F.read())
                        softcodes = softcodes.union(new_codes)
                        if len(new_codes):
                            files_to_update.append((modfile, new_codes))
            code_links = construct_softcode_links(softcodes)
            for (filepath, codes) in files_to_update:
                with open(filepath, 'r', encoding="utf-8") as F:
                    data = F.read()
                for code in codes:
                    data = data.replace(code, code_links[code])
                with open(filepath, 'w', encoding="utf-8") as F:
                    F.write(data)
            
            self.finished.emit()
        except Exception as e:
            self.messageLogFunc(f"The following exception occured when linking softcodes: {e}")
            self.releaseGuiFunc()
            

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
            self.runner.lockGui.connect(self.lockGuiFunc)
            self.runner.run()
        except Exception as e:
            self.messageLogFunc.emit(f"The following exception occured when packing mod files: {e}")
            self.releaseGui.emit()
            

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
                self.dscstools_handler.unpack_mvgl_plain(os.path.join(origin, archive + ".steam.mvgl"),
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
                          'bgm': 'ExtraMusic',
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
                    unpackers[archive](archive, origin, self.resources_loc, remove_input=False)
                
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
            self.finished.emit()
            self.releaseGui.emit()

    
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
                            
def make_blank_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as F:
        F.write("")

def make_blank_mbe(path, modpath):
    with open(modpath, 'r') as F:
        header = F.readline()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as F:
        F.write(header)


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
        try:
            indices = self.indices
            game_resources_loc = self.game_resources_loc
            resources_loc = self.resources_loc
            backups_loc = self.backups_loc
            dscstools_handler = self.dscstools_handler
            threadpool = self.threadpool
            messageLog = self.messageLog
            updateMessageLog = self.updateMessageLog
            lockGui = self.lockGui
            releaseGui = self.releaseGui
            
            gfd = dscstools_handler.generate_file_dumper
                
            missing_scripts = []
            new_scripts = []
            missing_mbes = []
            new_mbes = []
            with open(os.path.join("config", "filelist.json"), 'r') as F:
                filelist = json.load(F)
            for index in indices:
                if 'script_src' in index:
                    for script in index['script_src'].keys():
                        internal_path = os.path.join(*splitpath(script)[3:])
                        if not os.path.exists(os.path.join(resources_loc, 'base_scripts', internal_path)):
                            if internal_path[:-3] + "nut" in filelist:
                                missing_scripts.append(internal_path)
                            else:
                                new_scripts.append(internal_path)
                if 'mbe' in index:
                    for mbe in index['mbe'].keys():
                        internal_path = os.path.join(*splitpath(mbe)[3:])
                        if not os.path.exists(os.path.join(resources_loc, 'base_mbes', internal_path)):
                            if os.path.dirname(internal_path) in filelist:
                                missing_mbes.append(internal_path)
                            else:
                                new_mbes.append([internal_path, mbe])
                
            archive_origins = {archive: backup_ifdef(archive, game_resources_loc, backups_loc)
                               for archive in ['DSDB', 'DSDBA', 'DSDBS', 'DSDBSP', 'DSDBP']}
            # Strip out the individual tables and get the packed MBE archives they belong to
            missing_mbes = sorted(list(set([os.path.split(mbe_path)[0] for mbe_path in missing_mbes])))
            nmbes = len(missing_mbes)
            os.makedirs(os.path.join(resources_loc, 'base_mbes', 'data'), exist_ok=True)
            os.makedirs(os.path.join(resources_loc, 'base_mbes', 'message'), exist_ok=True)
            os.makedirs(os.path.join(resources_loc, 'base_mbes', 'text'), exist_ok=True)
            if nmbes:
                messageLog(f"Fetching {nmbes} missing mbes...")
                missing_mbe_paths = {mbe_path: os.path.join(archive_origins[filelist[mbe_path]], filelist[mbe_path] + '.steam.mvgl') for mbe_path in missing_mbes}
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
                
            for mbe_path, mod_mbe_path in new_mbes:
                make_blank_mbe(os.path.join(resources_loc, "base_mbes", mbe_path), mod_mbe_path)
            for script_path in new_scripts:
                make_blank_file(os.path.join(resources_loc, "base_scripts", script_path))
    
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
        except Exception as e:
            self.messageLog(f"An error occurred when collecting base resources: {e}")
            self.releaseGui()
    
