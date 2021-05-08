import os

from Utils.PluginLoad import load_sorted_plugins_in


def get_filetype_plugins():
    plugin_dir = os.path.join('plugins', 'filetypes')
    
    return [*load_sorted_plugins_in(plugin_dir), UnhandledFiletype]

class UnhandledFiletype:
    group = 'other'
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.isfile(os.path.join(path, filename)):
            return True
    
    @classmethod
    def produce_index(cls, path, filename, rule):
        if rule is None:
            rule = 'overwrite'
        return cls.group, os.path.join(path, filename), {filename: rule}
