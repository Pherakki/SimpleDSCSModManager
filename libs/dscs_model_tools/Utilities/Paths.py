import os


def normalise_abs_path(path):
    if os.name == 'nt' and path[1] == ':' and not path[2] == os.sep:
        return path[:2] + os.sep + path[2:]
    else:
        return path
