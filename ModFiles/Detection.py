import json
import os
import shutil
import zipfile

from UI.CymisWizard import CymisWizard
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
class Cymis:
    def __init__(self, modpath):
        self.modpath = modpath
        cymis_path = os.path.join(self.modpath, "INSTALL.json")
        self.wizard = CymisWizard(cymis_path)

    @staticmethod
    def check_if_match(modpath):
        return os.path.exists(os.path.join(modpath, "INSTALL.json"))       
    
    def launch_wizard(self):
        dir_contents = os.listdir(os.path.join(self.modpath, 'modfiles'))
        assert len(dir_contents) == 0, f"'modfiles' folder was not empty for Cymis installer: {len(dir_contents)} items found."
        
        return self.wizard.exec()

    def install(self):
        self.wizard.launch_installation()

modinstallers = [Cymis]

def check_installer_type(path):
    """
    Figures out which of the supported mod formats the input file/folder is in, if any.
    """
    for installer in modinstallers:
        if installer.check_if_match(path):
            return installer(path)
    return None


###################################
# FUNCTIONS INTENDED TO BE PUBLIC #
###################################
def install_mod_in_manager(mod_source_path, install_path, mbe_unpack):
    """
    Dumps the input file/folder to the install_path if it is a supported mod format.
    """
    mod = check_mod_type(mod_source_path)
    if mod:
        # Unpack / Copy the files
        mod.toLoose(os.path.join(install_path, mod.filename))
        
        # Unpack any MBEs
        for mbe_folder in ["data", "message", "text"]:
            data_path = os.path.join(install_path, mod.filename, "modfiles", mbe_folder)
            if os.path.exists(data_path):
                temp_path = os.path.join(data_path, 'temp')
                os.makedirs(temp_path, exist_ok=True)
                for item in os.listdir(data_path):
                    itempath = os.path.join(data_path, item)
                    if os.path.isfile(itempath) and os.path.splitext(item)[-1] == '.mbe':
                        temp_item_path = os.path.join(temp_path, item)
                        os.rename(os.path.join(data_path, item), temp_item_path)
                        mbe_unpack(item, temp_path, data_path)
                shutil.rmtree(temp_path)
        return True
    else:
        return False

def detect_mods(path):
    """Check for qualifying mods in the registered mods folder."""
    dirpath = os.path.join(path, "mods")
    os.makedirs(dirpath, exist_ok=True)
    
    detected_mods = []
    for item in os.listdir(dirpath):
        itempath = os.path.join(dirpath, item)
        modtype = LooseMod
        if modtype.check_if_match(itempath):
            detected_mods.append(modtype(itempath))
    return detected_mods

