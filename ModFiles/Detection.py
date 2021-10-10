import json
import os
import shutil
import zipfile

from PyQt5 import QtCore

from UI.CymisWizard import CymisWizard
from Utils.Exceptions import UnrecognisedModFormatError, ModInstallWizardError, ModInstallWizardCancelled
from Utils.Exceptions import UnrecognisedModFormatError, ModInstallWizardCancelled,\
                             InstallerWizardParsingError, SpecificInstallerWizardParsingError

###################
# MOD DEFINITIONS #
###################
class ModFile:
    def __init__(self, path):
        self.path = path
        self.filename = os.path.splitext(os.path.split(path)[-1])[0]
        self.name = None
        self.author = "-"
        self.version = "-"
        self.category = "-"
        self.description = ""
        
    def init_metadata(self, iostream):
        data = json.load(iostream)
        self.name = data.get('Name', self.filename)
        self.author = data.get('Author', "-")
        self.version = data.get('Version', "-")
        self.category = data.get('Category', "-")
        self.description = data.get('Description', "")
        
    @property
    def metadata(self):
        return [str(item) for item in [self.name, self.author, self.version, self.category]]
    
    @staticmethod
    def check_if_match(itempath):
        raise NotImplementedError
        
    def toLoose(self, path):
        raise NotImplementedError

