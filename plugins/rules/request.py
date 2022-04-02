import json
import os

from sdmmlib.dscstools import DSCSTools
from Utils.Settings import default_encoding

with open(os.path.join("config", "filelist.json"), 'r') as F:
    file_list = json.load(F)

all_archives = set(["DSDB", "DSDBA", "DSDBS", "DSDBSP", "DSDBP",
                    "DSDBbgm", "DSDBPDSEbgm", 
                    "DSDBse", "DSDBPse",
                    "DSDBvo", "DSDBPvo", "DSDBvous"])

class request_file:
    overrides_all_previous = False
    is_anchor = True
    is_weak_anchor = True
    is_solitary = False
    
    group = "Basic"
    
    def __call__(self, build_data):
        source      = build_data.source
        src         = build_data.source_file
        cache_loc   = build_data.cache_loc
        target      = build_data.target
        archive_loc = build_data.archives_loc
        backup_loc  = build_data.backups_loc
        request_src = os.path.splitext(src)[0]
        
        archive = None
        if os.path.exists(source):
            with open(source, 'r', encoding=default_encoding) as F:
                data = F.read()
                
            if len(data):
                if data in all_archives:
                    archive = data
                else:
                    raise ValueError(f"Archive \'{data}.steam.mvgl\', asked for by request file \'{source}\', does not exist.")
                    
                    
        if archive is None:
            archive = file_list[request_src]
        try:
            backup_archive = os.path.join(backup_loc, archive + ".steam.mvgl")
            archive_path = os.path.join(archive_loc, archive + ".steam.mvgl")
            if os.path.exists(backup_archive):
                get_path = backup_archive
            elif os.path.exists(archive_path):
                get_path = archive_path
            else:
                raise FileNotFoundError(f"Unable to locate {archive}.steam.mvgl. Have you deleted it?")
                
            # In case a the same request gets pulled twice..
            # extract to a folder unique to the target
            outpath = os.path.normpath(os.path.join(cache_loc, target + "_request"))
            os.makedirs(outpath, exist_ok=True)
            DSCSTools.extractMDB1File(get_path, outpath, request_src, True)
        except FileNotFoundError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Request file \'{request_src}\' not in vanilla archive \'{archive}.steam.mvgl\', source file is \'{source}\'.") from e
        
        extract_path = os.path.join(outpath, request_src)
        target_path = os.path.join(cache_loc, target)
        if not os.path.exists(target_path):
            os.rename(extract_path, target_path)
        else:
            os.remove(extract_path)
        
        # Deletes the folders created with the extractMDB1File line
        dirs = os.path.normpath(request_src).split(os.path.sep)
        for i in range(len(dirs)):
            os.rmdir(os.path.join(outpath, *dirs[:-(i+1)]))