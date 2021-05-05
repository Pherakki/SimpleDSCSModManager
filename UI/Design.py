from PyQt5 import QtCore, QtGui, QtWidgets
from datetime import datetime

from .CustomWidgets import ClickEmitComboBox, DragDropTreeView
        
###############################
# Top-Level Widget Containers #
###############################
class uiMainWidget:
    def __init__(self, parentWidget):
        self.define(parentWidget)
        self.lay_out()
        self.create_shortcuts()
        
    def define(self, parentWidget): 
        self.layout = QtWidgets.QGridLayout()
        
        self.main_area = uiMainArea(parentWidget)
        self.logging_area = uiLoggingArea(parentWidget)
        self.menu = uiMenu(parentWidget)
        
    def lay_out(self):
        self.layout.addLayout(self.main_area.layout, 0, 0)
        self.layout.addLayout(self.logging_area.layout, 1, 0)
        
    def create_shortcuts(self):
        self.profile_selector = self.main_area.mod_interaction_area.profile_interaction_widgets.profile_selector
        self.mods_display = self.main_area.mod_interaction_area.mods_display_area.mods_display
        self.game_location_textbox = self.main_area.action_tabs.configTab.game_location_textbox
        self.conflicts_graph = self.main_area.action_tabs.conflictsTab.conflicts_graph

        self.hook_menu = self.menu.hook
        self.hook_filemenu = self.menu.hook_filemenu
        self.hook_profle_interaction_widgets = self.main_area.mod_interaction_area.profile_interaction_widgets.hook
        self.hook_action_tabs = self.main_area.action_tabs.hook
        self.hook_config_tab = self.main_area.action_tabs.configTab.hook
        self.hook_extract_tab = self.main_area.action_tabs.extractTab.hook
        self.hook_mod_registry = self.main_area.mod_interaction_area.mods_display_area.mods_display.hook_registry_function
        self.hook_delete_mod_menu = self.main_area.mod_interaction_area.mods_display_area.hook_delete_mod
        self.hook_update_mod_info_window = self.main_area.mod_interaction_area.mods_display_area.update_mod_info_window
        self.hook_install_button = self.main_area.mod_interaction_area.mod_installation_widgets.hook_install_button
        self.hook_game_launch_button = self.main_area.mod_interaction_area.mod_installation_widgets.hook_game_launch_button
        self.hook_backup_button = self.main_area.mod_interaction_area.mod_installation_widgets.hook_backup_button
        
        self.log = self.logging_area.logview.log
        self.updateLog = self.logging_area.logview.updateLog
        
        self.set_mod_info = self.main_area.action_tabs.configTab.modinfo_region.setModInfo
        
    def enable_gui(self):
        self.toggle_active_gui(True)
        
    def disable_gui(self):
        self.toggle_active_gui(False)
        
    def toggle_active_gui(self, active):
        self.menu.toggle_active(active)
        self.main_area.mod_interaction_area.toggle_active(active)
        self.main_area.action_tabs.toggle_active(active)
        
        
################################
# High-Level Widget Containers #
################################
class uiMenu:
    def __init__(self, parentWidget):
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.fileMenu = QtWidgets.QMenu("&File", parentWidget)
        self.helpMenu = QtWidgets.QMenu("&Help", parentWidget)
        parentWidget.menuBar().addMenu(self.fileMenu)
        parentWidget.menuBar().addMenu(self.helpMenu)
                
        self.addModAction = QtWidgets.QAction("Add Mod...", parentWidget)
        self.fileMenu.addAction(self.addModAction)
        
        self.donateAction = QtWidgets.QAction("Support Digimon Game Research...", parentWidget)
        self.helpMenu.addAction(self.donateAction)
        
    def lay_out(self):
        pass
    
    def hook(self, open_patreon):
        self.donateAction.triggered.connect(open_patreon)
        
    def hook_filemenu(self, register_mod_dialog):
        self.addModAction.triggered.connect(register_mod_dialog)
        
    def enable(self):
        self.toggle_active(True)
        
    def disable(self):
        self.toggle_active(True)
        
    def toggle_active(self, active):
        self.addModAction.setEnabled(active)


