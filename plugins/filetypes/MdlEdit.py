import os
from CoreOperations.PluginLoaders.FiletypesPluginLoader import BaseBuildElement, BaseFiletype


def make_build_elem_class(i, ext):
    class ModelEditBuildElement(BaseBuildElement):
        __slots__ = tuple()
        rule_index = i
        build_element_id = ext + 'file'
        default_rule = 'mdledit_' + ext
        enable_softcodes = True
            
        @staticmethod
        def get_target(filepath):
            return os.path.extsep.join((os.path.splitext(filepath)[0], ext))
        
        @classmethod
        def get_rule(cls, filepath):
            return cls.default_rule
    
        @staticmethod
        def get_pack_name(filepath):
            return os.path.splitext(filepath)[0]
        
        @classmethod
        def get_filetype_cls(cls):
            return ModelEditFile
        
    return ModelEditBuildElement

class ModelEditFile(BaseFiletype):
    build_elements = [make_build_elem_class(i, ext) for i, ext in enumerate(["name", "skel", "geom", "anim"])]
    filetype_id = "mdledit"
    filepack = "Model"
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.splitext(filename)[-1] == '.mdledit':
            return True
        else:
            return False

        