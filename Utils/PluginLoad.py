import importlib
import inspect
import json
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
        classes_in_module = [m[0] for m in inspect.getmembers(module, inspect.isclass) if m[1].__module__ == module.__name__]
        results.extend([getattr(module, class_) for class_ in classes_in_module])
    return results

def get_plugin_sort_order(directory):
    priority_file = os.path.join(directory, "_priorities.json")
    if os.path.exists(priority_file):
        with open(priority_file, 'r') as F:
            order = json.load(F)
        return order
    else:
        return []

def sort_plugins(members, ordering):
    pass