import inspect
import os

from CoreOperations.PluginLoaders.PluginLoad import load_plugins_in


def get_rule_plugins(*groups):
    rule_categories = set(groups)
    plugin_dir = os.path.join('plugins', 'rules')
    rules = load_plugins_in(plugin_dir, inspect.isclass)
    if len(rule_categories):
        return {rule.__name__: rule() for rule in rules if rule.group in rule_categories}
    else:
        return {rule.__name__: rule() for rule in rules}
