from PyQt5 import QtCore, QtGui, QtWidgets
from datetime import datetime

from .CustomWidgets import ClickEmitComboBox, DragDropTreeView, LinkItem

translate = QtCore.QCoreApplication.translate

def safe_disconnect(func):
    try:
        func.disconnect()
    except TypeError:
        pass
        
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
        self.layout.setRowStretch(0, 4)
        self.layout.setRowStretch(1, 1)
        
    def create_shortcuts(self):
        self.profile_selector = self.main_area.mod_interaction_area.profile_interaction_widgets.profile_selector
        self.mods_display = self.main_area.mod_interaction_area.mods_display_area.mods_display
        self.game_location_textbox = self.main_area.action_tabs.configTab.game_location_textbox
        self.conflicts_graph = self.main_area.action_tabs.conflictsTab.conflicts_graph

        self.hook_menu                       = self.menu.hook
        self.hook_filemenu                   = self.menu.hook_filemenu
        self.hook_languageaction             = self.menu.hook_languageaction
        self.hook_profle_interaction_widgets = self.main_area.mod_interaction_area.profile_interaction_widgets.hook
        self.hook_action_tabs                = self.main_area.action_tabs.hook
        self.hook_modinfo_tab                = self.main_area.action_tabs.modInfoTab.hook
        self.hook_config_tab                 = self.main_area.action_tabs.configTab.hook
        self.hook_extract_tab                = self.main_area.action_tabs.extractTab.hook
        self.hook_mod_registry               = self.main_area.mod_interaction_area.mods_display_area.mods_display.hook_registry_function
        self.hook_delete_mod_menu            = self.main_area.mod_interaction_area.mods_display_area.hook_delete_mod
        self.hook_wizard_mod_menu            = self.main_area.mod_interaction_area.mods_display_area.hook_wizard_funcs
        self.hook_update_mod_info_window     = self.main_area.mod_interaction_area.mods_display_area.update_mod_info_window
        self.hook_install_button             = self.main_area.mod_interaction_area.mod_installation_widgets.hook_install_button
        self.hook_game_launch_button         = self.main_area.mod_interaction_area.mod_installation_widgets.hook_game_launch_button
        self.hook_backup_button              = self.main_area.mod_interaction_area.mod_installation_widgets.hook_backup_button
        
        self.log                             = self.logging_area.logview.log
        self.loglink                         = self.logging_area.logview.loglink
        self.updateLog                       = self.logging_area.logview.updateLog
        
        self.set_mod_info                    = self.main_area.action_tabs.modInfoTab.modinfo_region.setModInfo
        self.createLanguageMenu              = self.menu.createLanguageMenu
        
        # Widgets
        self.action_tabs                     = self.main_area.action_tabs
        self.mods_display_area               = self.main_area.mod_interaction_area.mods_display_area
        self.mod_installation_widgets        = self.main_area.mod_interaction_area.mod_installation_widgets
        self.profile_interaction_widgets     = self.main_area.mod_interaction_area.profile_interaction_widgets
        self.modinfo_tab                     = self.main_area.action_tabs.modInfoTab
        self.config_tab                      = self.main_area.action_tabs.configTab
        self.extract_tab                     = self.main_area.action_tabs.extractTab
        self.modinfo_region                  = self.modinfo_tab.modinfo_region
        
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
        self.parentWidget = parentWidget
        self.define(parentWidget)
        self.lay_out()
        self.set_language_func = lambda x: None
        
    def define(self, parentWidget):
        self.language_actions = []
        self.fileMenu = QtWidgets.QMenu(parentWidget)
        self.languageMenu = QtWidgets.QMenu(parentWidget)
        self.helpMenu = QtWidgets.QMenu(parentWidget)
        parentWidget.menuBar().addMenu(self.fileMenu)
        parentWidget.menuBar().addMenu(self.languageMenu)
        parentWidget.menuBar().addMenu(self.helpMenu)
                
        self.addModAction = QtWidgets.QAction(parentWidget)
        self.fileMenu.addAction(self.addModAction)
        
        self.donateAction = QtWidgets.QAction(parentWidget)
        self.helpMenu.addAction(self.donateAction)
        
        self.creditsAction = QtWidgets.QAction(parentWidget)
        self.creditsAction.triggered.connect(lambda : creditsPopup(self.parentWidget))
        self.helpMenu.addAction(self.creditsAction)
        
        self.aboutQtAction = QtWidgets.QAction(parentWidget)
        self.aboutQtAction.triggered.connect(lambda : QtWidgets.QMessageBox.aboutQt(self.parentWidget))
        self.helpMenu.addAction(self.aboutQtAction)
        
    def lay_out(self):
        pass
    
    def hook(self, open_patreon):
        self.donateAction.triggered.connect(open_patreon)
        
    def hook_filemenu(self, register_mod_dialog):
        self.addModAction.triggered.connect(register_mod_dialog)
        
    def hook_languageaction(self, set_language_func):
        self.set_language_func = set_language_func
        
    def enable(self):
        self.toggle_active(True)
        
    def disable(self):
        self.toggle_active(True)
        
    def toggle_active(self, active):
        self.addModAction.setEnabled(active)
        
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.fileMenu.setTitle(translate("UI::MenuBar", "&File"))
        self.languageMenu.setTitle(translate("UI::MenuBar", "&Language"))
        self.helpMenu.setTitle(translate("UI::MenuBar", "&Help"))
        self.addModAction.setText(translate("UI::FileMenu", "Add Mod..."))
        self.donateAction.setText(translate("UI::HelpMenu", "Support Digimon Game Research..."))
        self.creditsAction.setText(translate("UI::HelpMenu", "Credits"))
        self.aboutQtAction.setText(translate("UI::HelpMenu", "About Qt"))
        
    def createLanguageMenu(self, language_files):
        self.language_actions = []
        self.languageMenu.clear()
        def generate_func(file):
            return lambda : self.set_language_func(file) 
        for name, file in language_files.items():
            act = QtWidgets.QAction(name, self.parentWidget)
            act.triggered.connect(generate_func(file))
            self.language_actions.append(act)
            
            self.languageMenu.addAction(act)
            
