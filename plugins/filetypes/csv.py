import os
from src.CoreOperations.PluginLoaders.FiletypesPluginLoader import BaseBuildElement, BaseFiletype

class CSVFileBuildElement(BaseBuildElement):
    __slots__ = tuple()
    
    build_element_id = 'csv'
    default_rule = 'mberecord_merge'
    enable_softcodes = True
        
    @staticmethod
    def get_target(filepath):
        return filepath
    
    @classmethod
    def get_rule(cls, filepath):
        return cls.default_rule
        
    @staticmethod
    def get_pack_name(filepath):
        return filepath
    
    @classmethod
    def get_filetype_cls(cls):
        return CSVFile

    
class CSVFile(BaseFiletype):
    __slots__ = tuple()
    
    build_elements = [CSVFileBuildElement]
    filetype_id = "csv"
    filepack = "CSV"
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1].split('.')[-1] != 'mbe' and os.path.splitext(filename)[-1] == '.csv':
            return True
        else:
            return False
