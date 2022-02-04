import csv
import json
import os
from Utils.Path import splitpath

class MBE_table:
    group = 'mbe'
    default_rule = 'mberecord_merge'
    enable_softcodes = True
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1].split('.')[-1] == 'mbe' and os.path.splitext(filename)[-1] == '.csv':
            return True
        else:
            return False
        
    @staticmethod
    def get_target(filepath):
        return filepath
    
    @classmethod
    def get_rule(cls, filepath):
        return cls.default_rule
        
    # @classmethod
    # def produce_index(cls, path, filename):
    #     index = []
    #     mbe_filepath = os.path.join(path, filename)
    #     with open(mbe_filepath, 'r', encoding='utf8') as F:
    #         F.readline()
    #         id_len = id_lengths.get('/'.join(splitpath(mbe_filepath)[-3:]), 1)
    #         csvreader = csv.reader(F, delimiter=',', quotechar='"')
    #         for line in csvreader:
    #             record_id = [item.strip() for item in line[:id_len]]
    #             index.append(record_id)
    #     return cls.group, os.path.join(path, filename), [tuple(idx) for idx in index]

    @staticmethod
    def get_pack_name(filepath):
        return os.path.split(filepath)[0]
