import os

# from ModFiles.ScriptPatching import patch_scripts


def squirrel_concat(source_code, script_filepath):
    with open(script_filepath, 'r') as F:
        mod_source_code = F.read()
    source_code += "\n// CONCAT INPUT FILE: \n\n"
    source_code += mod_source_code
    
    return source_code
    