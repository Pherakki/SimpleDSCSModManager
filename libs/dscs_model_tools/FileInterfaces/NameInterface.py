from ..FileReaders.NameReader import NameReader


class NameInterface:
    def __init__(self):
        self.bone_names = []
        self.material_names = []

    @classmethod
    def from_file(cls, path):
        with open(path, 'rb') as F:
            namereader = NameReader(F)
            namereader.read()

        new_name_interface = cls()
        new_name_interface.bone_names = namereader.bone_names
        new_name_interface.material_names = namereader.material_names

        return new_name_interface

    def to_file(self, path):
        with open(path, 'wb') as F:
            readwriter = NameReader(F)

            bone_names = self.bone_names
            material_names = self.material_names

            readwriter.num_bone_names = len(bone_names)
            readwriter.num_material_names = len(material_names)

            num_ptrs = len(bone_names) + len(material_names)
            readwriter.bone_name_pointers = [8 + 4 * num_ptrs + sum([len(name) for name in bone_names[:i]])
                                             for i in range(len(bone_names))]

            readwriter.material_name_pointers = [readwriter.bone_name_pointers[-1] + len(bone_names[-1]) +
                                                 sum([len(name) for name in material_names[:i]])
                                                 for i in range(len(material_names))]
            readwriter.bone_names = bone_names
            readwriter.material_names = material_names

            readwriter.write()
