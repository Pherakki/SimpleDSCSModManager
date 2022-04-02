import os
from CoreOperations.ModRegistry.Softcoding import search_string_for_softcodes
from Utils.Softcodes import replace_softcodes

add_operator = "++"
remove_operator = "--"
constructor_operator = "::"

opcodes = set([add_operator, remove_operator, constructor_operator])

def scan_variables_for_softcodes(path, softcode_manager):
    text_softcodes = {}
    vardef_file = os.path.join(path, "VARIABLES.txt")
    if os.path.isfile(vardef_file):
        with open(vardef_file, 'r', encoding='utf8') as F:
            line = F.readline()
            line_offset = 0
            while line:
                potential_opcode = line[:2]
                if potential_opcode in opcodes:
                    for match in search_string_for_softcodes(line):
                        code_offset = match.start() - 1
                        match = match.group(0)
                        if match not in text_softcodes:
                            text_softcodes[match] = []
                        text_softcodes[match].append((code_offset + line_offset, len(match)+2))
                else:
                    cat_name = line.rstrip('\n').rstrip('\r').strip()
                    if cat_name not in softcode_manager.subcategories["VarLists"].keys:
                        softcode_manager.subcategories["VarLists"].add_variable(cat_name)
                line_offset = F.tell()
                line = F.readline()
    return text_softcodes

def parse_mod_variables(path, softcode_manager, softcode_lookup, text_softcodes):
    vardef_file = os.path.join(path, "VARIABLES.txt")
    if os.path.isfile(vardef_file):
        with open(vardef_file, 'rb') as F:
            data = F.read()
            data = replace_softcodes(data, text_softcodes, softcode_lookup)
            
        current_variable = None
        for line in data.decode('utf8').split('\n'):
            line = line.rstrip("\n")
            # Skip any blank lines or those that are only whitespace
            if not line or line.isspace():
                continue
            
            # Check if it's a line with an operation
            potential_opcode = line[:2]
            if potential_opcode in opcodes:
                # Call the opcode on the current variable if so
                line_value = line[2:].strip()
                current_variable.call_opcode(potential_opcode, line_value)
            else:
                # If not, it must be a variable def, so try to make a new one
                cat_name = line.rstrip('\n').rstrip('\r')
                current_variable = softcode_manager.subcategories["VarLists"].keys[cat_name]
            
            