from PyQt5 import QtGui, QtWidgets
from datetime import datetime

from .CustomWidgets import ComboBox, DragDropTreeView
        
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
        self.hook_profle_interaction_widgets = self.main_area.mod_interaction_area.profile_interaction_widgets.hook
        self.hook_action_tabs = self.main_area.action_tabs.hook
        self.hook_config_tab = self.main_area.action_tabs.configTab.hook
        self.hook_extract_tab = self.main_area.action_tabs.extractTab.hook
        self.hook_mod_registry = self.main_area.mod_interaction_area.mods_display_area.mods_display.hook_registry_function
        self.hook_install_button = self.main_area.mod_interaction_area.mod_installation_widgets.hook_install_button
        self.hook_backup_button = self.main_area.mod_interaction_area.mod_installation_widgets.hook_backup_button
        
        self.log = self.logging_area.logview.log
        
        
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
        
        self.profile_selector = ComboBox(parentWidget)
        
        
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
        
    def lay_out(self):
        self.layout.addWidget(self.mods_display, 0, 0)

        
class uiModInstallationWidgets:
    def __init__(self, parentWidget):
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.install_mods_button = QtWidgets.QPushButton("Install Mods", parentWidget)
        self.install_mods_button.setFixedWidth(120)
        self.restore_backups_button = QtWidgets.QPushButton("Restore Backups", parentWidget)
        self.restore_backups_button.setFixedWidth(120)
        
    def lay_out(self):
        self.layout.addWidget(self.install_mods_button, 0, 0)
        self.layout.addWidget(self.restore_backups_button, 0, 1)
        
    def hook_install_button(self, func):
        self.install_mods_button.clicked.connect(func)
        
    def hook_backup_button(self, func):
        self.restore_backups_button.clicked.connect(func)
        
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
        time_now = datetime.now()
        adj_message = f"[{time_now.hour:02}:{time_now.minute:02}] {message}"
        self.logview.addItem(adj_message)
        if self.logview.count() >= self.max_items:
            for i in range(self.logview.count() - self.max_items + 1):
                self.logview.takeItem(0)
        self.logview.scrollToBottom()
    
        
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
        
        self.dscstools_buttons_layout = QtWidgets.QGridLayout()
        self.update_dscstools_button = QtWidgets.QPushButton("Update DSCSTools", parentWidget)
        self.update_dscstools_button.setFixedWidth(120)
        
    def lay_out(self):
        self.dscstools_buttons_layout.addWidget(self.update_dscstools_button, 0, 0)
        self.layout.addLayout(self.game_location_layout, 0, 0)
        self.layout.addLayout(self.dscstools_buttons_layout, 1, 0)
        self.layout.setRowStretch(0, 0)
        self.layout.setRowStretch(1, 0)
        self.layout.setRowStretch(2, 1)
        self.setLayout(self.layout)
        
    def hook(self, find_gamelocation, update_dscstools):
        self.game_location_button.clicked.connect(find_gamelocation)
        self.update_dscstools_button.clicked.connect(update_dscstools)
        
class uiExtractTab(QtWidgets.QWidget):
    def __init__(self, parentWidget):
        self.mvgls = ["DSDB", "DSDBA", "DSDBse", "DSDBPse", "DSDBS", "DSDBSP", "DSDBP"]
        super().__init__()
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        self.archive_extract_buttons = {}
        
        for i, archive in enumerate(self.mvgls):
            button = QtWidgets.QPushButton(f"Extract {archive}", parentWidget)
            button.setFixedWidth(120)
            self.archive_extract_buttons[archive] = button

        
    def lay_out(self):
        self.layout.setRowStretch(0, 1)
        for i, archive in enumerate(self.mvgls):
            button = self.archive_extract_buttons[archive]
            self.layout.addWidget(button, i+1, 0)
            self.layout.setRowStretch(i+1, 0)
        self.layout.setRowStretch(i+2, 1)
        
        self.setLayout(self.layout)
        
    def hook(self, dscstools_dump_factory):
        for archive in self.mvgls:
            self.archive_extract_buttons[archive].clicked.connect(dscstools_dump_factory(archive))
            
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

