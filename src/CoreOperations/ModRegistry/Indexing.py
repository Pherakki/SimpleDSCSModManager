import hashlib
import json
import os
import sys

from PyQt5 import QtCore
from src.CoreOperations.ModRegistry.Softcoding import search_string_for_softcodes, search_bytestring_for_softcodes
from src.Utils.Path import splitpath
from src.CoreOperations.PluginLoaders.FiletypesPluginLoader import get_build_element_plugins_dict
from src.CoreOperations.ModRegistry.BuildScript import BuildScript

translate = QtCore.QCoreApplication.translate

class IndexFileException(Exception):
    def __init__(self, base_msg, modfile_name):
        super().__init__(self)
        self.base_msg = base_msg
        self.modfile_name = modfile_name
        
    def __str__(self):
        return f"{self.modfile_name}: {self.base_msg}"
    
def make_buildgraph_path(filepath):
    return os.path.join(*splitpath(filepath)[4:])

def index_mod_contents(modpath, filetypes):
    last_edit_time = 0
    paths_hash = hashlib.sha256()
    
    retval = {be.get_identifier(): {} for filetype in filetypes for be in filetype.get_build_elements()}

    for path, directories, files in os.walk(os.path.relpath(modpath)):
        for file in files:
            filepath = os.path.join(path, file)
            truncated_path = make_buildgraph_path(filepath)
            paths_hash.update(filepath.encode("utf8"))
            for filetype in filetypes:
                if filetype.checkIfMatch(path, file):
                    last_edit_time = max([os.path.getmtime(filepath), last_edit_time])
                    
                    for be in filetype.get_build_elements():
                        category = be.get_identifier()
                        try:
                            retval[category][filepath] = be(truncated_path)
                            
                        except Exception as e:
                            raise IndexFileException(e.__str__(), filepath)
                    break
                
    bonus_files = ["METADATA.json", "BUILD.json", "ALIASES.json"]
    for file in bonus_files:
        filepath = os.path.join(modpath, file)
        if os.path.exists(filepath):
            last_edit_time = max([os.path.getmtime(filepath), last_edit_time])
                
            
    return retval, last_edit_time, paths_hash.hexdigest()

def register_softcode(softcode_list, all_softcodes, aliased_match, aliases, offset):
    match = find_softcode_alias(aliased_match, aliases)
    if match not in softcode_list:
        softcode_list[match] = []
    softcode_list[match].append([offset, len(aliased_match) + 2]) # + 2 For [ and ]
    all_softcodes.add(match)
    
def find_softcode_alias(match, aliases):
    for alias, identity in aliases.items():
        if match[:len(alias)] == alias:
            return identity + match[len(alias):]
    return match
    
def index_mod_softcodes(modpath, filetypes, mod_contents_index, aliases):
    softcodable_filetypes = sorted(list(set([be.get_identifier() for filetype in filetypes for be in filetype.get_build_elements() if getattr(be, "enable_softcodes", False)])))
    softcodes = {}
    all_softcodes = set()
    for filetype in softcodable_filetypes:
        files = mod_contents_index[filetype]
        for file in files:

            file_softcodes = {}
            with open(file, 'rb') as F:
                line = F.readline()
                line_offset = 0
                while line:
                    for match in search_bytestring_for_softcodes(line):
                        code_offset = match.start() - 1
                        match = match.group(0)
                        match = match.decode('utf8')
                        register_softcode(file_softcodes, 
                                          all_softcodes, 
                                          match, aliases, 
                                          line_offset + code_offset)
                    line_offset = F.tell()
                    line = F.readline()
            softcodes[file] = file_softcodes
    return softcodes, all_softcodes
         
