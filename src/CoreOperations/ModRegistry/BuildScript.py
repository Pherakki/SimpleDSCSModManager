import copy
import itertools
import json
import os
import re

from PyQt5 import QtCore

from src.Utils.Path import splitpath, check_path_is_safe

translate = QtCore.QCoreApplication.translate

class RegexVariable:
    __slots__ = ("pattern",)
    
    def __init__(self, pattern):
        if type(pattern) != str:
            raise ValueError(translate("ModRegistry::BuildScript", "Regex Pattern is not a string, is type \'{0}\'.").format(type(pattern)))
        
        self.pattern = re.compile(pattern)
        
    def getValues(self, modfiles_dir):
        for root, _, files in os.walk(modfiles_dir):
            rel_root = os.path.relpath(root, modfiles_dir).lstrip(os.path.curdir).lstrip(os.sep)
            for file in files:
                filepath = os.path.join(rel_root, file)
                
                match = self.pattern.findall(filepath)
                
                if match:
                    yield match[0]
        
class RangeVariable:
    __slots__ = ("start", "stop", "step")
    
    def __init__(self, args):
        if type(args) != list:
            raise ValueError(translate("ModRegistry::BuildScript", "ModRegistry::BuildScript", "Range Variable is not a list, is type \'{0}\'.").format(type(args)))
        
        if len(args) != 3:
            raise ValueError(translate("ModRegistry::BuildScript", "Range Variable contains \'{0}\' entries, should contain 3 (Start, Stop, Step): {1}.").format(len(args), args))
            
        self.start, self.stop, self.step = args
        
    def getValues(self, modfiles_dir):
        for i in range(self.start, self.stop, self.step):
            yield (i,)
        
        

variable_types = {"Range": RangeVariable,
                  "Regex": RegexVariable}

def check_path(path):
    if os.path.pardir in os.path.realpath(path):
        raise ValueError(translate("ModRegistry::BuildScript", "Parent directory token {0} is not allowed in paths: \'{1}\'").format(os.path.pardir, path))

class BuildScriptStep:
    __slots__ = ("src_file", "rules", "rule_args")
    
    def __init__(self, target, src_file, rules=None, rule_args=None):
        
        check_path_is_safe(".", src_file, ".", "Build Script File Sources")
        check_path_is_safe(".", target, ".", "Build Script File Targets")
        self.src_file = src_file
        if rules is None:
            self.rules = rules
        elif type(rules) == str:
            self.rules = [rules]
        elif type(rules) == list:
            if not all(type(rule) == str for rule in rules):
                raise ValueError(translate("ModRegistry::BuildScript", "\'Rules\' for Mod File \'{0}\' of Target File \'{1}\' is a list, but not all rules are strings: {2}").format(src_file, target, rules))
            self.rules = rules
        elif type(rules) == dict:
            if not all(type(key) == str and type(value) == str for key, value in rules.items()):
                raise ValueError(translate("ModRegistry::BuildScript", "\'Rules\' for Mod File \'{0}\' of Target File \'{1}\' is a dict, but not all rule pairs are strings: {2}").format(src_file, target, rules))
            self.rules = rules
        else:
            raise ValueError(translate("ModRegistry::BuildScript", "\'Rules\' for Mod File \'{0}\' of Target File \'{1}\' is not a string, list, or dict: {2}").format(src_file, target, type(rules)))
        self.rule_args = rule_args
        
class BuildScriptPipeline:
    __slots__ = ("original_target_key", "buildsteps")
    
    def __init__(self, original_target_key, buildsteps):
        self.original_target_key = original_target_key
        self.buildsteps = buildsteps
        
