import importlib
import inspect
import os
import sys

from Utils.Path import splitpath

def load_plugins_in(directory):
    results = []
    for file in os.listdir(directory):
        file, ext = os.path.splitext(file)
        if ext != '.py':
            continue
        module_name = ".".join([*splitpath(directory), file])
        importlib.import_module(module_name)
        module = sys.modules[module_name]
        module_classes = [m[0] for m in inspect.getmembers(module, inspect.isclass) if m[1].__module__ == module.__name__]
        results.extend([getattr(module, class_) for class_ in module_classes])
    return results

def sort_plugins(members, ordering):
    pass