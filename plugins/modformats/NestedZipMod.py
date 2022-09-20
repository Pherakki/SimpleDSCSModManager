import os
import zipfile

from src.CoreOperations.ModRegistry.CoreModFormats import ModFile


class NestedZipMod(ModFile):
    def __init__(self, path):
        super().__init__(path)
        with zipfile.ZipFile(path, 'r') as F:
            filename, ext = os.path.splitext(path)
            filename = os.path.split(filename)[1]
            with F.open(f"{filename}/METADATA.json", 'r') as fJ:
                self.init_metadata(fJ)
            try:
                with F.open("DESCRIPTION.html", 'r', encoding="utf8") as fJ:
                    self.init_description(fJ)
            except:
                pass
                
    @staticmethod
    def check_if_match(itempath):
        if os.path.isfile(itempath):
            filename, ext = os.path.splitext(itempath)
            filename = os.path.split(filename)[1]
            if ext == '.zip':
                with zipfile.ZipFile(itempath, "r") as F:
                    required_name = os.path.join(filename, "modfiles")
                    required_name_zip = f"{filename}/modfiles"
                    directories = (set(os.path.join(*os.path.normpath(f).split(os.path.sep)[:2]) for f in F.namelist()))
                    
                    if required_name in directories and required_name_zip not in F.namelist():
                        return True
        return False
    
    def toLoose(self, path):
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            with zipfile.ZipFile(self.path, 'r') as zip_ref:
                zip_ref.extractall(os.path.split(path)[0])
                
    def get_filelist(self):
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            return zip_ref.namelist() 
