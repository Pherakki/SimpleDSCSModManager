from Utils.MBE import mbetable_to_dict
from Utils.Settings import default_encoding
#from CoreOperations.PluginLoaders.RulesPluginLoader import RuleBase

                
class mberecord_merge:
    overrides_all_previous = False
    is_anchor = True
    is_solitary = False
    
    group = "CSV"
    
    def __call__(self, build_data):
        filepath        = build_data.source
        result          = build_data.csv_data
        id_len          = build_data.id_len
        softcodes       = build_data.softcodes
        softcode_lookup = build_data.softcode_lookup
        encoding        = build_data.encoding
        
        data = {}
        header, _ = mbetable_to_dict(data, filepath, id_len, softcodes, softcode_lookup, encoding)
        max_records = len(header) - id_len
        
        for key, value in data.items():
            if key in result:
                result[key] = [(result[key][i] if subval == "" else subval) for i, subval in enumerate(value)][:max_records]
            else:
                result[key] = value[:max_records]
        
        build_data.csv_data = result
            
class mberecord_overwrite:
    overrides_all_previous = False
    is_anchor = True
    is_solitary = False
    
    group = "CSV"
    
    def __call__(self, build_data):
        filepath        = build_data.source
        result          = build_data.csv_data
        id_len          = build_data.id_len
        softcodes       = build_data.softcodes
        softcode_lookup = build_data.softcode_lookup
        encoding        = build_data.encoding
        
        header, _ = mbetable_to_dict(result, filepath, id_len, softcodes, softcode_lookup, encoding)
        max_records = len(header) - id_len
        
        for key, value in result.items():
            result[key] = value[:max_records]

        build_data.csv_data = result

class mberecord_append:
    overrides_all_previous = False
    is_anchor = True
    is_solitary = False
    
    group = "CSV"
    
    def __call__(self, build_data):
        filepath        = build_data.source
        result          = build_data.csv_data
        id_len          = build_data.id_len
        softcodes       = build_data.softcodes
        softcode_lookup = build_data.softcode_lookup
        encoding        = build_data.encoding
        fill_value      = build_data.rule_args[0] if len(build_data.rule_args) else '0'
        
        header, data = mbetable_to_dict({}, filepath, id_len, softcodes, softcode_lookup, encoding)
        
        max_records = len(header) - id_len
        for key, value in data.items():
            nonzero_data = [elem for elem in result.get(key, []) if elem != fill_value]
            new_data = [elem for elem in data[key] if elem not in nonzero_data]
            nonzero_data.extend(new_data)
            nonzero_data = nonzero_data[:max_records]
            
            nonzero_data.extend([fill_value]*(max_records - len(nonzero_data)))
            result[key] = nonzero_data[:max_records]
            
        build_data.csv_data = result

