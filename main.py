import json
import os
import shutil
import sys
import webbrowser

from PyQt5 import QtWidgets 
from PyQt5 import QtCore 
from PyQt5 import QtGui 
from PyQt5.QtCore import Qt

# https://doc.qt.io/qt-5/qfilesystemwatcher.html

from ModFiles.Detection import detect_mods, install_mod_in_manager
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
        self.ui.hook_profle_interaction_widgets(self.profile_handler)
        self.ui.hook_action_tabs(self.draw_conflicts_graph)
        self.ui.hook_config_tab(self.find_gamelocation, self.update_dscstools)
        self.ui.hook_extract_tab(self.dscstools_dump_factory)
        self.ui.hook_mod_registry(self.register_mod)
        
        # Init the UI data
        self.profile_handler.init_profiles()
        self.update_mods()
        self.ui.log("Testing Init")
        self.ui.log("Testing Init 2")
        self.ui.log("Testing Init 3")
        self.ui.log("Testing Init 4")

        
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
            success = install_mod_in_manager(mod_path, self.mods_loc)
            if success:
                self.ui.log(f"Successfully registered {mod_name}.")
                self.update_mods()
            else:
                self.ui.log(f"{mod_name} is not in a recognised mod format.")
        except Exception as e:
            self.ui.log(f"The following error occured when trying to register {mod_name}: {e}")

    def install_mods(self):
        patch_dir = os.path.join(self.output_loc, 'patch')
        dbdsp_dir = os.path.join(self.output_loc, 'DBDSP')
        #####################################################
        # Do all this shit in the patch generation state?!
        if not os.path.exists(patch_dir):
            self.draw_conflicts_graph()
        if os.path.exists(dbdsp_dir):
            shutil.rmtree(dbdsp_dir)
        shutil.copytree(patch_dir, dbdsp_dir)
        marked_files = parse_modfiles(dbdsp_dir)
        loose_mbes = marked_files[modelement_is_loose_mbe]
        for loose_mbe in loose_mbes:
            pass
            # Pack each mbe
            # Remove loose files
        #####################################################
        
        # Now here's the important bit
        # Pack up the DBDSP archive
        # ensure_backed_up('DBDSP')
        #shutil(dsdbp_dir, game_resources_dir)
    
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
    
        
    def draw_conflicts_graph(self, tabIdx):
        if tabIdx == 2:    
            self.ui.conflicts_graph.model().clear()
            mods = self.profile_handler.get_active_mods()
            graph = generate_patched_mods(mods, self.output_loc)  
            graph = prepare_graph_for_display(graph)
            self.ui.conflicts_graph.setAlternatingRowColors(True)
            header_labels = ["File", *[mod.name for mod in mods], "Used Mod"]
            self.ui.conflicts_graph.model().setHorizontalHeaderLabels(header_labels)
            self.draw_conflicts_subgraph(graph, mods)
                
    def draw_conflicts_subgraph(self, graph, mods, parent=None):
        colours = {0: QtGui.QColor( 150,  150,  150),
           1: QtGui.QColor(  0,   0,   0),
           2: QtGui.QColor(255, 255,   0),
           3: QtGui.QColor(  0,   0, 255),
           4: QtGui.QColor(255,   0,   0),
           5: QtGui.QColor(200, 255, 200),
           6: QtGui.QColor(  0, 255,   0),
           7: QtGui.QColor(  0, 255, 255)}
        
        if parent is None:
            parent = self.ui.conflicts_graph.model().invisibleRootItem()
        
        for j, (key, value) in enumerate(graph.items()):
            nameitem = QtGui.QStandardItem(key)
            modelitem = [nameitem, *[QtGui.QStandardItem() for _ in mods], QtGui.QStandardItem()]
            for i in range(len(mods)):
                if type(value) != dict:
                    modelitem[i+1].setData(colours[value[i]], QtCore.Qt.BackgroundRole)
                #else:
                #    modelitem[i+1].setData(colours[0], QtCore.Qt.BackgroundRole)
            for item in modelitem:                
                item.setEditable(False)
            parent.appendRow(modelitem)
            if type(value) == dict:
                self.draw_conflicts_subgraph(value, mods, nameitem)
            

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