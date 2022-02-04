import os
from hashlib import blake2b
from Utils.Settings import default_encoding

def hashFilepack(mm_root, filepack):
    hasher = blake2b()
    for build_pipeline in filepack.get_build_pipelines():
        for build_step in build_pipeline:
            hasher.update(build_step.src.encode(default_encoding))
            hasher.update(build_step.rule.encode(default_encoding))
            edit_time = os.path.getmtime(os.path.join(mm_root, build_step.mod, build_step.src))
            hasher.update(str(edit_time).encode(default_encoding))
            if build_step.rule_args is not None:
                for arg in build_step.rule_args:
                    hasher.update(arg.encode(default_encoding))
            if build_step.softcodes is not None:
                for (category, key), softcode_offsets in build_step.softcodes.items():
                    hasher.update(category.encode(default_encoding))
                    hasher.update(key.encode(default_encoding))
                    for offset in softcode_offsets:
                        hasher.update(str(offset).encode(default_encoding))
    return hasher.hexdigest()
