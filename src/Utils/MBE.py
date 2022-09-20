import csv
import os

from src.Utils.Settings import default_encoding
from src.Utils.Softcodes import replace_softcodes


def mbetable_to_dict(result, filepath, id_size, softcodes, softcode_lookup, encoding=default_encoding):
    header = None
    try:
        if softcodes is None:
            working_fp = filepath
        else:
            working_fp = filepath + ".working"
            with open(filepath, 'rb') as F, open(working_fp, 'wb') as G:
                G.write(replace_softcodes(F.read(), softcodes, softcode_lookup))
                
                
        with open(working_fp, 'r', newline='', encoding=encoding) as F:
            csvreader = csv.reader(F, delimiter=',', quotechar='"')
            csvreader_data = iter(csvreader)
            header = next(csvreader_data)
            for line in csvreader_data:
                if not(line):
                    continue
                data = line
                # Might have to go careful that there are no duplicates
                record_id = tuple(data[:id_size])
                result[record_id] = data[id_size:]
    except Exception as e:
        raise e
    finally:
        if softcodes is not None:
            os.remove(working_fp)
    return header, result

def dict_to_mbetable(filepath, header, result, encoding=default_encoding):
    with open(filepath, 'w', newline='', encoding=encoding) as F:
        csvwriter = csv.writer(F, delimiter=',', quotechar='"')
        csvwriter.writerow(header)
        for key, value in result.items():
            csvwriter.writerow(([*key, *value]))
