import os

from ModFiles.ScriptPatching import patch_scripts


def scriptfunction_overwrite(working_script_filepath, script_filepath):
    wsd, wdf = os.path.split(working_script_filepath)
    patch_filepath = os.path.join(wsd, '_' + wdf)
    patch_scripts(working_script_filepath, script_filepath, patch_filepath)
    os.remove(working_script_filepath)
    os.rename(patch_filepath, working_script_filepath)
