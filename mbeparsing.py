import json
import os
#import PIL
import shutil
import tempfile
#  'hackers_memory_para.mbe'
# 'battle_command_effect' 'item'
# ('data/', 'model_attach_para.mbe', 'event.csv')
# ('data/', 'model_attach_para.mbe', 'npc.csv')

#from ModFiles.Detection import detect_mods


with open("config/mberules.json", 'r') as F:
    mbe_rules = json.load(F)
with open("config/mberules.json", 'r') as F:
    mbe_record_sizes = json.load(F)
    
def overwrite(working_dir, file, path, open_mbes, graph, n):
    shutil.copy2(file, os.path.join(path, file[len(working_dir)+1:]))
    for i, elem in enumerate(graph):
        if elem != 0:
            graph[i] = 1
    graph.append(5)
            
def overwrite_mbe_records(working_dir, file, path, open_mbes, graphs, n):
    filepath = os.path.join(working_dir, file)
    file_contents = parse_id_mbe(filepath)
    key = os.path.join(os.path.split(file))
    if key not in open_mbes:
        open_mbes[key] = {}
    for record_id, record in file_contents.items():
        record_key = os.path.join(file, record_id)
        open_mbes[key][record_id] = record
        if record_key not in graphs:
            graphs[record_key] = [0]*n
        graphs[record_key].append(2)
    graphs[key].append(2)
    os.remove(filepath)
    

        
def append_mbe_records(working_dir, file, path, open_mbes, graphs, n):
    filepath = os.path.join(working_dir, file)
    file_contents = parse_id_mbe(filepath)
    key = os.path.join(os.path.split(file))
    any_exceeded_max = False
    if key not in open_mbes:
        open_mbes[key] = {}
    for record_id, record in file_contents.items():
        open_mbes[key][record_id].extend(record)
        record_key = os.path.join(file, record_id)
        if record_key not in graphs:
            graphs[record_key] = [0]*n
        if len(open_mbes[key][record_id]) > mbe_record_sizes:
            any_exceeded_max = True
            graphs[record_key] = 4
        else:
            graphs[record_key] = 3
    if any_exceeded_max:
        graphs[file] = 4
    else:
        graphs[file] = 3
    os.remove(filepath)

overwrite_states = {
        0: {'Type': 'Unaffected'},
        1: {'Type': 'Overwritten'},
        2: {'Type': 'Records Overwritten'},
        3: {'Type': 'Records Extended'},
        4: {'Type': 'Records Exceeded Size Limit'},
        5: {'Type': 'In Use'},
        6: {'Type': 'New File'},
        7: {'Type': 'UDIM tile overwritten'}
}

overwrite_rules = {
        'overwrite': overwrite,
        'overwrite_mbe_records': overwrite_mbe_records,
        'append_mbe_records': append_mbe_records
}


mbe_dir = r"./extracted_mbes/extracted_mbes/"
example_mbe = mbe_dir + "data/digimon_common_para.mbe/"

class mbe_contents(dict):
    def __init__(self, header):
        super().__init__(self)
        self.column_headers = header.split(',')

def parse_id_mbe(file_path):
    with open(file_path, 'r') as F:
        contents = mbe_contents(F.readline().splitlines()[0])
        for line in F.read().splitlines():
            content = line.split(',')
            contents[content[0]] = content[1:]
    return contents

class modelement_is_directory:
    pass

class modelement_is_unsorted_directory:
    pass

class modelement_is_unsorted_file:
    pass

class modelement_is_packed_mbe:
    @staticmethod
    def get_name():
        return 'packed_mbe'
    
    @staticmethod
    def test(item):
        if os.path.splitext(item)[-1] == '.mbe':
            return True
        return False
    
class modelement_is_loose_mbe:
    @staticmethod
    def get_name():
        return 'loose_mbe'
    
    @staticmethod
    def test(item):
        if os.path.isdir(item) and item.split('.')[-1] == 'mbe':
            return True
        return False

# Grab from a config?
directory_tests = [modelement_is_loose_mbe]
file_tests = [modelement_is_packed_mbe]

def run_tests(tests, items_to_test, results, installation_rules):
    for test in tests:
        passed, failed = [], []
        for fullpath in items_to_test:
            (passed if test.test(fullpath) else failed).append(fullpath)
        #for element in passed:
        #    installation_rules[element] = test.installation_rule
        results[test] = passed
        items_to_test = failed
    return items_to_test

def parse_modfiles(mod_path):
    dir_items = os.scandir(mod_path)
    directories = []
    files = []
    installation_rules = []
    for dir_item in dir_items:
        (directories if dir_item.is_dir() else files).append(dir_item.path)
    results = {}
    results[modelement_is_unsorted_file] = run_tests(file_tests, files, results, installation_rules)
    results[modelement_is_unsorted_directory] = run_tests(directory_tests, directories, results, installation_rules)
    results[modelement_is_directory] = directories
    
    for directory_path in directories:
        for result_id, result in parse_modfiles(directory_path).items():
            if result_id in results:
                results[result_id].extend(result)
            else:
                results[result_id] = result
    return results

def generate_patched_mods(mods, output_dir):
    graphs = {}
    open_mbes = {}
    file_test_classes = [modelement_is_unsorted_file, *file_tests]
    with tempfile.TemporaryDirectory() as patch_dir:
        for i, mod in enumerate(mods):
            with tempfile.TemporaryDirectory() as working_dir:
                mod.toLoose(working_dir)
                working_dir_length = len(working_dir)
                marked_files = parse_modfiles(working_dir)
                
                for directory in marked_files[modelement_is_unsorted_directory]:
                    os.makedirs(os.path.join(patch_dir, directory[working_dir_length+1:]), exist_ok=True)
                files_used = []
                for file_class in file_test_classes:
                    for filename in marked_files[file_class]:
                        key = os.path.split(filename[working_dir_length+1:])
                        if key[0] == '':
                            key = key[1:]
                        key = os.path.join(*key)
                        files_used.append(key)
                        rule = mbe_rules.get(key, 'overwrite')
                        
                        if key not in graphs:
                            graphs[key] = [0]*i
                        overwrite_rules[rule](working_dir, filename, patch_dir, open_mbes, graphs[key], i)
                for filename in graphs:
                    if filename not in files_used:
                        graphs[filename].append(0)
            
        true_patch_dir = os.path.join(output_dir, 'patch')
        if os.path.exists(true_patch_dir):
            shutil.rmtree(true_patch_dir)
        #os.makedirs(true_patch_dir, exist_ok=True)
        shutil.copytree(patch_dir, true_patch_dir)
        
    return graphs

#script_loc = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))
#mods = detect_mods(script_loc)

#patchgraph = generate_patched_mods(mods)

#import time

#times = []
#for _ in range(50):
#    st = time.time()
#    patchgraph = generate_patched_mods(mods)
#    ed = time.time()
#    times.append(ed-st)
    
#import numpy as np

# Approx 40ms to fully parse a single mod
#print(np.mean(times), np.std(times))
                    