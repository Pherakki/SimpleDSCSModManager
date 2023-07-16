import array
import json
import os
import sys

from PyQt5 import QtCore

from src.Utils.JSONHandler import JSONHandler

translate = QtCore.QCoreApplication.translate

class SoftcodeCategoryDefinition:
    __slots__ = ("name", "min", "max", "span", "src", "value_lambda", "methods", "subcategory_defs")
    
    def __init__(self, name, _min, _max, src, value_lambda, methods, subcategory_defs):
        self.name = name
        self.min = _min
        self.max = _max
        self.span = _max - _min
        self.src = src
        self.subcategory_defs = subcategory_defs
        self.value_lambda = value_lambda
        self.methods = methods
        
    @classmethod
    def init_from_dict(cls, name, dct):
        children = dct.get("children", {})
        subcategory_defs = []
        subcategory_defs = [SoftcodeCategoryDefinition.init_from_dict(child_name, child_def)
                            for child_name, child_def in children.items()]
        
        return cls(name, dct["min"], dct["max"], dct.get("src"), dct["value"], dct.get("methods", {}), subcategory_defs)

    def get_category_sources(self, *names):
        out = {}
        out[self.name] = self.src
        for subcat in self.subcategory_defs:
            out.update(subcat.get_category_sources())
        
    def call_formatting_func(self, func_def_dict, value, parent_value):
        # Handle other vars
        arglist = [None]*(len(func_def_dict))
        arglist[0] = value
        for idx, value in func_def_dict.items():
            if idx == "return":
                continue
            elif value == "parent":
                arglist[int(idx)] = parent_value
            elif value == "hex":
                arglist[int(idx)] = hex(arglist[int(idx)])[2:].lower()
            else:
                raise Exception(f"Unknown formatting argument \'{value}\'.")
        return func_def_dict["return"].format(*arglist)

class SoftcodeCategory:
    __slots__ = ("key_gaps", "definition", "keys")
    
    def __init__(self, definition, data):
        self.key_gaps = array.array('H')
        self.definition = definition
        self.keys = {}
        self.add_data(data)
        
    def add_data(self, data):
        for key, subdata in data.items():
            self.keys[key] = SoftcodeKey(subdata[0], self.definition.subcategory_defs, (subdata[1] if len(subdata) > 1 else {}))

        values = sorted([sk.value for sk in self.keys.values()])[::-1]
        
        if len(values):
            current_val = values[0]
            self.key_gaps = array.array('H')
            for val in values[1:]:
                if val != current_val - 1:
                    self.key_gaps.append(current_val)
                    self.key_gaps.append(val + 1)
                current_val = val
            if current_val != self.definition.min:
                self.key_gaps.append(current_val)
                self.key_gaps.append(self.definition.min)
            
        
    def generate_next_key(self):
        if len(self.key_gaps):
            upper_bound, lower_bound = self.key_gaps[-2:]
            self.key_gaps[-1] += 1
            if self.key_gaps[-1] == upper_bound:
                self.key_gaps.pop()
                self.key_gaps.pop()
            return lower_bound
        
        if len(self.keys) <= self.definition.span:
            return len(self.keys) + self.definition.min
        
        raise LookupError("No free slots available.")
        
    def get(self, key_name):
        if key_name not in self.keys:
            self.keys[key_name] = SoftcodeKey(self.generate_next_key(), self.definition.subcategory_defs, {})
        return self.keys[key_name]
    
    def get_data_as_serialisable(self):
        return {key_name: key.get_data_as_serialisable() for key_name, key in self.keys.items()}
    
class SoftcodeKey:
    chunk_delimiter = "|"
    kv_delimiter = "::"
    
    __slots__ = ("value", "subcategories")
    
    def __init__(self, value, subcategories, data):
        self.value = value
        self.subcategories = {sys.intern(subcat.name) : SoftcodeCategory(subcat, data.get(sys.intern(subcat.name), {})) 
                              for subcat in subcategories}

        
    def lookup_softcode(self, softcode_key):
        current_chunk, _, remaining_key = softcode_key.partition(self.chunk_delimiter)
        category, _, key = current_chunk.partition(self.kv_delimiter)

        key, _, method_name = key.partition(self.kv_delimiter)
        
        # Remove () from method
        method_name = method_name[:-2]

        try:
            subcat = self.subcategories[category]
        except KeyError as e:
            raise KeyError(translate("SoftcodeManager", "Softcode Category \"{category_name}\" does not exist.").format(category_name=category)) from e
        next_softcode = subcat.get(key)
        if remaining_key == '':
            if method_name == '':
                method_data = subcat.definition.value_lambda
            else:
                method_data = subcat.definition.methods[method_name]
                
            return subcat.definition.call_formatting_func(method_data, next_softcode.value, self.value)
        else:
            return next_softcode.lookup_softcode(remaining_key)
        
    def get_data_as_serialisable(self):
        res = [self.value]
        if len(self.subcategories):
            res.append({cat_name: cat.get_data_as_serialisable() for cat_name, cat in self.subcategories.items()})
        return res
        