# class ModManagerUI:
#     def define_ui(self): 
#         self.define_menu()
#         self.define_main_window()
#         self.define_mod_interaction_area()
#         self.define_action_tabs()
#         self.define_log_history()
        
#     def define_main_window(self):
#         self.window = QtWidgets.QWidget() 
#         self.layout = QtWidgets.QGridLayout() 
#         self.setCentralWidget(self.window) 
#         self.window.setLayout(self.layout)
        
#     def define_menu(self):
#         self.fileMenu = QtWidgets.QMenu("&File", self)
#         self.helpMenu = QtWidgets.QMenu("&Help", self)
#         self.menuBar().addMenu(self.fileMenu)
#         self.menuBar().addMenu(self.helpMenu)
        
#         self.donateAction = QtWidgets.QAction("Support Digimon Game Research...", self)
#         self.helpMenu.addAction(self.donateAction)
        
#     def define_mod_interaction_area(self):
#         self.define_profile_interaction_widgets()
#         self.define_mods_display()
#         self.define_mod_installation_widgets()
    
#     def define_mods_display(self):    
#         self.mods_display = DragDropTreeView(self) 
#         model = QtGui.QStandardItemModel(self.mods_display)
#         model.setHorizontalHeaderLabels(["Name", "Author", "Version", "Category"])
#         self.mods_display.setModel(model)
#         self.mods_display.setMinimumSize(500, 300)
#         self.mods_display.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  
#         self.mods_display.setColumnWidth(0, 200)
#         self.mods_display.setColumnWidth(2, 50)
        
#     def define_profile_interaction_widgets(self):
#         self.new_profile_button = QtWidgets.QPushButton("New Profile", self)
#         self.new_profile_button.setFixedWidth(100)
#         self.rename_profile_button = QtWidgets.QPushButton("Rename Profile", self)
#         self.rename_profile_button.setFixedWidth(100)
#         self.delete_profile_button = QtWidgets.QPushButton("Delete Profile", self)
#         self.delete_profile_button.setFixedWidth(100)
        
#         self.profile_selector = ComboBox(self)
        
#     def define_mod_installation_widgets(self):
#         self.install_mods_button = QtWidgets.QPushButton("Install Mods", self)
#         self.install_mods_button.setFixedWidth(120)
#         self.restore_backups_button = QtWidgets.QPushButton("Restore Backups", self)
#         self.restore_backups_button.setFixedWidth(120)
        
#     def define_action_tabs(self):
#         self.actions = QtWidgets.QTabWidget()
#         self.actions.setMinimumSize(500, 300)
#         self.configTab = QtWidgets.QWidget()
#         self.extractTab = QtWidgets.QWidget()
#         self.dscstoolsTab = QtWidgets.QWidget()
#         self.conflictsTab = QtWidgets.QWidget()
#         self.actions.addTab(self.configTab, "Configuration")
#         self.actions.addTab(self.extractTab, "Extract")
#         self.actions.addTab(self.conflictsTab, "Conflicts")
        
#         self.define_config_tab()
        
#     def define_config_tab(self):
#         layout = QtWidgets.QGridLayout()
#         self.game_location_layout = QtWidgets.QGridLayout()
#         self.game_location_label = QtWidgets.QLabel("Game Location:  ", self)
#         self.game_location_textbox = QtWidgets.QLineEdit(self)
#         self.game_location_textbox.setReadOnly(True)
#         self.game_location_button = QtWidgets.QPushButton("...", self)
#         self.game_location_button.setFixedWidth(20)
#         self.game_location_layout.addWidget(self.game_location_label, 0, 0)
#         self.game_location_layout.addWidget(self.game_location_textbox, 0, 1)
#         self.game_location_layout.addWidget(self.game_location_button, 0, 2)
#         self.game_location_layout.setSpacing(0)
#         self.dscstools_buttons_layout = QtWidgets.QGridLayout()
#         self.update_dscstools_button = QtWidgets.QPushButton("Update DSCSTools", self)
#         self.update_dscstools_button.setFixedWidth(120)
        