class LooseMod(ModFile):
    def __init__(self, path):
        super().__init__(path)
        metadata_path = os.path.join(path, 'METADATA.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as F:
                self.init_metadata(F)
        self.wizard = None
        
    @staticmethod
    def check_if_match(itempath):
        if os.path.isdir(itempath):
            if os.path.exists(os.path.join(itempath, "modfiles/")):
                return True
        return False
    
    def toLoose(self, path):
        shutil.copytree(self.path, path, dirs_exist_ok=True)
    
        
class ZipMod(ModFile):
    def __init__(self, path):
        super().__init__(path)
        with zipfile.ZipFile(path, 'r') as F:
            with F.open("METADATA.json", 'r') as fJ:
                self.init_metadata(fJ)
        
    @staticmethod
    def check_if_match(itempath):
        if os.path.isfile(itempath):
            filename, ext = os.path.splitext(itempath)
            if ext == '.zip':
                with zipfile.ZipFile(itempath, "r") as F:
                    if 'modfiles/' in F.namelist():
                        return True
        return False
        
    def toLoose(self, path):
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            zip_ref.extractall(path)
    
class NestedZipMod(ModFile):
    def __init__(self, path):
        super().__init__(path)
        with zipfile.ZipFile(path, 'r') as F:
            filename, ext = os.path.splitext(path)
            with F.open("{filename}/METADATA.json", 'r') as fJ:
                self.init_metadata(fJ)
                
    @staticmethod
    def check_if_match(itempath):
        if os.path.isfile(itempath):
            filename, ext = os.path.splitext(itempath)
            if ext == '.zip':
                with zipfile.ZipFile(itempath, "r") as F:
                    if f"{filename}/modfiles/" in F.namelist():
                        return True
        return False
    
    def toLoose(self, path):
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            with zip_ref.open(f'{self.filename}') as zf, open(path, 'wb') as f:
                shutil.copyfileobj(zf, f)

modformats = [LooseMod, ZipMod, NestedZipMod]

def check_mod_type(path):
    """
    Figures out which of the supported mod formats the input file/folder is in, if any.
    """
    for modformat in modformats:
        if modformat.check_if_match(path):
            return modformat(path)
    return False

##############
# INSTALLERS #
##############
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
            self.messageLog.emit(f"Registry wizard encountered an error: {e}.")
            self.finished.connect(lambda: shutil.rmtree(self.modpath))
        finally:
            self.finished.emit()
            
    def try_set_logger(self, log):
        if self.wizard.installer.enable_debug:
            self.wizard.log = log
            self.wizard.installer.log = log
            
    @staticmethod
    def installer_error_message(msg):
        return f"Error parsing CYMIS INSTALL.JSON script: {msg}"
        
        
    

modinstallers = [Cymis]

def check_installer_type(path, messageLog):
    """
    Figures out which of the supported mod formats the input file/folder is in, if any.
    """
    for installer in modinstallers:
        if installer.check_if_match(path):
            try:
                return installer(path, messageLog)
            except Exception as e:
                if hasattr(installer, "installer_error_message"):
                    raise SpecificInstallerWizardParsingError(installer.installer_error_message(e.__str__())) from e
                else:
                    raise InstallerWizardParsingError(e.__str__()) from e
    return None


###################################
# FUNCTIONS INTENDED TO BE PUBLIC #
###################################
def install_mod_in_manager(mod_source_path, install_path, mbe_unpack, thread, messageLog, updateMessageLog):
    """
    Dumps the input file/folder to the install_path if it is a supported mod format.
    """
    mod = check_mod_type(mod_source_path)
    mod_name = os.path.split(mod_source_path)[-1]
    if mod:
        modpath = os.path.join(install_path, mod.filename)
        try:
            # Unpack / Copy the files           
            mod.toLoose(modpath)
            
            wizard = check_installer_type(modpath, messageLog)
            if wizard is not None:
                try:
                    if not wizard.launch_wizard():
                        raise ModInstallWizardCancelled()
                    wizard.moveToThread(thread)
                    
                    wizard.messageLog.connect(messageLog)
                    wizard.success.connect(lambda: wizard.messageLog.emit(f"Successfully registered {mod_name}."))
                    wizard.finished.connect(thread.quit)
                    
                    thread.started.connect(lambda: wizard.messageLog.emit("Registering mod..."))
                    thread.started.connect(wizard.install)
                    
                    thread.start()
                except ModInstallWizardCancelled as e:
                    raise e
                    
            # # Unpack any MBEs
            # for mbe_folder in ["data", "message", "text"]:
            #     data_path = os.path.join(install_path, mod.filename, "modfiles", mbe_folder)
            #     if os.path.exists(data_path):
            #         temp_path = os.path.join(data_path, 'temp')
            #         os.makedirs(temp_path, exist_ok=True)
            #         for item in os.listdir(data_path):
            #             itempath = os.path.join(data_path, item)
            #             if os.path.isfile(itempath) and os.path.splitext(item)[-1] == '.mbe':
            #                 temp_item_path = os.path.join(temp_path, item)
            #                 os.rename(os.path.join(data_path, item), temp_item_path)
            #                 mbe_unpack(item, temp_path, data_path)
            #         shutil.rmtree(temp_path)
            return
        except Exception as e:
            shutil.rmtree(modpath)
            raise e
    else:
        raise UnrecognisedModFormatError()

def detect_mods(path, log, ignore_debugs=True):
    """Check for qualifying mods in the registered mods folder."""
    dirpath = os.path.join(path, "mods")
    os.makedirs(dirpath, exist_ok=True)
    
    detected_mods = []
    for item in os.listdir(dirpath):
        itempath = os.path.join(dirpath, item)
        modtype = LooseMod
        if modtype.check_if_match(itempath):
            try:
                mod_obj = modtype(itempath)
            except json.decoder.JSONDecodeError as e:
                log(f"An error occured when reading {item}/METADATA.json: {e}")
                continue
            # If the mod has a wizard defined, attach it for reinstallation purposes
            try:
                wizard = check_installer_type(itempath, None if ignore_debugs else log)
                if wizard is not None:
                    mod_obj.wizard = wizard
                    wizard.try_set_logger(log)
            except InstallerWizardParsingError as e:
                log(f"Error creating the registry wizard for {mod_obj.name}: {e}.")
                continue
            except SpecificInstallerWizardParsingError as e:
                log(e.__str__())
                continue
            except Exception as e:
                log(f"An unhandled error occured when reading {mod_obj.name} data: {e}")
            #except json.decoder.JSONDecodeError as e:
            #    log(f"An error occured when reading INSTALL.json for {mod_obj.name}: {e}")
            #    continue
            detected_mods.append(mod_obj)
    return detected_mods

