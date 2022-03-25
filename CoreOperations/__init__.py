import os
import shutil
import gc

from PyQt5 import QtCore, QtWidgets
from PyQt5 import QtCore, QtGui, QtWidgets

from CoreOperations.BackupsManager import BackupsManager
from CoreOperations.ConfigManager import ConfigManager
from CoreOperations.PathManager import PathManager
from CoreOperations.ProcLauncher import ProcLauncher
from CoreOperations.ProfileManager import ProfileManager
from CoreOperations.ModInstallation import ModInstaller
from CoreOperations.ModRegistry import ModRegistry
from CoreOperations.SoftcodeManager import SoftcodeManager
from CoreOperations.Tools.DSCSToolsHandler import DSCSToolsHandler
from CoreOperations.Tools.VGAudioHandler import VGAudioHandler
from sdmmlib.dscstools import DSCSTools
from Utils.Threading import ThreadRunner, UIAccessThreadRunner

translate = QtCore.QCoreApplication.translate

class CoreOperations:
    def __init__(self, main_window):
        self.init = False
        self.__worker = None
        
        self.main_window = main_window
        
        self.backups_manager = BackupsManager()
        self.config_manager = ConfigManager(self.main_window.ui)
        self.paths = PathManager(main_window.directory, self.config_manager)
        self.profile_manager = ProfileManager(main_window.ui, self.paths)
        self.profile_manager.init_profiles()
        self.softcode_manager = SoftcodeManager(self.paths)
        self.mod_registry = ModRegistry(main_window.ui, self.paths, self.profile_manager, self.main_window.raise_exception.emit)
        self.dscstools = DSCSToolsHandler()
        self.vgaudio = VGAudioHandler(self.paths.mm_root)

    def __dispose_workers(self):
        self.__worker = None
        gc.collect()

    def install_mods(self):
        self.profile_manager.save_profile()
        if not self.check_for_game_resources(): return
        self.__worker = ModInstaller(self.main_window.ui, self, self.main_window.threadpool, parent=self.main_window, )
        self.__worker.install()
        self.__worker.exiting.connect(self.__dispose_workers)

    def uninstall_mods(self):
        if not self.check_for_game_resources(): return
        self.main_window.ui.log(translate("CoreOps::UninstallMods", "Removing modded files..."))
        shutil.copytree(self.paths.backups_loc, self.paths.game_resources_loc, dirs_exist_ok=True)
        plugins_path = self.paths.game_plugins_loc
        error_msg = translate("CoreOps::UninstallMods", "Something is horribly wrong with the plugins path: {plugins_path}").format(plugins_path=plugins_path)
        assert len(plugins_path) > 7, error_msg
        assert len(os.path.split(plugins_path)[0]) > 5, error_msg
        if os.path.isdir(plugins_path):
            for file in os.listdir(plugins_path):
                os.remove(os.path.join(plugins_path, file))
        self.main_window.ui.log(translate("CoreOps::UninstallMods", "Vanilla files restored, plugins removed."))

    def register_mod_filedialog(self):
        """
        Opens a file dialog and passes the path on to register_mod.
        """
        file = QtWidgets.QFileDialog.getOpenFileUrl(self.main_window, translate("CoreOps::AddMod", "Select a mod archive"), filter="Zip Files (*.zip)")[0].toLocalFile()
        if file != '' and file != '.':
            self.mod_registry.register_mod(file)
    
    def launch_game(self):
        if not self.check_for_game_exe(): return
        self.main_window.ui.log(translate("CoreOps::GameLaunch", "Launching game..."))
        self.__worker = ProcLauncher(self, self.main_window.ui, parent=self.main_window)
        self.__worker.launch_game()
        self.__worker.exiting.connect(self.__dispose_workers)
        self.main_window.block.emit()
    
    def purge_indices(self):
        self.main_window.ui.log(translate("CoreOps::PurgeModIndices", "Purging mod indices..."))
        def workfunc(log, updateLog, enable_gui):
            if not os.path.isdir(self.paths.mods_loc):
                updateLog.emit(translate("CoreOps::PurgeModIndices", "Purging mod indices... no mods folder detected."))
            else:
                n_purged = 0
                for modfolder in os.listdir(self.paths.mods_loc):
                    index_file = os.path.join(self.paths.mods_loc, modfolder, self.paths.index_file_name)
                    if os.path.isfile(index_file):
                        os.remove(index_file)
                        n_purged += 1
                if n_purged:
                    updateLog.emit(translate("CoreOps::PurgeModIndices", "Purging mod indices... purge complete."))
                else:
                    updateLog.emit(translate("CoreOps::PurgeModIndices", "Purging mod indices... no indices found."))
            enable_gui.emit()
                    
        thrd = UIAccessThreadRunner(self.main_window)
        self.main_window.ui.disable_gui()
        thrd.runInThread(self.main_window.ui, self.main_window, lambda : None, workfunc)

                
    def purge_cache(self):
        self.main_window.ui.log(translate("CoreOps::PurgeCache", "Purging cache..."))
        
        def workfunc(log, updateLog, enable_gui):
            removed_index = False
            removed_cache = False
            if os.path.isfile(self.paths.patch_cache_index_loc):
                os.remove(self.paths.patch_cache_index_loc)
                removed_index = True
            if os.path.isdir(self.paths.patch_cache_loc):
                shutil.rmtree(self.paths.patch_cache_loc)
                removed_cache = True
                
            if removed_cache and removed_index:
                updateLog.emit(translate("CoreOps::PurgeCache", "Purging cache... purge complete."))
            elif removed_cache and not removed_index:
                updateLog.emit(translate("CoreOps::PurgeCache", "Purging cache... cached files purged, no index found."))
            elif not removed_cache and removed_index:
                updateLog.emit(translate("CoreOps::PurgeCache", "Purging cache... index purged, no cached files found."))
            else:
                updateLog.emit(translate("CoreOps::PurgeCache", "Purging cache... cache is already empty."))
            enable_gui.emit()
            
        thrd = UIAccessThreadRunner(self.main_window)
        self.main_window.ui.disable_gui()
        thrd.runInThread(self.main_window.ui, self.main_window, lambda : None, workfunc)

                
            
    def purge_mm_resources(self):
        self.main_window.ui.log(translate("CoreOps::PurgeCache", "Purging mod manager resources..."))
        
        def workfunc(log, updateLog, enable_gui):
            if os.path.isdir(self.paths.resources_loc):
                shutil.rmtree(self.paths.resources_loc)
                updateLog.emit(translate("CoreOps::PurgeCache", "Purging mod manager resources... purge complete."))
            else:
                updateLog.emit(translate("CoreOps::PurgeCache", "Purging mod manager resources... no resources to purge."))
            enable_gui.emit()
            
        thrd = UIAccessThreadRunner(self.main_window)
        self.main_window.ui.disable_gui()
        thrd.runInThread(self.main_window.ui, self.main_window, lambda : None, workfunc)

    def purge_softcode_cache(self):
        self.main_window.ui.log(translate("CoreOps::PurgeSoftcodeCache", "Purging softcode cache..."))
        res = QtWidgets.QMessageBox.warning(self.main_window, 
                                            translate("CoreOps::PurgeSoftcodeCache", 'Attempting to delete softcode cache'), 
                                            translate("CoreOps::PurgeSoftcodeCache", "Warning: you are attemtping to clear your softcode cache.<br><br><b>Do not proceed unless you know exactly what you are doing.</b><br><br>This action is virtually guaranteed to break any existing savegames that use mods with softcodes. Do not proceed unless you have a very good reason."), 
                                            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        if res == QtWidgets.QMessageBox.Ok:
            def workfunc(log, updateLog, enable_gui):
                if os.path.isdir(self.paths.softcode_cache_loc):
                    shutil.rmtree(self.paths.softcode_cache_loc)
                    os.makedirs(self.paths.softcode_cache_loc)
                    updateLog.emit(translate("CoreOps::PurgeCache", "Purging softcode cache... purge complete."))
                else:
                    updateLog.emit(translate("CoreOps::PurgeSoftcodeCache", "Purging softcode cache... softcode cache is already empty."))
                enable_gui.emit()
                
            thrd = UIAccessThreadRunner(self.main_window)
            self.main_window.ui.disable_gui()
            thrd.runInThread(self.main_window.ui, self.main_window, lambda : None, workfunc)
        elif res == QtWidgets.QMessageBox.Cancel:
            self.main_window.ui.updateLog(translate("CoreOps::PurgeSoftcodeCache", "Purging softcode cache... action cancelled by user."))
        else:
            assert 0, translate("CoreOps::PurgeSoftcodeCache", "Something has gone horribly wrong with the softcode warning box!")
    
        
    def setCrashLogMethod(self, i):
        if i == 0:
            func = self.main_window.log_exception
            if self.init: self.main_window.ui.log(translate("CoreOps::ExceptionHandling", "Exception handling changed to \"Log\" mode."))
        if i == 1:
            func = self.main_window.throw_exception
            if self.init: self.main_window.ui.log(translate("CoreOps::ExceptionHandling", "Exception handling changed to \"CTD + Make Crashlog\" mode. Logs will be written to {filepath}.").format(filepath=self.paths.logs_loc))
        self.main_window.rehook_crash_handler(func)
        if self.init: self.config_manager.set_crash_pref(i)
    
    def getBlockMethods(self):
        return [translate("CoreOps::GameLaunchPopup", "Popup"), translate("CoreOps::GameLaunchPopup", "Quit")]
            
    def setBlockMethod(self, i):
        if i == 0:
            func = self.main_window.blocker_window
            if self.init: self.main_window.ui.log(translate("CoreOps::GameLaunchPopup", "Window blocking changed to \"Popup\" mode."))
        if i == 1:
            func = self.main_window.quit_program
            if self.init: self.main_window.ui.log(translate("CoreOps::GameLaunchPopup", "Window blocking changed to \"Quit\" mode."))
        self.main_window.rehook_block_handler(func)
        if self.init: self.config_manager.set_block_pref(i)
    
    def getCrashLogMethods(self):
        return [translate("CoreOps::ExceptionHandling", "UI"), translate("CoreOps::ExceptionHandling", "CTD + Logfile")]
    
    def update_mod_info_window(self, display_info):
        mod = self.profile_manager.mods[display_info[-1]]
        info = [mod.name, mod.filename, mod.author, mod.version, mod.description]
        info = [translate("UI::ModInfo::UnknownSelection", "[Unknown]") if item == '-' else item for item in info]
        self.main_window.ui.set_mod_info(*info)
    
    def logThreadedOperationComplete(self, msg):
        self.main_window.ui.updateLog(msg)
        self.main_window.ui.enable_gui()
    
    def locate_game_resources_folder_loop(self):
        location = None
        while (location is None or not os.path.isdir(location)):
            if location is None:
                res = QtWidgets.QMessageBox.question(self.main_window, 
                                                     translate("CoreOps::PathFinding", 'Game not found'), 
                                                    translate("CoreOps::PathFinding", "Game resources were not found. Please select the game resources folder."), 
                                                    QtWidgets.QMessageBox.Ok)
            else:
                res = QtWidgets.QMessageBox.question(self.main_window, 
                                                     translate("CoreOps::PathFinding", 'Game not found'), 
                                                     translate("CoreOps::PathFinding", "Game resources were not found in the location {filepath}. Please select the game resources folder.").format(filepath=location), 
                                                     QtWidgets.QMessageBox.Ok)

            
            origin = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self.main_window, translate("CoreOps::PathFinding", "Select your game location:")))
            
            if origin == "." or origin == "":
                return None
            
            path_stem, path_folder = os.path.split(origin)
            # Check if the resources folder was selected
            if path_folder == "resources":
                if os.path.exists(os.path.join(origin, "DSDB.steam.mvgl")):
                    location = origin
            elif path_folder == "app_digister":
                res_folder = os.path.join(path_stem, "resources")
                if os.path.exists(os.path.join(res_folder, "DSDB.steam.mvgl")):
                    location = res_folder
            elif os.path.exists(os.path.join(origin, "resources")):
                if os.path.exists(os.path.join(origin, "resources", "DSDB.steam.mvgl")):
                    location = os.path.join(origin, "resources")
            
        self.main_window.ui.game_location_textbox.setText(os.path.split(location)[0])
        return location
        
    def check_for_game_resources(self):
        if not self.paths.game_resources_loc_is_valid():
            res = self.locate_game_resources_folder_loop()
            if res is None:
                return False
            else:
                self.config_manager.set_game_loc(os.path.split(res)[0])
                return True
        return True
    
        
    def check_for_game_exe(self):
        if not self.paths.game_executable_loc_is_valid():
            res = self.locate_game_resources_folder_loop()
            if res is None:
                return False
            else:
                self.config_manager.set_game_loc(os.path.split(res)[0])
                return True
        return True
    
    def change_game_location(self):
        game_loc = self.paths.game_loc
        res = self.locate_game_resources_folder_loop()
        if res is not None:
            game_loc = os.path.split(res)[0]
        self.config_manager.set_game_loc(game_loc)
    
    ################
    # MDB1 DUMPING #
    ################
    def create_MDB1_dump_method(self, archive):
        def retfunc():
            if not self.check_for_game_resources(): return
            self.extract_MDB1_from_archive(archive)
        return retfunc
    
    def extract_MDB1_from_archive(self, archive):
        archive_path = os.path.join(self.paths.game_resources_loc, f"{archive}.steam.mvgl")
        archive_path = self.backups_manager.get_backed_up_filepath_if_exists(archive_path, self.paths.game_resources_loc, self.paths.backups_loc)
        self.extract_MDB1_from(archive_path, extract_contents=True)
        
    def extract_MDB1_from(self, archive_path, extract_contents):
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Asking for output path..."))
        extract_path = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self.main_window, translate("Common", "Select a folder to unpack to:")))
        if (extract_path == '' or extract_path == '.') or not os.path.isdir(extract_path):
            self.main_window.ui.log(translate("CoreOps::LogMessage", "Operation cancelled."))
            return
        
        mdb1_ex = self.dscstools.generateMDB1Extractor(self.main_window.threadpool, self, archive_path, extract_path, parent=self.main_window)
        mdb1_ex.raise_exception.connect(self.main_window.raise_exception)
        mdb1_ex.log.connect(self.main_window.ui.log)
        mdb1_ex.updateLog.connect(self.main_window.ui.updateLog)
        mdb1_ex.raise_exception.connect(self.main_window.ui.enable_gui)
        
        archive_dir = (os.path.split(archive_path)[1]).split('.')[0]
        
        data_mbe_ex = self.make_MBE_extractor(os.path.join(extract_path, archive_dir, "data"))
        msg_mbe_ex = self.make_MBE_extractor(os.path.join(extract_path, archive_dir, "message"))
        txt_mbe_ex = self.make_MBE_extractor(os.path.join(extract_path, archive_dir, "text"))
        script_ex = self.make_script_extractor(os.path.join(extract_path, archive_dir, "script64"))
        
        mdb1_ex.success.connect(data_mbe_ex.execute)
        data_mbe_ex.success.connect(msg_mbe_ex.execute)
        msg_mbe_ex.success.connect(txt_mbe_ex.execute)
        txt_mbe_ex.success.connect(script_ex.execute)
        
        script_ex.success.connect(lambda: self.main_window.ui.log(translate("CoreOps::LogMessage", "Extraction complete.")))
        script_ex.finished.connect(self.main_window.ui.enable_gui)
        
        self.main_window.ui.disable_gui()
        mdb1_ex.execute()
        
    def extract_MDB1(self):
        self.main_window.ui.log("Asking for input path...")
        archive_path = os.path.normpath(QtWidgets.QFileDialog.getOpenFileName(self.main_window, translate("Common", "Select an MDB1 archive:"))[0])
        if (archive_path == '' or archive_path == '.') or not os.path.isfile(archive_path):
            self.main_window.ui.log("Operation cancelled.")
            return
        
        self.extract_MDB1_from(archive_path, extract_contents=False)

    def pack_MDB1(self):
        self.main_window.ui.log("Asking for input path...")
        archive_path = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self.main_window, translate("Common", "Select an unpacked MDB1 archive:")))
        if (archive_path == '' or archive_path == '.') or not os.path.isdir(archive_path):
            self.main_window.ui.log("Operation cancelled.")
            return
        
        thrd = ThreadRunner(self.main_window)
        dst = archive_path + ".steam.mvgl"
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Packing MDB1 to {filepath}...").format(filepath=dst))
        self.main_window.ui.disable_gui()
        thrd.runInThread(self.main_window, lambda : self.logThreadedOperationComplete(translate("CoreOps::LogMessage", "Packing MDB1 to {filepath}... MDB1 packed.").format(filepath=dst)), DSCSTools.packMDB1, archive_path, dst, DSCSTools.CompressMode.normal, False)


    ################
    # AFS2 DUMPING #
    ################
    def create_AFS2_dump_method(self, archive):
        def retfunc():
            if not self.check_for_game_resources(): return
            self.extract_AFS2_from_archive(archive)
        return retfunc
    
    def extract_AFS2_from_archive(self, archive):
        archive_path = os.path.join(self.paths.game_resources_loc, f"{archive}.steam.mvgl")
        archive_path = self.backups_manager.get_backed_up_filepath_if_exists(archive_path, self.paths.game_resources_loc, self.paths.backups_loc)
        self.extract_AFS2_from(archive_path)
        
    def extract_AFS2_from(self, archive_path):
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Asking for output path..."))
        extract_path = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self.main_window, translate("Common", "Select a folder to unpack to:")))
        if (extract_path == '' or extract_path == '.') or not os.path.isdir(extract_path):
            self.main_window.ui.log(translate("CoreOps::LogMessage", "Operation cancelled."))
            return

        extract_path = os.path.join(extract_path, os.path.split(archive_path)[1])
        thrd = ThreadRunner(self.main_window)
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Unpacking AFS2 to {filepath}...").format(filepath=extract_path))
        self.main_window.ui.disable_gui()
        thrd.runInThread(self.main_window, lambda : self.logThreadedOperationComplete(translate("CoreOps::LogMessage", "Extracting AFS2 to {filepath}... AFS2 extracted.").format(filepath=extract_path)), DSCSTools.extractAFS2, archive_path, extract_path)
    
        
    def extract_AFS2(self):
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Asking for input path..."))
        archive_path = os.path.normpath(QtWidgets.QFileDialog.getOpenFileName(self.main_window, translate("Common", "Select an AFS2 archive:"))[0])
        if (archive_path == '' or archive_path == '.') or not os.path.isfile(archive_path):
            self.main_window.ui.log(translate("CoreOps::LogMessage", "Operation cancelled."))
            return
        
        self.extract_AFS2_from(archive_path)

    def pack_AFS2(self):
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Asking for input path..."))
        archive_path = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self.main_window, translate("Common", "Select an unpacked AFS2 archive:")))
        if (archive_path == '' or archive_path == '.') or not os.path.isfile(archive_path):
            self.main_window.ui.log(translate("CoreOps::LogMessage", "Operation cancelled."))
            return
        
        thrd = ThreadRunner(self.main_window)
        dst = archive_path + ".steam.mvgl"
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Packing AFS2 to {filepath}...").format(filepath=dst))
        self.main_window.ui.disable_gui()
        thrd.runInThread(self.main_window, lambda : self.logThreadedOperationComplete(translate("CoreOps::LogMessage", "Packing AFS2 to {filepath}... AFS2 packed.").format(filepath=dst)), DSCSTools.packAFS2, archive_path, dst)

    ###############
    # MBE DUMPING #
    ###############
    def make_MBE_extractor(self, mbe_folder):
        mbe_ex = self.dscstools.generateMBEExtractor(self.main_window.threadpool, self, mbe_folder, parent=self.main_window)
        mbe_ex.raise_exception.connect(self.main_window.raise_exception)
        mbe_ex.log.connect(self.main_window.ui.log)
        mbe_ex.updateLog.connect(self.main_window.ui.updateLog)
        mbe_ex.raise_exception.connect(self.main_window.ui.enable_gui)
        
        return mbe_ex       
    
    def extract_MBEs_from(self, mbe_folder):
        mbe_ex = self.make_MBE_extractor(mbe_folder)
        mbe_ex.finished.connect(self.main_window.ui.enable_gui)
        self.main_window.ui.disable_gui()
        mbe_ex.execute()

    def extract_MBEs(self):
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Asking for input path..."))
        mbes_path = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self.main_window, translate("Common", "Select a folder containing packed MBEs:")))
        if (mbes_path == '' or mbes_path == '.') or not os.path.isdir(mbes_path):
            self.main_window.ui.log(translate("CoreOps::LogMessage", "Operation cancelled."))
            return
        
        self.extract_MBEs_from(mbes_path)
        
    def pack_MBEs_from(self, mbe_folder):            
        mbe_pk = self.dscstools.generateMBEPacker(self.main_window.threadpool, self, mbe_folder, parent=self.main_window)
        mbe_pk.raise_exception.connect(self.main_window.raise_exception)
        mbe_pk.log.connect(self.main_window.ui.log)
        mbe_pk.updateLog.connect(self.main_window.ui.updateLog)
        mbe_pk.finished.connect(self.main_window.ui.enable_gui)
        
        self.main_window.ui.disable_gui()
        mbe_pk.execute()

    def pack_MBEs(self):
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Asking for input path..."))
        mbes_path = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self.main_window, translate("Common", "Select a folder containing unpacked MBEs:")))
        if (mbes_path == '' or mbes_path == '.') or not os.path.isdir(mbes_path):
            self.main_window.ui.log(translate("CoreOps::LogMessage", "Operation cancelled."))
            return
        
        self.pack_MBEs_from(mbes_path)
        
    ##################
    # SCRIPT DUMPING #
    ##################
    def make_script_extractor(self, script_folder):
        script_ex = self.dscstools.generateScriptExtractor(self.main_window.threadpool, self, script_folder, parent=self.main_window)
        script_ex.raise_exception.connect(self.main_window.raise_exception)
        script_ex.log.connect(self.main_window.ui.log)
        script_ex.updateLog.connect(self.main_window.ui.updateLog)
        script_ex.raise_exception.connect(self.main_window.ui.enable_gui)
        
        return script_ex       
    
    def extract_scripts_from(self, script_folder):
        script_ex = self.make_script_extractor(script_folder)
        script_ex.finished.connect(self.main_window.ui.enable_gui)
        self.main_window.ui.disable_gui()
        script_ex.execute()

    def extract_scripts(self):
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Asking for input path..."))
        script_folder = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self.main_window, translate("Common", "Select a folder containing compiled scripts:")))
        if (script_folder == '' or script_folder == '.') or not os.path.isdir(script_folder):
            self.main_window.ui.log(translate("CoreOps::LogMessage", "Operation cancelled."))
            return
        
        self.extract_scripts_from(script_folder)
        
    def pack_scripts_from(self, script_folder):            
        script_pk = self.dscstools.generateScriptPacker(self.main_window.threadpool, self, script_folder, parent=self.main_window)
        script_pk.raise_exception.connect(self.main_window.raise_exception)
        script_pk.log.connect(self.main_window.ui.log)
        script_pk.updateLog.connect(self.main_window.ui.updateLog)
        script_pk.finished.connect(self.main_window.ui.enable_gui)
        
        self.main_window.ui.disable_gui()
        script_pk.execute()

    def pack_scripts(self):
        self.main_window.ui.log(translate("CoreOps::LogMessage", "Asking for input path..."))
        script_folder = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self.main_window, translate("Common", "Select a folder containing script source codes:")))
        if (script_folder == '' or script_folder == '.') or not os.path.isdir(script_folder):
            self.main_window.ui.log(translate("CoreOps::LogMessage", "Operation cancelled."))
            return
        
        self.pack_scripts_from(script_folder)
        