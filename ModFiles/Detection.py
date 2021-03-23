import distutils
from distutils import dir_util
import json
import os
import shutil
import zipfile

class ModFile:
    def __init__(self, path):
        self.path = path
        self.filename = os.path.splitext(os.path.split(path)[-1])[0]
        self.name = None
        self.author = "-"
        self.version = "-"
        self.category = "-"
        
    def init_metadata(self, iostream):
        data = json.load(iostream)
        self.name = data.get('Name', self.filename)
        self.author = data.get('Author', "-")
        self.version = data.get('Version', "-")
        self.category = data.get('Category', "-")
        
    @property
    def metadata(self):
        return [str(item) for item in [self.name, self.author, self.version, self.category]]
    
    @staticmethod
    def checkIfMatch(itempath):
        raise NotImplementedError
        
    def toLoose(self, path):
        raise NotImplementedError

class LooseMod(ModFile):
    def __init__(self, path):
        super().__init__(path)
        with open(os.path.join(path, 'METADATA.json'), 'r') as F:
            self.init_metadata(F)
    
    @staticmethod
    def checkIfMatch(itempath):
        if os.path.isdir(itempath):
            if os.path.exists(os.path.join(itempath, "modfiles/")):
                return True
        return False
    
    def toLoose(self, path):
        distutils.dir_util.copy_tree(os.path.join(self.path, 'modfiles'), path)
    
        
class ZipMod(ModFile):
    def __init__(self, path):
        super().__init__(path)
        with zipfile.ZipFile(path, 'r') as F:
            with F.open("METADATA.json", 'r') as fJ:
                self.init_metadata(fJ)
        
    @staticmethod
    def checkIfMatch(itempath):
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
    def checkIfMatch(itempath):
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

modtypes = [LooseMod, ZipMod, NestedZipMod]

def detect_mods(path):
    dirpath = os.path.join(path, "mods")
    os.makedirs(dirpath, exist_ok=True)
    
    detected_mods = []
    for item in os.listdir(dirpath):
        itempath = os.path.join(dirpath, item)
        for modtype in modtypes:
            if modtype.checkIfMatch(itempath):
                detected_mods.append(modtype(itempath))
                break
    return detected_mods