class uiMainArea:
    def __init__(self, parentWidget):
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.mod_interaction_area = uiModInteractionArea(parentWidget)
        self.action_tabs = uiActionTabs(parentWidget)
        
    def lay_out(self):
        self.layout.addLayout(self.mod_interaction_area.layout, 0, 0)
        self.layout.addLayout(self.action_tabs.layout, 0, 1)
        
class uiLoggingArea:
    def __init__(self, parentWidget):
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.logview = uiLogHistory(parentWidget)
        
    def lay_out(self):
        self.layout.addLayout(self.logview.layout, 0, 0)
        
        
###################################
# Mod Interaction Area Containers #
###################################
class uiModInteractionArea:
    def __init__(self, parentWidget):
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.profile_interaction_widgets = uiProfileInteractionWidgets(parentWidget)
        self.mods_display_area = uiModsDisplay(parentWidget)
        self.mod_installation_widgets = uiModInstallationWidgets(parentWidget)
        
    def lay_out(self):
        self.layout.addLayout(self.profile_interaction_widgets.layout, 0, 0)
        self.layout.addLayout(self.mods_display_area.layout, 1, 0)
        self.layout.addLayout(self.mod_installation_widgets.layout, 2, 0)
    
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        self.profile_interaction_widgets.toggle_active(active)
        self.mods_display_area.toggle_active(active)
        self.mod_installation_widgets.toggle_active(active)
        
    
class uiProfileInteractionWidgets:
    def __init__(self, parentWidget):
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.new_profile_button = QtWidgets.QPushButton("New Profile", parentWidget)
        self.new_profile_button.setFixedWidth(100)
        self.rename_profile_button = QtWidgets.QPushButton("Rename Profile", parentWidget)
        self.rename_profile_button.setFixedWidth(100)
        self.delete_profile_button = QtWidgets.QPushButton("Delete Profile", parentWidget)
        self.delete_profile_button.setFixedWidth(100)
        
        self.profile_selector = ClickEmitComboBox(parentWidget)
        self.profile_selector.wheelEvent = lambda event: None
        
        
    def lay_out(self):
        self.layout.addWidget(self.new_profile_button, 0, 0)
        self.layout.addWidget(self.rename_profile_button, 0, 1)
        self.layout.addWidget(self.delete_profile_button, 0, 2)
        self.layout.addWidget(self.profile_selector, 0, 3)
        
    def hook(self, profile_handler):
        self.new_profile_button.clicked.connect(profile_handler.new_profile)
        self.rename_profile_button.clicked.connect(profile_handler.rename_profile)
        self.delete_profile_button.clicked.connect(profile_handler.delete_profile)
        self.profile_selector.popupAboutToBeShown.connect(profile_handler.save_profile)
        self.profile_selector.currentIndexChanged.connect(profile_handler.apply_profile)
    
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        self.new_profile_button.setEnabled(active)
        self.rename_profile_button.setEnabled(active)
        self.delete_profile_button.setEnabled(active)
        self.profile_selector.setEnabled(active)
    

class uiModsDisplay:
    def __init__(self, parentWidget):
        super().__init__()
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        self.mods_display = DragDropTreeView(parentWidget) 
        model = QtGui.QStandardItemModel(self.mods_display)
        model.setHorizontalHeaderLabels(["Name", "Author", "Version", "Category"])
        self.mods_display.setModel(model)
        self.mods_display.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  
        self.mods_display.setColumnWidth(0, 200)
        self.mods_display.setColumnWidth(2, 50)
        self.mods_display.setMinimumSize(500, 300)
        
        self.contextMenu = QtWidgets.QMenu()
        self.deleteModAction = self.contextMenu.addAction("Delete Mod")
        
        self.mods_display.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.mods_display.customContextMenuRequested.connect(self.menuContextTree)
        self.deleteModFunction = None
        
        
    def lay_out(self):
        self.layout.addWidget(self.mods_display, 0, 0)
    
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        self.mods_display.setEnabled(active)

    def menuContextTree(self, point):
        try:
            self.deleteModAction.triggered.disconnect()
        except TypeError:
            pass

        # Infos about the node selected.
        index = self.mods_display.indexAt(point)

        if not index.isValid():
            return

        self.deleteModAction.triggered.connect(lambda: self.deleteModFunction(index.row()))

        self.contextMenu.exec_(self.mods_display.mapToGlobal(point))
        
    def hook_delete_mod(self, func):
        self.deleteModFunction = func
        
    def update_mod_info_window(self, func):
        self.mods_display.update_mods_func = func
        