def get_targets_softcodes(filetargets, aliases):
    target_softcodes = {}
    all_softcodes = set()
    for filepath, targets in filetargets.items():
        for target in targets:
            target_softcodes[target] = {}
            for match in search_string_for_softcodes(target):
                code_offset = match.start() - 1
                code = match.group(0)
                register_softcode(target_softcodes[target], 
                                  all_softcodes, 
                                  code, aliases,
                                  code_offset)

            if not len(target_softcodes[target]):
                del target_softcodes[target]
    return target_softcodes, all_softcodes

def include_autorequests(config_path, contents, archive_lookup):
    request_build_element = get_build_element_plugins_dict()[("request", "request")]
    with open(os.path.join(config_path, "filelist.json"), 'r') as F:
        filelist = json.load(F)
    out = {}
    
    for filetype in contents:
        for file, build_element in contents[filetype].items():
            key = archive_lookup[file]
            if key not in out:
                out[key] = set()
            archive_requests = out[key]
            archive_requests.update(build_element.get_autorequests(file))
                
    contents["autorequests"] = {}
    for archive, entries in out.items():
        for entry in sorted(entries):
            # If the file isn't a vanilla file, just ignore it
            # Fine since it's an autorequest; if it's a full request it will
            # error on another code path
            
            # Cut off the mods/modname/modfiles bit
            trunc_entry = os.path.sep.join(os.path.normpath(entry).split(os.path.sep)[4:])
            trunc_entry = os.path.splitext(trunc_entry)[0] # Split off the "request" bit

            if trunc_entry not in filelist:
                continue
            archive_lookup[entry] = archive
            contents["autorequests"][entry] = request_build_element(make_buildgraph_path(entry))


def alias_decoder(obj):
    if type(obj) == dict:
        return {k.rstrip(":") + "::" : v.rstrip(":") + "::" for k, v in obj.items()}
    elif type(obj) == str:
        return obj
    else:
        assert 0, "ALIASES.json must be a dict of strings."
    
