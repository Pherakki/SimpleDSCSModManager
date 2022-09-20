import os
import sys

from src.CoreOperations.PluginLoaders.FiletypesPluginLoader import BaseBuildElement, BaseFiletype


class UncompiledScriptBuildElement(BaseBuildElement):
    __slots__ = tuple()
    
    build_element_id = sys.intern('script_src')
    default_rule =  sys.intern('squirrel_concat')
    enable_softcodes = True
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1] == 'script64' and os.path.splitext(filename)[-1] == '.txt':
            return True
        else:
            return False
        
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
        return UncompiledScript
        

class UncompiledScript(BaseFiletype):
    __slots__ = tuple()
    
    build_elements = [UncompiledScriptBuildElement]
    filetype_id =  sys.intern("script_src")
    filepack = sys.intern("Script")
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1] == 'script64' and os.path.splitext(filename)[-1] == '.txt':
            return True
        else:
            return False
