import os
from src.CoreOperations.PluginLoaders.FiletypesPluginLoader import BaseBuildElement, BaseFiletype

class SqModBuildElement(BaseBuildElement):
    __slots__ = tuple()
    
    build_element_id = 'sqmod'
    default_rule = 'squirrel_modify'
    enable_softcodes = True
    
    @staticmethod
    def get_target(filepath):
        return os.path.splitext(filepath)[0] + ".txt"
    
    @classmethod
    def get_rule(cls, filepath):
        return cls.default_rule

    @staticmethod
    def get_pack_name(filepath):
        return filepath

    @classmethod
    def get_filetype_cls(cls):
        return SqMod
    
    
class SqMod(BaseFiletype):
    __slots__ = tuple()
    
    build_elements = [SqModBuildElement]
    filetype_id = "sqmod"
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1] == 'script64' and os.path.splitext(filename)[-1] == '.sqmod':
            return True
        else:
            return False
    
