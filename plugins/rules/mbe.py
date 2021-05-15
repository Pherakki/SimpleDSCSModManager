def mberecord_overwrite(record_id, mbe_data, mod_mbe_data, record_size):
    mbe_data[record_id] = mod_mbe_data[record_id]
    
def mberecord_join(record_id, mbe_data, mod_mbe_data, record_size):
    max_records = record_size - 1
    nonzero_data = [elem for elem in mbe_data.get(record_id, []) if elem != '0']
    new_data = [elem for elem in mod_mbe_data[record_id] if elem not in nonzero_data]
    nonzero_data.extend(new_data)
    nonzero_data = nonzero_data[:max_records]
    # Pad out the records such that there are always 6 evolution entries + the ID
    nonzero_data.extend(['0']*(max_records - len(nonzero_data)))
    mbe_data[record_id] = nonzero_data
