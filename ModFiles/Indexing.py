import csv
import os
from Utils.PluginLoad import load_plugins_in


filetype_plugins = load_plugins_in(os.path.join('plugins', 'filetypes'))
    
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

filetypes = [*filetype_plugins, UnhandledFiletype]

def generate_mod_index(modpath, rules):
    # Register .mbe records + rules,
    # Register .hca files + rules,
    # Register all other files + rules
    retval = {'mbe': {}, 'hca': {}, 'other': {}, 'script_src': {}}
    for path, directories, files in os.walk(os.path.relpath(modpath)):
        for file in files:
            for filetype in filetypes:
                if filetype.checkIfMatch(path, file):
                    rule = rules.get(os.path.join(path, file))
                    category, key, index_data = filetype.produce_index(path, file, rule)
                    if key not in retval[category]:
                        retval[category][key] = {}
                    retval[category][key].update(index_data)
                    break
                
                
    return retval
        
def splitpath(path):
    return os.path.normpath(path).split(os.path.sep)

