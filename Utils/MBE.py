import os
import shutil

def mbe_batch_pack(path, dscstools_handler, log=lambda x: x):
    temp_path = os.path.join(path, 'temp')
    os.mkdir(temp_path)
    for mbe_folder in ['data', 'message', 'text']:
        mbe_folder_path = os.path.join(path, mbe_folder)
        if os.path.exists(mbe_folder_path):
            log(f"Packing MBEs in {mbe_folder}...")
            for folder in os.listdir(mbe_folder_path):
                # Generate the mbe inside the 'temp' directory
                dscstools_handler.pack_mbe(folder, 
                                           os.path.abspath(mbe_folder_path), 
                                           os.path.abspath(temp_path))
                shutil.rmtree(os.path.join(mbe_folder_path, folder))
                # Move the packed MBE out out 'temp' and into the correct path
                os.rename(os.path.join(temp_path, folder), os.path.join(mbe_folder_path, folder))
    os.rmdir(temp_path)
    