class creditsPopup:
    def __init__(self, win):
        msgBox = QtWidgets.QMessageBox(win)
        msgBox.setWindowTitle(translate("UI::Credts", "Credits"))
        
        msgBoxText = translate("UI::Credits", "The people on this list have all significantly contributed to SimpleDSCSModManager in some way. They have my deepest thanks.")
        msgBoxText += "<br><br>"
        msgBoxText += "<b>" + translate("UI::Credits", "Special Thanks") + "</b>"
        msgBoxText += "<br>"
        msgBoxText += " " + translate("Common::ListElementsSeparator", ", ").join(["Romsstar", "SydMontague"])
        msgBoxText += "<br>"
        msgBoxText += "<br>"
        msgBoxText +=" <b>" + translate("UI::Credits", "Bugtesting") + "</b>"
        msgBoxText += "<br>"
        msgBoxText += " " + translate("Common::ListElementsSeparator", ", ").join(["A Heroic Panda", "KiroAkashima", "SydMontague"])
        msgBoxText += "<br>"
        msgBoxText += "<br>"
        msgBoxText += "<b>" + translate("UI::Credits", "Translations") + "</b>"
        msgBoxText += "<br>"
        msgBoxText += u"Español (España):"
        msgBoxText += " " + translate("Common::ListElementsSeparator", ", ").join(["IlDucci"])
        # More translations here
        
        msgBoxText += "<br>"
        msgBoxText += "<br>"
        msgBoxText += "<b>" + translate("UI::Credits", "Tool and Software Dependencies") + "</b>"
        msgBoxText += "<br>"
        msgBoxText += "<a href=\"https://github.com/SydMontague/DSCSTools\">"
        msgBoxText += u"DSCSTools</a>: SydMontague"
        msgBoxText += "<br>"
        msgBoxText += "<a href=\"https://sourceforge.net/projects/squirrel/files/squirrel2/squirrel%202.2.4%20stable/\">"
        msgBoxText += u"Squirrel 2.2.4</a>: Alberto Demichelis"
        msgBoxText += "<br>"
        msgBoxText += "<a href=\"https://github.com/SydMontague/NutCracker\">"
        msgBoxText += u"NutCracker</a>: DamianXVI (64-bit port: SydMontague)"
        msgBoxText += "<br>"
        msgBoxText += "<a href=\"https://github.com/Thealexbarney/VGAudio\">"
        msgBoxText += u"VGAudio</a>: Thealexbarney"
        msgBoxText += "<br>"
        msgBoxText += "<a href=\"https://github.com/Pherakki/Blender-Tools-for-DSCS/\">"
        msgBoxText += u"Blender Tools for DSCS</a>: Pherakki"
        
        msgBox.setText(msgBoxText)
        
        msgBox.exec_()


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
        
        self.new_profile_button = QtWidgets.QPushButton(parentWidget)
        self.new_profile_button.setFixedWidth(100)
        self.rename_profile_button = QtWidgets.QPushButton(parentWidget)
        self.rename_profile_button.setFixedWidth(100)
        self.delete_profile_button = QtWidgets.QPushButton(parentWidget)
        self.delete_profile_button.setFixedWidth(100)
        
        self.profile_selector = ClickEmitComboBox(parentWidget)
        self.profile_selector.wheelEvent = lambda event: None
        
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):      
        self.new_profile_button.setText(translate("UI::NewProfileButton", "New Profile"))
        self.rename_profile_button.setText(translate("UI::RenameProfileButton", "Rename Profile"))
        self.delete_profile_button.setText(translate("UI::DeleteProfileButton", "Delete Profile"))
        
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
    

