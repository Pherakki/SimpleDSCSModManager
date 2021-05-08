import inspect
import os

from PyQt5 import QtCore

from Utils.PluginLoad import load_plugins_in
from Utils.Path import splitpath


def get_patcher_plugins():
    plugin_dir = os.path.join('plugins', 'patchers')
    
    return [patcher for patcher in [*load_plugins_in(plugin_dir, inspect.isclass), patch_others]]

class patch_others(QtCore.QRunnable):
    group = 'other'
    singular_msg = "copying file"
    plural_msg = "copying files"
    
    def __init__(self, rules_dictionary, working_dir, resources_dir, other_filepath, other_rules,
                 update_messagelog, update_finished, raise_exception):
        super().__init__()
        
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.other_filepath = other_filepath
        self.other_rules = other_rules
        
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        
        self.rules_dictionary = rules_dictionary
        
    def run(self):
        try:
            working_dir = self.working_dir
            other_filepath = self.other_filepath
            other_rules = self.other_rules
            
            local_filepath = os.path.join(*splitpath(other_filepath)[3:])
            working_filepath = os.path.join(working_dir, local_filepath)
            working_path = os.path.join(*splitpath(working_filepath)[:-1]) + os.path.sep
            if not os.path.exists(working_path):
                os.makedirs(working_path, exist_ok=True)

            assert len(other_rules) == 1, f"More than one rule: {other_rules}"
            rule_name = list(other_rules.values())[0]
            self.rules_dictionary[rule_name](working_filepath, other_filepath)
            
            self.update_messagelog(local_filepath)
            self.update_finished()
        except Exception as e:
            self.raise_exception(e)
            