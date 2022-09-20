import os
import shutil

default_MBD1s = {"DSDB", "DSDBA", "DSDBS", "DSDBSP", "DSDBP", "DSDBse", "DSDBPse"}
default_AFS2s = {"DSDBbgm", "DSDBPDSEbgm", "DSDBvo", "DSDBPvo", "DSDBPvous"}

def replace_backed_up_file(src, dst, dst_folder, backup_folder):
    if os.path.exists(dst):
        rel_filepath = os.path.relpath(dst, dst_folder)
        backup_dst = os.path.normpath(os.path.join(backup_folder, rel_filepath))
        if not os.path.exists(backup_dst):
            os.makedirs(os.path.split(backup_dst)[0], exist_ok=True)
            shutil.copy2(dst, backup_dst)
    shutil.copy2(src, dst)
    
def try_back_up_file(dst, dst_folder, backup_folder):
    rel_filepath = os.path.relpath(dst, dst_folder)
    backup_dst = os.path.normpath(os.path.join(backup_folder, rel_filepath))
    if not os.path.exists(backup_dst):
        os.makedirs(os.path.split(backup_dst)[0], exist_ok=True)
        shutil.copy2(dst, backup_dst)

    
def restore_backed_up_file(dst, dst_folder, backup_folder):
    rel_filepath = os.path.relpath(dst, dst_folder)
    backup_dst = os.path.normpath(os.path.join(backup_folder, rel_filepath))
    if os.path.exists(backup_dst):
        shutil.copy2(backup_dst, dst)
        
def get_backed_up_filepath_if_exists(dst, dst_folder, backup_folder):
    rel_filepath = os.path.relpath(dst, dst_folder)
    backup_dst = os.path.normpath(os.path.join(backup_folder, rel_filepath))
    if os.path.exists(backup_dst):
        return backup_dst
    else:
        return dst