class uiModsDisplay(QtCore.QObject):
    def __init__(self, parentWidget):
        super().__init__(parentWidget)
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        self.mods_display = DragDropTreeView(parentWidget) 

        self.md_model = QtGui.QStandardItemModel(self.mods_display)
        self.md_model.setHorizontalHeaderLabels([translate("UI::ModsDisplay", "Name"), translate("UI::ModsDisplay", "Author"), translate("UI::ModsDisplay", "Version"), translate("UI::ModsDisplay", "Category")])
        self.mods_display.setModel(self.md_model)
        
        self.mods_display.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  
        self.mods_display.setColumnWidth(0, 200)
        self.mods_display.setColumnWidth(2, 50)
        self.mods_display.setMinimumSize(500, 300)
        
        self.contextMenu = QtWidgets.QMenu()
        self.reinstallModAction = self.contextMenu.addAction("Re-register...")
        self.deleteModAction = self.contextMenu.addAction("Delete Mod")
        
        self.mods_display.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.mods_display.customContextMenuRequested.connect(self.menuContextTree)
        self.deleteModFunction = None
        self.hasWizardFunc = None
        self.reinstallModFunction = None
        
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):    
        self.md_model.setHorizontalHeaderLabels([translate("UI::ModsDisplay", "Name"), translate("UI::ModsDisplay", "Author"), translate("UI::ModsDisplay", "Version"), translate("UI::ModsDisplay", "Category")])
        self.reinstallModAction.setText(translate("UI::ModRightClickMenu", "Re-register..."))
        self.deleteModAction.setText(translate("UI::ModRightClickMenu", "Delete Mod"))
        
        
    def lay_out(self):
        self.layout.addWidget(self.mods_display, 0, 0)
    
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        self.mods_display.setEnabled(active)

    @QtCore.pyqtSlot(QtCore.QPoint)
    def menuContextTree(self, point):
        safe_disconnect(self.deleteModAction.triggered)
        safe_disconnect(self.reinstallModAction.triggered)

        # Infos about the node selected.
        index = self.mods_display.indexAt(point)

        if not index.isValid():
            return
        
        mod_id = self.mods_display.display_data[index.row()][self.mods_display.id_column]
        
        has_wizard = self.hasWizardFunc(mod_id)
        self.reinstallModAction.setEnabled(has_wizard)

        self.reinstallModAction.triggered.connect(lambda: self.reinstallModFunction(mod_id))
        self.deleteModAction.triggered.connect(lambda: self.deleteModFunction(mod_id))

        self.contextMenu.exec_(self.mods_display.mapToGlobal(point))
        
    def hook_delete_mod(self, func):
        self.deleteModFunction = func
        
    def hook_wizard_funcs(self, hasWizardFunc, reinstallModFunction):
        self.hasWizardFunc = hasWizardFunc
        self.reinstallModFunction = reinstallModFunction
        
    def update_mod_info_window(self, func):
        self.mods_display.update_mods_func = func
        
    def hook_itemchanged(self, func):
        self.mods_display.model.itemChanged.connect(func)

