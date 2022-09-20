from .BaseRW import BaseRW


class NameReader(BaseRW):
    """
    A class to read name files. These files are split into three main sections:
        1. Two integers that state how many bone names and material names are contained within the file.
        2. A section of file pointers, one per bone name and one per material name.
        3. A continuous string of ascii characters that, when split at the locations given by the file pointers,
           resolves to bone names and material names.

    Completion status
    ------
    (o) NameReader can successfully parse all name files in DSDB archive within current constraints.
    (o) NameReader can fully interpret all data in name files in DSDB archive.
    (o) NameReader can write data to name files.
    """
    def __init__(self, bytestream):
        super().__init__(bytestream)

        self.num_bone_names = None
        self.num_material_names = None
        self.bone_name_pointers = None
        self.bone_names = None
        self.material_name_pointers = None
        self.material_names = None

    def read(self):
        """
        Reads the name file.
        """
        self.read_write(self.read_buffer, self.read_ascii)
        self.interpret_name_data()

    def write(self):
        """
        Writes the name file.
        """
        self.reinterpret_name_data()
        self.read_write(self.write_buffer, self.write_ascii)

    def read_write(self, buffer_operator, ascii_operator):
        self.rw_header(buffer_operator)
        self.rw_pointers(buffer_operator)
        self.rw_bone_names(ascii_operator)
        self.rw_material_names(ascii_operator)

    def rw_header(self, rw_operator):
        self.assert_file_pointer_now_at(0)

        rw_operator('num_bone_names', 'I')
        rw_operator('num_material_names', 'I')
        
    def rw_pointers(self, rw_operator):
        rw_operator('bone_name_pointers', 'I'*self.num_bone_names, force_1d=True)
        rw_operator('material_name_pointers', 'I'*self.num_material_names, force_1d=True)

    def rw_bone_names(self, rw_operator_ascii):
        if len(self.bone_name_pointers) == 0:
            self.bone_names = ''
            return
        self.assert_file_pointer_now_at(self.bone_name_pointers[0])
        if len(self.material_name_pointers) == 0:
            rw_operator_ascii('bone_names')
        else:
            bytes_to_read = self.material_name_pointers[0] - self.bytestream.tell()
            rw_operator_ascii('bone_names', bytes_to_read)

    def rw_material_names(self, rw_operator_ascii):
        if len(self.material_name_pointers) == 0:
            self.material_names = ''
            return
        self.assert_file_pointer_now_at(self.material_name_pointers[0])
        rw_operator_ascii('material_names')

    # There is probably a cleaner way of reading the bone names in.
    # This works for the moment though!
    def split_string_by_ptrs(self, ascii_string, ptrs):
        # Split up the ascii-string into its constituent components.
        # The file pointers point to the start of each sub-string.
        retval = []
        for st, ed in zip(ptrs[:-1], ptrs[1:]):
            # The file pointers are absolute locations, so we need to translate them to be relative to the start of the
            # byte-string.
            rel_st = st - ptrs[0]
            rel_ed = ed - ptrs[0]
            stringslice = ascii_string[rel_st:rel_ed]
            retval.append(stringslice)
        # The for loop will miss off the final sub-string because the file pointers just point to the starts of the
        # strings, so read it now
        if len(ptrs) > 0:
            ed = ptrs[-1] - ptrs[0]
            retval.append(ascii_string[ed:])

        return retval

    def interpret_name_data(self):
        self.bone_names = self.split_string_by_ptrs(self.bone_names, self.bone_name_pointers)
        assert len(self.bone_names) == self.num_bone_names, "Number of bone names is different to number of bone entries."
        self.material_names = self.split_string_by_ptrs(self.material_names, self.material_name_pointers)
        assert len(self.material_names) == self.num_material_names, "Number of material names is different to number of material entries."

    def reinterpret_name_data(self):
        assert len(self.bone_names) == self.num_bone_names, "Number of bone names is different to number of bone entries."
        self.bone_names = ''.join(self.bone_names)
        assert len(self.material_names) == self.num_material_names, f"Number of material names is different to number of material entries: {self.material_names}, {self.num_material_names}"
        self.material_names = ''.join(self.material_names)

