import shutil


def overwrite(working_filepath, other_filepath):
    shutil.copy2(other_filepath, working_filepath)
