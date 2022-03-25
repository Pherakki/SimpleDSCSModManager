import os
from CoreOperations.PluginLoaders.FiletypesPluginLoader import BaseBuildElement, BaseFiletype, get_filetype_plugins

class RequestFileBuildElement(BaseBuildElement):
    __slots__ = tuple()
    
    build_element_id = "request"
    default_rule = 'request_file'
    enable_softcodes = False
    
    @staticmethod
    def get_target(filepath):
        return os.path.splitext(filepath)[0]
    
    @classmethod
    def get_rule(cls, filepath):
        return cls.default_rule
    
    # Not actually needed?
    @staticmethod
    def get_pack_name(filepath):
        return filepath
    
    @classmethod
    def get_filetype_cls(cls):
        return RequestFile

class RequestFile(BaseFiletype):
    filetype_id = "request"
    build_elements = [RequestFileBuildElement]
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.splitext(filename)[-1] == '.request':
            return True
        else:
            return False