import csv
import os
import shutil
from .ScriptPatching import patch_scripts

def generate_patch(indices, working_dir, resources_dir):
    for index in indices:
        patch_mbes(index, working_dir, resources_dir)
        patch_script_src(index, working_dir, resources_dir)
        patch_others(index, working_dir, resources_dir)

            
def patch_mbes(index, working_dir, resources_dir):
    for mbe_table_filepath, mbe_rules in index['mbe'].items():
        mbe_table_filepath = os.path.relpath(mbe_table_filepath)
        # E.g. data/mbe_folder/table.csv
        mbe_table_datapath = os.path.join(*splitpath(mbe_table_filepath)[-3:])
        working_mbe_filepath = os.path.join(working_dir, mbe_table_datapath)

        if not os.path.exists(working_mbe_filepath):
            working_mbe_path = os.path.split(working_mbe_filepath)[0] + os.path.sep
            os.makedirs(working_mbe_path, exist_ok=True)
            resource_filepath = os.path.join(resources_dir, 'base_mbes', mbe_table_datapath)
            resource_path = os.path.split(resource_filepath)[0]
            for file in os.listdir(resource_path):
                shutil.copy2(os.path.join(resource_path, file), os.path.join(working_mbe_path, file))
        
        # Join the records of the two tables
        header, mbe_data = mbetable_to_dict(working_mbe_filepath)
        _, mod_mbe_data = mbetable_to_dict(mbe_table_filepath)
        for record_id, record_rule in mbe_rules.items():
            # record_rule(record_id, mbe_data)
            mbe_data[record_id] = mod_mbe_data[record_id]
        dict_to_mbetable(working_mbe_filepath, header, mbe_data)
        
        
def patch_script_src(index, working_dir, resources_dir):
    for script_filepath, script_rules in index['script_src'].items():
        script_filepath = os.path.relpath(script_filepath)
        local_filepath = os.path.join(*splitpath(script_filepath)[3:])
        
        working_script_filepath = os.path.join(working_dir, local_filepath)
        wsd, wdf = os.path.split(working_script_filepath)
        patch_filepath = os.path.join(wsd, '_' + wdf)
        
        if not os.path.exists(working_script_filepath):
            working_script_path = os.path.split(working_script_filepath)[0] + os.path.sep
            os.makedirs(working_script_path, exist_ok=True)
            resource_path = os.path.join(resources_dir, 'base_scripts', 'script64')
            for file in os.listdir(resource_path):
                shutil.copy2(os.path.join(resource_path, file), os.path.join(working_script_path, file))
                
                
        patch_scripts(working_script_filepath, script_filepath, patch_filepath)
        os.remove(working_script_filepath)
        os.rename(patch_filepath, working_script_filepath)
        
def patch_others(index, working_dir, resources_dir):
    for other_filepath, other_rules in index['other'].items():
        local_filepath = os.path.join(*splitpath(other_filepath)[3:])
        working_filepath = os.path.join(working_dir, local_filepath)
        working_path = os.path.join(*splitpath(working_filepath)[:-1]) + os.path.sep
        if not os.path.exists(working_path):
            os.makedirs(working_path, exist_ok=True)
        # Only if 'overwrite' rule...
        shutil.copy2(other_filepath, working_filepath)
            
id_lengths = {'mon_design_para.mbe\Monster.csv': 2}
known_duplicates = [(('107', '1'), 'mon_design_para.mbe\Monster.csv')]            

def mbetable_to_dict(filepath):
    header = None
    result = {}
    with open(filepath, 'r', encoding='utf8') as F:
        header = F.readline()
        csvreader = csv.reader(F, delimiter=',', quotechar='"')
        for line in csvreader:
            data = line
            id_length_key = '\\'.join(splitpath(filepath)[-2:])
            id_size = id_lengths.get(id_length_key, 1)
            record_id = tuple(data[:id_size])
            if record_id not in result:
                result[record_id] = data[id_size:]
            elif (record_id, id_length_key) in known_duplicates:
                pass
            else:
                assert 0, f"Duplicate ID {record_id} in {filepath}, mod manager not ready to handle this situation yet. Please raise an issue on the GitHub page."
    return header, result

def dict_to_mbetable(filepath, header, result):
    with open(filepath, 'w', newline='', encoding='utf8') as F:
        F.write(header)
        csvwriter = csv.writer(F, delimiter=',', quotechar='"')
        for key, value in result.items():
            csvwriter.writerow(([*key, *value]))

            
def splitpath(path):
    return os.path.normpath(path).split(os.path.sep)
