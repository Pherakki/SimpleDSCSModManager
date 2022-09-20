import os

from src.Utils.Settings import default_encoding
from src.Utils.Softcodes import replace_softcodes
# from ModFiles.ScriptPatching import patch_scripts


class squirrel_concat:
    overrides_all_previous = False
    is_anchor = True
    is_solitary = False
    
    group = "Script"
    
    def __call__(self, build_data):
        script_filepath = build_data.source
        source_code     = build_data.source_code
        softcodes       = build_data.softcodes
        softcode_lookup = build_data.softcode_lookup
        
        with open(script_filepath, 'rb') as F:
            mod_source_code = replace_softcodes(F.read(), softcodes, softcode_lookup).decode(default_encoding)
        source_code += "\n// CONCAT INPUT FILE: \n\n"
        source_code += mod_source_code
        
        
        return source_code
    