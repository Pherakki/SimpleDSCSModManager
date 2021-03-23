import os

{
    'archive': 'DSDB',
    'addition_rule': 'overwrite',
    'num_columns': 2
}

def mbe_overwrite(base, overwrite):
    """
    Replaces an mbe record if it exists, else creates one.
    """
    for key, value in overwrite.items():
        base[key] = value
        
    return base

def mbe_extend(base, overwrite):
    """
    Extends the entries for a particular MBE record if it exists, else creates one.
    """
    for key, value in overwrite.items():
        if key not in base:
            base[key] = value
        else:
            base[key].extend(value)
            
    return base

addition_rules_lookup = {'overwrite': mbe_overwrite, 'extend': mbe_extend}
overwrite_states = {
        0: {'Type': 'Unaffected'},
        1: {'Type': 'Overwritten'},
        2: {'Type': 'Extended'},
        3: {'Type': 'Exceeded Size Limit'},
        4: {'Type': 'In Use'}
}

def generate_autorequest_index(modfiles):
    ref_files = [os.path.splitext(file) for file in modfiles]
    name_files, not_name_files = [], []
    for file, ext in ref_files:
        (name_files if ext == '.name' else not_name_files).append(file)
    del ref_files
    
    skel_files, not_skel_files = [], []
    for file, ext in not_name_files:
        (skel_files if ext == '.skel' else not_skel_files).append(file)
    del not_name_files
    
    geom_files, not_geom_files = [], []
    for file, ext in not_skel_files:
        (geom_files if ext == '.geom' else not_geom_files).append(file)
    del not_skel_files
    
    
def generate_csv_index(csv_table):
    entry_generator = (csv_line.split(',') for csv_line in csv_table.split('\n'))
    return {entry[0]: entry[1:] for entry in entry_generator}

def generate_overwrite_graph(files):
    entries = {entry: 1 for entry in files[:-1]}
    entries[files[-1]] = 4
    return entries

def generate_mbe_graph(files, rules, ns_added, max_limit):
    aggregated_size = 0
    entries = {}
    length = len(files)
    for i, (file, rule, n_added) in enumerate(zip(files, rules, ns_added)):
        if rule == 'overwrite':
            entries = {entry: 1 for entry in entries}
            if i == length:
                entries[file] = 4
            else:
                entries[file] = 2
            aggregated_size = n_added
        elif rule == 'append':
            aggregated_size += n_added
            entries[file] = 2 if aggregated_size <= max_limit else 3
        else:
            raise ValueError(rf"Rule '{rule}' was not recognised.")
            
def generate_modfiles_graph(mods):
    graph_frames = {}
    for mod in mods:
        for file in mod.files:
            if file not in graph_frames:
                graph_frames.append([])
            graph_frames[file].append(mod)
    for modlist in graph_frames:
        # Change this to whatever the correct function is
        generate_overwrite_graph(modlist)