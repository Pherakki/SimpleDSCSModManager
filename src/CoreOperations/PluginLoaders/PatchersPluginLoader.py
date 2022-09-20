import inspect
import os

from src.CoreOperations.PluginLoaders.PluginLoad import load_sorted_plugins_in
from plugins.patchers import BasePatcher


def get_patcher_plugins():
    plugin_dir = os.path.join('plugins', 'patchers')
    
    return load_sorted_plugins_in(plugin_dir, lambda x: issubclass(x, BasePatcher) and type(x) != BasePatcher if inspect.isclass(x) else False)


def get_patcher_plugins_dict():
    return {patcher.group: patcher for patcher in get_patcher_plugins()}