#         self.dscstools_buttons_layout.addWidget(self.update_dscstools_button, 0, 0)
        
#         layout.addLayout(self.game_location_layout, 0, 0)
#         layout.addLayout(self.dscstools_buttons_layout, 1, 0)
#         layout.setRowStretch(0, 0)
#         layout.setRowStretch(1, 0)
#         layout.setRowStretch(2, 1)
        
#         self.configTab.setLayout(layout)
        
#     def define_log_history(self):
#         self.logview = QtWidgets.QListWidget()
#         self.logview.setAlternatingRowColors(True)
#         self.logview.setWordWrap(False) 
#         self.logview.setFixedHeight(100)
    
#     def layout_ui(self):
#         profile_interaction_widgets = QtWidgets.QGridLayout()
#         profile_interaction_widgets.addWidget(self.new_profile_button, 0, 0)
#         profile_interaction_widgets.addWidget(self.rename_profile_button, 0, 1)
#         profile_interaction_widgets.addWidget(self.delete_profile_button, 0, 2)
#         profile_interaction_widgets.addWidget(self.profile_selector, 0, 3)
        
#         mods_display_area = QtWidgets.QGridLayout()
#         mods_display_area.addWidget(self.mods_display, 0, 0)
        
#         mods_installation_widgets = QtWidgets.QGridLayout()
#         mods_installation_widgets.addWidget(self.install_mods_button, 0, 0)
#         mods_installation_widgets.addWidget(self.restore_backups_button, 0, 1)
        
#         leftpane = QtWidgets.QGridLayout()
#         leftpane.addLayout(profile_interaction_widgets, 0, 0)
#         leftpane.addLayout(mods_display_area, 1, 0)
#         leftpane.addLayout(mods_installation_widgets, 2, 0)
        
#         rightpane = QtWidgets.QGridLayout()
#         rightpane.addWidget(self.actions, 0, 0)
        
#         main_area = QtWidgets.QGridLayout()
#         main_area.addLayout(leftpane, 0, 0)
#         main_area.addLayout(rightpane, 0, 1)
        
#         logging_area = QtWidgets.QGridLayout()
#         logging_area.addWidget(self.logview, 0, 0)
        
#         self.layout.addLayout(main_area, 0, 0)
#         self.layout.addLayout(logging_area, 1, 0)
        
           
#     def hook_ui(self, open_patreon, profile_handler, draw_conflicts_graph, find_gamelocation, update_dscstools):
#         self.hook_menu(open_patreon)
#         self.hook_profile_interaction_widgets(profile_handler)
#         self.hook_mod_installation_widgets()
#         self.hook_tabs(draw_conflicts_graph, find_gamelocation, update_dscstools)
        
#     def hook_profile_interaction_widgets(self, profile_handler):
#         self.new_profile_button.clicked.connect(profile_handler.new_profile)
#         self.rename_profile_button.clicked.connect(profile_handler.rename_profile)
#         self.delete_profile_button.clicked.connect(profile_handler.delete_profile)
#         self.profile_selector.popupAboutToBeShown.connect(profile_handler.save_profile)
#         self.profile_selector.currentIndexChanged.connect(profile_handler.apply_profile)
    
#     def hook_menu(self, open_patreon):
#         self.donateAction.triggered.connect(open_patreon)

#     def hook_mod_installation_widgets(self):
#         pass
    
#     def hook_tabs(self, draw_conflicts_graph, find_gamelocation, update_dscstools):
#         self.actions.currentChanged.connect(draw_conflicts_graph)
        
#         # Config tab
#         self.game_location_button.clicked.connect(find_gamelocation)
#         self.update_dscstools_button.clicked.connect(update_dscstools)
    
    