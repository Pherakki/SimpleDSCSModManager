import inspect
import os
import shutil

from CoreOperations.PluginLoaders.PluginLoad import load_plugins_in


def get_rule_plugins():
    plugin_dir = os.path.join('plugins', 'rules')
    rules = load_plugins_in(plugin_dir, inspect.isfunction)
    return {rule.__name__: rule for rule in [*rules, overwrite]}


def overwrite(src, dst):
    shutil.copy2(src, dst)
