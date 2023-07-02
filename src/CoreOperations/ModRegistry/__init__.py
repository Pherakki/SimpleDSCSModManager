import json
import os
import shutil

from PyQt5 import QtCore, QtGui

from src.CoreOperations.ModRegistry.Indexing import build_index
from src.CoreOperations.ModRegistry.ModFormatVersions import mod_format_versions
from src.CoreOperations.PluginLoaders.FiletypesPluginLoader import get_filetype_plugins
from src.CoreOperations.PluginLoaders.ModFormatsPluginLoader import get_modformat_plugins, LooseMod
from src.CoreOperations.PluginLoaders.ModInstallersPluginLoader import get_modinstallers_plugins
from src.Utils.Exceptions import UnrecognisedModFormatError, ModInstallWizardCancelled,\
                                 InstallerWizardParsingError, SpecificInstallerWizardParsingError

translate = QtCore.QCoreApplication.translate

def get_mod_version(path):
    metadata_path = os.path.join(path, 'METADATA.json')
    with open(metadata_path, 'r', encoding="utf-8") as F:
        metadata = json.load(F)

    version = metadata.get("FormatVersion", 1)
    highest_version = max(mod_format_versions.keys())
    assert type(version) is int, translate("ModRegistry", "Mod version is not an integer.")
    assert version <= highest_version, translate("ModRegistry", "Mod version ({version}) is more recent than the highest supported version ({highest_version}).".format(version=version,highest_version=highest_version))
    assert version in mod_format_versions, translate("ModRegistry", "Unrecognised mod version \'{version}\'.").format(version=version)
    return version

    
def check_mod_type(path):
    """
    Figures out which of the supported mod formats the input file/folder is in, if any.
    """
    for modformat in get_modformat_plugins():
        if modformat.check_if_match(path):
            return modformat(path)
    return False

def check_installer_type(path, messageLog):
    """
    Figures out which of the supported mod formats the input file/folder is in, if any.
    """
    for installer in get_modinstallers_plugins():
        if installer.check_if_match(path):
            try:
                return installer(path, messageLog)
            except Exception as e:
                if hasattr(installer, "installer_error_message"):
                    raise SpecificInstallerWizardParsingError(installer.installer_error_message(e.__str__())) from e
                else:
                    raise InstallerWizardParsingError(e.__str__()) from e
    return False
    
