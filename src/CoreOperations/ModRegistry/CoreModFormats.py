import os
import shutil

from src.Utils.JSONHandler import JSONHandler


class ModFile:
    def __init__(self, path):
        self.path = path
        self.filename = os.path.splitext(os.path.split(path)[-1])[0]
        self.name = None
        self.author = "-"
        self.version = "-"
        self.category = "-"
        self.description = ""
        
    def init_metadata(self, data):
        self.name = data.get('Name', self.filename)
        self.author = data.get('Author', "-")
        self.version = data.get('Version', "-")
        self.category = data.get('Category', "-")
        self.description = data.get('Description', "")
        
    def init_description(self, iostream):
        self.description = iostream.read()
        
    @property
    def metadata(self):
        return [str(item) for item in [self.name, self.author, self.version, self.category]]
    
    @staticmethod
    def check_if_match(itempath):
        raise NotImplementedError
        
    def toLoose(self, path):
        raise NotImplementedError
        
    def get_filelist(self):
        raise NotImplementedError


class LooseMod(ModFile):
    def __init__(self, path):
        super().__init__(path)
        metadata_path = os.path.join(path, 'METADATA.json')
        with JSONHandler(metadata_path, "Error reading JSON file 'METADATA.json'") as stream:
            self.init_metadata(stream)

        desc_path = os.path.join(path, 'DESCRIPTION.html')
        if os.path.exists(desc_path):
            with open(desc_path, 'r', encoding="utf8") as fJ:
                self.init_description(fJ)
        self.wizard = None
        
    @staticmethod
    def check_if_match(itempath):
        if os.path.isdir(itempath):
            if os.path.exists(os.path.join(itempath, "modfiles/")):
                return True
        return False
    
    def toLoose(self, path):
        shutil.copytree(self.path, path, dirs_exist_ok=True)
        
    def get_filelist(self):
        return [os.path.join(parent_dir, file) for parent_dir, _, files in os.walk(self.path) for file in files]
