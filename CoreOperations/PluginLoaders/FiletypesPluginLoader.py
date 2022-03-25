import inspect
import os

from CoreOperations.PluginLoaders.PluginLoad import load_sorted_plugins_in


def get_filetype_plugins():
    plugin_dir = os.path.join('plugins', 'filetypes')
    
    return [*load_sorted_plugins_in(plugin_dir, lambda x: issubclass(x, BaseFiletype) if inspect.isclass(x) else False), UnhandledFiletype]

def get_build_element_plugins():
    plugin_dir = os.path.join('plugins', 'filetypes')
    
    return [*load_sorted_plugins_in(plugin_dir, lambda x: issubclass(x, BaseBuildElement) if inspect.isclass(x) else False), UnhandledFiletypeBuildElement]

def get_targettable_filetypes():
    return [plugin for plugin in get_filetype_plugins() if hasattr(plugin, "filepack")]

def get_type_of_file(path, filename):
    for plugin in get_filetype_plugins():
        if plugin.checkIfMatch(path, filename):
            return plugin
    return None
def get_build_element_plugins_dict():
    return {plugin.get_identifier(): plugin for plugin in get_build_element_plugins()}

        
class BaseFiletype:
    __slots__ = tuple()
    
    @staticmethod
    def checkIfMatch(path, filename):
        raise NotImplementedError()
    
    @staticmethod
    def get_target(filepath):
        raise NotImplementedError()
    
    @classmethod
    def get_rule(cls, filepath):
        raise NotImplementedError()

    @staticmethod
    def get_pack_name(filepath):
        raise NotImplementedError()

class UnhandledFiletype(BaseFiletype):
    group = 'other'
    default_rule = 'overwrite'
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.isfile(os.path.join(path, filename)):
            return True
    
    @staticmethod
    def get_target(filepath):
        return filepath
    
    @classmethod
    def get_rule(cls, filepath):
        return cls.default_rule

    @staticmethod
    def get_pack_name(filepath):
        return filepath
