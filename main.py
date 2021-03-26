import json
import os
import shutil
import sys
import webbrowser
from distutils import dir_util

from PyQt5 import QtWidgets 
from PyQt5 import QtCore 
from PyQt5 import QtGui 
from PyQt5.QtCore import Qt

# https://doc.qt.io/qt-5/qfilesystemwatcher.html

from ModFiles.Detection import detect_mods, install_mod_in_manager
from ModFiles.Indexing import generate_mod_index
from ModFiles.PatchGen import generate_patch
from UI.DSCSToolsHandler import DSCSToolsHandler
from UI.Design import uiMainWidget
from UI.ProfileHandler import ProfileHandler
from mbeparsing import generate_patched_mods, parse_modfiles, modelement_is_loose_mbe
  
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
        self.dscstools_loc = os.path.normpath(os.path.join(script_loc, "dscstools"))
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
        self.ui.hook_extract_tab(self.dscstools_dump_factory)
        self.ui.hook_mod_registry(self.register_mod)
        self.ui.hook_install_button(self.install_mods)
        self.ui.hook_backup_button((lambda: restore_backups(self.game_resources_loc, self.ui.log)))
        
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

    def register_mod(self, mod_path):
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
        file = QtWidgets.QFileDialog.getOpenFileUrl(self, "Select a mod")
        self.register_mod(file[0].toLocalFile())


    def install_mods(self):
        self.profile_handler.save_profile()
        self.update_mods()
        self.profile_handler.save_profile()
        self.ui.disable_gui()
        self.thread = QtCore.QThread()

        self.worker = InstallModsWorkerThread(self.output_loc, self.resources_loc, 
                                              self.game_resources_loc,
                                              self.profile_handler, self.dscstools_handler)
        
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.messageLog.connect(self.ui.log)
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
                self.dscstools_handler.dump_mvgl(archive, self.game_resources_loc, self.resources_loc)
        return retval
    
        
    # def draw_conflicts_graph(self, tabIdx):
    #     if tabIdx == 2:    
    #         self.ui.conflicts_graph.model().clear()
    #         mods = self.profile_handler.get_active_mods()
    #         graph = generate_patched_mods(mods, self.output_loc)  
    #         graph = prepare_graph_for_display(graph)
    #         self.ui.conflicts_graph.setAlternatingRowColors(True)
    #         header_labels = ["File", *[mod.name for mod in mods], "Used Mod"]
    #         self.ui.conflicts_graph.model().setHorizontalHeaderLabels(header_labels)
    #         self.draw_conflicts_subgraph(graph, mods)
                
    # def draw_conflicts_subgraph(self, graph, mods, parent=None):
    #     colours = {0: QtGui.QColor( 150,  150,  150),
    #        1: QtGui.QColor(  0,   0,   0),
    #        2: QtGui.QColor(255, 255,   0),
    #        3: QtGui.QColor(  0,   0, 255),
    #        4: QtGui.QColor(255,   0,   0),
    #        5: QtGui.QColor(200, 255, 200),
    #        6: QtGui.QColor(  0, 255,   0),
    #        7: QtGui.QColor(  0, 255, 255)}
        
    #     if parent is None:
    #         parent = self.ui.conflicts_graph.model().invisibleRootItem()
        
    #     for j, (key, value) in enumerate(graph.items()):
    #         nameitem = QtGui.QStandardItem(key)
    #         modelitem = [nameitem, *[QtGui.QStandardItem() for _ in mods], QtGui.QStandardItem()]
    #         for i in range(len(mods)):
    #             if type(value) != dict:
    #                 modelitem[i+1].setData(colours[value[i]], QtCore.Qt.BackgroundRole)
    #             #else:
    #             #    modelitem[i+1].setData(colours[0], QtCore.Qt.BackgroundRole)
    #         for item in modelitem:                
    #             item.setEditable(False)
    #         parent.appendRow(modelitem)
    #         if type(value) == dict:
    #             self.draw_conflicts_subgraph(value, mods, nameitem)
            

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
                                           rf"DSCSTools is up-to-date.", QtWidgets.QMessageBox.Ok)
    
    def get_dscstools(self):
        zipped_dscstools = os.path.join(self.dscstools_loc, "DSCSTools.zip")
        version = self.dscstools_handler.deploy_dscstools(zipped_dscstools)
        self.config['dscstools_version'] = version
        self.write_config()
    
    def closeEvent(self, *args, **kwargs):
        self.profile_handler.save_profile()
        super().closeEvent(*args, **kwargs)
        
def prepare_graph_for_display(graph):
    directories = {}
    files = {}
    for key in sorted(graph):
        keysplit = key.split('/')
        value = graph[key]
        if len(keysplit) > 1:
            if keysplit[0] not in directories:
                directories[keysplit[0]] = {}
            directories[keysplit[0]]['/'.join(keysplit[1:])] = value
        else:
            files[key] = value
            
    for key, value in directories.items():
        directories[key] = prepare_graph_for_display(value)
            
    return {**directories, **files}