class uiModInstallationWidgets:
    def __init__(self, parentWidget):
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.install_mods_button = QtWidgets.QPushButton(parentWidget)
        self.install_mods_button.setFixedWidth(120)
        self.launch_game_button = QtWidgets.QPushButton(parentWidget)
        self.launch_game_button.setFixedWidth(120)
        self.restore_backups_button = QtWidgets.QPushButton(parentWidget)
        self.restore_backups_button.setFixedWidth(120)     
        
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):    
        self.install_mods_button.setText(translate("UI::InstallModsButton", "Install Mods"))
        self.launch_game_button.setText(translate("UI::LaunchGameButton", "Launch Game"))
        self.restore_backups_button.setText(translate("UI::UninstallModsButton", "Restore Backups"))
        
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
        
        
class uiLogHistory(QtCore.QObject):
    def __init__(self, parentWidget):
        super().__init__()
        self.max_items = 500
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.logview = QtWidgets.QListWidget()
        self.logview.setAlternatingRowColors(True)
        self.logview.setWordWrap(False) 
        self.logview.setMinimumHeight(110)
        
        
    def lay_out(self):
        self.layout.addWidget(self.logview, 0, 0)
        
    @QtCore.pyqtSlot(str)
    def log(self, message):
        self.loglink(message)
        #adj_message = self.timestamp_string(message)
        #self.logview.addItem(adj_message)
        #self.cull_messages()
        #self.logview.scrollToBottom()
        
    @QtCore.pyqtSlot(str)
    def loglink(self, message):
        adj_message = self.timestamp_string(message)
        linkwidget = LinkItem(adj_message)
        dummyItem = QtWidgets.QListWidgetItem(self.logview)
        dummyItem.setSizeHint(QtCore.QSize(0, 18))
        
        self.logview.addItem(dummyItem)
        self.logview.setItemWidget(dummyItem, linkwidget)
        
        self.cull_messages()
        self.logview.scrollToBottom()
        
    @QtCore.pyqtSlot(str)
    def updateLog(self, message):
        #adj_message = self.timestamp_string(message)
        self.logview.takeItem(self.logview.count() - 1)
        #self.logview.addItem(adj_message)
        self.loglink(message)
        #self.logview.scrollToBottom()
    
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
        self.retranslateUi()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.actions = QtWidgets.QTabWidget()
        self.actions.setMinimumSize(500, 300)
        self.modInfoTab = uiModInfoTab(parentWidget)
        self.configTab = uiConfigTab(parentWidget)
        self.extractTab = uiExtractTab(parentWidget)
        self.conflictsTab = uiConflictsTab(parentWidget)
        
    def lay_out(self):
        self.actions.addTab(self.modInfoTab, "Mod Info")
        self.actions.addTab(self.configTab, "Configuration")
        self.actions.addTab(self.extractTab, "Extract")
        #self.actions.addTab(self.conflictsTab, "Conflicts")
        
        self.layout.addWidget(self.actions, 0, 0)
        
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.actions.setTabText(0, translate("UI::ModInfoTab", "Mod Info"))
        self.actions.setTabText(1, translate("UI::ModInfoTab", "Configuration"))
        self.actions.setTabText(2, translate("UI::ModInfoTab", "Extract"))
        #self.actions.setTabText(3, translate("UI::ModInfoTab", "Conflicts"))
        
    def hook(self, draw_conflicts_graph):
        self.actions.currentChanged.connect(draw_conflicts_graph)
    
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)   
        
    def toggle_active(self, active):
        self.modInfoTab.toggle_active(active)
        self.configTab.toggle_active(active)
        self.extractTab.toggle_active(active)
        self.conflictsTab.toggle_active(active)
    
class uiModInfoTab(QtWidgets.QWidget):
    def __init__(self, parentWidget):
        super().__init__()
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QVBoxLayout()
        
        self.modinfo_region= ModInfoRegion(parentWidget)
        
    def lay_out(self):
        self.layout.addLayout(self.modinfo_region.layout, 0)
        self.setLayout(self.layout)
        
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        pass
    
    def hook(self):
        pass
        