class uiModInstallationWidgets:
    def __init__(self, parentWidget):
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.install_mods_button = QtWidgets.QPushButton("Install Mods", parentWidget)
        self.install_mods_button.setFixedWidth(120)
        self.launch_game_button = QtWidgets.QPushButton("Launch Game", parentWidget)
        self.launch_game_button.setFixedWidth(120)
        self.restore_backups_button = QtWidgets.QPushButton("Restore Backups", parentWidget)
        self.restore_backups_button.setFixedWidth(120)
        
    def lay_out(self):
        self.layout.addWidget(self.install_mods_button, 0, 0)
        self.layout.addWidget(self.launch_game_button, 0, 1)
        self.layout.addWidget(self.restore_backups_button, 0, 2)
        
    def hook_install_button(self, func):
        self.install_mods_button.clicked.connect(func)
        
    def hook_game_launch_button(self, func):
        self.launch_game_button.clicked.connect(func)
        
    def hook_backup_button(self, func):
        self.restore_backups_button.clicked.connect(func)
        
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        self.install_mods_button.setEnabled(active)
        self.launch_game_button.setEnabled(active)
        self.restore_backups_button.setEnabled(active)
        
class uiLogHistory():
    def __init__(self, parentWidget):
        self.max_items = 500
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.logview = QtWidgets.QListWidget()
        self.logview.setAlternatingRowColors(True)
        self.logview.setWordWrap(False) 
        self.logview.setFixedHeight(100)
        
    def lay_out(self):
        self.layout.addWidget(self.logview, 0, 0)
        
    def log(self, message):
        adj_message = self.timestamp_string(message)
        self.logview.addItem(adj_message)
        self.cull_messages()
        self.logview.scrollToBottom()
        self.logview.scrollToBottom()
        
    def updateLog(self, message):
        adj_message = self.timestamp_string(message)
        self.logview.takeItem(self.logview.count() - 1)
        self.logview.addItem(adj_message)
        self.logview.scrollToBottom()
    
    def timestamp_string(self, string):
        time_now = datetime.now()
        return f"[{time_now.hour:02}:{time_now.minute:02}] {string}"
    
    def cull_messages(self):
        if self.logview.count() >= self.max_items:
            for i in range(self.logview.count() - self.max_items + 1):
                self.logview.takeItem(0)
                
##########################
# Action Tabs Containers #
##########################
class uiActionTabs:
    def __init__(self, parentWidget):
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.actions = QtWidgets.QTabWidget()
        self.actions.setMinimumSize(500, 300)
        self.configTab = uiConfigTab(parentWidget)
        self.extractTab = uiExtractTab(parentWidget)
        self.conflictsTab = uiConflictsTab(parentWidget)
        
    def lay_out(self):
        self.actions.addTab(self.configTab, "Configuration")
        self.actions.addTab(self.extractTab, "Extract")
        self.actions.addTab(self.conflictsTab, "Conflicts")
        
        self.layout.addWidget(self.actions, 0, 0)
        
    def hook(self, draw_conflicts_graph):
        self.actions.currentChanged.connect(draw_conflicts_graph)
    
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)   
        
    def toggle_active(self, active):
        self.configTab.toggle_active(active)
        self.extractTab.toggle_active(active)
        self.conflictsTab.toggle_active(active)
    
