from PyQt5 import QtCore, QtGui, QtWidgets
from datetime import datetime
import os

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
        self.preferencesMenu = QtWidgets.QMenu(parentWidget)
        self.helpMenu = QtWidgets.QMenu(parentWidget)
        parentWidget.menuBar().addMenu(self.fileMenu)
        parentWidget.menuBar().addMenu(self.languageMenu)
        parentWidget.menuBar().addMenu(self.preferencesMenu)
        parentWidget.menuBar().addMenu(self.helpMenu)
                
        self.addModAction = QtWidgets.QAction(parentWidget)
        self.fileMenu.addAction(self.addModAction)
        
        self.colourThemeAction = QtWidgets.QAction(parentWidget)
        def popup_colours():
            ctsp = ColourThemeSelectionPopup(self.parentWidget)
            ctsp.exec_()
        self.colourThemeAction.triggered.connect(popup_colours)
        self.preferencesMenu.addAction(self.colourThemeAction)
        
        self.docsAction = QtWidgets.QAction(parentWidget)
        self.helpMenu.addAction(self.docsAction)
        
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
    
    def hook(self, ops):
        self.donateAction.triggered.connect(lambda : supportPopup(self.parentWidget, ops.paths))
        self.docsAction.triggered.connect(ops.paths.open_docs)
        
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
        self.preferencesMenu.setTitle(translate("UI::MenuBar", "&Preferences"))
        self.helpMenu.setTitle(translate("UI::MenuBar", "&Help"))
        self.addModAction.setText(translate("UI::FileMenu", "Add Mod..."))
        self.colourThemeAction.setText(translate("UI::PrefsMenu", "Edit Appearance..."))
        self.docsAction.setText(translate("UI::HelpMenu", "Help and Modding Guides..."))
        self.donateAction.setText(translate("UI::HelpMenu", "Support Digimon Modding Tools"))
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
     
