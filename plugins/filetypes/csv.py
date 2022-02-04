import csv
import json
import os
from Utils.Path import splitpath

class MBE_table:
    group = 'csv'
    default_rule = 'mberecord_merge'
    enable_softcodes = True
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1].split('.')[-1] != 'mbe' and os.path.splitext(filename)[-1] == '.csv':
            return True
        else:
            return False
        
    @staticmethod
    def get_target(filepath):
        return filepath
    
    @classmethod
    def get_rule(cls, filepath):
        return cls.default_rule
        
    @staticmethod
    def get_pack_name(filepath):
        return filepath
