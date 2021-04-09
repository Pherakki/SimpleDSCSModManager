function_dec = "function "
len_function_dec = len(function_dec)


def is_function_declaration(line):
    """If the line starts with "function ", return True, else False"""
    return line[:len_function_dec] == function_dec
    
def get_next_function(bytestream):
    """
    Scan the input bytestream from its current position and return the next
    complete function definition.
    """
    start_position = bytestream.tell()
    inside_function = False
    n_lines = 0
    for line in bytestream:
        # Breaks the for loop the second time a function declaration is found
        if is_function_declaration(line):
            if inside_function:
                break
            else:
                inside_function = True
        n_lines += 1
    
    bytestream.seek(start_position)
    retval = []
    for _ in range(n_lines):
        retval.append(bytestream.readline())
    
    return retval

def get_preamble(bytestream):
    start_position = bytestream.tell()
    n_lines = 0
    for line in bytestream:
        # Breaks the for loop the second time a function declaration is found
        if is_function_declaration(line):
            break
        n_lines += 1
        
    bytestream.seek(start_position)
    retval = []
    for _ in range(n_lines):
        retval.append(bytestream.readline())
    
    return retval    

def function_should_be_replaced(src_lines, replacement_functions):
    """
    Checks if the function is one that should be replaced.
    """
    should_be_replaced = False
    for funcname in replacement_functions.keys():
        if function_dec + funcname + "(" in src_lines[0]:
            should_be_replaced = True
            break
    return should_be_replaced


def replace_function(src_lines, replacement_functions):
    """
    Returns the substitude source code for a function.
    """
    function_name = src_lines[0][len_function_dec:].split('(')[0]
    return replacement_functions.pop(function_name)


def patch_scripts(base_script, overwrite_script, out_script):
    overwrite_funcs = {}
    func = ['']
    with open(overwrite_script, 'r') as file_in:
        patch_preamble = get_preamble(file_in)
        
        while len(func) != 0:
            func = get_next_function(file_in)
            if len(func) == 0:
                break
            func_name = func[0][len_function_dec:].split('(')[0]
            overwrite_funcs[func_name] = func
            
        
    with open(base_script, 'r') as file_in, open(out_script, 'w') as file_out:
        func = ['']
        base_preamble = get_preamble(file_in)
        
        for line in base_preamble:
            file_out.write(line)
        for line in patch_preamble:
            file_out.write(line)
        
        while len(func) != 0:
            func = get_next_function(file_in)
            if len(func) == 0:
                break
            
            # Remove the function from overwrite_functions and substitute it in to the base file,
            # if it is already defined in the base file
            if function_should_be_replaced(func, overwrite_funcs):
                func = replace_function(func, overwrite_funcs)
                
            for line in func:
                file_out.write(line)
                
        for func_src in overwrite_funcs.values():
            for line in func_src:
                file_out.write(line)