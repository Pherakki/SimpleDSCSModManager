from Utils.MBE import mbetable_to_dict
from Utils.Settings import default_encoding
    
def mberecord_merge(result, filepath, id_len, softcodes=None, softcode_lookup=None, encoding=default_encoding):
    data = {}
    mbetable_to_dict(data, filepath, id_len, softcodes, softcode_lookup, encoding)
    
    for key, value in data.items():
        if key in result:
            result[key] = [(result[key][i] if subval == "" else subval) for i, subval in enumerate(value)]
        else:
            result[key] = value
            
def mberecord_overwrite(result, filepath, id_len, softcodes=None, softcode_lookup=None, encoding=default_encoding):
    mbetable_to_dict(result, filepath, id_len, softcodes, softcode_lookup, encoding)

def mberecord_append(result, filepath, id_len, softcodes=None, softcode_lookup=None, encoding=default_encoding, fill_value='0'):
    header, data = mbetable_to_dict({}, filepath, id_len, softcodes, softcode_lookup, encoding)
    
    max_records = len(header) - id_len
    for key, value in data.items():
        nonzero_data = [elem for elem in result.get(key, []) if elem != fill_value]
        new_data = [elem for elem in data[key] if elem not in nonzero_data]
        nonzero_data.extend(new_data)
        nonzero_data = nonzero_data[:max_records]
        
        nonzero_data.extend([fill_value]*(max_records - len(nonzero_data)))
        result[key] = nonzero_data[:max_records]
