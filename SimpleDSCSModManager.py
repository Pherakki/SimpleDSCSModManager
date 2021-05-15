import json
import os
import shutil
import subprocess
import sys
import webbrowser

from PyQt5 import QtWidgets 
from PyQt5 import QtCore

# https://doc.qt.io/qt-5/qfilesystemwatcher.html

from CodeHandlers.DSCSToolsArchiveWorker import DumpArchiveWorkerThread  # Need to deprecate this
from CodeHandlers.DSCSToolsHandler import DSCSToolsHandler
from CodeHandlers.GenericThreadRunner import GenericThreadRunner
from CodeHandlers.ScriptHandler import ScriptHandler
from ModFiles.Detection import detect_mods, install_mod_in_manager
from Subprocesses.Downloader import DSCSToolsDownloader
from Subprocesses.InstallMods import InstallModsWorker
from ToolHandlers.ProfileHandler import ProfileHandler
from UI.Design import uiMainWidget
from Utils.Exceptions import UnrecognisedModFormatError, ModInstallWizardError, ModInstallWizardCancelled
  
script_loc = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))

patreon_addr = r'https://www.patreon.com/sydmontague'
def open_patreon():
    webbrowser.open_new_tab(patreon_addr)

  
class MainWindow(QtWidgets.QMainWindow): 
    def __init__(self, parent=None): 
        super().__init__(parent)
        
        # Init the UI
        self.window = QtWidgets.QWidget() 
        self.setWindowTitle("SimpleDSCSModManager")
        #self.setWindowIcon(QtGui.QIcon(scriptDir + os.path.sep + 'logo.png'))
        self.setCentralWidget(self.window)
        self.ui = uiMainWidget(self)
        self.window.setLayout(self.ui.layout)
        
        # Set up the directories we're going to need
        self.config_loc = os.path.normpath(os.path.join(script_loc, "config"))
        self.compiler_loc = os.path.normpath(os.path.join(script_loc, "tools", "squirrel"))
        self.dscstools_loc = os.path.normpath(os.path.join(script_loc, "tools", "dscstools"))
        self.nutcracker_loc = os.path.normpath(os.path.join(script_loc, "tools", "nutcracker"))
        self.mods_loc = os.path.normpath(os.path.join(script_loc, "mods"))
        self.output_loc = os.path.normpath(os.path.join(script_loc, "output"))
        self.profiles_loc = os.path.normpath(os.path.join(script_loc, "profiles"))
        self.resources_loc = os.path.normpath(os.path.join(script_loc, "resources"))
        
        os.makedirs(self.config_loc, exist_ok=True)
        os.makedirs(self.compiler_loc, exist_ok=True)
        os.makedirs(self.dscstools_loc, exist_ok=True)
        os.makedirs(self.nutcracker_loc, exist_ok=True)
        os.makedirs(self.mods_loc, exist_ok=True)
        os.makedirs(self.profiles_loc, exist_ok=True)
        os.makedirs(self.resources_loc, exist_ok=True)

        # Set up mod handling variables
        self.mods = []
        self.modpath_to_id = None
        self.modid_to_path = None
        
        # Set up the configuration and handlers
        self.read_config()
        self.script_handler = ScriptHandler(os.path.join(self.nutcracker_loc, 'NutCracker.exe'),
                                            os.path.join(self.compiler_loc, 'sq.exe'))
        self.dscstools_handler = DSCSToolsHandler('', os.path.join(self.dscstools_loc, 'DSCSTools.exe'))
        self.profile_handler = ProfileHandler(self.profiles_loc, self.ui.profile_selector, self.ui.mods_display, self)
        self.check_dscstools()
        
        # Hook the UI
        self.ui.hook_menu(open_patreon)
        self.ui.hook_filemenu(self.register_mod_filedialog)
        self.ui.hook_profle_interaction_widgets(self.profile_handler)
        #self.ui.hook_action_tabs(self.draw_conflicts_graph)
        self.ui.hook_config_tab(self.find_gamelocation_check, self.update_dscstools)
        self.ui.hook_extract_tab(self.mdb1_dump_factory, self.afs2_dump_factory,
                                 self.dscstools_handler,
                                 self.extract_MDB1, self.pack_MDB1,
                                 self.extract_MBEs, self.pack_MBEs,
                                 self.decompile_scripts, self.compile_scripts)
        self.ui.hook_mod_registry(self.register_mod)
        self.ui.hook_install_button(self.install_mods)
        self.ui.hook_game_launch_button(self.launch_game)
        self.ui.hook_delete_mod_menu(self.unregister_mod)
        self.ui.hook_wizard_mod_menu(self.mod_has_wizard, self.reinstall_mod)
        self.ui.hook_update_mod_info_window(self.update_mod_info_window)
        self.ui.hook_backup_button((lambda: restore_backups(self.game_resources_loc, 
                                                            self.backups_loc, self.ui.log)))
        
        # Init the UI data
        self.profile_handler.init_profiles()
        self.threadpool = QtCore.QThreadPool()
        self.update_mods()
        
        self.ui.log("SimpleDSCSModManager initialised.")
        self.ui.loglink(f"""Enjoying Cyber Sleuth modding? Consider supporting more projects like this on <a href="{patreon_addr}">Patreon</a>!""")


    @property
    def game_resources_loc(self):
        return os.path.normpath(os.path.join(self.game_loc, "resources"))
    
    @property
    def game_executable_loc(self):
        return os.path.normpath(os.path.join(self.game_loc, "app_digister", "Digimon Story CS.exe"))

    @property
    def game_loc(self):
        return os.path.normpath(str(self.config['game_loc']))
    
    @property
    def backups_loc(self):
        return os.path.join(self.game_resources_loc, 'backup')
    
    def launch_game(self):
        subprocess.run([self.game_executable_loc], creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.game_loc)

    def update_mod_info_window(self, display_info):
        mod = self.mods[display_info[-1]]
        info = [mod.name, mod.filename, mod.author, mod.version, mod.description]
        info = ['[Unknown]' if item == '-' else item for item in info]
        self.ui.set_mod_info(*info)

    def register_mod(self, mod_path):
        """
        Checks if the file/folder at mod_path is an accepted mod format, and if so,
        copies it into the modmanager 'mods' folder and updates the mod list.
        """
        mod_name = os.path.split(mod_path)[-1]
        try:
            self.ui.log(f"Attempting to register {mod_name}...")
            try:
                install_mod_in_manager(mod_path, self.mods_loc, self.dscstools_handler.unpack_mbe)
                self.ui.log(f"Successfully registered {mod_name}.")
            except ModInstallWizardCancelled:
                self.ui.log(f"Did not install {mod_name}: wizard was cancelled.")
            except ModInstallWizardError as e:
                self.ui.log(f"Installation wizard encountered an error: {e}.")
            except UnrecognisedModFormatError:
                self.ui.log(f"{mod_name} is not in a recognised mod format.")
            except Exception as e:
                raise e
                self.ui.log(f"The mod manager encountered an unhandled error when attempting to install {mod_name}: {e}.")
        except Exception as e:
            shutil.rmtree(os.path.join(self.mods_loc, mod_name))
            self.ui.log(f"The following error occured when trying to register {mod_name}: {e}")
            raise e
        finally:
            self.update_mods()

    def register_mod_filedialog(self):
        """
        Opens a file dialog and passes the path on to register_mod.
        """
        file = QtWidgets.QFileDialog.getOpenFileUrl(self, "Select a mod archive")[0].toLocalFile()
        if file != '' and file != '.':
            self.register_mod(file)

    def unregister_mod(self, index):
        mod_name = os.path.split(self.mods[index].path)[1]
        try:
            shutil.rmtree(self.mods[index].path)
            self.ui.log(f"Removed {mod_name}.")
        except Exception as e:
            self.ui.log(f"The following error occured when trying to delete {mod_name}: {e}")
        finally:
            self.update_mods()

    def install_mods(self):
        self.profile_handler.save_profile()
        self.update_mods()
        self.profile_handler.save_profile()
        self.thread = QtCore.QThread()

        self.worker = InstallModsWorker(self.output_loc, self.resources_loc, self.game_resources_loc,  self.backups_loc,
                                   self.profile_handler, self.dscstools_handler, self.script_handler, self.threadpool,
                                   self.thread)
        self.worker.lockGuiFunc = self.ui.disable_gui
        self.worker.releaseGuiFunc = self.ui.enable_gui
        self.worker.messageLogFunc = self.ui.log
        self.worker.updateMessageLogFunc = self.ui.updateLog
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.worker.run()


    def read_config(self):
        config_file_loc = os.path.join(self.config_loc, "config.json")
        if os.path.exists(config_file_loc):
            with open(config_file_loc, 'r') as F:
                self.config = json.load(F)
        else:
            self.config = {'game_loc': script_loc, 'dscstools_version': None}
            self.write_config()
            
    def write_config(self):
        with open(os.path.join(self.config_loc, "config.json"), 'w') as F:
            json.dump(self.config, F, indent=4)
    
    def mdb1_dump_factory(self, archive):
        def retval():
            if self.check_gamelocation():
                result = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder to export to:"))

                if result == '' or result == '.':
                    return
                backup_filepath = os.path.join(self.backups_loc, self.dscstools_handler.base_archive_name(archive))
                if os.path.exists(backup_filepath):
                    use_loc = self.backups_loc
                else:
                    use_loc = self.game_resources_loc

                gad = self.dscstools_handler.generate_archive_dumper
                worker = gad(os.path.join(use_loc, self.dscstools_handler.base_archive_name(archive)),
                             os.path.join(result, archive), self.threadpool,
                             self.ui.log, self.ui.updateLog, 
                             self.ui.disable_gui, self.ui.enable_gui)
                
                gme = self.dscstools_handler.generate_mbe_extractor
                datmbe_worker = gme(os.path.join(result, archive, 'data'), 
                                    os.path.join(result, archive, 'data'),
                                    self.threadpool,
                                    self.ui.log, self.ui.updateLog, 
                                    self.ui.disable_gui, self.ui.enable_gui)
                msgmbe_worker = gme(os.path.join(result, archive, 'message'), 
                                    os.path.join(result, archive, 'message'), 
                                    self.threadpool,
                                    self.ui.log, self.ui.updateLog, 
                                    self.ui.disable_gui, self.ui.enable_gui)
                texmbe_worker = gme(os.path.join(result, archive, 'text'), 
                                    os.path.join(result, archive, 'text'),
                                    self.threadpool,
                                    self.ui.log, self.ui.updateLog, 
                                    self.ui.disable_gui, self.ui.enable_gui)
                
                gsd = self.script_handler.generate_script_decompiler
                script_worker = gsd(os.path.join(result, archive, 'script64'), 
                                    os.path.join(result, archive, 'script64'), 
                                    self.threadpool, self.ui.disable_gui, self.ui.enable_gui,                   
                                    self.ui.log, self.ui.updateLog, remove_input=True)
                
                worker.finished.connect(lambda: datmbe_worker.run())
                datmbe_worker.finished.connect(lambda: msgmbe_worker.run())
                msgmbe_worker.finished.connect(lambda: texmbe_worker.run())
                texmbe_worker.finished.connect(lambda: script_worker.run())
                script_worker.finished.connect(lambda: self.ui.log(f"Finished extracting {archive}."))

                worker.run()
                
        return retval
    
    def afs2_dump_factory(self, archive):
        def retval():
            if self.check_gamelocation():
                result = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder to export to:"))

                if result == '' or result == '.':
                    return
                backup_filepath = os.path.join(self.backups_loc, f'{archive}.steam.mvgl')
                if os.path.exists(backup_filepath):
                    use_loc = self.backups_loc
                else:
                    use_loc = self.game_resources_loc
                    
                self.thread = QtCore.QThread()
        
                self.worker = DumpArchiveWorkerThread(archive, use_loc, result, self.dscstools_handler, self.dscstools_handler.unpack_afs2)
                self.worker.moveToThread(self.thread)
                self.thread.started.connect(self.worker.run)
                self.worker.finished.connect(self.thread.quit)
                self.worker.finished.connect(self.worker.deleteLater)
                self.thread.finished.connect(self.thread.deleteLater)
                self.worker.messageLog.connect(self.ui.log)
                self.worker.updateMessageLog.connect(self.ui.updateLog)
                self.worker.lockGui.connect(self.ui.disable_gui)
                self.worker.releaseGui.connect(self.ui.enable_gui)
                self.thread.start()
                
        return retval
    
    def extract_MDB1(self):
        input_loc = os.path.normpath(QtWidgets.QFileDialog.getOpenFileName(self, "Select an MDB1 archive:")[0])
        if input_loc == '' or input_loc == '.':
            return
        output_loc = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder to export to:"))
        if output_loc == '' or output_loc == '.':
            return
        
        input_dir, archive = os.path.split(input_loc)
        gad = self.dscstools_handler.generate_archive_dumper
        worker = gad(input_loc, os.path.join(output_loc, archive), self.threadpool,
                     self.ui.log, self.ui.updateLog, self.ui.disable_gui, self.ui.enable_gui)
        worker.run()
        
    def pack_MDB1(self):
        input_loc = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select an unpacked MDB1 archive:"))
        if input_loc == '' or input_loc == '.':
            return
        output_loc = os.path.normpath(QtWidgets.QFileDialog.getSaveFileName(self, "Export to file:")[0])
        if output_loc == '' or output_loc == '.':
            return

        self.thread = QtCore.QThread()
        self.worker = GenericThreadRunner(lambda: self.dscstools_handler.pack_mvgl_plain(input_loc, output_loc, remove_input=False),
                                          f"Packing MDB1 to {output_loc}...",
                                          "packiing MDB1")
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.messageLog.connect(self.ui.log)
        self.worker.updateMessageLog.connect(self.ui.updateLog)
        self.worker.lockGui.connect(self.ui.disable_gui)
        self.worker.releaseGui.connect(self.ui.enable_gui)
        self.thread.start()
    
    def extract_MBEs(self):
        input_loc = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder containing MBEs to unpack:"))
        if input_loc == '' or input_loc == '.':
            return
        output_loc = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder to export to:"))
        if output_loc == '' or output_loc == '.':
            return
        

        gme = self.dscstools_handler.generate_mbe_extractor
        mbe_worker = gme(input_loc,
                         output_loc,
                         self.threadpool,
                         self.ui.log, self.ui.updateLog, 
                         self.ui.disable_gui, self.ui.enable_gui)
        mbe_worker.run()
        
        
    def pack_MBEs(self):
        input_loc = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder containing MBEs to pack:"))
        if input_loc == '' or input_loc == '.':
            return
        output_loc = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder to export to:"))
        if output_loc == '' or output_loc == '.':
            return
        

        gmp = self.dscstools_handler.generate_mbe_packer
        mbe_worker = gmp(input_loc,
                         output_loc,
                         self.threadpool,
                         self.ui.log, self.ui.updateLog, 
                         self.ui.disable_gui, self.ui.enable_gui)
        mbe_worker.run()

    def decompile_scripts(self):
        input_loc = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder containing scripts to be decompiled:"))
        if input_loc == '' or input_loc == '.':
            return
        output_loc = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder to export to:"))
        if output_loc == '' or output_loc == '.':
            return
        gsd = self.script_handler.generate_script_decompiler
        worker = gsd(input_loc, output_loc, self.threadpool,
                  self.ui.disable_gui, self.ui.enable_gui, self.ui.log, self.ui.updateLog)
        worker.run()
        
    def compile_scripts(self):
        input_loc = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder containing scripts to be compiled:"))
        if input_loc == '' or input_loc == '.':
            return
        output_loc = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select a folder to export to:"))
        if output_loc == '' or output_loc == '.':
            return

        gsc = self.script_handler.generate_script_compiler
        worker = gsc(input_loc, output_loc, self.threadpool,
                  self.ui.disable_gui, self.ui.enable_gui, self.ui.log, self.ui.updateLog)
        worker.run()
    
    def update_mods(self):
        try:
            self.mods = detect_mods(script_loc)
        except Exception as e:
            print(f"Error: {e}")
        self.modpath_to_id = {mod.path: i for i, mod in enumerate(self.mods)}
        self.modid_to_path = {i: mod.path for i, mod in enumerate(self.mods)}
        self.profile_handler.update_mod_info(self.mods, self.modpath_to_id)
        self.profile_handler.apply_profile()

    def mod_has_wizard(self, index):
        mod = self.mods[index]

        return mod.wizard is not None

    def reinstall_mod(self, index):
        mod = self.mods[index]
        mod_name = os.path.split(mod.path)[1]
        try:
            modfiles_dir = os.path.join(self.mods[index].path, "modfiles")
            wizard = mod.wizard
            if not wizard.launch_wizard():
                raise ModInstallWizardCancelled()
            shutil.rmtree(modfiles_dir)
            os.mkdir(modfiles_dir)
            wizard.install()
            self.ui.log(f"Re-installed {mod_name}.")
        except Exception as e:
            self.ui.log(f"The following error occured when trying to delete {mod_name}: {e}")
        finally:
            self.update_mods()


    def check_gamelocation(self):
        if self.game_loc is None or not os.path.exists(os.path.join(str(self.game_loc), "app_digister", "Digimon Story CS.exe")):
            if not self.find_gamelocation():
                return False
        self.ui.game_location_textbox.setText(self.game_loc)
        return True
            
    def find_gamelocation(self):
        result = os.path.join(self.game_loc)
        while not os.path.exists(result):
            QtWidgets.QMessageBox.question(self, 'Game not found', 
                                           rf"Game executable was not found in the location {result}. Please select the folder containing the folders 'app_digister' and 'resources'.", QtWidgets.QMessageBox.Ok)
            result = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select your game location:"))

            if result == '' or result == '.':
                self.config['game_loc'] = ''
                return False
        self.config['game_loc'] = result
        self.ui.game_location_textbox.setText(result)
        self.write_config()
        
        return True
    
    def find_gamelocation_check(self):
        result = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select your game location:"))
        while not os.path.exists(result):
            QtWidgets.QMessageBox.question(self, 'Game not found', 
                                           rf"Game executable was not found in the location {result}. Please select the folder containing the folders 'app_digister' and 'resources'.", QtWidgets.QMessageBox.Ok)
            result = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select your game location:"))

            if result == '' or result == '.':
                self.config['game_loc'] = ''
                return False
        self.config['game_loc'] = result
        self.ui.game_location_textbox.setText(result)
        self.write_config()
        
        return True
    
    def check_dscstools(self):
        executable = os.path.join(self.dscstools_loc, "DSCSTools.pyd")
        if not os.path.exists(executable):
            buttons = QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            msgBox = QtWidgets.QMessageBox.question(self, "DSCSTools not found", "DSCSTools was not detected on your computer. Would you like to download it?", buttons)
            
            if msgBox == QtWidgets.QMessageBox.Yes:
                self.get_dscstools()
    
    def update_dscstools(self):
        version = DSCSToolsDownloader.get_dscstools_tag()
        if version != self.config['dscstools_version']:
            buttons = QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            msgBox = QtWidgets.QMessageBox.question(self, "New DSCSTools version found", f"A new version of DSCSTools was found ({version}). Would you like to update?", buttons)
            
            if msgBox == QtWidgets.QMessageBox.Yes:
                self.get_dscstools()
        else:
            QtWidgets.QMessageBox.question(self, 'Version OK',
                                           r"DSCSTools is up-to-date.", QtWidgets.QMessageBox.Ok)
    
    def get_dscstools(self):
        zipped_dscstools = os.path.join(self.dscstools_loc, "DSCSTools.zip")
        
        self.thread = QtCore.QThread()
        self.worker = DSCSToolsDownloader(zipped_dscstools)     
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.messageLog.connect(self.ui.log)
        self.worker.updateMessageLog.connect(self.ui.updateLog)
        self.worker.lockGui.connect(self.ui.disable_gui)
        self.worker.releaseGui.connect(self.ui.enable_gui)
        self.worker.emitTag.connect(self.update_dscstools_tag)
        self.thread.start()      
        
    def update_dscstools_tag(self, version):
        self.config['dscstools_version'] = version
        try:
            self.write_config()
        except Exception as e:
            self.ui.log(f"The following error occurred when attempting to save the DSCSTools version information: {e}")
    
    def closeEvent(self, *args, **kwargs):
        self.profile_handler.save_profile()
        super().closeEvent(*args, **kwargs)


