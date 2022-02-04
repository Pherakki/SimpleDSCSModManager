import os
import json

from Utils.SqModImpl import modify_squirrel_source

def squirrel_modify(source_code, sqmod_path):
    with open(sqmod_path, 'r') as F:
        modifications = json.load(F)
    return modify_squirrel_source(source_code, modifications)