class ModInfoRegion:
    def __init__(self, parentWidget):
        super().__init__()
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QGridLayout()
        
        self.modname_label = QtWidgets.QLabel(parentWidget)
        self.modfolder_label = QtWidgets.QLabel(parentWidget)
        self.modauthors_label = QtWidgets.QLabel(parentWidget)
        self.modversion_label = QtWidgets.QLabel(parentWidget)
        self.moddesc_box = QtWidgets.QTextBrowser(parentWidget) # QtWidgets.QTextEdit("", parentWidget)
        # self.moddesc_box.setReadOnly(True)
        
        none_selected = translate("UI::ModInfo::NoSelection", "[None Selected]")
        self.active_modname = none_selected
        self.active_modfolder = none_selected
        self.active_modauthors = none_selected
        self.active_modversion = none_selected
        self.active_moddesc = ""
        
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):   
        self.modname_label.setText(translate("UI::ModInfo", "Mod Name: {string}").format(string=self.active_modname))
        self.modfolder_label.setText(translate("UI::ModInfo", "Mod Folder: {string}").format(string=self.active_modfolder))
        self.modauthors_label.setText(translate("UI::ModInfo", "Author(s): {string}").format(string=self.active_modauthors))
        self.modversion_label.setText(translate("UI::ModInfo", "Version: {string}").format(string=self.active_modversion))
        self.moddesc_box.setText(self.active_moddesc)
        
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
        self.active_modname = string
        
    def setModFolder(self, string):
        self.active_modfolder = string
        
    def setModAuthor(self, string):
        self.active_modauthors = string
        
    def setModVersion(self, string):
        self.active_modversion = string
        
    def setModDesc(self, string):
        self.active_moddesc = string
        
    def setModInfo(self, name, folder, author, version, desc):
        self.setModName(name)
        self.setModFolder(folder)
        self.setModAuthor(author)
        self.setModVersion(version)
        self.setModDesc(desc)
        self.retranslateUi()

class uiConfigTab(QtWidgets.QWidget):
    
    def __init__(self, parentWidget):
        super().__init__()
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.layout = QtWidgets.QVBoxLayout()
        
        self.game_location_layout = QtWidgets.QHBoxLayout()
        self.game_location_label = QtWidgets.QLabel(parentWidget)
        self.game_location_textbox = QtWidgets.QLineEdit(parentWidget)
        self.game_location_textbox.setReadOnly(True)
        self.game_location_button = QtWidgets.QPushButton("...", parentWidget)
        self.game_location_button.setFixedWidth(20)
        self.game_location_layout.addWidget(self.game_location_label)
        self.game_location_layout.addWidget(self.game_location_textbox)
        self.game_location_layout.addWidget(self.game_location_button)
        self.game_location_layout.setSpacing(0)
        
        
        self.buttons_layout = QtWidgets.QGridLayout()
        self.update_dscstools_button = QtWidgets.QPushButton(parentWidget)
        self.update_dscstools_button.setFixedWidth(120)
        self.update_dscstools_button.setEnabled(False)
        
        self.purge_softcodes_button = QtWidgets.QPushButton(parentWidget)
        self.purge_softcodes_button.setFixedWidth(120)
        
        self.purge_indices_button = QtWidgets.QPushButton(parentWidget)
        self.purge_indices_button.setFixedWidth(120)
        
        self.purge_cache_button = QtWidgets.QPushButton(parentWidget)
        self.purge_cache_button.setFixedWidth(120)
        
        self.purge_resources_button = QtWidgets.QPushButton(parentWidget)
        self.purge_resources_button.setFixedWidth(120)
        
        self.crash_handle_layout = QtWidgets.QHBoxLayout(parentWidget)
        self.crash_handle_label = QtWidgets.QLabel()
        self.crash_handle_label.setFixedWidth(120)
        self.crash_handle_box = QtWidgets.QComboBox(parentWidget)
        self.crash_handle_box.setFixedWidth(120)
        
        self.block_handle_layout = QtWidgets.QHBoxLayout(parentWidget)
        self.block_handle_label = QtWidgets.QLabel()
        self.block_handle_label.setFixedWidth(120)
        self.block_handle_box = QtWidgets.QComboBox(parentWidget)
        self.block_handle_box.setFixedWidth(120)
        
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.game_location_label.setText(translate("UI::GameLocationLabel", "Game Location: "))
        
        self.update_dscstools_button.setText(translate("UI::UpdateDSCSToolsButton", "Update DSCSTools"))
        self.purge_softcodes_button.setText(translate("UI::PurgeSoftcodes", "Purge softcodes"))
        self.purge_indices_button.setText(translate("UI::PurgeModIndicesButton", "Purge mod indices"))
        self.purge_cache_button.setText(translate("UI::PurgeModCacheButton", "Purge mod cache"))
        self.purge_resources_button.setText(translate("UI::PurgeResourcesButton", "Purge mod resources"))
        
        self.crash_handle_label.setText(translate("UI::CrashMethodBox", "Crash method: "))
        self.block_handle_label.setText(translate("UI::GameLaunchMethodBox", "Game launch method: "))
        
        for i, text in enumerate(self.crash_handler_options()):
            self.crash_handle_box.setItemText(i, text)
        for i, text in enumerate(self.block_handler_operations()):
            self.block_handle_box.setItemText(i, text)
        
    def lay_out(self):
        self.crash_handle_layout.addWidget(self.crash_handle_label, 0)
        self.crash_handle_layout.addWidget(self.crash_handle_box, 0)
        
        self.block_handle_layout.addWidget(self.block_handle_label, 0)
        self.block_handle_layout.addWidget(self.block_handle_box, 0)
        
        self.buttons_layout.addWidget(self.update_dscstools_button, 0, 0)
        self.buttons_layout.addWidget(self.purge_softcodes_button, 1, 0)
        self.buttons_layout.addWidget(self.purge_indices_button, 2, 0)
        self.buttons_layout.addWidget(self.purge_cache_button, 3, 0)
        self.buttons_layout.addWidget(self.purge_resources_button, 4, 0)
        
        self.layout.addLayout(self.game_location_layout, 0)
        self.layout.addLayout(self.buttons_layout, 1)
        self.layout.addLayout(self.crash_handle_layout, 2)
        self.layout.addLayout(self.block_handle_layout, 3)
        self.setLayout(self.layout)
        
    def hook(self, find_gamelocation, update_dscstools, purge_softcodes, purge_indices,
             purge_cache, purge_resources, update_crash_handler, crash_handler_options,
             update_block_handler, block_handler_operations):
        self.crash_handler_options = crash_handler_options
        self.block_handler_operations = block_handler_operations
        
        self.game_location_button.clicked.connect(find_gamelocation)
        self.update_dscstools_button.clicked.connect(update_dscstools)
        self.purge_softcodes_button.clicked.connect(purge_softcodes)
        self.purge_indices_button.clicked.connect(purge_indices)
        self.purge_cache_button.clicked.connect(purge_cache)
        self.purge_resources_button.clicked.connect(purge_resources)
        self.crash_handle_box.currentIndexChanged.connect(update_crash_handler)
        self.block_handle_box.currentIndexChanged.connect(update_block_handler)
        
        for option in crash_handler_options():
            self.crash_handle_box.addItem(option)
        for option in block_handler_operations():
            self.block_handle_box.addItem(option)
            
        
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        self.game_location_textbox.setEnabled(active)
        self.game_location_button.setEnabled(active)
        # self.update_dscstools_button.setEnabled(active)
        self.purge_softcodes_button.setEnabled(active)
        self.purge_indices_button.setEnabled(active)
        self.purge_cache_button.setEnabled(active)
        self.purge_resources_button.setEnabled(active)
        self.crash_handle_box.setEnabled(active)
        self.block_handle_box.setEnabled(active)
        
