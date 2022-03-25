import os
import sys

from CoreOperations.ModRegistry.Softcoding import search_string_for_softcodes, search_bytestring_for_softcodes
from Utils.Path import splitpath


class IndexFileException(Exception):
    def __init__(self, base_msg, modfile_name):
        super().__init__(self)
        self.base_msg = base_msg
        self.modfile_name = modfile_name
        
    def __str__(self):
        return f"{self.modfile_name}: {self.base_msg}"
    
def make_buildgraph_path(filepath):
    return os.path.join(*splitpath(filepath)[3:])

def index_mod_contents(modpath, filetypes):
    last_edit_time = 0
    retval = {filetype.group: {} for filetype in filetypes}
    for path, directories, files in os.walk(os.path.relpath(modpath)):
        for file in files:
            for filetype in filetypes:
                category = filetype.group
                if filetype.checkIfMatch(path, file):
                    filepath = os.path.join(path, file)
                    last_edit_time = max([os.path.getmtime(filepath), last_edit_time])
                    try:
                        retval[category][filepath] = filetype.get_target(os.path.join(*splitpath(filepath)[3:]))
                    except Exception as e:
                        raise IndexFileException(e.__str__(), filepath)
                    break
                
            
    return retval, last_edit_time


def index_mod_softcodes(modpath, filetypes, mod_contents_index):
    softcodable_filetypes = sorted(list(set([filetype.group for filetype in filetypes if getattr(filetype, "enable_softcodes", False)])))
    softcodes = {}
    all_softcodes = set()
    for filetype in softcodable_filetypes:
        files = mod_contents_index[filetype]
        for file in files:
            file_softcodes = {}
            with open(file, 'rb') as F:
                line = F.readline()
                line_offset = F.tell()
                while line:
                    for match in search_bytestring_for_softcodes(line):
                        code_offset = match.start() - 1
                        match = match.group(0)
                        print(match)
                        match = match.decode('utf8')
                        if match not in file_softcodes:
                            file_softcodes[match] = []
                        file_softcodes[match].append(line_offset + code_offset)
                        all_softcodes.add(match)
                    line_offset = F.tell()
                    line = F.readline()
            softcodes[file] = file_softcodes
    return softcodes, all_softcodes
         
def get_targets_softcodes(filetargets):
    target_softcodes = {}
    all_softcodes = set()
    for filepath, targets in filetargets.items():
        for target in targets:
            target_softcodes[target] = {}
            for match in search_string_for_softcodes(target):
                code_offset = match.start() - 1
                code = match.group(0)
                if code not in target_softcodes[target]:
                    target_softcodes[target][code] = []
                target_softcodes[target][code].append(code_offset)
                all_softcodes.add(code)
            if not len(target_softcodes[target]):
                del target_softcodes[target]
    return target_softcodes, all_softcodes
    
    contents, last_edit_time = index_mod_contents(filepath, filetypes)
    contents_softcodes, all_softcodes = index_mod_softcodes(filepath, filetypes, contents)
def build_index(config_path, filepath, filetypes, archive_getter, archive_from_path_getter, targets_getter, rules_getter, filepath_getter):
    archives = archive_getter(filepath, contents)
    targets = targets_getter(filepath, contents, archives)
    rules = rules_getter(filepath, contents)
    
    target_softcodes, all_target_softcodes = get_targets_softcodes(targets)

    all_softcodes = all_softcodes.union(all_target_softcodes)
    
    mod_key = sys.intern("mod")
    src_key = sys.intern("src")
    softcode_key = sys.intern("softcodes")
    rule_key = sys.intern("rule")
        
    filetype_map = {f.group : f for f in filetypes}
    
    # Do a pass over the contents of the file to figure out how they should
    # be categorised
    index = {}
    for filetype in contents:
        for file, _target in contents[filetype].items():
            if file in targets:
                file_targets = targets[file]
            else:
                file_targets = [_target]
                
            archive_type, archive = archives[file]
            
            # Build Archive Type Level
            if archive_type not in index:
                index[archive_type] = {}
            archive_type_index = index[archive_type]
            
            # Build Archive Level
            if archive not in archive_type_index:
                archive_type_index[archive] = {}
            archive_index = archive_type_index[archive]
                
            # Build File Target Level
            for target in file_targets:
                new_target = filepath_getter(target, archive)
                if new_target not in archive_index:
                    archive_index[new_target] = {"build_steps": []}
                    if target in target_softcodes:
                        archive_index[new_target]["softcodes"] = target_softcodes[target]
                target_info = archive_index[new_target]["build_steps"]
                
                # Now build the index entry
                path_elements = splitpath(file)
                mod_path_sec = sys.intern(os.path.join(*path_elements[:3]))
                file_path_sec = sys.intern(os.path.join(*path_elements[3:]))
                entry = {mod_key: mod_path_sec, src_key: file_path_sec}
                file_softcodes = contents_softcodes.get(file, {}) # {softcode_map[key]: value for key, value in contents_softcodes.get(file, {}).items()}
                if len(file_softcodes):
                    entry[softcode_key] = file_softcodes
                if file in rules:
                    entry[rule_key] = rules[file]
                else:
                    entry[rule_key] = filetype_map[filetype].get_rule(file)
                target_info.append(entry)

    # Cull the index of any empty groups... makes it a bit smaller on disk
    # and in memory
    # Since these groups are mostly added dynamically inside the main indexing
    # loop now, the first two of these at least probably won't be empty...
    # Keep in in since it's cheap to do and might end up removing the dynamic
    # index build and make it static again in the future
    for archive_type in list(index.keys()):
        # Delete if empty
        if not len(index[archive_type]):
            del index[archive_type]
            continue
        # Else, continue
        archive_type_index = index[archive_type]
        for archive in list(archive_type_index.keys()):
            # Delete if empty
            if not len(archive_type_index[archive]):
                del archive_type_index[archive]
                continue
            # Else, continue
            archive_index = archive_type_index[archive]
            for filetype in list(archive_index.keys()):
                if not len(archive_index[filetype]):
                    del index[archive][filetype]
                

    softcode_dump = [sys.intern(key) for key in sorted(all_softcodes)]

    return {'data': index, 'softcodes': softcode_dump, "last_edit_time": last_edit_time}
