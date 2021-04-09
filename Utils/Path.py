import os

def splitpath(path):
    return os.path.normpath(path).split(os.path.sep)