def try_to_locate_game_exe():
    for middle in [['Program Files (x86)', 'Steam'],
                   ['Games']]:
        trial_path = os.path.join(r"C:", *middle, "steamapps", "common", "Digimon Story Cyber Sleuth Complete Edition", "app_digister", "Digimon Story CS.exe")
        if os.path.exists(trial_path):
            return os.path.normpath(os.path.join(r"C:", *middle, "steamapps", "common", "Digimon Story Cyber Sleuth Complete Edition"))

def create_backups(game_resources_loc, logfunc):
    backup_dir = os.path.join(game_resources_loc, 'backup', 'DSDBP.steam.mvgl')
    if not os.path.exists(backup_dir):
        logfunc("Creating backup...")
        os.mkdir(os.path.split(backup_dir)[0])
        shutil.copy2(os.path.join(game_resources_loc, 'DSDBP.steam.mvgl'), backup_dir)
        
def restore_backups(game_resources_loc, logfunc):
    try:
        logfunc("Restoring backup...")
        
        backup_dir = os.path.join(game_resources_loc, 'backup', 'DSDBP.steam.mvgl')
        shutil.copy2(backup_dir, os.path.join(game_resources_loc, 'DSDBP.steam.mvgl'))
        
        logfunc("Backup restored.")
    except Exception as e:
        logfunc(f"The following error occured when trying to restore the backup: {e}")


class InstallModsWorkerThread(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    releaseGui = QtCore.pyqtSignal()
    
    def __init__(self, output_loc, resources_loc, game_resources_loc, 
                 profile_handler, dscstools_handler, parent=None):
        super().__init__(parent)
        self.output_loc = output_loc
        self.resources_loc = resources_loc
        self.game_resources_loc = game_resources_loc
        self.profile_handler = profile_handler
        self.dscstools_handler = dscstools_handler
        
    def run(self):
        try:
            self.messageLog.emit("Preparing to patch mods together...")
            patch_dir = os.path.relpath(os.path.join(self.output_loc, 'patch'))
            dbdsp_dir = os.path.relpath(os.path.join(self.output_loc, 'DSDBP'))
            mvgl_loc = os.path.join(self.output_loc, 'DSDBP.steam.mvgl')
            if os.path.exists(patch_dir):
                shutil.rmtree(patch_dir)
            if os.path.exists(dbdsp_dir):
                shutil.rmtree(dbdsp_dir)
            if os.path.exists(mvgl_loc):
                os.remove(mvgl_loc)
                
            # Do this on mod registry...
            self.messageLog.emit("Indexing mods...")
            indices = []
            for mod in self.profile_handler.get_active_mods():
                modfiles_path = os.path.relpath(os.path.join(mod.path, "modfiles"))
                indices.append(generate_mod_index(modfiles_path, {}))
            self.messageLog.emit(f"Indexed ({len(indices)}) active mods.")
            self.messageLog.emit("Generating patch...")
            generate_patch(indices, patch_dir, self.resources_loc)
            
            # Pack each mbe
            temp_path = os.path.join(patch_dir, 'temp')
            os.mkdir(temp_path)
            for mbe_folder in ['data', 'message', 'text']:
                mbe_folder_path = os.path.join(patch_dir, mbe_folder)
                if os.path.exists(mbe_folder_path):
                    
                    for folder in os.listdir(mbe_folder_path):
                        # Generate the mbe inside the 'temp' directory
                        self.dscstools_handler.pack_mbe(folder, 
                                                        os.path.abspath(mbe_folder_path), 
                                                        os.path.abspath(temp_path))
                        shutil.rmtree(os.path.join(mbe_folder_path, folder))
                        # Move the packed MBE out out 'temp' and into the correct path
                        os.rename(os.path.join(temp_path, folder), os.path.join(mbe_folder_path, folder))
            os.rmdir(temp_path)
            
            self.messageLog.emit("Generating patched MVGL archive (this may take a few minutes)...")
        
            dsdbp_resource_loc = os.path.join(self.resources_loc, 'DSDBP')
            if not os.path.exists(dsdbp_resource_loc):
                self.messageLog.emit("Base DSDBP archive not found, generating...")
                self.dscstools_handler.dump_mvgl('DSDBP', self.game_resources_loc, self.resources_loc)
            shutil.copytree(dsdbp_resource_loc, dbdsp_dir)
            dir_util.copy_tree(patch_dir, dbdsp_dir)
            self.dscstools_handler.pack_mvgl('DSDBP', self.output_loc, self.output_loc, remove_input=False)
            self.dscstools_handler.encrypt_mvgl('DSDBP', self.output_loc, self.output_loc, remove_input=True)
            self.messageLog.emit("Installing patched archive...")
            # Now here's the important bit
            create_backups(self.game_resources_loc, self.messageLog.emit)
            shutil.copy2(mvgl_loc, os.path.join(self.game_resources_loc, 'DSDBP.steam.mvgl'))
            
            self.messageLog.emit("Mods successfully installed.")
            
        except Exception as e:
            self.messageLog.emit(f"The following error occured when trying to install modlist: {e}")
            raise e
        finally:
            self.releaseGui.emit()
            self.finished.emit()


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