import os
import json

from Utils.Settings import default_encoding
from Utils.Softcodes import replace_softcodes
from Utils.SqModImpl import modify_squirrel_source

class squirrel_modify:
    overrides_all_previous = False
    is_anchor = True
    is_solitary = False
    
    group = "Script"
    
    def __call__(self, build_data):
        sqmod_path      = build_data.source
        source_code     = build_data.source_code
        softcodes       = build_data.softcodes
        softcode_lookup = build_data.softcode_lookup
        
        with open(sqmod_path, 'rb') as F:
            modifications = replace_softcodes(F.read(), softcodes, softcode_lookup)
            modifications = json.loads(modifications.decode(default_encoding))
        return modify_squirrel_source(source_code, modifications)

# overwrite