class ColourThemeSelectionPopup(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.themes = []
        self.theme_indices = {}
        self.name_buf = None
        
        self.mainwindow = parent
        self.style_engine = self.mainwindow.style_engine
        self.setWindowTitle(translate("UI::ColorThemePopup", "Colour Preferences"))
        
        layout = QtWidgets.QVBoxLayout()
        self.theme_select = QtWidgets.QComboBox(self)
        
        self.new_theme_button = QtWidgets.QPushButton(translate("UI::ColorThemePopup", "Create New Theme"), self)
        self.delete_theme_button = QtWidgets.QPushButton(translate("UI::ColorThemePopup", "Delete Theme"), self)
        
        width = 0
        width = max(width, self.new_theme_button.width())
        #width = max(width, self.edit_theme_button.width())
        width = max(width, self.delete_theme_button.width())
        
        self.theme_select.setFixedWidth(width + 30)
        self.new_theme_button.setFixedWidth(width)
        self.delete_theme_button.setFixedWidth(width)
        
        self.setFixedSize(3*width,200)
        
        layout.addStretch(1)
        layout.addWidget(self.theme_select, alignment = QtCore.Qt.AlignCenter)
        layout.addWidget(self.new_theme_button, alignment = QtCore.Qt.AlignCenter)
        layout.addWidget(self.delete_theme_button, alignment = QtCore.Qt.AlignCenter)
        layout.addStretch(1)
        
        layout.setAlignment(QtCore.Qt.AlignCenter)
        
        # Put in centre of the screen
        rect = self.frameGeometry()
        centre = QtWidgets.QDesktopWidget().availableGeometry().center()
        rect.moveCenter(centre)
        self.move(rect.topLeft())
        
        self.setLayout(layout)
        
        self.set_available_themes()
        self.new_theme_button.clicked.connect(self.create_theme)
        self.delete_theme_button.clicked.connect(self.delete_theme)
        
    def set_available_themes(self):
        try:
            self.theme_select.currentTextChanged.disconnect()
        except:
            pass
        self.theme_indices.clear()
        self.theme_select.clear()
        self.theme_indices["Light"] = len(self.theme_indices)
        self.theme_select.addItem("Light")
        self.theme_indices["Dark"] = len(self.theme_indices)
        self.theme_select.addItem("Dark")
        for theme in self.style_engine.styles:
            self.theme_indices[theme] = len(self.theme_indices)
            self.theme_select.addItem(theme)
        self.theme_select.setCurrentIndex(self.theme_indices[self.style_engine.active_style])
        self.select_theme(self.style_engine.active_style)
        self.theme_select.currentTextChanged.connect(self.select_theme)
    
    def select_theme(self, item):
        if item == "Light":
            self.style_engine.set_style("Light")
            #self.edit_theme_button.disable()
            self.delete_theme_button.setEnabled(False)
        elif item == "Dark":
            self.style_engine.set_style("Dark")
            #self.edit_theme_button.disable()
            self.delete_theme_button.setEnabled(False)
        else:
            self.style_engine.set_style(item)
            #self.edit_theme_button.enable()
            self.delete_theme_button.setEnabled(True)
        self.mainwindow.ops.config_manager.set_style_pref(item)
                
    @QtCore.pyqtSlot(str)
    def receive_name(self, name):
        self.name_buf = name.strip()
            
    def create_theme(self):
        start_style = self.theme_select.currentText()
        proposed_name = self.style_engine.generate_new_style_name("New Theme")
        cctp = CreateColourThemePopup(self, self.mainwindow, proposed_name, translate("UI::ColorThemePopup", "New Colour Theme"))
        cctp.communicate_name_change.connect(self.receive_name)
        if cctp.exec_():
            nm = self.name_buf # This gets set when the Ok button is pressed on cctp
            self.style_engine.styles[nm] = self.style_engine.get_active_style()
            self.style_engine.styles = {k: v for k, v in sorted(self.style_engine.styles.items())}
            self.style_engine.save_style(nm)
            self.set_available_themes()
            self.theme_select.setCurrentIndex(self.theme_indices[nm])
        else:
            self.select_theme(start_style)
            
    def delete_theme(self):
        # First switch the style to a different one...
        style_name = self.theme_select.currentText()
        active_style_idx = self.theme_indices[style_name]
        # Will always have built-ins, so we're ok to go to the previous idx
        new_style = list(self.theme_indices.keys())[active_style_idx - 1]
        self.select_theme(new_style)
        
        # Now it's safe to delete the theme we intended to delete
        self.style_engine.delete_style(style_name)
        self.set_available_themes()
        
            
        
        
        
class CreateColourThemePopup(QtWidgets.QDialog):
    communicate_name_change = QtCore.pyqtSignal(str)
    
    def __init__(self, parent, mainwindow, initial_name, window_name):
        super().__init__(parent)
        self.mainwindow = mainwindow
        self.style_engine = mainwindow.style_engine
        self.setGeometry(100,100,400,600)
        self.setWindowTitle(window_name)
        self.buildColourEdits(initial_name)
        
    def hexcolour(self, colour):
        return f"{colour[0]:02x}{colour[1]:02x}{colour[2]:02x}"
        
    def open_colour_dialog(self, accessor, button):
        def func():
            active_style = self.mainwindow.style_engine.get_active_style()
            original_colour = accessor(active_style).c
            dialog = QtWidgets.QColorDialog(self)
            dialog.currentColorChanged.connect(lambda: self.update_style(accessor, dialog, button))
            dialog.setCurrentColor(original_colour)
            if not dialog.exec_():
                accessor(active_style).c = original_colour
                self.set_button_style(button, original_colour)
                self.mainwindow.style_engine.apply_style(active_style)
            
        return func
        
    def update_style(self, accessor, dialog, button):
        style = self.mainwindow.style_engine.get_active_style()
        accessor(style).c = dialog.currentColor()
        self.mainwindow.style_engine.apply_style(style)
        self.set_button_style(button, accessor(style).c)
    
    def set_button_style(self, button, c):
        colour = [c.red(), c.green(), c.blue()]
        button.setStyleSheet(f"background-color:#{self.hexcolour(colour)};\
                        border: 2px solid #222222")
    
    def buildColourEdits(self, initial_name):
        active_style = self.mainwindow.style_engine.get_active_style()
        
        layout = QtWidgets.QGridLayout()
        
        namebox_layout = QtWidgets.QHBoxLayout()
        self.name_box = QtWidgets.QLineEdit(self)
        self.name_box.setText(initial_name)
        namebox_layout.addStretch(1)
        namebox_layout.addWidget(self.name_box)
        namebox_layout.addStretch(1)
        
        
        settings_layout = QtWidgets.QGridLayout()
        settings_layout.setColumnStretch(0, 1)
        settings_layout.setColumnStretch(2, 1)
        
        base_groupbox = self.buildBaseGroupBox(lambda x: x.active, active_style)
        settings_layout.addWidget(base_groupbox,      0, 1)
        text_groupbox = self.buildTextGroupBox(lambda x: x.active, active_style)
        settings_layout.addWidget(text_groupbox,      1, 1)
        links_groupbox = self.buildLinksGroupBox(lambda x: x.active, active_style)
        settings_layout.addWidget(links_groupbox,     2, 1)
        highlight_groupbox = self.buildHighlightGroupBox(lambda x: x.active, active_style)
        settings_layout.addWidget(highlight_groupbox, 3, 1)
        tooltips_groupbox = self.buildTooltipGroupBox(lambda x: x.active, active_style)
        settings_layout.addWidget(tooltips_groupbox,  4, 1)
        shading_groupbox = self.buildShadingGroupBox(lambda x: x.active, active_style)
        settings_layout.addWidget(shading_groupbox,   5, 1)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        ok_button = QtWidgets.QPushButton("Accept", self)
        cancel_button = QtWidgets.QPushButton("Cancel", self)
        ok_button.clicked.connect(self.handle_ok)
        cancel_button.clicked.connect(lambda: self.done(0))
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(namebox_layout, 1, 1)
        layout.addLayout(settings_layout, 2, 1)
        layout.addLayout(button_layout,   3, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(2, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(layout.rowCount(), 1)
        
        self.setLayout(layout)
        
    def addColorSelector(self, label_text, row, accessor, style, layout):
        label  = QtWidgets.QLabel(label_text, self)
        button = QtWidgets.QPushButton("", self)
        self.set_button_style(button, accessor(style).c)
        label.setFixedWidth(label.width())
        button.setFixedWidth(40)
        button.clicked.connect(self.open_colour_dialog(accessor, button))
        layout.addWidget(label, row, 0)
        layout.addWidget(button, row, 1)
        
    def buildBasicGroupBox(self, style, name, contents):
        groupbox = QtWidgets.QGroupBox(name, self)
        gbox_layout = QtWidgets.QGridLayout()
        for i, (label_text, accessor) in enumerate(contents):
            self.addColorSelector(label_text, i, accessor, style, gbox_layout)
            
        gbox_layout.setRowStretch(0, 1)
        gbox_layout.setRowStretch(gbox_layout.columnCount(), 1)
        groupbox.setLayout(gbox_layout)
        return groupbox
        
    def buildBaseGroupBox(self, group_accessor, style):
        return self.buildBasicGroupBox(
            style, 
            translate("UI::ColorThemePopup", "Base Colours"), 
            [
                [ translate("UI::ColorThemePopup", "Window"        ), lambda x: group_accessor(x).window   ],
                [ translate("UI::ColorThemePopup", "Base"          ), lambda x: group_accessor(x).base     ],
                [ translate("UI::ColorThemePopup", "Button"        ), lambda x: group_accessor(x).button   ],
                [ translate("UI::ColorThemePopup", "Alternate Base"), lambda x: group_accessor(x).alt_base ]
            ]
        )
        
    def buildTextGroupBox(self, group_accessor, style):
        groupbox = QtWidgets.QGroupBox(translate("UI::ColorThemePopup", "Text"), self)
        gbox_layout = QtWidgets.QGridLayout()
        self.addColorSelector("Text",        1, lambda x: group_accessor(x).text, style, gbox_layout)
        
        checkbox_layout = QtWidgets.QHBoxLayout()
        checkbox = QtWidgets.QCheckBox(self)
        label = QtWidgets.QLabel(translate("UI::ColorThemePopup", "Unified Colours"))
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.addWidget(label)
        checkbox_layout.addStretch(1)
        gbox_layout.addLayout(checkbox_layout, 2, 0, 1, 2)
        
        self.addColorSelector("Window Text", 3, lambda x: group_accessor(x).window_text, style, gbox_layout)
        self.addColorSelector("Button Text", 4, lambda x: group_accessor(x).button_text, style, gbox_layout)
        self.addColorSelector("Bright Text", 5, lambda x: group_accessor(x).bright_text, style, gbox_layout)
        gbox_layout.setRowStretch(0, 1)
        gbox_layout.setRowStretch(gbox_layout.columnCount(), 1)
        groupbox.setLayout(gbox_layout)
        return groupbox
        
    def buildLinksGroupBox(self, group_accessor, style):
        return self.buildBasicGroupBox(
            style, 
            translate("UI::ColorThemePopup", "Links"), 
            [
                [ translate("UI::ColorThemePopup", "Link"),         lambda x: group_accessor(x).link         ],
                [ translate("UI::ColorThemePopup", "Link Visited"), lambda x: group_accessor(x).link_visited ]
            ]
        )
        
    def buildHighlightGroupBox(self, group_accessor, style):
        return self.buildBasicGroupBox(
            style, 
            translate("UI::ColorThemePopup", "Highlight"), 
            [
                [ translate("UI::ColorThemePopup", "Highlight"),        lambda x: group_accessor(x).highlight        ],
                [ translate("UI::ColorThemePopup", "Highlighted Text"), lambda x: group_accessor(x).highlighted_text ]
            ]
        )
           
    def buildTooltipGroupBox(self, group_accessor, style):
        return self.buildBasicGroupBox(
            style, 
            translate("UI::ColorThemePopup", "ToolTips"), 
            [
                [ translate("UI::ColorThemePopup", "ToolTip Base"), lambda x: group_accessor(x).tooltip_base ],
                [ translate("UI::ColorThemePopup", "ToolTip Text"), lambda x: group_accessor(x).tooltip_text ]
            ]
        )
               
    def buildShadingGroupBox(self, group_accessor, style):
        return self.buildBasicGroupBox(
            style, 
            translate("UI::ColorThemePopup", "Shading"), 
            [
                [ translate("UI::ColorThemePopup", "Light"),    lambda x: group_accessor(x).light    ],
                [ translate("UI::ColorThemePopup", "MidLight"), lambda x: group_accessor(x).midlight ],
                [ translate("UI::ColorThemePopup", "Mid"),      lambda x: group_accessor(x).mid      ],
                [ translate("UI::ColorThemePopup", "Dark"),     lambda x: group_accessor(x).dark     ],
                [ translate("UI::ColorThemePopup", "Shadow"),   lambda x: group_accessor(x).shadow   ]
            ]
        )
    
    def handle_ok(self):
        name = self.name_box.text()
        if name in self.style_engine.styles or name in self.style_engine.builtin_styles:
            err = QtWidgets.QMessageBox()
            err.setIcon(QtWidgets.QMessageBox.Warning)
            err.setWindowTitle("Name already defined")
            err.setText(f"Error: '{name}' is already defined. Choose another name.")
            err.setStandardButtons(QtWidgets.QMessageBox.Ok)
            err.exec_()
            return
        self.communicate_name_change.emit(name)
        self.done(1)
            
     
class creditsPopup:
    def __init__(self, win):
        msgBox = QtWidgets.QMessageBox(win)
        msgBox.setWindowTitle(translate("UI::Credts", "Credits"))
        
        msgBoxText = translate("UI::Credits", "The people on this list have all significantly contributed to SimpleDSCSModManager in some way. They have my deepest thanks.")
        msgBoxText += "<br><br>"
        msgBoxText += "<b>" + translate("UI::Credits", "Programming Contributions") + "</b>"
        msgBoxText += "<br>"
        msgBoxText += " " + translate("Common::ListElementsSeparator", ", ").join(["Pherakki"])
        msgBoxText += "<br>"
        msgBoxText += "<br>"
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
        
class supportPopup:
    def __init__(self, win, paths):
        msgBox = QtWidgets.QMessageBox(win)
        msgBox.setWindowTitle(translate("UI::Support", "Support"))
        
        msgBoxText = "<b>Pherakki</b>"
        msgBoxText += "<br>"
        msgBoxText += translate("UI::Support", "The author of SimpleDSCSModManager. Does not currently accept donations.")
        
        msgBoxText += "<br><br>"
        msgBoxText += "<b>SydMontague</b>"
        msgBoxText += "<br>"
        msgBoxText += translate("UI::Support", "Produces lots of cool Digimon modding tools, and frequently discusses SimpleDSCSModManager feature development with me. Creator of DSCSTools, which the mod manager could not exist without. You can support SydMontague's projects on {hyperlink_open}Patreon{hyperlink_close}, which are not paywalled.").format(hyperlink_open=f"<a href=\"{paths.syd_patreon}\">", hyperlink_close="</a>")
        
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
        self.logview.setWordWrap(True) 
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
        self.vgaudio_widget = QtWidgets.QWidget()
        self.vgaudio_layout = QtWidgets.QGridLayout()
        
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
        #self.hca_to_wav = self.new_button("", parentWidget)
        self.wav_to_hca = self.new_button("", parentWidget)
        self.wav_to_hca_looped = self.new_button("", parentWidget)
        
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
        #self.hca_to_wav.setText(translate("UI::ExtractTab", "Convert HCA to WAV"))
        self.wav_to_hca.setText(translate("UI::ExtractTab", "Convert WAV to HCA"))
        self.wav_to_hca_looped.setText(translate("UI::ExtractTab", "Convert WAV to Looped HCA"))
    
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
        
        self.vgaudio_layout.addWidget(self.sounds_label, 0, 0)
        self.vgaudio_layout.setRowStretch(0, 0)
        for i, button in enumerate((self.wav_to_hca, self.wav_to_hca_looped)): 
            self.vgaudio_layout.addWidget(button, i+1, 0)
            self.vgaudio_layout.setRowStretch(i+1, 0)
        self.vgaudio_widget.setLayout(self.vgaudio_layout)
        
        self.manualextract_layout.setRowStretch(0, 1)
        self.manualextract_layout.addWidget(self.dscstools_widget, 1, 0)
        self.manualextract_layout.addWidget(self.scripts_widget, 2, 0)
        self.manualextract_layout.addWidget(self.vgaudio_widget, 3, 0)
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
             decompile_scripts, compile_scripts,
             convert_hca_to_wav, convert_wav_to_hca,
             convert_wav_to_hca_looped):
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
        #self.hca_to_wav.clicked.connect(convert_hca_to_wav)
        self.wav_to_hca.clicked.connect(convert_wav_to_hca)
        self.wav_to_hca_looped.clicked.connect(convert_wav_to_hca_looped)
                
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
        #self.hca_to_wav.setEnabled(active)
        self.wav_to_hca.setEnabled(active)
        self.wav_to_hca_looped.setEnabled(active)
            
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
        
    