import inspect
import os

from CoreOperations.PluginLoaders.PluginLoad import load_sorted_plugins_in


def get_filetype_plugins():
    plugin_dir = os.path.join('plugins', 'filetypes')
    
    return [*load_sorted_plugins_in(plugin_dir, inspect.isclass), UnhandledFiletype]

def get_filetype_plugins_dict():
    return {plugin.group: plugin for plugin in get_filetype_plugins()}

def get_type_of_file(path, filename):
    for plugin in get_filetype_plugins():
        if plugin.checkIfMatch(path, filename):
            return plugin
    return None
        
class BaseFiletype:
    @staticmethod
    def checkIfMatch(path, filename):
        raise NotImplementedError()
    
    @staticmethod
    def get_target(filepath):
        raise NotImplementedError()
    
    @classmethod
    def get_rule(cls, filepath):
        raise NotImplementedError()
    
    @classmethod
    def produce_index(cls, path, filename):
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
    
    @classmethod
    def produce_index(cls, path, filename):
        return cls.group, os.path.join(path, filename), [filename]

    @staticmethod
    def get_pack_name(filepath):
        return filepath