class uiExtractTab(QtWidgets.QScrollArea):
    def __init__(self, parentWidget):
        self.data_mvgls = ["DSDB", "DSDBA", "DSDBS", "DSDBSP", "DSDBP"]
        self.sound_mvgls = ["DSDBse", "DSDBPse"]
        self.bgm_afs2s = ["DSDBbgm", "DSDBPDSEbgm"]
        self.vo_afs2s = ["DSDBvo", "DSDBPvo", "DSDBPvous"]
        self.data_archive_extract_buttons = {}
        self.snds_archive_extract_buttons = {}
        self.bgm_afs2_extract_buttons = {}
        self.vo_afs2_extract_buttons = {}
        
        super().__init__()
        self.define(parentWidget)
        self.lay_out()
        
    def define(self, parentWidget):
        self.scrollArea = QtWidgets.QWidget()
        self.scrollArealayout = QtWidgets.QGridLayout()
        
        self.autoextract_widget = QtWidgets.QWidget()
        self.autoextract_layout = QtWidgets.QGridLayout()
        self.mdb1_layout = QtWidgets.QVBoxLayout()
        self.afs2_layout = QtWidgets.QVBoxLayout()
        
        self.manualextract_widget = QtWidgets.QWidget()
        self.manualextract_layout = QtWidgets.QGridLayout()
        self.dscstools_widget = QtWidgets.QWidget()
        self.dscstools_layout = QtWidgets.QGridLayout()
        self.scripts_widget = QtWidgets.QWidget()
        self.scripts_layout= QtWidgets.QGridLayout()
        self.vgstream_widget = QtWidgets.QWidget()
        self.vgstream_layout = QtWidgets.QGridLayout()
        
        self.data_mdb1_label = QtWidgets.QLabel()
        self.data_mdb1_label.setAlignment(QtCore.Qt.AlignCenter)
        for i, archive in enumerate(self.data_mvgls):
            button = QtWidgets.QPushButton(parentWidget)
            button.setFixedWidth(130)
            button.setFixedHeight(22)
            self.data_archive_extract_buttons[archive] = button

        self.snds_mdb1_label = QtWidgets.QLabel()
        self.snds_mdb1_label.setAlignment(QtCore.Qt.AlignCenter)
        for i, archive in enumerate(self.sound_mvgls):
            button = QtWidgets.QPushButton(parentWidget)
            button.setFixedWidth(130)
            button.setFixedHeight(22)
            self.snds_archive_extract_buttons[archive] = button
            
        self.bgm_afs2_label = QtWidgets.QLabel()
        self.bgm_afs2_label.setAlignment(QtCore.Qt.AlignCenter)
        for i, archive in enumerate(self.bgm_afs2s):
            button = QtWidgets.QPushButton(parentWidget)
            button.setFixedWidth(130)
            button.setFixedHeight(22)
            self.bgm_afs2_extract_buttons[archive] = button
            
        self.vo_afs2_label = QtWidgets.QLabel()
        self.vo_afs2_label.setAlignment(QtCore.Qt.AlignCenter)
        for i, archive in enumerate(self.vo_afs2s):
            button = QtWidgets.QPushButton(parentWidget)
            button.setFixedWidth(130)
            button.setFixedHeight(22)
            self.vo_afs2_extract_buttons[archive] = button
            
        self.dscstools_label = QtWidgets.QLabel()
        self.dscstools_label.setAlignment(QtCore.Qt.AlignCenter)
        self.extract_mdb1_button = self.new_button("", parentWidget)
        self.pack_mdb1_button = self.new_button("", parentWidget)
        self.extract_afs2_button = self.new_button("", parentWidget)
        self.pack_afs2_button = self.new_button("", parentWidget)
        self.extract_mbes_button = self.new_button("", parentWidget)
        self.pack_mbes_button = self.new_button("", parentWidget)
        
        self.scripts_label = QtWidgets.QLabel()
        self.scripts_label.setAlignment(QtCore.Qt.AlignCenter)
        self.decompile_scripts_button = self.new_button("", parentWidget)
        self.compile_scripts_button = self.new_button("", parentWidget)
        
        self.sounds_label = QtWidgets.QLabel()
        self.sounds_label.setAlignment(QtCore.Qt.AlignCenter)
        self.hca_to_wav = self.new_button("", parentWidget)
        self.hca_to_wav.setEnabled(False)
        self.wav_to_hca = self.new_button("", parentWidget)
        self.wav_to_hca.setEnabled(False)
        
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.data_mdb1_label.setText(translate("UI::ExtractTab", "Auto-Extract Database Files"))
        for archive, button in self.data_archive_extract_buttons.items():
            button.setText(translate("UI::ExtractTab", "Extract {item}").format(item=archive))
            
        self.snds_mdb1_label.setText(translate("UI::ExtractTab", "Auto-Extract SFX Files"))
        for archive, button in self.snds_archive_extract_buttons.items():
            button.setText(translate("UI::ExtractTab", "Extract {item}").format(item=archive))
            
        self.bgm_afs2_label.setText(translate("UI::ExtractTab","Auto-Extract BGM"))
        for archive, button in self.bgm_afs2_extract_buttons.items():
            button.setText(translate("UI::ExtractTab", "Extract {item}").format(item=archive))
            
        self.vo_afs2_label.setText(translate("UI::ExtractTab", "Auto-Extract Voice Lines"))
        for archive, button in self.vo_afs2_extract_buttons.items():
            button.setText(translate("UI::ExtractTab", "Extract {item}").format(item=archive))
            
        self.dscstools_label.setText(translate("UI::ExtractTab", "General Data Extraction"))
        self.extract_mdb1_button.setText(translate("UI::ExtractTab", "Extract MDB1"))
        self.pack_mdb1_button.setText(translate("UI::ExtractTab",    "Pack MDB1"))
        self.extract_afs2_button.setText(translate("UI::ExtractTab", "Extract AFS2"))
        self.pack_afs2_button.setText(translate("UI::ExtractTab",    "Pack AFS2"))
        self.extract_mbes_button.setText(translate("UI::ExtractTab", "Extract MBEs"))
        self.pack_mbes_button.setText(translate("UI::ExtractTab",    "Pack MBEs"))
        
        self.scripts_label.setText(translate("UI::ExtractTab", "Scripts"))
        self.decompile_scripts_button.setText(translate("UI::ExtractTab", "Decompile scripts"))
        self.compile_scripts_button.setText(translate("UI::ExtractTab", "Compile scripts"))
        
        self.sounds_label.setText(translate("UI::ExtractTab", "Sounds"))
        self.hca_to_wav.setText(translate("UI::ExtractTab", "Convert HCA to WAV"))
        self.wav_to_hca.setText(translate("UI::ExtractTab", "Convert WAV to HCA"))
    
    def lay_out(self):
        # Lay out the LHS button pane
        self.mdb1_layout.addWidget(self.data_mdb1_label, 0)
        for i, archive in enumerate(self.data_mvgls):
            button = self.data_archive_extract_buttons[archive]
            self.mdb1_layout.addWidget(button, 0)
            
        self.mdb1_layout.addWidget(self.snds_mdb1_label, 0)
        for i, archive in enumerate(self.sound_mvgls):
            button = self.snds_archive_extract_buttons[archive]
            self.mdb1_layout.addWidget(button, 0)
        
        self.afs2_layout.addWidget(self.bgm_afs2_label, 0)
        for i, archive in enumerate(self.bgm_afs2s):
            button = self.bgm_afs2_extract_buttons[archive]
            self.afs2_layout.addWidget(button, 0)
            
        self.afs2_layout.addWidget(self.vo_afs2_label, 0)
        for i, archive in enumerate(self.vo_afs2s):
            button = self.vo_afs2_extract_buttons[archive]
            self.afs2_layout.addWidget(button, 0)
        
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
        
    def hook(self, mbd1_dump_factory, afs2_dump_factory, 
             extract_mdb1, pack_mdb1,
             extract_afs2, pack_afs2,
             extract_mbes, pack_mbes,
             decompile_scripts, compile_scripts):
        for archive in self.data_mvgls:
            self.data_archive_extract_buttons[archive].clicked.connect(mbd1_dump_factory(archive))
        for archive in self.sound_mvgls:
            self.snds_archive_extract_buttons[archive].clicked.connect(mbd1_dump_factory(archive))
        for archive in self.bgm_afs2s:
            self.bgm_afs2_extract_buttons[archive].clicked.connect(afs2_dump_factory(archive))
        for archive in self.vo_afs2s:
            self.vo_afs2_extract_buttons[archive].clicked.connect(afs2_dump_factory(archive))
        self.extract_mdb1_button.clicked.connect(extract_mdb1)
        self.pack_mdb1_button.clicked.connect(pack_mdb1)
        self.extract_afs2_button.clicked.connect(extract_afs2)
        self.pack_afs2_button.clicked.connect(pack_afs2)
        self.extract_mbes_button.clicked.connect(extract_mbes)
        self.pack_mbes_button.clicked.connect(pack_mbes)
        self.decompile_scripts_button.clicked.connect(decompile_scripts)
        self.compile_scripts_button.clicked.connect(compile_scripts)
                
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        for button in self.data_archive_extract_buttons.values():
            button.setEnabled(active)
        for button in self.snds_archive_extract_buttons.values():
            button.setEnabled(active)
        for button in self.bgm_afs2_extract_buttons.values():
            button.setEnabled(active)
        for button in self.vo_afs2_extract_buttons.values():
            button.setEnabled(active)
        self.extract_mdb1_button.setEnabled(active)
        self.pack_mdb1_button.setEnabled(active)
        self.extract_afs2_button.setEnabled(active)
        self.pack_afs2_button.setEnabled(active)
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
        self.conflicts_graph = QtWidgets.QLabel("Work In Progress")#QtWidgets.QTreeView()
        self.conflicts_graph.setAlignment(QtCore.Qt.AlignCenter)
        # model = QtGui.QStandardItemModel(self.conflicts_graph)
        # self.conflicts_graph.setModel(model)
        
    def lay_out(self):
        self.layout.addWidget(self.conflicts_graph, 0, 0)
        self.setLayout(self.layout)
        
    def enable(self):
        self.toggle_active(True)   
        
    def disable(self):
        self.toggle_active(False)
        
    def toggle_active(self, active):
        self.conflicts_graph.setEnabled(active)
        
    