class ModRegistry:
    def __init__(self, ui, paths, profile_manager, raise_exception):
        self.ui = ui
        self.paths = paths
        self.profile_manager = profile_manager
        self.raise_exception = raise_exception
        
    
    def index_mod(self, modpath):
        mod_format_version = mod_format_versions[get_mod_version(modpath)]
        index = build_index(self.paths.config_loc,
                            os.path.join(modpath, "modfiles"), 
                            get_filetype_plugins(), 
                            mod_format_version.get_archives, 
                            mod_format_version.get_archive_from_path, 
                            mod_format_version.get_targets, 
                            mod_format_version.get_rules,
                            mod_format_version.get_filepath)
        return index
    
    def save_index(self, modpath, index):
        with open(os.path.join(modpath, "INDEX.json"), 'w', encoding="utf-8") as F:
            json.dump(index, F, indent=None, separators=(',', ':'))
            
    def register_mod(self, path):
        mod_name = os.path.split(path)[-1]
        try:
            self.ui.log(translate("ModRegistry", "Attempting to register {mod_name}...").format(mod_name=mod_name))
            
            # Need to shove this into a thread
            try:
                mod = check_mod_type(path)
                if mod:
                    modpath = os.path.join(self.paths.mods_loc, mod.filename)       
                    mod.toLoose(modpath)
                    wizard = check_installer_type(modpath, self.ui.log)
                    if wizard:
                        if not wizard.launch_wizard():
                            raise ModInstallWizardCancelled()
                        wizard.install()
                    self.save_index(modpath, self.index_mod(modpath))
                    self.update_mods()
                else:
                    raise UnrecognisedModFormatError()


            except ModInstallWizardCancelled:
                self.ui.log(translate("ModRegistry", "Did not register {mod_name}: wizard was cancelled.").format(mod_name=mod_name))
            except UnrecognisedModFormatError:
                self.ui.log(translate("ModRegistry", "{mod_name} is not in a recognised mod format.").format(mod_name=mod_name))
            except InstallerWizardParsingError as e:
                self.ui.log(translate("ModRegistry", "Error creating the registry wizard for {mod_name}: {error}.").format(mod_name=mod_name, error=e))
            except SpecificInstallerWizardParsingError as e:
                self.ui.log(e.__str__())
            except Exception as e:
                self.ui.log(translate("ModRegistry", "The mod manager encountered an unhandled error when attempting to register {mod_name}: {error}.").format(mod_name=mod_name, error=e))
        except Exception as e:
            shutil.rmtree(os.path.join(self.paths.mods_loc, mod_name))
            self.ui.log(translate("ModRegistry", "The following error occured when trying to register {mod_name}: {error}").format(mod_name=mod_name, error=e))
    
        
    def unregister_mod(self, index):
        mod_name = os.path.split(self.profile_manager.mods[index].path)[1]
        try:
            shutil.rmtree(self.profile_manager.mods[index].path)
            self.ui.log(translate("ModRegistry", "Removed {mod_name}.").format(mod_name=mod_name))
        except Exception as e:
            self.ui.log(translate("ModRegistry", "The following error occured when trying to delete {mod_name}: {error}").format(mod_name=mod_name, error=e))
        finally:
            self.update_mods()

    def open_mod_folder(self, index):
        full_path = self.profile_manager.mods[index].path
        if not os.path.exists(full_path):
            self.ui.log(translate("ModRegistry",
                                  "CRITICAL INTERNAL ERROR: '{mod_path}' does not exist and cannot be opened. Please report this as a bug, with instructions on how to reproduce.".format(
                                      mod_path=full_path)))
            return
        if not os.path.isdir(full_path):
            self.ui.log(translate("ModRegistry",
                                  "CRITICAL INTERNAL ERROR: '{mod_path}' is a file and not a directory. Please report this as a bug, with instructions on how to reproduce.".format(
                                      mod_path=full_path)))
            return
        try:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(full_path))
        except Exception as e:
            self.ui.log(translate("ModRegistry", "The following error occured when trying to open folder {mod_name}: {error}").format(mod_name=mod_name, error=e))

    def mod_has_wizard(self, index):
        mod = self.profile_manager.mods[index]

        return mod.wizard is not None
    
    def reregister_mod(self, index):
        mod = self.profile_manager.mods[index]
        mod_name = os.path.split(mod.path)[1]
        try:
            modfiles_dir = os.path.join(self.profile_manager.mods[index].path, "modfiles")
            wizard = mod.wizard
            if not wizard.launch_wizard():
                self.ui.log(translate("ModRegistry", "Did not register {mod_name}: wizard was cancelled.").format(mod_name=mod_name))
                return
            shutil.rmtree(modfiles_dir)
            os.mkdir(modfiles_dir)
            
            self.thread = QtCore.QThread()
            self.thread.started.connect(self.ui.disable_gui)
            self.thread.finished.connect(self.ui.enable_gui)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(self.update_mods)
            
            wizard.moveToThread(self.thread)
            
            wizard.messageLog.connect(self.ui.log)
            wizard.success.connect(lambda: wizard.messageLog.emit(translate("ModRegistry", "Successfully re-registered {mod_name}.").format(mod_name=mod_name)))
            wizard.finished.connect(self.thread.quit)
            
            self.thread.started.connect(lambda: wizard.messageLog.emit(translate("ModRegistry", "Registering mod...")))
            self.thread.started.connect(wizard.install)
            
            self.thread.start()
        except Exception as e:
            self.ui.log(translate("ModRegistry", "The following error occured when trying to re-register {mod_name}: {error}").format(mod_name=mod_name, error=e))


    def detect_mods(self, ignore_debugs=True):
        """Check for qualifying mods in the registered mods folder."""
        dirpath = self.paths.mods_loc
        os.makedirs(dirpath, exist_ok=True)
        
        detected_mods = []
        for item in os.listdir(dirpath):
            itempath = os.path.join(dirpath, item)
            modtype = LooseMod
            if modtype.check_if_match(itempath):
                try:
                    mod_obj = modtype(itempath)
                except json.decoder.JSONDecodeError as e:
                    self.ui.log(translate("ModRegistry", "An error occured when reading {mod_path}/METADATA.json: {error}").format(mod_path=item, error=e))
                    continue
                # If the mod has a wizard defined, attach it for reinstallation purposes
                try:
                    wizard = check_installer_type(itempath, None if ignore_debugs else self.ui.log)
                    if wizard:
                        mod_obj.wizard = wizard
                        wizard.try_set_logger(self.ui.log)
                except InstallerWizardParsingError as e:
                    self.ui.log(translate("ModRegistry", "Error creating the registry wizard for {mod_name}: {error}.").format(mod_name=mod_obj.name, error=e))
                    continue
                except SpecificInstallerWizardParsingError as e:
                    self.ui.log(e.__str__())
                    continue
                except Exception as e:
                    self.ui.log(translate("ModRegistry", "An unhandled error occured when reading {mod_name} data: {error}").format(mod_name=mod_obj.name, error=e))
    
                detected_mods.append(mod_obj)
        return detected_mods

    def update_mods(self):
        try:
            mods = self.detect_mods(ignore_debugs=True)
            modpath_to_id = {mod.path: i for i, mod in enumerate(mods)}
            self.profile_manager.update_mod_info(mods, modpath_to_id)
            self.profile_manager.apply_profile()
            return mods
        except Exception as e:
            self.raise_exception(Exception(translate("ModRegistry", "An unknown error occured during mod detection: {error}").format(error=e)))
        return []
