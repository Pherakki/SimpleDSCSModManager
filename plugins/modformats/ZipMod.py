import json
import os
import zipfile

from src.CoreOperations.ModRegistry.CoreModFormats import ModFile


class ZipMod(ModFile):
    def __init__(self, path):
        super().__init__(path)
        with zipfile.ZipFile(path, 'r') as F:
            with F.open("METADATA.json", 'r') as fJ:
                self.init_metadata(json.load(fJ))
            try:
                with F.open("DESCRIPTION.html", 'r', encoding="utf8") as fJ:
                    self.init_description(fJ)
            except:
                pass
        
    @staticmethod
    def check_if_match(itempath):
        if os.path.isfile(itempath):
            filename, ext = os.path.splitext(itempath)
            if ext == '.zip':
                with zipfile.ZipFile(itempath, "r") as F:
                    directories = (set(os.path.normpath(f).split(os.path.sep)[0] for f in F.namelist()))
                    if 'modfiles' in directories and 'modfiles' not in F.namelist():
                        return True
        return False
        
    def toLoose(self, path):
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            zip_ref.extractall(path)
    
    def get_filelist(self):
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            return zip_ref.namelist() 
