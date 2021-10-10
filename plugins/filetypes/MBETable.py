import csv
import json
import os
from Utils.Path import splitpath

with open(os.path.join("config", "mberecordidsizes.json"), 'r') as F:
    id_lengths = json.load(F)

class MBE_table:
    group = 'mbe'
    enable_softcodes = True
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1].split('.')[-1] == 'mbe' and os.path.splitext(filename)[-1] == '.csv':
            return True
        else:
            return False
        
    @classmethod
    def produce_index(cls, path, filename, rule):
        index = []
        if rule is None:
            rule = 'mberecord_overwrite'
        mbe_filepath = os.path.join(path, filename)
        with open(mbe_filepath, 'r', encoding='utf8') as F:
            F.readline()
            id_len = id_lengths.get('/'.join(splitpath(mbe_filepath)[-3:]), 1)
            csvreader = csv.reader(F, delimiter=',', quotechar='"')
            for line in csvreader:
                record_id = [item.strip() for item in line[:id_len]]
                index.append(record_id)
        return cls.group, os.path.join(path, filename), {tuple(idx): rule for idx in index}
