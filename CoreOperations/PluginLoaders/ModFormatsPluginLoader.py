import inspect
import os

from CoreOperations.ModRegistry.CoreModFormats import LooseMod, ModFile
from CoreOperations.PluginLoaders.PluginLoad import load_plugins_in


def get_modformat_plugins():
    plugin_dir = os.path.join('plugins', 'modformats')
    
    return [*load_plugins_in(plugin_dir, lambda x: issubclass(x, ModFile) if inspect.isclass(x) else False), LooseMod]
