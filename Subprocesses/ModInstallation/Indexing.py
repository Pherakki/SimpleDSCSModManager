import hashlib
import os
from Utils.Path import splitpath

class IndexFileException(Exception):
    def __init__(self, base_msg, modfile_name):
        super().__init__(self)
        self.base_msg = base_msg
        self.modfile_name = modfile_name
        
    def __str__(self):
        return f"{self.modfile_name}: {self.base_msg}"
        
def generate_mod_hash(modpath):
    """
    Don't bother using this - it's way cheaper just to index everything every time
    """
    hasher = hashlib.sha256()
    chunksize = 1 << 16
    for path, directory, files in os.walk(modpath):
        # Hash the filepath
        for file in files:
            hasher.update(path.encode("utf-8"))
            hasher.update(file.encode("utf-8"))
            with open(os.path.join(path, file), 'rb') as F:
                F.seek(os.SEEK_END)
                size = F.tell()
                F.seek(0)
                
                for chunk_i in range((size // chunksize) + 1):
                    hasher.update(F.read(chunksize))
    return hasher.hexdigest()
                    

def generate_mod_index(modpath, rules, filetypes):
    retval = {filetype.group: {} for filetype in filetypes}
    for path, directories, files in os.walk(os.path.relpath(modpath)):
        for file in files:
            for filetype in filetypes:
                if filetype.checkIfMatch(path, file):
                    filepath = os.path.join(*splitpath(path)[3:], file)
                    try:
                        rule = rules.get(filepath)
                        category, key, index_data = filetype.produce_index(path, file, rule)
                        if key not in retval[category]:
                            retval[category][key] = {}
                        retval[category][key].update(index_data)
                    except UnicodeDecodeError:
                        raise IndexFileException("File was not saved with utf-8 encoding.", filepath)
                    except Exception as e:
                        raise IndexFileException(e.__str__(), filepath)
                    break
                
            
    return retval
