import csv
import os

id_lengths = {'mon_design_para.mbe\Monster.csv': 2}

class MBE_table:
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1].split('.')[-1] == 'mbe' and os.path.splitext(filename)[-1] == '.csv':
            return True
        else:
            return False
        
    @staticmethod
    def produce_index(path, filename, rule):
        index = []
        if rule is None:
            rule = 'mbe_overwrite'
        mbe_filepath = os.path.join(path, filename)
        with open(mbe_filepath, 'r', encoding='utf8') as F:
            F.readline()
            id_len = id_lengths.get('\\'.join(splitpath(mbe_filepath)[-2:]), 1)
            csvreader = csv.reader(F, delimiter=',', quotechar='"')
            for line in csvreader:
                record_id = [item.strip() for item in line[:id_len]]
                index.append(record_id)
        return 'mbe', os.path.join(path, filename), {tuple(idx): rule for idx in index}
    
class Other:
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.isfile(os.path.join(path, filename)):
            return True
    
    def produce_index(path, filename, rule):
        if rule is None:
            rule = 'overwrite'
        return 'other', os.path.join(path, filename), {filename: rule}

filetypes = [MBE_table, Other]

def generate_mod_index(modpath, rules):
    # Register .mbe records + rules,
    # Register .hca files + rules,
    # Register all other files + rules
    retval = {'mbe': {}, 'hca': {}, 'other': {}}
    for path, directories, files in os.walk(os.path.relpath(modpath)):
        for file in files:
            for filetype in filetypes:
                if filetype.checkIfMatch(path, file):
                    rule = rules.get(os.path.join(path, file))
                    category, key, index_data = filetype.produce_index(path, file, rule)
                    if key not in retval[category]:
                        retval[category][key] = {}
                    retval[category][key].update(index_data)
                    break
                
                
    return retval
        
def splitpath(path):
    return os.path.normpath(path).split(os.path.sep)

