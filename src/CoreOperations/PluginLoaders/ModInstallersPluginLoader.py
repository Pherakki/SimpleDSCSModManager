import inspect
import os
import shutil

from PyQt5 import QtCore

from src.CoreOperations.PluginLoaders.PluginLoad import load_sorted_plugins_in
from src.UI.CymisWizard import CymisWizard

translate = QtCore.QCoreApplication.translate

def get_modinstallers_plugins():
    return [Cymis]

class Cymis(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    success = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    
    def __init__(self, modpath, messageLog):
        super().__init__()
        self.modpath = modpath
        cymis_path = os.path.join(self.modpath, "INSTALL.json")
        self.wizard = CymisWizard(cymis_path, messageLog)

    @staticmethod
    def check_if_match(modpath):
        return os.path.exists(os.path.join(modpath, "INSTALL.json"))       
    
    def launch_wizard(self):
        return self.wizard.exec()

    @QtCore.pyqtSlot()
    def install(self):
        try:
            self.wizard.launch_installation()
            self.success.emit()
        except Exception as e:
            self.messageLog.emit(translate("ModWizards::CYMIS", "Registry wizard encountered an error: {error}.").format(error=e))
            self.finished.connect(lambda: shutil.rmtree(self.modpath))
        finally:
            self.finished.emit()
            
    def try_set_logger(self, log):
        if self.wizard.installer.enable_debug:
            self.wizard.log = log
            self.wizard.installer.log = log
            
    @staticmethod
    def installer_error_message(msg):
        return translate("ModWizards::CYMIS", "Error parsing CYMIS INSTALL.JSON script: {msg}").format(msg=msg)
        
        