class BuildScript:
    def __init__(self):
        self.target_dict = {}
        
    def check_if_key_exists(self, key, current_keys):
        if key in current_keys:
            raise ValueError(translate("ModRegistry::BuildScript", "File Target \'{0}\' produced more than once by Build Script entry \'{1}\'.").format(key, self.target_dict[key].original_target_key))

        if key in self.target_dict:
            raise ValueError(translate("ModRegistry::BuildScript", "File Target \'{0}\' already defined by Build Script entry \'{1}\'.").format(key, self.target_dict[key].original_target_key))
        
    @staticmethod
    def extract_build_steps(key, definition):
        # If the entry looks like "file": "file"
        if type(definition) == str:
            return BuildScriptPipeline(key, [BuildScriptStep(key, definition)])
            
        # If the entry looks like "file": [["file", "rules"], ["file", "rules"], ...]
        # or "file": ["file", "rules"]
        elif type(definition) == list:
            if not len(definition):
                raise ValueError(translate("ModRegistry::BuildScript", "Build Steps list for File Target \'{0}\' is empty.").format(key))
            
            if type(definition[0]) == list:
                # If the entry looks like "file": [["file", "rules"], ["file", "rules"], ...]
                return BuildScriptPipeline(key, [BuildScriptStep(key, *subdef) for subdef in definition])
            else:
                # If the entry looks like "file": ["file", "rules"]
                return BuildScriptPipeline(key, [BuildScriptStep(key, *definition)])
            
        else:
            raise ValueError(translate("ModRegistry::BuildScript", "Invalid type for Build Steps of Target File \'{0}\': \'{1}\'.").format(key, type(definition)))

        
    @classmethod
    def from_json(cls, json_file, modfiles_dir):
        with open(json_file, 'r') as F:
            data = json.load(F)
        
        instance = cls()
        if type(data) != dict:
            raise ValueError(translate("ModRegistry::BuildScript", "Build Script has type \'{0}\', not \'dict\'.".format(type(data))))

        for key, definition in data.items():
            check_path_is_safe(".", key, ".", "Build Script File Targets")
            
            # If the entry looks like "file": { "BuildSteps": [["file", "rule"], ...], "Variables": [...]}
            if type(definition) == dict:
                if "BuildSteps" not in definition:
                    raise ValueError(translate("ModRegistry::BuildScript", "\'BuildSteps\' data is missing for File Target \'{0}\'.".format(key)))
                
                variables = definition.get("Variables", [])
                
                if type(variables) != list:
                    raise ValueError(translate("ModRegistry::BuildScript", "\'Variables\' argument for File Target \'{0}\' has type \'{1}\', not \'list\'.".format(key, type(variables))))
            
                var_generators = []
                for vardef_i, vardef in enumerate(variables):
                    if type(vardef) != dict:
                        raise ValueError(translate("ModRegistry::BuildScript", "Definition of variable \'{0}\' for File Target \'{1}\' has type \'{2}\', not \'dict\'.".format(vardef_i, key, type(vardef))))
                    if len(vardef) != 1:
                        raise ValueError(translate("ModRegistry::BuildScript", "Definition of variable \'{0}\' for File Target \'{1}\' has \'{2}\' definitions; must contain strictly one.".format(vardef_i, key, len(vardef))))
                        
                    varclass, varclass_args = list(vardef.items())[0]
                    
                    if varclass not in variable_types:
                        raise ValueError(translate("ModRegistry::BuildScript", "Unknown variable type \'{0}\' encountered in the Variables for File Target \'{1}\'.".format(varclass, key)))
                        
                    try:
                        var_inst = variable_types[varclass](varclass_args)
                    except Exception as e:
                        raise ValueError(translate("ModRegistry::BuildScript", "Invalid argument list provided to Variable of type \'{0}\' in the Variables for File Target \'{1}\'; error was: {2}").format(varclass, key, e.__str__())) from e
                        
                    var_generators.append(var_inst)
                    
                
                build_steps = cls.extract_build_steps(key, definition["BuildSteps"])
                keys_in_this_def = set()
                for key_combo in itertools.product(*[var.getValues(modfiles_dir) for var in var_generators]):
                    
                    key_combo = [subitem for item in key_combo for subitem in item]
                    
                    try:
                        formatted_key = key.format(*key_combo)
                    except Exception as e:
                        raise ValueError(translate("ModRegistry::BuildScript", "Encountered error when inserting Variables into File Target \'{0}\'; error was: {1}").format(key, e.__str__()))
                        
                    instance.check_if_key_exists(formatted_key, keys_in_this_def)
                    keys_in_this_def.add(formatted_key)    
                    
                    build_steps_cpy = copy.deepcopy(build_steps)
                    for build_step in build_steps_cpy.buildsteps:
                        src_file = build_step.src_file
                          
                        try:
                            formatted_src_file = src_file.format(*key_combo)
                        except Exception as e:
                            raise ValueError(translate("ModRegistry::BuildScript", "Encountered error when inserting Variables into Build Step Source File \'{0}\' for Target File \'{1}\'; error was: {2}").format(src_file, key, e.__str__()))
                            
                        build_step.src_file = formatted_src_file
                        
                    instance.target_dict[formatted_key] = build_steps_cpy
            else:
                instance.check_if_key_exists(key, [])
                instance.target_dict[key] = cls.extract_build_steps(key, definition)
                
        return instance
