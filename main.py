import json
import os
import shutil
import sys
import webbrowser

from PyQt5 import QtWidgets 
from PyQt5 import QtCore

# https://doc.qt.io/qt-5/qfilesystemwatcher.html

from ModFiles.Detection import detect_mods, install_mod_in_manager
from UI.DSCSToolsHandler import DSCSToolsHandler
from UI.Design import uiMainWidget
from UI.ProfileHandler import ProfileHandler
from Subprocesses.InstallMods import InstallModsWorkerThread
from Subprocesses.DumpArchive import DumpArchiveWorkerThread
  
script_loc = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))

def open_patreon():
    webbrowser.open_new_tab(r'https://www.patreon.com/sydmontague')

  
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
        self.dscstools_loc = os.path.normpath(os.path.join(script_loc, "tools", "dscstools"))
        self.mods_loc = os.path.normpath(os.path.join(script_loc, "mods"))
        self.output_loc = os.path.normpath(os.path.join(script_loc, "output"))
        self.profiles_loc = os.path.normpath(os.path.join(script_loc, "profiles"))
        self.resources_loc = os.path.normpath(os.path.join(script_loc, "resources"))
        
        os.makedirs(self.config_loc, exist_ok=True)
        os.makedirs(self.dscstools_loc, exist_ok=True)
        os.makedirs(self.mods_loc, exist_ok=True)
        os.makedirs(self.profiles_loc, exist_ok=True)
        os.makedirs(self.resources_loc, exist_ok=True)

        # Set up mod handling variables
        self.mods = []
        self.modpath_to_id = None
        self.modid_to_path = None
        
        # Set up the configuration and handlers
        self.read_config()
        self.dscstools_handler = DSCSToolsHandler('', os.path.join(self.dscstools_loc, 'DSCSTools.exe'))
        self.profile_handler = ProfileHandler(self.profiles_loc, self.ui.profile_selector, self.ui.mods_display, self)
        self.check_dscstools()
        
        # Hook the UI
        self.ui.hook_menu(open_patreon)
        self.ui.hook_filemenu(self.register_mod_filedialog)
        self.ui.hook_profle_interaction_widgets(self.profile_handler)
        #self.ui.hook_action_tabs(self.draw_conflicts_graph)
        self.ui.hook_config_tab(self.find_gamelocation, self.update_dscstools)
        self.ui.hook_extract_tab(self.dscstools_dump_factory, self.dscstools_afs2_dump_factory)
        self.ui.hook_mod_registry(self.register_mod)
        self.ui.hook_install_button(self.install_mods)
        self.ui.hook_delete_mod_menu(self.unregister_mod)
        self.ui.hook_backup_button((lambda: restore_backups(self.game_resources_loc, 
                                                            self.backups_loc, self.ui.log)))
        
        # Init the UI data
        self.profile_handler.init_profiles()
        self.update_mods()
        self.ui.log("SimpleDSCSModManager initialised.")

        
    @property
    def game_resources_loc(self):
        return os.path.normpath(os.path.join(self.game_loc, "resources"))

    @property
    def game_loc(self):
        return os.path.normpath(str(self.config['game_loc']))
    
    @property
    def backups_loc(self):
        return os.path.join(self.game_resources_loc, 'backup')

    def register_mod(self, mod_path):
        """
        Checks if the file/folder at mod_path is an accepted mod format, and if so,
        copies it into the modmanager 'mods' folder and updates the mod list.
        """
        mod_name = os.path.split(mod_path)[-1]
        self.ui.log(f"Attempting to register {mod_name}...")
        try:
            success = install_mod_in_manager(mod_path, self.mods_loc, self.dscstools_handler.unpack_mbe)
            if success:
                self.ui.log(f"Successfully registered {mod_name}.")
            else:
                self.ui.log(f"{mod_name} is not in a recognised mod format.")
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
        file = QtWidgets.QFileDialog.getOpenFileUrl(self, "Select a mod archive")
        if file != '' and file != '.':
            self.register_mod(file[0].toLocalFile())
            
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

        self.worker = InstallModsWorkerThread(self.output_loc, self.resources_loc, 
                                              self.game_resources_loc, self.backups_loc,
                                              self.profile_handler, self.dscstools_handler)
        
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

            
    def dscstools_dump_factory(self, archive):
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
        
                self.worker = DumpArchiveWorkerThread(archive, use_loc, result, self.dscstools_handler)
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
    
    def dscstools_afs2_dump_factory(self, archive):
        def retval():
            pass
        return retval

    def update_mods(self):
        self.mods = detect_mods(script_loc)
        self.modpath_to_id = {mod.path: i for i, mod in enumerate(self.mods)}
        self.modid_to_path = {i: mod.path for i, mod in enumerate(self.mods)}
        self.profile_handler.update_mod_info(self.mods, self.modpath_to_id)
        self.profile_handler.apply_profile()

    def check_gamelocation(self):
        if self.game_loc is None or not os.path.exists(os.path.join(str(self.game_loc), "app_digister", "Digimon Story CS.exe")):
            if not self.find_gamelocation():
                return False
        self.ui.game_location_textbox.setText(self.game_loc)
        return True
            
    def find_gamelocation(self):
        resolved_path = os.path.join(self.game_loc, "app_digister", "Digimon Story CS.exe")
        while not os.path.exists(resolved_path):
            QtWidgets.QMessageBox.question(self, 'Game not found', 
                                           rf"Game executable was not found in the location {resolved_path}. Please select the folder containing the folders 'app_digister' and 'resources'.", QtWidgets.QMessageBox.Ok)
            result = os.path.normpath(QtWidgets.QFileDialog.getExistingDirectory(self, "Select your game location:"))

            if result == '' or result == '.':
                self.config['game_loc'] = ''
                return False
        self.config['game_loc'] = result
        self.ui.game_location_textbox.setText(result)
        self.write_config()
        
        return True
    
    def check_dscstools(self):
        executable = os.path.join(self.dscstools_loc, "DSCSTools.exe")
        if not os.path.exists(executable):
            buttons = QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            msgBox = QtWidgets.QMessageBox.question(self, "DSCSTools not found", "DSCSTools was not detected on your computer. Would you like to download it?", buttons)
            
            if msgBox == QtWidgets.QMessageBox.Yes:
                self.get_dscstools()
    
    def update_dscstools(self):
        version = self.dscstools_handler.get_dscstools_tag()
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
        version = self.dscstools_handler.deploy_dscstools(zipped_dscstools)
        self.config['dscstools_version'] = version
        self.write_config()
    
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
        
        backup_dir = os.path.join(backup_loc, 'DSDBP.steam.mvgl')
        shutil.copy2(backup_dir, os.path.join(game_resources_loc, 'DSDBP.steam.mvgl'))
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