class SoftcodeManager(SoftcodeKey):
    __slots__ = ("category_defs", "paths")
    
    def __init__(self, paths):
        self.paths = paths
        self.category_defs = []
        super().__init__(None, self.category_defs, {})
        
    
    def load_softcode_data(self):
        # Variables
        self.category_defs.append(SoftcodeListVariableCategory.definition)
        self.subcategories[sys.intern("VarLists")] = SoftcodeListVariableCategory()
        
        for file in os.listdir(self.paths.softcodes_loc):
            self.load_subcategory_from_json(file)
        
    def unload_softcode_data(self):
        self.subcategories = {}
    
    def add_subcategory(self, subcategory, data):
        self.category_defs.append(subcategory)
        self.subcategories[sys.intern(subcategory.name)] = SoftcodeCategory(subcategory, data)
        
    def load_subcategory_from_json(self, main_filename):
        try:
            with JSONHandler(os.path.join(self.paths.softcodes_loc, f"Error reading '{main_filename}'")) as stream:
                dct = stream
        except json.decoder.JSONDecodeError as e:
            print('error', e)
        except Exception as e:
            raise Exception(f"Attempted to read Softcode definition \'{main_filename}\', encountered error: {e}") from e
        category_name = os.path.splitext(main_filename)[0]
        category_def = SoftcodeCategoryDefinition.init_from_dict(category_name, dct["definition"])
        
        
        cache_loc = os.path.join(self.paths.softcode_cache_loc, main_filename)
        try:
            with JSONHandler(cache_loc, f"Error reading '{main_filename}'") as data:
                dct["codes"] = data
        except json.decoder.JSONDecodeError as e:
            print('error', e)
        except Exception as e:
            raise Exception(f"Attempted to read cached Softcode definitions \'{main_filename}\', encountered error: {e}") from e
        
        self.add_subcategory(category_def, dct["codes"])
        
    # @classmethod
    # def init_from_json(cls, main_filepath, cache_filepath=None):
    #     with open(main_filepath, 'r', encoding="utf8") as F:
    #         dct = json.load(F)
    #     category_name = os.path.splitext(os.path.split(main_filepath)[1])[0]
    #     category_defs = [SoftcodeCategoryDefinition.init_from_dict(category_name, dct["definition"])]

    #     return cls(category_defs, {"Digimon": dct["codes"]})
        
    def dump_codes_to_json(self):
        for subcat_name, subcat in self.subcategories.items():
            if hasattr(subcat, "get_data_as_serialisable"):
                filepath = os.path.join(self.paths.softcode_cache_loc, os.path.extsep.join((subcat_name, "json")))
                parent_path = os.path.split(filepath)[0]
                if not os.path.isdir(parent_path):
                    os.makedirs(parent_path)
                with open(filepath, 'w', encoding="utf8") as F:
                    json.dump(subcat.get_data_as_serialisable(), F, separators=(',', ':'))


    
def wrap_strings(values):
    return ("\"{var}\"" for var in values)

def splat(values):
    return ",".join(values)

def splat_strings(values):
    return ",".join(wrap_strings(values))

def as_list(values):
    return f"[{','.join(values)}]"

def as_list_strings(values):
    return f"[{','.join(wrap_strings(values))}]"

def as_braced_list(values):
    return f"{{{','.join(values)}}}"

def as_braced_list_strings(values):
    return f"{{{','.join(wrap_strings(values))}}}"
    
class SoftcodeListVariableCategoryDefinition:
    methods = {
            "splat": splat, 
            "splat_strings": splat_strings, 
            "as_list": as_list,
            "as_list_strings": as_list_strings,
            "as_braced_list": as_braced_list,
            "as_braced_list_strings": as_braced_list_strings
        }
        
    @staticmethod
    def call_formatting_func( func_def, values, parent_value):
        return func_def(values)
        
    @staticmethod
    def value_lambda(values):
        return f"[{','.join(wrap_strings(values))}]"
    
class SoftcodeListVariableCategory:
    __slots__ = ("keys",)
    definition = SoftcodeListVariableCategoryDefinition
    
    def __init__(self):
        self.keys = {}
    
    def get(self, key):
        try:
            return self.keys[key]
        except KeyError as e:
            raise KeyError(f"No Variable List \'{key}\' is defined.") from e
            
    def add_variable(self, name):
        self.keys[name] = SoftcodeListVariable()

class SoftcodeListVariable:
    __slots__ = ("value", "opcodes", "is_default")
    
    def __init__(self):
        self.is_default = True
        self.value = []
        
        self.opcodes = {
            "::": self.set_default,
            "++": self.add,
            "--": self.remove
        }
        
    def call_opcode(self, opcode, arg):
        op = self.opcodes.get(opcode)
        if op:
            op(arg)
        else:
            raise Exception(f"Unknown operator \'{opcode}\' for SoftcodeListVariable.")
        
    def set_default(self, value):
        if self.is_default:
            self.value = [item.strip() for item in value.split(',')]
        
    def add(self, value):
        if self.is_default:
            self.value = []
        self.value.append(value)
        self.is_default = False
        
    def remove(self, value):
        if self.is_default:
            self.value = []
        try:
            self.value.remove(value)
        except Exception:
            pass
        
        self.is_default = False
        