class uiConfigTab(QtWidgets.QWidget):
    def __init__(self, parentWidget):
        super().__init__()
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.game_location_layout = QtWidgets.QGridLayout()
        self.game_location_label = QtWidgets.QLabel("Game Location:  ", parentWidget)
        self.game_location_textbox = QtWidgets.QLineEdit(parentWidget)
        self.game_location_textbox.setReadOnly(True)
        self.game_location_button = QtWidgets.QPushButton("...", parentWidget)
        self.game_location_button.setFixedWidth(20)
        self.game_location_layout.addWidget(self.game_location_label, 0, 0)
        self.game_location_layout.addWidget(self.game_location_textbox, 0, 1)
        self.game_location_layout.addWidget(self.game_location_button, 0, 2)
        self.game_location_layout.setSpacing(0)
        
        self.modinfo_region= ModInfoRegion(parentWidget)
        
        self.dscstools_buttons_layout = QtWidgets.QGridLayout()
        self.update_dscstools_button = QtWidgets.QPushButton("Update DSCSTools", parentWidget)
        self.update_dscstools_button.setFixedWidth(120)
        self.update_dscstools_button.setEnabled(False)
        
    def lay_out(self):
        self.dscstools_buttons_layout.addWidget(self.update_dscstools_button, 0, 0)
        self.layout.addLayout(self.game_location_layout, 0, 0)
        self.layout.addLayout(self.dscstools_buttons_layout, 1, 0)
        self.layout.addLayout(self.modinfo_region.layout, 2, 0)
        self.layout.setRowStretch(0, 0)
        self.layout.setRowStretch(1, 0)
        self.layout.setRowStretch(2, 1)
        self.setLayout(self.layout)
        
    def hook(self, find_gamelocation, update_dscstools):
        self.game_location_button.clicked.connect(find_gamelocation)
        self.update_dscstools_button.clicked.connect(update_dscstools)
        
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        self.game_location_textbox.setEnabled(active)
        self.game_location_button.setEnabled(active)
        # self.update_dscstools_button.setEnabled(active)
        
class ModInfoRegion:
    def __init__(self, parentWidget):
        super().__init__()
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.modname_label = QtWidgets.QLabel("Mod Name: [Unknown]", parentWidget)
        self.modfolder_label = QtWidgets.QLabel("Mod Folder: [Unknown]", parentWidget)
        self.modauthors_label = QtWidgets.QLabel("Author(s): [Unknown]", parentWidget)
        self.modversion_label = QtWidgets.QLabel("Version: [Unknown]", parentWidget)
        self.moddesc_box = QtWidgets.QTextEdit("", parentWidget)
        self.moddesc_box.setReadOnly(True)
        
        
    def lay_out(self):
        self.layout.addWidget(self.modname_label, 0, 0)
        self.layout.setRowStretch(0, 0)
        self.layout.addWidget(self.modfolder_label, 1, 0)
        self.layout.setRowStretch(1, 0)
        self.layout.addWidget(self.modauthors_label, 2, 0)
        self.layout.setRowStretch(2, 0)
        self.layout.addWidget(self.modversion_label, 3, 0)
        self.layout.setRowStretch(3, 0)
        self.layout.addWidget(self.moddesc_box, 4, 0)
        
    def setModName(self, string):
        self.modname_label.setText(f"Mod Name: {string}")
        
    def setModFolder(self, string):
        self.modfolder_label.setText(f"Mod Folder: {string}")
        
    def setModAuthor(self, string):
        self.modauthors_label.setText(f"Author(s): {string}")
        
    def setModVersion(self, string):
        self.modversion_label.setText(f"Version: {string}")
        
    def setModDesc(self, string):
        self.moddesc_box.setText(string)
        
    def setModInfo(self, name, folder, author, version, desc):
        self.setModName(name)
        self.setModFolder(folder)
        self.setModAuthor(author)
        self.setModVersion(version)
        self.setModDesc(desc)

