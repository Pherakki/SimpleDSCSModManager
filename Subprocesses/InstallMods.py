import json
import os
import shutil
import time

from PyQt5 import QtCore 

from ModFiles.Indexing import generate_mod_index
from ModFiles.PatchGen import generate_patch
from ModFiles.PatchGenMultithreaded import generate_patch_mt
from Utils.MBE import mbe_batch_pack, mbe_batch_unpack
from Utils.Path import splitpath


class InstallModsWorkerThread(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    updateMessageLog = QtCore.pyqtSignal(str)
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()
    
    def __init__(self, output_loc, resources_loc, game_resources_loc,  backups_loc,
                 profile_handler, dscstools_handler, script_handler, parent=None):
        super().__init__(parent)
        self.output_loc = output_loc
        self.resources_loc = resources_loc
        self.game_resources_loc = game_resources_loc
        self.backups_loc = backups_loc
        self.profile_handler = profile_handler
        self.dscstools_handler = dscstools_handler
        self.script_handler = script_handler
        
    def run(self):
        try:
            self.lockGui.emit()
            self.messageLog.emit("Preparing to patch mods together...")
            patch_dir = os.path.relpath(os.path.join(self.output_loc, 'patch'))
            dbdsp_dir = os.path.relpath(os.path.join(self.output_loc, 'DSDBP'))
            mvgl_loc = os.path.join(self.output_loc, 'DSDBP.steam.mvgl')
            decrypt_loc = os.path.join(self.output_loc, 'DSDBP_decrypted')
            if os.path.exists(patch_dir):
                shutil.rmtree(patch_dir)
            if os.path.exists(dbdsp_dir):
                shutil.rmtree(dbdsp_dir)
            if os.path.exists(mvgl_loc):
                os.remove(mvgl_loc)
            if os.path.exists(decrypt_loc):
                os.remove(decrypt_loc)
                
            # Do this on mod registry...
            self.messageLog.emit("Indexing mods...")
            indices = []
            for mod in self.profile_handler.get_active_mods():
                modfiles_path = os.path.relpath(os.path.join(mod.path, "modfiles"))
                indices.append(generate_mod_index(modfiles_path, {}))
            self.messageLog.emit(f"Indexed ({len(indices)}) active mods.")
            if len(indices) == 0:
                raise Exception("No mods activated.")
            bootstrap_index_resources(indices, self.game_resources_loc, self.resources_loc, 
                                      self.backups_loc,
                                      self.dscstools_handler, self.script_handler,
                                      self.messageLog.emit, self.updateMessageLog.emit)
            self.messageLog.emit("Generating patch...")
            generate_patch(indices, patch_dir, self.resources_loc)
            
            # Pack each mbe
            mbe_batch_pack(patch_dir, self.dscstools_handler, self.messageLog.emit, self.updateMessageLog.emit)
            script_loc = os.path.join(patch_dir, "script64")
            scripts = os.listdir(script_loc)
            nscripts = len(scripts)
            if nscripts:
                self.messageLog.emit("")
                for i, script in enumerate(scripts):
                    self.updateMessageLog.emit(f"Compiling script {i+1}/{nscripts} [{script}]")
                    self.script_handler.compile_script(script, 
                                                       os.path.abspath(script_loc), 
                                                       os.path.abspath(script_loc), remove_input=True)
            self.messageLog.emit("Generating patched MVGL archive (this may take a few minutes)...")
        
            dsdbp_resource_loc = os.path.join(self.resources_loc, 'DSDBP')
            if not os.path.exists(dsdbp_resource_loc):
                self.messageLog.emit("Base DSDBP archive not found, generating...")
                origin = backup_ifdef('DSDBP', self.game_resources_loc, self.backups_loc)
                self.dscstools_handler.unpack_mvgl('DSDBP', origin, self.resources_loc)
            shutil.copytree(dsdbp_resource_loc, dbdsp_dir)
            shutil.copytree(patch_dir, dbdsp_dir, dirs_exist_ok=True)
            self.dscstools_handler.pack_mvgl('DSDBP', self.output_loc, self.output_loc, remove_input=False)
            os.rename(os.path.join(self.output_loc, self.dscstools_handler.decrypted_archive_name('DSDBP')),
                      os.path.join(self.output_loc, self.dscstools_handler.base_archive_name('DSDBP')))
            
            self.messageLog.emit("Installing patched archive...")
            # Now here's the important bit
            create_backups(self.game_resources_loc, self.backups_loc, self.messageLog.emit)
            shutil.copy2(mvgl_loc, os.path.join(self.game_resources_loc, 'DSDBP.steam.mvgl'))
            
            self.messageLog.emit("Mods successfully installed.")
            
        except Exception as e:
            self.messageLog.emit(f"The following error occured when trying to install modlist: {e}")
            raise e
        finally:
            self.releaseGui.emit()
            self.finished.emit()
            
            
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
        
        self.worker = None
        self.thread = thread
        self.worker2 = None
        self.thread2 = QtCore.QThread()
        self.worker3 = None
        self.thread3 = QtCore.QThread()
        self.br = None
        
        self.indices = None
        
    def run(self):
        try:
            self.lockGuiFunc()
            self.messageLogFunc("Preparing to patch mods together...")
            patch_dir = os.path.relpath(os.path.join(self.output_loc, 'patch'))
            dbdsp_dir = os.path.relpath(os.path.join(self.output_loc, 'DSDBP'))
            mvgl_loc = os.path.join(self.output_loc, 'DSDBP.steam.mvgl')
            decrypt_loc = os.path.join(self.output_loc, 'DSDBP_decrypted')
            if os.path.exists(patch_dir):
                shutil.rmtree(patch_dir)
            if os.path.exists(dbdsp_dir):
                shutil.rmtree(dbdsp_dir)
            if os.path.exists(mvgl_loc):
                os.remove(mvgl_loc)
            if os.path.exists(decrypt_loc):
                os.remove(decrypt_loc)
  
            self.worker = PatchGenerator(patch_dir, self.output_loc, self.game_resources_loc,
                                         self.resources_loc, self.backups_loc,
                                         self.dscstools_handler, self.script_handler, self.profile_handler)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.messageLog.connect(self.messageLogFunc)
            self.worker.updateMessageLog.connect(self.updateMessageLogFunc)
            self.worker.lockGui.connect(self.lockGuiFunc)
            self.worker.releaseGui.connect(self.releaseGuiFunc)

            # self.patchgen_worker = generate_patch_mt(patch_dir, self.resources_loc, self.threadpool, self.messageLogFunc)
            
            # def relay_indices(lst):
            #     self.patchgen_worker.indices = lst
            
            # self.worker.emitIndices.connect(relay_indices)
            
            self.br = multithreaded_bootstrap_index_resources(None, self.game_resources_loc, 
                                                              self.resources_loc, self.backups_loc,
                                                              self.dscstools_handler, self.script_handler,
                                                              self.threadpool,
                                                              self.messageLogFunc, self.updateMessageLogFunc,
                                                              self.lockGuiFunc, self.releaseGuiFunc)
            self.worker3 = PatchGenerator2(patch_dir, self.output_loc, self.game_resources_loc,
                                         self.resources_loc, self.backups_loc,
                                         self.dscstools_handler, self.script_handler, self.profile_handler)
            self.worker3.moveToThread(self.thread3)
            self.thread3.started.connect(self.worker3.run)
            self.worker3.finished.connect(self.thread3.quit)
            self.worker3.finished.connect(self.worker3.deleteLater)
            self.thread3.finished.connect(self.thread3.deleteLater)
            self.worker3.messageLog.connect(self.messageLogFunc)
            self.worker3.updateMessageLog.connect(self.updateMessageLogFunc)
            self.worker3.lockGui.connect(self.lockGuiFunc)
            self.worker3.releaseGui.connect(self.releaseGuiFunc)
             
            def relay_indices(lst):
                print("RELAYING INDICES")
                self.br.indices = lst
                self.worker3.indices = lst
            self.worker.emitIndices.connect(relay_indices)
             
                
            # Pack the resources              
            gmp = self.dscstools_handler.generate_mbe_packer
            self.datmbe_worker = gmp(os.path.join(patch_dir, 'data'), 
                                     os.path.join(patch_dir, 'data'),
                                     self.threadpool,
                                     self.messageLogFunc, self.updateMessageLogFunc, 
                                     self.lockGuiFunc, self.releaseGuiFunc)
            self.msgmbe_worker = gmp(os.path.join(patch_dir, 'message'), 
                                     os.path.join(patch_dir, 'message'), 
                                     self.threadpool,
                                     self.messageLogFunc, self.updateMessageLogFunc, 
                                     self.lockGuiFunc, self.releaseGuiFunc)
            self.texmbe_worker = gmp(os.path.join(patch_dir, 'text'), 
                                     os.path.join(patch_dir, 'text'),
                                     self.threadpool,
                                     self.messageLogFunc, self.updateMessageLogFunc, 
                                     self.lockGuiFunc, self.releaseGuiFunc)
            gsc = self.script_handler.generate_script_compiler
            script_worker = gsc(os.path.abspath(os.path.join(patch_dir, 'script64')), 
                                os.path.abspath(os.path.join(patch_dir, 'script64')),
                                self.threadpool,
                                self.lockGuiFunc, self.releaseGuiFunc,
                                self.messageLogFunc, self.updateMessageLogFunc,
                                remove_input=True)

            self.worker2 = FinaliseInstallation(dbdsp_dir, patch_dir, mvgl_loc, self.output_loc, self.resources_loc,
                                                self.game_resources_loc, self.backups_loc, self.dscstools_handler)
            self.worker2.moveToThread(self.thread2)
            self.thread2.started.connect(self.worker2.run)
            self.worker2.finished.connect(self.thread2.quit)
            self.worker2.finished.connect(self.worker2.deleteLater)
            self.thread2.finished.connect(self.thread2.deleteLater)
            self.worker2.messageLog.connect(self.messageLogFunc)
            self.worker2.updateMessageLog.connect(self.updateMessageLogFunc)
            self.worker2.lockGui.connect(self.lockGuiFunc)
            self.worker2.releaseGui.connect(self.releaseGuiFunc)

            self.worker.continue_execution.connect(self.datmbe_worker.run)
            # self.worker.continue_execution.connect(self.patchgen_worker.run)
            # self.patchgen_worker.finished.connect(lambda: datmbe_worker.run())
            self.datmbe_worker.finished.connect(lambda: msgmbe_worker.run())
            msgmbe_worker.finished.connect(lambda: texmbe_worker.run())
            texmbe_worker.finished.connect(lambda: script_worker.run())
            script_worker.finished.connect(lambda: self.thread2.start())
            
            self.worker2.finished.connect(self.finished.emit)

            self.thread.start()

        except Exception as e:
            self.messageLogFunc(f"The following error occured when trying to install modlist: {e}")
            raise e



class PatchGenerator(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    continue_execution = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    updateMessageLog = QtCore.pyqtSignal(str)
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()
    emitIndices = QtCore.pyqtSignal(list)
    
    def __init__(self, patch_loc, output_loc, game_resources_loc, resources_loc,
                 backups_loc, dscstools_handler, script_handler, profile_handler):
        super().__init__()
        self.patch_dir = patch_loc
        self.output_loc = output_loc
        self.game_resources_loc = game_resources_loc
        self.resources_loc = resources_loc
        self.backups_loc = backups_loc
        self.dscstools_handler = dscstools_handler
        self.script_handler = script_handler
        self.profile_handler = profile_handler
    
    def run(self):
        try:
            # Do this on mod registry...
            self.messageLog.emit("Indexing mods...")
            indices = []
            for mod in self.profile_handler.get_active_mods():
                modfiles_path = os.path.relpath(os.path.join(mod.path, "modfiles"))
                indices.append(generate_mod_index(modfiles_path, {}))
            self.messageLog.emit(f"Indexed ({len(indices)}) active mods.")
            if len(indices) == 0:
                raise Exception("No mods activated.")
            
            self.emitIndices.emit(indices)
            self.continue_execution.emit()
            # return
            # bootstrap_index_resources(indices, self.game_resources_loc, self.resources_loc, 
            #                           self.backups_loc,
            #                           self.dscstools_handler, self.script_handler,
            #                           self.messageLog.emit, self.updateMessageLog.emit)
            # self.emitIndices.emit(indices)
            # self.messageLog.emit("Generating patch...")
            # generate_patch(indices, self.patch_dir, self.resources_loc)
            # self.continue_execution.emit()
        except Exception as e:
            raise e
        finally:
            self.releaseGui.emit()
            self.finished.emit()
            
            
class PatchGenerator2(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    continue_execution = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    updateMessageLog = QtCore.pyqtSignal(str)
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()
    emitIndices = QtCore.pyqtSignal(list)
    
    def __init__(self, patch_loc, output_loc, game_resources_loc, resources_loc,
                 backups_loc, dscstools_handler, script_handler, profile_handler):
        super().__init__()
        self.patch_dir = patch_loc
        self.output_loc = output_loc
        self.game_resources_loc = game_resources_loc
        self.resources_loc = resources_loc
        self.backups_loc = backups_loc
        self.dscstools_handler = dscstools_handler
        self.script_handler = script_handler
        self.profile_handler = profile_handler
        self.indices = None
    
    def run(self):
        try:
            self.lockGui.emit()
            self.messageLog.emit("Generating patch...")
            generate_patch(self.indices, self.patch_dir, self.resources_loc)
            self.continue_execution.emit()
        except Exception as e:
            raise e
        finally:
            self.releaseGui.emit()
            self.finished.emit()


class FinaliseInstallation(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    updateMessageLog = QtCore.pyqtSignal(str)
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()

    def __init__(self, dbdsp_dir, patch_dir, mvgl_loc, output_loc, resources_loc, game_resources_loc, backups_loc,
                 dscstools_handler):
        super().__init__()
        self.dbdsp_dir = dbdsp_dir
        self.patch_dir = patch_dir
        self.mvgl_loc = mvgl_loc
        self.output_loc = output_loc
        self.resources_loc = resources_loc
        self.game_resources_loc = game_resources_loc
        self.backups_loc = backups_loc

        self.dscstools_handler = dscstools_handler

    def run(self):
        try:
            self.lockGui.emit()
            self.messageLog.emit("Generating patched MVGL archive (this may take a few minutes)...")

            dsdbp_resource_loc = os.path.join(self.resources_loc, 'DSDBP')
            if not os.path.exists(dsdbp_resource_loc):
                self.messageLog.emit("Base DSDBP archive not found, generating...")
                origin = backup_ifdef('DSDBP', self.game_resources_loc, self.backups_loc)
                self.dscstools_handler.unpack_mvgl_plain(os.path.join(origin, 'DSDBP.steam.mvgl'), 
                                                         os.path.join(self.resources_loc, 'DSDBP'))

            shutil.copytree(dsdbp_resource_loc, self.dbdsp_dir)
            shutil.copytree(self.patch_dir, self.dbdsp_dir, dirs_exist_ok=True)
            self.dscstools_handler.pack_mvgl('DSDBP', self.output_loc, self.output_loc, remove_input=False)
            os.rename(os.path.join(self.output_loc, self.dscstools_handler.decrypted_archive_name('DSDBP')),
                      os.path.join(self.output_loc, self.dscstools_handler.base_archive_name('DSDBP')))

            self.messageLog.emit("Installing patched archive...")
            # Now here's the important bit
            create_backups(self.game_resources_loc, self.backups_loc, self.messageLog.emit)
            shutil.copy2(self.mvgl_loc, os.path.join(self.game_resources_loc, 'DSDBP.steam.mvgl'))

            self.messageLog.emit("Mods successfully installed.")
        except Exception as e:
            self.messageLog.emit(f"The following error occured when trying to install modlist: {e}")
            raise e
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
                            
                            
def bootstrap_index_resources(indices, game_resources_loc, resources_loc, backups_loc,
                              dscstools_handler, script_handler,
                              messageLog, updateMessageLog):
    missing_scripts = []
    missing_mbes = []
    for index in indices:
        for script in index['script_src'].keys():
            internal_path = os.path.join(*splitpath(script)[3:])
            if not os.path.exists(os.path.join(resources_loc, 'base_scripts', internal_path)):
                print(os.path.join(resources_loc, 'base_scripts', internal_path))
                missing_scripts.append(internal_path)
        for mbe in index['mbe'].keys():
            internal_path = os.path.join(*splitpath(mbe)[3:])
            if not os.path.exists(os.path.join(resources_loc, 'base_mbes', internal_path)):
                missing_mbes.append(internal_path)
            
    with open(os.path.join("config", "filelist.json"), 'r') as F:
        filelist = json.load(F)
        
    archive_origins = {archive: backup_ifdef(archive, game_resources_loc, backups_loc)
                       for archive in ['DSDB', 'DSDBA', 'DSDBS', 'DSDBSP', 'DSDBP']}
        
    nmbes = len(missing_mbes)
    if nmbes:
        messageLog(f"Fetching {nmbes} missing mbes...")
        messageLog("")
        os.makedirs(os.path.join(resources_loc, 'base_mbes', 'data'), exist_ok=True)
        os.makedirs(os.path.join(resources_loc, 'base_mbes', 'message'), exist_ok=True)
        os.makedirs(os.path.join(resources_loc, 'base_mbes', 'text'), exist_ok=True)
        temp_resource_datapath = os.path.join(resources_loc, 'base_mbes', 'temp')
        for i, internal_path in enumerate(missing_mbes):
            updateMessageLog(f"Unpacking MBE {i+1}/{nmbes} [{internal_path}]")
            archive = filelist[internal_path]
            dscstools_handler.get_file_from_MDB1(archive + '.steam.mvgl', archive_origins[archive], os.path.join(resources_loc, 'base_mbes'), internal_path)
            
            internal_datapath, mbe = os.path.split(internal_path)
            original_resource_datapath = os.path.join(resources_loc, 'base_mbes', archive + '.steam.mvgl', internal_datapath)
            resource_datapath = os.path.join(resources_loc, 'base_mbes', internal_datapath)
            # Can move this out and do a multithreaded decompile...
            dscstools_handler.extract_mbe(mbe, original_resource_datapath, resource_datapath)
            os.remove(os.path.join(original_resource_datapath, mbe))
    nscripts = len(missing_scripts)
    
    if nscripts:
        messageLog(f"Fetching {nscripts} missing scripts...")
        messageLog("")
        os.makedirs(os.path.join(resources_loc, 'base_scripts', 'script64'), exist_ok=True)
        for i, internal_path in enumerate(missing_scripts):
            internal_path = internal_path[:-3] + 'nut'
            updateMessageLog(f"Unpacking script {i+1}/{nscripts} [{internal_path}]")
            archive = filelist[internal_path]
            dscstools_handler.get_file_from_MDB1(archive + '.steam.mvgl', archive_origins[archive], os.path.join(resources_loc, 'base_scripts'), internal_path)
            
            internal_datapath, script = os.path.split(internal_path)
            original_resource_datapath = os.path.join(resources_loc, 'base_scripts', archive + '.steam.mvgl', internal_datapath)
            resource_datapath = os.path.join(resources_loc, 'base_scripts', internal_datapath)
            # Can move this out and do a multithreaded decompile...
            script_handler.decompile_script(script, original_resource_datapath, resource_datapath, remove_input=True)
            
class multithreaded_bootstrap_index_resources(QtCore.QObject):
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
        print("RUNNING BOOTSTRAP")
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
            for script in index['script_src'].keys():
                internal_path = os.path.join(*splitpath(script)[3:])
                if not os.path.exists(os.path.join(resources_loc, 'base_scripts', internal_path)):
                    print(os.path.join(resources_loc, 'base_scripts', internal_path))
                    missing_scripts.append(internal_path)
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
        