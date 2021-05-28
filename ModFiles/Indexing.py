import csv
import os
from Utils.Path import splitpath


def generate_mod_index(modpath, rules, filetypes):
    # Register .mbe records + rules,
    # Register .hca files + rules,
    # Register all other files + rules
    retval = {filetype.group: {} for filetype in filetypes}
    for path, directories, files in os.walk(os.path.relpath(modpath)):
        for file in files:
            for filetype in filetypes:
                if filetype.checkIfMatch(path, file):
                    rule = rules.get(os.path.join(*splitpath(path)[3:], file))
                    category, key, index_data = filetype.produce_index(path, file, rule)
                    if key not in retval[category]:
                        retval[category][key] = {}
                    retval[category][key].update(index_data)
                    break
                
            
    return retval
