import json
import os

from PyQt5 import QtCore

from Utils.Path import splitpath, check_path_is_safe

translate = QtCore.QCoreApplication.translate

class ModFormatVersion1:
    version = 1
    
    # This will bug out because the metadata doesn't include the prefix
    # Honestly, all filepaths should _not_ include the prefix...
    @staticmethod
    def get_archives(modpath, contents):
        afs2 = {'DSDBbgm', 'DSDBPDSEbgm', 'DSDBvo', 'DSDBPvo', 'DSDBPvous'}
        out = {}
        for filetype in contents:
            for filepath in contents[filetype]:
                out[filepath] = ("MDB1", "DSDBP")
        with open(os.path.split(modpath)[0] + os.sep + "METADATA.json", 'r') as F:
            metadata = json.load(F)
        if "Archives" in metadata:
            for file, archive in metadata["Archives"].items():
                assert type(archive) == str, translate("ModMetadataParsing", "'Archive' for file {file} was not a string: {archive}.").format(file=file, archive=archive)
                assert archive not in afs2, translate("ModMetadataParsing", "'Archive' for file {file} cannot be an AFS2 archive: {archive}'").format(file=file, archive=archive)
                out[file] = ("MDB1", archive)
        return out

    @staticmethod
    def get_archive_from_path(path, a, b):
        return ("MDB1", "DSDBP")

    @staticmethod
    def get_targets(modpath, contents, archives):
        modpath_rel = os.path.join(*splitpath(modpath)[-3:])
        out = {}
        with open(os.path.split(modpath)[0] + os.sep + "METADATA.json", 'r') as F:
            metadata = json.load(F)
        already_handled_files = set()
        if "Targets" in metadata:
            for file, targets in metadata["Targets"].items():
                file = os.path.normpath(os.path.join(modpath_rel, file))
                if type(targets) == list:
                    out[file] = []
                    for target in targets:
                        target = os.path.normpath(target)
                        check_path_is_safe(modpath_rel, target, modpath_rel, "Targets")
                        out[file].append(target)
                elif type(targets) == str:
                    targets = os.path.normpath(targets)
                    check_path_is_safe(modpath_rel, targets, modpath_rel, "Targets")
                    out[file] = [targets]
                else:
                    raise Exception(translate("ModMetadataParsing", "'Targets' for file {file} was not a list or string.").format(file=file))
                already_handled_files.add(file)
        if "TargetSub" in metadata:
            patterns = metadata["TargetSub"].items()
            for old, new in patterns:
                assert os.path.pardir not in new, translate("ModMetadataParsing", "Cannot refer to parent paths in TargetSub.")
                
            for rt, _, files in os.walk(modpath_rel):
                if rt == modpath_rel:
                    pathroot = ""
                else:
                    pathroot = os.path.relpath(rt, modpath_rel)
                for file in files:
                    filepath = os.path.join(rt, file)
                    if filepath not in already_handled_files:
                        target = file
                        for old, new in patterns:
                            target = target.replace(old, new)
                            check_path_is_safe(modpath_rel, target, rt, "TargetSub")
                        out[filepath] = [os.path.join(pathroot, target)]

        return out
    
    @staticmethod    
    def get_rules(modpath, contents):
        out = {}
        with open(os.path.split(modpath)[0] + os.sep + "METADATA.json", 'r') as F:
            metadata = json.load(F)
        if "Rules" in metadata:
            for file, rule in metadata["Rules"].items():
                assert type(rule) == str, translate("ModMetadataParsing", "'Rule' for file {file} was not a string.").format(file=file)
                out[file] = rule
        return out
    
    @staticmethod
    def get_filepath(filepath, archive):
        return filepath
    
class ModFormatVersion2(ModFormatVersion1):
    version = 2
    default_mdb1s = {'DSDB', 'DSDBA', 'DSDBS', 'DSDBSP', 'DSDBP',
             'DSDBse', 'DSDBPse'}
    default_afs2 = {'DSDBbgm', 'DSDBPDSEbgm', 'DSDBvo', 'DSDBPvo', 'DSDBPvous'}
    
    @staticmethod
    def get_archives( modpath, contents):
        out = {}

        with open(os.path.split(modpath)[0] + os.sep + "METADATA.json", 'r') as F:
            metadata = json.load(F)
            
        mod_MDB1s = set(metadata.get("MDB1", []))
        mod_AFS2s = set(metadata.get("AFS2", []))
        
        for filetype in contents:
            for file in contents[filetype]:
                out[file] = ModFormatVersion2.get_archive_from_path(file, mod_MDB1s, mod_AFS2s)
        return out
    
    @staticmethod
    def get_archive_from_path(file, mod_MDB1s, mod_AFS2s):
        splitpoint = 4
        splitpath = file.split(os.sep, splitpoint) # mods / name / filetype / archive
        
        # Find the name of what might be a folder containing the file
        archive = splitpath[splitpoint-1]
        
        # Match that up to an archive type
        if    archive in ModFormatVersion2.default_mdb1s or archive in mod_MDB1s: archive_type = "MDB1"
        elif  archive in ModFormatVersion2.default_afs2  or archive in mod_AFS2s: archive_type = "AFS2"
        else:                                                                     archive_type = None
        
        # Return the archive classification and archive name
        if archive_type is not None: return (archive_type, splitpath[splitpoint-1])
        else:                        return ("LooseFiles", "loose")
    
    @staticmethod
    def get_filepath(filepath, archive):
        # Cuts off the Archive folder from the filepath if the Archive name is not 'loose'
        if archive == "loose":
            return filepath
        else:
            return filepath.split(os.path.sep, 1)[1]

    # @staticmethod
    # def get_targets(modpath, contents, archives):
    #     out = {}
    #     for filetype, ft_pairs in contents.items():
    #         for file, target in ft_pairs.items():
    #             archive_type, archive_name = archives[file]
    #             if archive_type != "LooseFiles":
    #                 # Cut off the archive directory from the target name
    #                 ft_pairs[file] = target.split(os.path.sep, 1)[1]
    #     with open(os.path.split(modpath)[0] + os.sep + "METADATA.json", 'r') as F:
    #         metadata = json.load(F)
    #     if "Targets" in metadata:
    #         for file, targets in metadata["Targets"].items():
    #             assert type(targets) == list, f"'Targets' for file {file} was not a list."
    #             out[file].extend(targets)
    #     return out
    
mod_format_versions = {1: ModFormatVersion1,
                       2: ModFormatVersion2}
