import os
import shutil

def is_unpacked_mbe_table(path):
    return path[-3:] == 'mbe' and os.path.isdir(path)

def is_packed_mbe_table(path):
    return path[-3:] == 'mbe' and os.path.isfile(path)

# Unify these two functions...?
def mbe_batch_pack(path, dscstools_handler, log=lambda x: x, updateLog=lambda x: x):
    temp_path = os.path.join(path, 'temp')
    os.mkdir(temp_path)
    for mbe_folder in ['data', 'message', 'text']:
        mbe_folder_path = os.path.join(path, mbe_folder)
        if os.path.exists(mbe_folder_path):
            log(f"Packing MBEs in {mbe_folder}...")
            mbe_folder_contents = os.listdir(mbe_folder_path)
            mbes_to_pack = []
            not_mbes = []
            for directory in mbe_folder_contents:
                (mbes_to_pack if is_unpacked_mbe_table(os.path.join(mbe_folder_path, directory)) else not_mbes).append(directory)
            
            if len(not_mbes):
                log(f"Found ({len(not_mbes)}) non-mbe items that will not be packed:")
                for item in not_mbes:
                    log(f"    {item}")
                    
            num_mbes = len(mbes_to_pack)
            if num_mbes:
                log("")  # <- Will be overwritten by updateLog
            for i, folder in enumerate(mbes_to_pack):
                # Generate the mbe inside the 'temp' directory
                dscstools_handler.pack_mbe(folder, 
                                           os.path.abspath(mbe_folder_path), 
                                           os.path.abspath(temp_path))
                shutil.rmtree(os.path.join(mbe_folder_path, folder))
                # Move the packed MBE out out 'temp' and into the correct path
                os.rename(os.path.join(temp_path, folder), os.path.join(mbe_folder_path, folder))
                updateLog(f"Packed {i+1}/{num_mbes} [{folder}]")
    os.rmdir(temp_path)
    
def mbe_batch_unpack(path, dscstools_handler, log=lambda x: x, updateLog=lambda x: x, report_missing=True):
    temp_path = os.path.join(path, 'temp')
    os.makedirs(temp_path, exist_ok=True)
    for mbe_folder in ['data', 'message', 'text']:
        mbe_folder_path = os.path.join(path, mbe_folder)
        if os.path.exists(mbe_folder_path):
            log(f"Unpacking MBEs in {mbe_folder}...")
            mbe_folder_contents = os.listdir(mbe_folder_path)
            mbes_to_pack = []
            not_mbes = []
            for directory in mbe_folder_contents:
                (mbes_to_pack if is_packed_mbe_table(os.path.join(mbe_folder_path, directory)) else not_mbes).append(directory)
            
            if len(not_mbes) and report_missing:
                log(f"Found ({len(not_mbes)}) non-mbe items that will not be unpacked:")
                for item in not_mbes:
                    log(f"    {item}")
            
            num_mbes = len(mbes_to_pack)                    
            if num_mbes:
                log("")  # <- Will be overwritten by updateLog
            for i, folder in enumerate(mbes_to_pack):
                # Generate the mbe inside the 'temp' directory
                dscstools_handler.unpack_mbe(folder, 
                                           os.path.abspath(mbe_folder_path), 
                                           os.path.abspath(temp_path))
                os.remove(os.path.join(mbe_folder_path, folder))
                # Move the unpacked MBE out out 'temp' and into the correct path
                shutil.move(os.path.join(temp_path, folder), os.path.join(mbe_folder_path, folder))
                updateLog(f"Unpacked {i+1}/{num_mbes} [{folder}]")
    os.rmdir(temp_path)