def build_index(config_path, filepath, filetypes, archive_getter, archive_from_path_getter, targets_getter, rules_getter, filepath_getter):
    alias_path = os.path.join(os.path.split(filepath)[0], "ALIASES.json")
    if os.path.isfile(alias_path):
        try:
            with open(alias_path, 'r') as F:
                aliases = json.load(F, object_hook=alias_decoder)
        except Exception as e:
            raise Exception(translate("Indexing", "Could not read ALIASES.json, error was \"{error_msg}\".").format(error_msg=e.__str__()))
    else:
        aliases = {}
        
    buildscript_path = os.path.join(os.path.split(filepath)[0], "BUILD.json")
    if os.path.isfile(buildscript_path):
        try:
            buildscript = BuildScript.from_json(buildscript_path, filepath)
        except Exception as e:
            raise e
            raise Exception(translate("Indexing", "Could not read BUILD.json, error was \"{error_msg}\".").format(error_msg=e.__str__()))
    else:
        buildscript = None
    
    contents, last_edit_time, contents_hash = index_mod_contents(filepath, filetypes)
    contents_softcodes, all_softcodes = index_mod_softcodes(filepath, filetypes, contents, aliases)
    archives = archive_getter(filepath, contents)
    targets = targets_getter(filepath, contents, archives)
    rules = rules_getter(filepath, contents)

    buildscript_targets = {}
    if buildscript:
        mod_path_sec = splitpath(filepath)[-4:]
        for target, buildscript_pipeline in buildscript.target_dict.items():
            for buildstep in buildscript_pipeline.buildsteps:
                src = os.path.normpath(os.path.join(*mod_path_sec, buildstep.src_file))
                if src not in buildscript_targets:
                    buildscript_targets[src] = []
                buildscript_targets[src].append(os.path.normpath(target))
    
    target_softcodes, all_target_softcodes = get_targets_softcodes({**targets, **buildscript_targets}, aliases)


    all_softcodes = all_softcodes.union(all_target_softcodes)
    
    mod_key = sys.intern("mod")
    src_key = sys.intern("src")
    softcode_key = sys.intern("softcodes")
    rule_key = sys.intern("rule")
    rule_args_key = sys.intern("rule_args")
        
    include_autorequests(config_path, contents, archives)

    # Do a pass over the contents of the file to figure out how they should
    # be categorised
    index = {}
    for filetype in contents:
        for file, _target in contents[filetype].items():
            # If the file is used by the buildscript, then skip it
            # The buildscript overrides whatever it was originally going to build
            if file in buildscript_targets:
                continue
            
            # Redirect the target files of a source file if necessary
            if file in targets:
                targetpaths = targets[file]
                #assert type(targetpath) == list, "Invalid targetpath, not a list"
                #assert len(targetpath) == 1, "Invalid targetpath, length != 1"
                file_targets = [type(_target)(targetpath) for targetpath in targetpaths]
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
            # Make an entry for each Target the source file builds to
            for build_element in file_targets:
                target = build_element.get_target(build_element.filepath)
                new_target = filepath_getter(target, archive)
                if new_target not in archive_index:
                    archive_index[new_target] = {"build_steps": []}
                    if target in target_softcodes:
                        archive_index[new_target]["softcodes"] = target_softcodes[target]
            
            target_info = archive_index[new_target]["build_steps"]
            
            # Now build the index entry
            path_elements = splitpath(file)
            mod_path_sec = sys.intern(os.path.join(*path_elements[:4]))
            file_path_sec = sys.intern(os.path.join(*path_elements[4:]))
            entry = {mod_key: mod_path_sec, src_key: file_path_sec}
            file_softcodes = contents_softcodes.get(file, {}) # {softcode_map[key]: value for key, value in contents_softcodes.get(file, {}).items()}
            if len(file_softcodes):
                entry[softcode_key] = file_softcodes

            if file in rules:
                entry[rule_key] = rules[file]
            else:
                entry[rule_key] = build_element.get_rule(file)
            target_info.append(entry)
       
    # Now add in the buildscript
    if buildscript:
        mod_path_sec = os.path.join(*splitpath(filepath)[-4:])
        for target, build_pipeline in buildscript.target_dict.items():
            target = os.path.normpath(target)
            full_target = os.path.join(mod_path_sec, os.path.normpath(target))
            archive_type, archive = archive_from_path_getter(full_target, {}, {})
            
            # Build Archive Type Level
            if archive_type not in index:
                index[archive_type] = {}
            archive_type_index = index[archive_type]
            
            # Build Archive Level
            if archive not in archive_type_index:
                archive_type_index[archive] = {}
            archive_index = archive_type_index[archive]
            
            new_target = filepath_getter(target, archive)
            archive_index[new_target] = {"build_steps": []}
            
            build_data = archive_index[new_target]["build_steps"]
            
            
            for buildstep in build_pipeline.buildsteps:
                file_path_sec = os.path.normpath(buildstep.src_file)
                file = os.path.join(mod_path_sec, file_path_sec)
                entry = {mod_key: mod_path_sec, src_key: file_path_sec}
                file_softcodes = contents_softcodes.get(file, {})
                
                if len(file_softcodes):
                    entry[softcode_key] = file_softcodes
                    
                if buildstep.rules:
                    entry[rule_key] = buildstep.rules[0]
                else:
                    build_element = None
                    for filetype in contents:
                        print(">", contents[filetype], file)
                        if file in contents[filetype]:
                            build_element = contents[filetype][file]
                            break
                    if not build_element:
                        raise Exception(translate("Indexing", "Unable to locate source file \'{filepath}\' referenced in BUILD.json.").format(filepath=file_path_sec))
                    entry[rule_key] = build_element.get_rule(file)
                build_data.append(entry)
                
                if buildstep.rule_args:
                    entry[rule_args_key] = buildstep.rule_args[0]
                
            if target in target_softcodes:
                archive_index[new_target]["softcodes"] = target_softcodes[target]
                
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

    return {'data': index, 'softcodes': softcode_dump, "last_edit_time": last_edit_time, "contents_hash": contents_hash}
