def mberecord_overwrite(record_id, mbe_data, mod_mbe_data):
    mbe_data[record_id] = mod_mbe_data[record_id]
    
def mberecord_join(record_id, mbe_data, mod_mbe_data):
    new_data = [elem for elem in mod_mbe_data[record_id] if elem not in mbe_data[record_id]]
    mbe_data[record_id].extend(new_data)