def try_to_locate_game_exe():
    for middle in [['Program Files (x86)', 'Steam'],
                   ['Games']]:
        trial_path = os.path.join(r"C:", *middle, "steamapps", "common", "Digimon Story Cyber Sleuth Complete Edition", "app_digister", "Digimon Story CS.exe")
        if os.path.exists(trial_path):
            return os.path.normpath(os.path.join(r"C:", *middle, "steamapps", "common", "Digimon Story Cyber Sleuth Complete Edition"))

        
def restore_backups(game_resources_loc, backup_loc, logfunc):
    try:
        logfunc("Restoring backup...")
        for file in os.listdir(backup_loc):
            backup_dir = os.path.join(backup_loc, file)
            shutil.copy2(backup_dir, os.path.join(game_resources_loc, file))
        logfunc("Backup restored.")
        
    except Exception as e:
        logfunc(f"The following error occured when trying to restore the backup: {e}")


if __name__ == '__main__':    
    app = QtWidgets.QApplication([]) 
  
    win = MainWindow() 
    win.show() 
    
    # Check for the exe in the most likely places
    if not os.path.exists(os.path.join(win.game_loc, "app_digister", "Digimon Story CS.exe")):
        win.config['game_loc'] = try_to_locate_game_exe()
        win.write_config()
    win.check_gamelocation()
  
    sys.exit(app.exec_())
