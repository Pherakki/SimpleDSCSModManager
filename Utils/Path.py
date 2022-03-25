import os
from PyQt5 import QtCore

translate = QtCore.QCoreApplication.translate

def splitpath(path):
    return os.path.normpath(path).split(os.path.sep)


def calc_most_recent_file_edit_time(path):
    max_time = 0
    for root, subdirs, files in os.walk(path):
        for file in files:
            path = os.path.join(root, file)
            max_time = max([os.path.getmtime(path), max_time])
    return max_time

def path_is_parent(parent_path, child_path):
    """https://stackoverflow.com/a/37095733"""
    # Smooth out relative path names, note: if you are concerned about symbolic links, you should use os.path.realpath too
    parent_path = os.path.normcase(os.path.abspath(os.path.realpath(parent_path)))
    child_path = os.path.normcase(os.path.abspath(os.path.realpath(child_path)))

    # Compare the common path of the parent and child path with the common path of just the parent path. Using the commonpath method on just the parent path will regularise the path name in the same way as the comparison that deals with both paths, removing any trailing path separator
    return os.path.commonpath([parent_path]) == os.path.commonpath([parent_path, child_path])

def check_path_is_safe(parent_path, target_path, rt, src):
    assert os.path.pardir not in target_path, translate("ModMetadataParsing", "Cannot refer to parent paths in '{metadata_item}': {target_path}.").format(metadata_item=src, target_path=target_path)
    assert not os.path.isabs(target_path), translate("ModMetadataParsing", "Cannot make absolute paths in '{metadata_item}': {target_path}.").format(metadata_item=src, target_path=target_path)
    assert path_is_parent(parent_path, os.path.join(rt, target_path)), translate("ModMetadataParsing", "'{metadata_item}' Metadata error: Target {mod_path} is not a subdirectory of {parent_path}!").format(metadata_item=src, mod_path=os.path.join(rt, target_path), parent_path=parent_path)
    