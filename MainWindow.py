import json
import os

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets 

from CoreOperations import CoreOperations
from UI.Design import uiMainWidget
from UI.StyleEngine import StyleEngine

translate = QtCore.QCoreApplication.translate


class MainWindow(QtWidgets.QMainWindow):
    raise_exception = QtCore.pyqtSignal(Exception)
    block = QtCore.pyqtSignal()
    style_sheet_changed = QtCore.pyqtSignal()
    
    directory = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))
    
    def __init__(self, app, parent=None): 
        super().__init__(parent)
        
        self.__app = app
        self.style_engine = StyleEngine(app)
        
        self.threadpool = QtCore.QThreadPool()
        self.translator = QtCore.QTranslator(self)
        
        # Define the members of this class in the __init functions
        self.rehook_crash_handler(self.throw_exception)
        self.__init_ui()
        self.__init_core_operators()
        self.__init_ui_hooks()
        self.__set_language()
        self.ui.main_area.action_tabs.configTab.crash_handle_box.setCurrentIndex(self.ops.config_manager.get_crash_pref())
        self.ui.main_area.action_tabs.configTab.block_handle_box.setCurrentIndex(self.ops.config_manager.get_block_pref())
        self.ops.init = True

        self.style_engine.apply_style(self.style_engine.light_style)
        
        self.ui.log(translate("MainWindow", "SimpleDSCSModManager initialised."))
        self.ui.loglink(translate("MainWindow", "Want to contribute to modding tools or develop mods? Consider joining the {hyperlink_open}Digimon Modding Community discord server{hyperlink_close}.").format(hyperlink_open="<a href=\"{self.ops.paths.discord_invite}\">", hyperlink_close="</a>"))
        self.ui.log(translate("MainWindow","If you're encountering issues installing mods, remember to use SimpleDSCSModManager in a non-protected location (e.g. not Desktop, Documents, etc.) and run it in Admin mode."))
        
    def closeEvent(self, event):
        try:
            self.ops.profile_manager.save_profile()
        except Exception as e:
            raise Exception(f"Failed to close manager: {e}")
        finally:
            # close window
            event.accept()
            self.__app.quit()
            
        
    @QtCore.pyqtSlot(str)
    def changeLanguage(self, qm_filename):
        if qm_filename:
            self.translator.load(qm_filename, self.ops.paths.localisations_loc)
            QtWidgets.QApplication.instance().installTranslator(self.translator)
            self.ops.config_manager.set_lang_pref(os.path.splitext(qm_filename)[0])
            self.retranslate_all()
        else:
            QtWidgets.QApplication.instance().removeTranslator(self.translator)
        
    @QtCore.pyqtSlot(str)
    def loggedChangedLanguage(self, qm_filename):
        self.changeLanguage(qm_filename)
        self.ui.log(translate("MainWindow", "Language changed to English (US)."))
    
    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate_all()
        super().changeEvent(event)
        
    def retranslate_all(self):
        self.retranslateUi()
        self.ui.menu.retranslateUi()
        self.ui.action_tabs.retranslateUi()
        self.ui.mods_display_area.retranslateUi()
        self.ui.mod_installation_widgets.retranslateUi()
        self.ui.profile_interaction_widgets.retranslateUi()
        self.ui.config_tab.retranslateUi()
        self.ui.extract_tab.retranslateUi()
        self.ui.modinfo_region.retranslateUi()

    def retranslateUi(self):
        self.setWindowTitle(translate("MainWindow", "SimpleDSCSModManager"))
        
    def loadLanguageOptions(self):
        out = {}
        if os.path.isdir(self.ops.paths.localisations_loc):
            if os.path.isfile(self.ops.paths.localisations_names_loc):

                with open(self.ops.paths.localisations_names_loc, 'r', encoding="utf8") as F:
                    names = json.load(F)
            else:
                self.ui.log(translate("UI::Localisation", "Language names file \"{filepath}\" was not found. Using default language names.").format(filepath=self.ops.paths.localisations_names_loc))
                names = {}
                    
            for file in os.listdir(self.ops.paths.localisations_loc):
                filename, ext = os.path.splitext(file)
                if ext == ".qm":
                    display_name = names.get(filename)
                    if display_name is None:
                        ql = QtCore.QLocale(filename)
                        self.ui.log(translate("UI::Localisation", "Could not find language name \"{lang_name}\" in the languages names file. Using default name.").format(lang_name=filename))

                        display_name = f"{ql.languageToString(ql.language())} ({ql.countryToString(ql.country())})"
                    out[display_name] = file
        else:
            self.ui.log(translate("UI::Localisation", "Languages directory \"{filepath}\" was not found. No translation files loaded.").format(filepath=self.ops.paths.localisations_loc))
        return out
        
    def __init_ui(self):
        self.window = QtWidgets.QWidget() 
        try:
            self.icon = QtGui.QIcon(os.path.join("img", 'icon_256.png'))
            self.setWindowIcon(self.icon)
        except:
            pass
        self.setCentralWidget(self.window)
        self.ui = uiMainWidget(self)
        self.window.setLayout(self.ui.layout)
        
    def __init_core_operators(self):
        self.ops = CoreOperations(self)
        self.ops.mod_registry.update_mods()
        
        
    def __set_language(self):
        lang = self.ops.config_manager.get_lang_pref()
        if lang is None:
            lang = "en-US"
        elif not os.path.isfile(os.path.join(self.ops.paths.localisations_loc, lang) + ".qm"):
            self.ui.log(translate("MainWindow", "Translation file for {language} was not found.").format(language=lang))
            lang = "en-US"
        self.changeLanguage(lang + ".qm")
        
        
            

    def __init_ui_hooks(self):
        self.ui.hook_menu(self.ops)
        self.ui.hook_filemenu(self.ops.register_mod_filedialog)
        self.ui.hook_languageaction(self.loggedChangedLanguage)
        self.ui.hook_mod_registry(self.ops.mod_registry.register_mod)
        self.ui.hook_profle_interaction_widgets(self.ops.profile_manager)
        self.ui.hook_install_button(self.ops.install_mods)
        self.ui.hook_backup_button(self.ops.uninstall_mods)
        self.ui.hook_game_launch_button(self.ops.launch_game)
        self.ui.hook_update_mod_info_window(self.ops.update_mod_info_window)
        self.ui.hook_delete_mod_menu(self.ops.mod_registry.unregister_mod)
        self.ui.hook_wizard_mod_menu(self.ops.mod_registry.mod_has_wizard, self.ops.mod_registry.reregister_mod)
        self.ui.hook_config_tab(self.ops.change_game_location, 
                                lambda:None,
                                self.ops.purge_softcode_cache,
                                self.ops.purge_indices,
                                self.ops.purge_cache,
                                self.ops.purge_mm_resources,
                                self.ops.setCrashLogMethod,
                                self.ops.getCrashLogMethods,
                                self.ops.setBlockMethod,
                                self.ops.getBlockMethods)
        self.ui.hook_extract_tab(self.ops.create_MDB1_dump_method,
                                 self.ops.create_AFS2_dump_method,
                                 self.ops.extract_MDB1,
                                 self.ops.pack_MDB1,
                                 self.ops.extract_AFS2,
                                 self.ops.pack_AFS2,
                                 self.ops.extract_MBEs,
                                 self.ops.pack_MBEs,
                                 self.ops.extract_scripts,
                                 self.ops.pack_scripts,
                                 self.ops.convert_HCAs_to_WAVs,
                                 self.ops.convert_WAVs_to_HCAs,
                                 self.ops.convert_WAV_to_looped_HCA)
        self.ui.mods_display.model().itemChanged.connect(self.ops.profile_manager.save_profile)
        
        self.ui.createLanguageMenu(self.loadLanguageOptions())
       
    def rehook_crash_handler(self, func):
        try:     self.raise_exception.disconnect() 
        except:  pass
        finally: self.raise_exception.connect(func)
        
        
    @QtCore.pyqtSlot(Exception)
    def log_exception(self, exception):
        self.ui.log(exception.__str__())
        
    @QtCore.pyqtSlot(Exception)
    def throw_exception(self, exception):
        raise exception
        
    def rehook_block_handler(self, func):
        try:     self.block.disconnect() 
        except:  pass
        finally: self.block.connect(func)
        
    @QtCore.pyqtSlot()
    def blocker_window(self):
        self.ui.disable_gui()
        QtWidgets.QMessageBox.about(self, 
                                    translate("GameRunningPopup", "Game Running"), 
                                    translate("GameRunningPopup", "The game is currently running. Click the button below to unlock the mod manager once the game has been quit."))
        self.ui.enable_gui()
        
    @QtCore.pyqtSlot()
    def quit_program(self):
        self.close()