import csv
import json
import os
import shutil

from PyQt5 import QtCore

from Utils.Path import splitpath

with open(os.path.join("config", "mberecordidsizes.json"), 'r') as F:
    id_lengths = json.load(F)
with open(os.path.join("config", "mberecordsizes.json"), 'r') as F:
    max_record_sizes = json.load(F)
    
known_duplicates = []
with open(os.path.join("config", "mbeduplicaterecords.json"), 'r') as F:
    for key, value in json.load(F).items():
        for subkey in value:
            known_duplicates.append((tuple(subkey), key))

class mbe_patcher(QtCore.QRunnable):
    group = 'mbe'
    singular_msg = "patching MBE"
    plural_msg = "patching MBEs"
    
    def __init__(self, rules_dictionary, working_dir, resources_dir, mbe_table_filepath, mbe_rules,
                 update_messagelog, update_finished, raise_exception):
        super().__init__()
        
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.mbe_table_filepath = mbe_table_filepath
        self.mbe_rules = mbe_rules
        
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        
        self.rules_dictionary = rules_dictionary
        
    def run(self):
        try:
            mbe_table_filepath = self.mbe_table_filepath
            working_dir = self.working_dir
            resources_dir = self.resources_dir
            mbe_rules = self.mbe_rules
            
            mbe_table_filepath = os.path.relpath(mbe_table_filepath)
            local_filepath = os.path.join(*splitpath(mbe_table_filepath)[3:])
            # E.g. data/mbe_folder/table.csv
            mbe_table_datapath = os.path.join(*splitpath(mbe_table_filepath)[-3:])
            working_mbe_filepath = os.path.join(working_dir, mbe_table_datapath)
    
            if not os.path.exists(working_mbe_filepath):
                working_mbe_path = os.path.split(working_mbe_filepath)[0] + os.path.sep
                os.makedirs(working_mbe_path, exist_ok=True)
                resource_filepath = os.path.join(resources_dir, 'base_mbes', mbe_table_datapath)
                # Need to copy every table inside the MBE
                resource_path = os.path.split(resource_filepath)[0]
                for file in os.listdir(resource_path):
                    shutil.copy2(os.path.join(resource_path, file), os.path.join(working_mbe_path, file))
            
            # Join the records of the two tables
            header, mbe_data = mbetable_to_dict(working_mbe_filepath)
            _, mod_mbe_data = mbetable_to_dict(mbe_table_filepath)
            for record_id, record_rule in mbe_rules.items():
                key = '/'.join(splitpath(mbe_table_filepath)[-3:])
                self.rules_dictionary[record_rule](record_id, mbe_data, mod_mbe_data, max_record_sizes.get(key, 1))
            dict_to_mbetable(working_mbe_filepath, header, mbe_data)
            
            self.update_messagelog(local_filepath)
            self.update_finished()
        except Exception as e:
            self.raise_exception(e)
               

def mbetable_to_dict(filepath):
    header = None
    result = {}
    id_length_key = '/'.join(splitpath(filepath)[-3:])
    id_size = id_lengths.get(id_length_key, 1)
    print(id_length_key, id_size)
    with open(filepath, 'r', encoding='utf8') as F:
        header = F.readline()
        csvreader = csv.reader(F, delimiter=',', quotechar='"')
        for line in csvreader:
            data = line
            record_id = tuple(data[:id_size])
            if record_id not in result:
                result[record_id] = data[id_size:]
            elif id_length_key in id_lengths:
                print(">>>", "Hit a duplicate in", filepath)
                result[record_id] = data[id_size:]
            else:
                assert 0, f"Duplicate ID {record_id} in {filepath}, mod manager not ready to handle this situation yet. Please raise an issue on the GitHub page."
    return header, result

def dict_to_mbetable(filepath, header, result):
    with open(filepath, 'w', newline='', encoding='utf8') as F:
        F.write(header)
        csvwriter = csv.writer(F, delimiter=',', quotechar='"')
        for key, value in result.items():
            csvwriter.writerow(([*key, *value]))