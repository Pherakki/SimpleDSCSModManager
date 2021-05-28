import os
import json

from ModFiles.ScriptModding import modify_squirrel_source

def squirrel_modify(working_script_filepath, sqmod_path):
    wsd, wdf = os.path.split(working_script_filepath)
    
    with open(sqmod_path, 'r') as F:
        modifications = json.load(F)
    modify_squirrel_source(working_script_filepath, modifications)# , patch_filepath)
