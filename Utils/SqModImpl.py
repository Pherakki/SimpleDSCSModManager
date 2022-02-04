# Could include a "limit_to" term here to limit operations to a single scope

####################
# PARSER UTILITIES #
####################


def make_arg_ids(args):
    mapping = []
    for item in args:
        if item[:2] == '{#' and item[-1] == '}':
            mapping.append(item)
        else:
            expr = '{#'
            expr2 = '}'
            assert 0, f"Item '{item}' did not begin with '{expr}' and end with '{expr2}'."
    return mapping

def make_arg_map(fn_args, arg_map):
    out = {}
    for arg, identifier in zip(fn_args, arg_map):
        out[identifier] = arg
    return out

def make_arg_generator(arg):
    def mapping(arg_map):
        to_return = arg
        for identifier, replacement in arg_map.items():
            to_return = to_return.replace(identifier, replacement)
        return to_return
    return mapping

def parse_function_call(source_code):
    function_call, function_args = source_code.split('(', 1)
    function_call += '('
    function_args = [item.strip() for item in function_args.rsplit(')', 1)[0].split(',')]
    
    return function_call, function_args

def parse_and_replace_arg(arg, function_arg_map):
    for item, value in function_arg_map.items():
        arg.replace(item, value)
    return arg
   
#################
# MODIFICATIONS #
#################
def add_preamble(source_code, kwargs):
    code = kwargs["code"]
    source_code_lines = source_code.split('\n')
    insert_pos = 0
    for i, line in enumerate(source_code_lines):
        if line[:9] != "function ":
            continue
        else:
            insert_pos = i
            break
        
    source_code_lines.insert(insert_pos, '\n' + code + '\n\n')
        
def replace(source_code, kwargs):
    old = kwargs["replace"]
    new = kwargs["with"]
    
    return source_code.replace(old, new)

def replace_call(source_code, kwargs):
    old = kwargs["replace_call"]
    new = kwargs["with"]
    
    old_function_call, old_function_args = parse_function_call(old)
    new_function_call, new_function_args = parse_function_call(new)
    arg_ids = make_arg_ids(old_function_args)
    new_arg_generators = [make_arg_generator(arg) for arg in new_function_args]
    
    source_code_lines = source_code.split('\n')
    for i, line in enumerate(source_code_lines):
        if old_function_call in line:
            start_pos = line.index(old_function_call)
            _, fn_args = parse_function_call(line[start_pos:])
            
            arg_map = make_arg_map(fn_args, arg_ids)
            
            new_fn_args = [generator(arg_map) for generator in new_arg_generators]
            
            source_code_lines[i] = line[:start_pos] + new_function_call + ", ".join(new_fn_args) + ");"
    return "\n".join(source_code_lines)
            
def replace_call_in_funcs(source_code, kwargs):
    """
    Functionally the same as replace_call, but includes an extra check
    Should probably unify the two functions
    """
    old = kwargs["replace_call_in_funcs"]
    new = kwargs["with"]
    funcs = kwargs["funcs"]
    
    old_function_call, old_function_args = parse_function_call(old)
    new_function_call, new_function_args = parse_function_call(new)
    arg_ids = make_arg_ids(old_function_args)
    new_arg_generators = [make_arg_generator(arg) for arg in new_function_args]
    
    source_code_lines = source_code.split('\n')
    is_replacement_active = False
    for i, line in enumerate(source_code_lines):   
        if line[:9] == "function ":
            if any([func + "(" in line for func in funcs]):
                is_replacement_active = True
            else:
                is_replacement_active = False
        
        if not is_replacement_active:
            continue
        
        if old_function_call in line:
            start_pos = line.index(old_function_call)
            _, fn_args = parse_function_call(line[start_pos:])
            
            arg_map = make_arg_map(fn_args, arg_ids)
            
            new_fn_args = [generator(arg_map) for generator in new_arg_generators]
            
            source_code_lines[i] = line[:start_pos] + new_function_call + ", ".join(new_fn_args) + ");"
    return "\n".join(source_code_lines)

modification_table = {'add_preamble': add_preamble,
                      'replace': replace,
                      'replace_call': replace_call,
                      'replace_call_in_funcs': replace_call_in_funcs}


def modify_squirrel_source(source_code, modifications): 
    for modification in modifications:
        source_code = modification_table[list(modification.keys())[0]](source_code, modification)
      
    return source_code
