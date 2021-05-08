import os
import shutil

from PyQt5 import QtCore

from Utils.Path import splitpath


class patch_script_src(QtCore.QRunnable):
    group = 'script_src'
    singular_msg = "patching script"
    plural_msg = "patching scripts"
    
    def __init__(self, rules_dictionary, working_dir, resources_dir, script_filepath, script_rules,
                 update_messagelog, update_finished, raise_exception):
        super().__init__()
        
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.script_filepath = script_filepath
        self.script_rules = script_rules
        
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        
        self.rules_dictionary = rules_dictionary
        
    def run(self):
        try:
            working_dir = self.working_dir
            resources_dir = self.resources_dir
            script_filepath = self.script_filepath
            script_rules = self.script_rules
            
            script_filepath = os.path.relpath(script_filepath)
            local_filepath = os.path.join(*splitpath(script_filepath)[3:])
            
            working_script_filepath = os.path.join(working_dir, local_filepath)
            
            if not os.path.exists(working_script_filepath):
                working_script_path = os.path.split(working_script_filepath)[0] + os.path.sep
                os.makedirs(working_script_path, exist_ok=True)
                resource_path = os.path.join(resources_dir, 'base_scripts', local_filepath)
                shutil.copy2(resource_path, working_script_filepath)
                    
            # I.e. execute rule
            assert len(script_rules) == 1, f"More than one rule: {script_rules}"
            rule_name = list(script_rules.values())[0]
            self.rules_dictionary[rule_name](working_script_filepath, script_filepath)
            
            self.update_messagelog(local_filepath)
            self.update_finished()
        except Exception as e:
            self.raise_exception(e)