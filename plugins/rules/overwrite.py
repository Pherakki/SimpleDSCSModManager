import os
import shutil


class overwrite:
    overrides_all_previous = True
    is_anchor = True
    is_solitary = False
    
    group = "Basic"
    
    def __call__(self, build_data):
        src = build_data.source
        dst = build_data.build_target
        os.makedirs(os.path.split(dst)[0], exist_ok=True)
        shutil.copy2(src, dst)