class uiExtractTab(QtWidgets.QScrollArea):
    def __init__(self, parentWidget):
        self.mvgls = ["DSDB", "DSDBA", "DSDBS", "DSDBSP", "DSDBP", "DSDBse", "DSDBPse"]
        self.afs2s = ["DSDBbgm", "DSDBPDSEbgm", "DSDBvo", "DSDBPvo", "DSDBPvous"]
        self.archive_extract_buttons = {}
        self.afs2_extract_buttons = {}
        
        super().__init__()
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.scrollArea = QtWidgets.QWidget()
        self.scrollArealayout = QtWidgets.QGridLayout()
        
        self.autoextract_widget = QtWidgets.QWidget()
        self.autoextract_layout = QtWidgets.QGridLayout()
        self.mdb1_layout = QtWidgets.QGridLayout()
        self.afs2_layout = QtWidgets.QGridLayout()
        
        self.manualextract_widget = QtWidgets.QWidget()
        self.manualextract_layout = QtWidgets.QGridLayout()
        self.dscstools_widget = QtWidgets.QWidget()
        self.dscstools_layout = QtWidgets.QGridLayout()
        self.scripts_widget = QtWidgets.QWidget()
        self.scripts_layout= QtWidgets.QGridLayout()
        self.vgstream_widget = QtWidgets.QWidget()
        self.vgstream_layout = QtWidgets.QGridLayout()
        
        self.mdb1_label = QtWidgets.QLabel("Auto-Extract Data")
        self.mdb1_label.setAlignment(QtCore.Qt.AlignCenter)
        
        for i, archive in enumerate(self.mvgls):
            button = QtWidgets.QPushButton(f"Extract {archive}", parentWidget)
            button.setFixedWidth(130)
            button.setFixedHeight(22)
            self.archive_extract_buttons[archive] = button
        for i, archive in enumerate(self.afs2s):
            button = QtWidgets.QPushButton(f"Extract {archive}", parentWidget)
            button.setFixedWidth(130)
            button.setFixedHeight(22)
            self.afs2_extract_buttons[archive] = button
            
        self.dscstools_label = QtWidgets.QLabel("General Data Extraction")
        self.dscstools_label.setAlignment(QtCore.Qt.AlignCenter)
        self.extract_mdb1_button = self.new_button("Extract MDB1", parentWidget)
        self.pack_mdb1_button = self.new_button("Pack MDB1", parentWidget)
        self.extract_afs2_button = self.new_button("Extract AFS2", parentWidget)
        self.extract_afs2_button.setEnabled(False)
        self.pack_afs2_button = self.new_button("Pack AFS2", parentWidget)
        self.pack_afs2_button.setEnabled(False)
        self.extract_mbes_button = self.new_button("Extract MBEs", parentWidget)
        self.pack_mbes_button = self.new_button("Pack MBEs", parentWidget)
        
        self.scripts_label = QtWidgets.QLabel("Scripts")
        self.scripts_label.setAlignment(QtCore.Qt.AlignCenter)
        self.decompile_scripts_button = self.new_button("Decompile scripts", parentWidget)
        self.compile_scripts_button = self.new_button("Compile scripts", parentWidget)
        
        self.sounds_label = QtWidgets.QLabel("Sounds")
        self.sounds_label.setAlignment(QtCore.Qt.AlignCenter)
        self.hca_to_wav = self.new_button("Convert HCA to WAV", parentWidget)
        self.hca_to_wav.setEnabled(False)
        self.wav_to_hca = self.new_button("Convert WAV to HCA", parentWidget)
        self.wav_to_hca.setEnabled(False)
        
    def lay_out(self):
        # Lay out the LHS button pane
        self.mdb1_layout.addWidget(self.mdb1_label, 0, 0)
        self.mdb1_layout.setRowStretch(0, 0)
        for i, archive in enumerate(self.mvgls):
            button = self.archive_extract_buttons[archive]
            self.mdb1_layout.addWidget(button, i+1, 0)
            self.mdb1_layout.setRowStretch(i+1, 0)
        
        for i, archive in enumerate(self.afs2s):
            button = self.afs2_extract_buttons[archive]
            self.afs2_layout.addWidget(button, i, 0)
            self.afs2_layout.setRowStretch(i, 0)
        
        self.autoextract_layout.setRowStretch(0, 1)
        self.autoextract_layout.addLayout(self.mdb1_layout, 1, 0)
        self.autoextract_layout.addLayout(self.afs2_layout, 2, 0)
        self.autoextract_layout.setRowStretch(3, 1)
        self.autoextract_widget.setLayout(self.autoextract_layout)
        
        # Lay out the RHS button pane
        self.dscstools_layout.addWidget(self.dscstools_label, 0, 0)
        self.dscstools_layout.setRowStretch(0, 0)
        for i, button in enumerate((self.extract_mdb1_button, self.pack_mdb1_button,
                                    self.extract_afs2_button, self.pack_afs2_button,
                                    self.extract_mbes_button, self.pack_mbes_button)): 
            self.dscstools_layout.addWidget(button, i+1, 0)
            self.dscstools_layout.setRowStretch(i+1, 0)
        self.dscstools_widget.setLayout(self.dscstools_layout)
          
        self.scripts_layout.addWidget(self.scripts_label, 0, 0)
        self.scripts_layout.setRowStretch(0, 0)
        for i, button in enumerate((self.decompile_scripts_button, self.compile_scripts_button)): 
            self.scripts_layout.addWidget(button, i+1, 0)
            self.scripts_layout.setRowStretch(i+1, 0)
        self.scripts_widget.setLayout(self.scripts_layout)
        
        self.vgstream_layout.addWidget(self.sounds_label, 0, 0)
        self.vgstream_layout.setRowStretch(0, 0)
        for i, button in enumerate((self.hca_to_wav, self.wav_to_hca)): 
            self.vgstream_layout.addWidget(button, i+1, 0)
            self.vgstream_layout.setRowStretch(i+1, 0)
        self.vgstream_widget.setLayout(self.vgstream_layout)
        
        self.manualextract_layout.setRowStretch(0, 1)
        self.manualextract_layout.addWidget(self.dscstools_widget, 1, 0)
        self.manualextract_layout.addWidget(self.scripts_widget, 2, 0)
        self.manualextract_layout.addWidget(self.vgstream_widget, 3, 0)
        self.manualextract_layout.setRowStretch(4, 1)
        self.manualextract_widget.setLayout(self.manualextract_layout)
           
        # Bring it all together
        self.scrollArealayout.setColumnStretch(0, 1)
        self.scrollArealayout.setColumnStretch(2, 1)
        self.scrollArealayout.setColumnStretch(4, 1)
        self.scrollArealayout.setRowStretch(0, 1)
        self.scrollArealayout.setRowStretch(2, 1)
        self.scrollArealayout.addWidget(self.autoextract_widget, 1, 1)
        self.scrollArealayout.addWidget(self.manualextract_widget, 1, 3)
        self.scrollArea.setLayout(self.scrollArealayout)
        
        self.setWidget(self.scrollArea)
        self.setWidgetResizable(True)
        
    def hook(self, mbd1_dump_factory, afs2_dump_factory, dscstools_handler, 
             extract_mdb1, pack_mdb1,
             extract_mbes, pack_mbes,
             decompile_scripts, compile_scripts):
        for archive in self.mvgls:
            self.archive_extract_buttons[archive].clicked.connect(mbd1_dump_factory(archive))
        for archive in self.afs2s:
            self.afs2_extract_buttons[archive].clicked.connect(afs2_dump_factory(archive))
        self.extract_mdb1_button.clicked.connect(extract_mdb1)
        self.pack_mdb1_button.clicked.connect(pack_mdb1)
        self.extract_mbes_button.clicked.connect(extract_mbes)
        self.pack_mbes_button.clicked.connect(pack_mbes)
        self.decompile_scripts_button.clicked.connect(decompile_scripts)
        self.compile_scripts_button.clicked.connect(compile_scripts)
                
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        for button in self.archive_extract_buttons.values():
            button.setEnabled(active)
        for button in self.afs2_extract_buttons.values():
            button.setEnabled(active)
        self.extract_mdb1_button.setEnabled(active)
        self.pack_mdb1_button.setEnabled(active)
        self.extract_mbes_button.setEnabled(active)
        self.pack_mbes_button.setEnabled(active)
        self.decompile_scripts_button.setEnabled(active)
        self.compile_scripts_button.setEnabled(active)
            
    def new_button(self, text, parentWidget):
        button = QtWidgets.QPushButton(text, parentWidget)
        button.setFixedWidth(130)
        button.setFixedHeight(22)
        return button


class uiConflictsTab(QtWidgets.QWidget):
    def __init__(self, parentWidget):
        super().__init__()
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        self.conflicts_graph = QtWidgets.QTreeView()
        model = QtGui.QStandardItemModel(self.conflicts_graph)
        self.conflicts_graph.setModel(model)
        
    def lay_out(self):
        self.layout.addWidget(self.conflicts_graph, 0, 0)
        self.setLayout(self.layout)
        
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        self.conflicts_graph.setEnabled(active)
        
    