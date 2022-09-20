from .BaseRW import BaseRW

class PhysReader(BaseRW):
    def __init__(self, bytestream):
        super().__init__(bytestream)

        # Variables that appear in the file header
        self.filetype = None
        self.filetype_identifier = 2
        self.ragdoll_count = 0
        self.collider_count = 0
        self.material_names_count = 0
        self.bone_names_count = 0

        self.ragdolls_offset = 0
        self.colliders_offset = 0
        self.offset_3 = 0
        self.offset_4 = 0

        self.ragdolls = []
        self.collider_ptrs = []
        self.colliders = []
        self.material_names_offset = None
        self.bone_names_offset = None

    def read(self):
        self.read_write(self.read_buffer, 'read', self.init_structs, self.read_ascii, self.read_raw, self.cleanup_ragged_chunk_read)
        self.interpret_phys_data()

    def write(self):
        self.reinterpret_phys_data()
        self.read_write(self.write_buffer, 'write', lambda : None, self.write_ascii, self.write_raw, self.cleanup_ragged_chunk_write)

    def read_write(self, rw_operator, rw_method, init_structs, rw_operator_ascii, rw_operator_raw, chunk_cleanup):
        self.assert_file_pointer_now_at(0)

        rw_operator_ascii('filetype', 4)
        self.assert_equal("filetype", "PHYS"[::-1])
        rw_operator("filetype_identifier", "I")
        rw_operator("ragdoll_count", "I")
        rw_operator("collider_count", "I")
        rw_operator("material_names_count", "I")
        rw_operator("bone_names_count", "I")

        self.assert_equal("filetype_identifier", 2)

        rw_operator("ragdolls_offset", "Q")
        rw_operator("colliders_offset", "Q")
        rw_operator("material_names_offset", "Q")
        rw_operator("bone_names_offset", "Q")

        init_structs()
        self.rw_ragdolls(rw_method)
        chunk_cleanup(self.bytestream.tell(), 0x08)
        self.rw_colliders(rw_operator, rw_method)
        self.assert_file_pointer_now_at(self.material_names_offset)
        rw_operator_raw("material_names", 0x40 *self.material_names_count)
        self.assert_file_pointer_now_at(self.bone_names_offset)
        rw_operator_raw("bone_names", 0x40 *self.bone_names_count)

    def init_structs(self):
        self.ragdolls = [RagdollEntry(self.bytestream) for _ in range(self.ragdoll_count)]
        self.colliders = [ColliderData(self.bytestream) for _ in range(self.collider_count)]

    def rw_ragdolls(self, rw_method):
        self.assert_file_pointer_now_at(self.ragdolls_offset)
        for phys_bone in self.ragdolls:
            getattr(phys_bone, rw_method)()

    def rw_colliders(self, rw_operator, rw_method):
        self.assert_file_pointer_now_at(self.colliders_offset)
        rw_operator("collider_ptrs", "Q" *self.collider_count, force_1d=True)
        for ptr, coldata in zip(self.collider_ptrs, self.colliders):
            self.assert_file_pointer_now_at(ptr)
            getattr(coldata, rw_method)()

    def interpret_phys_data(self):
        self.material_names = self.chunk_list(self.material_names, 0x40)
        self.material_names = [nm.strip(b'\x00').decode('ascii') for nm in self.material_names]

        self.bone_names = self.chunk_list(self.bone_names, 0x40)
        self.bone_names = [nm.strip(b'\x00').decode('ascii') for nm in self.bone_names]


    def reinterpret_phys_data(self):
        self.material_names = [nm.ljust(0x40, b'\x00').encode('ascii') for nm in self.material_names]
        self.material_names = b''.join(self.material_names)

        self.bone_names = [nm.ljust(0x40, b'\x00').encode('ascii') for nm in self.bone_names]
        self.bone_names = b''.join(self.bone_names)


class RagdollEntry(BaseRW):
    def __init__(self, bytestream):
        super().__init__(bytestream)

        # Variables that appear in the file header
        # Get the scaled quaternion by doing:
        #  1) Convert bone quaternion to rotation matrix
        #  2) Multiply rotation matrix by scale matrix
        #  3) Covert back to quaternion without normalising
        self.position = None
        self.scaled_quaternion = None
        self.unknown_3vec = None
        self.unknown_float = 0
        self.collider_id = 0
        self.unknown_flag = 0
        self.ragdoll_name = None

    def print(self):
        print(self.position, self.scaled_quaternion, self.unknown_3vec, self.unknown_float, self.collider_id, self.unknown_flag, self.ragdoll_name)


    def read(self):
        self.read_write(self.read_buffer, self.read_raw)
        self.interpret_ragdoll()

    def write(self):
        self.reinterpret_ragdoll()
        self.read_write(self.write_buffer, self.write_raw)

    def read_write(self, rw_operator, rw_operator_raw):
        rw_operator("position", "fff")
        rw_operator("scaled_quaternion", "ffff")
        rw_operator("unknown_3vec", "fff")
        rw_operator("unknown_float", "f")
        rw_operator("collider_id", "I")
        rw_operator("unknown_flag", "I")
        rw_operator_raw("ragdoll_name", 0x18)

        self.assert_equal("unknown_3vec", (0.20000000298023224, 0.20000000298023224, 0.6000000238418579))

    def interpret_ragdoll(self):
        self.ragdoll_name = self.ragdoll_name.strip(b'\x00').decode('ascii')

    def reinterpret_ragdoll(self):
        self.ragdoll_name = self.ragdoll_name.ljust(b'\x00', 0x18).encode('ascii')


class ColliderData(BaseRW):
    def __init__(self, bytestream):
        super().__init__(bytestream)

        # Variables that appear in the file header
        self.filetype = None
        self.data = None

    def read(self):
        self.read_buffer("filetype", "Q")
        if self.filetype == 0:
            self.data = SimpleCollider(self.bytestream)
        elif self.filetype == 2:
            self.data = ComplexCollider(self.bytestream)
        self.data.read()

    def write(self):
        self.write_buffer("filetype", "Q")
        if self.filetype == 0:
            if type(self.data) != SimpleCollider:
                raise Exception(f"Collider filetype is {self.filetype}, but data type is {type(self.data)}.")
        elif self.filetype == 2:
            if type(self.data) != ComplexCollider:
                raise Exception(f"Collider filetype is {self.filetype}, but data type is {type(self.data)}.")
        self.data.write()

    def print(self):
        print(self.filetype, type(self.data))
        self.data.print()


class SimpleCollider(BaseRW):
    """
    A simple cuboid collider, defined only by the bounding box corners.
    Sits at the position dictated by the Ragdoll entry it is attached to.
    """
    def __init__(self, bytestream):
        super().__init__(bytestream)
        self.bounding_box_corner = 0
        self.flag = 0

    def print(self):
        print(self.bounding_box_corner, self.flag)

    def read(self):
        self.read_write(self.read_buffer)

    def write(self):
        self.read_write(self.write_buffer)

    def read_write(self, rw_operator):
        rw_operator("bounding_box_corner", "fff")
        rw_operator("flag", "I")


class ComplexCollider(BaseRW):
    def __init__(self, bytestream):
        super().__init__(bytestream)
        self.vertex_count = 0
        self.triangle_count = 0
        self.unknown_coord_1 = 0
        self.unknown_coord_2 = 0

        self.triangles_offset = 0
        self.vertex_positions_offset = 0
        self.submesh_material_indices_offset = 0
        self.submesh_bone_indices_offset = 0

        self.triangle_indices = None
        self.vertex_positions = None
        self.submesh_material_indices = None
        self.submesh_material_indices_pad = 0
        self.submesh_bone_indices = None
        self.submesh_bone_indices_pad = 0

    def print(self):
        print(self.vertex_count, self.triangle_count, self.unknown_coord_1, self.unknown_coord_2)
        #print(self.triangles_offset, self.vertex_positions_offset, self.offset_3, self.offset_4)
        #print(self.triangle_indices)
        #print(self.vertex_positions)
        print(self.submesh_material_indices)
        print(self.submesh_bone_indices)

    def read(self):
        self.read_write(self.read_buffer)
        self.interpret_mesh_collider_data()

    def write(self):
        self.reinterpret_mesh_collider_data()
        self.read_write(self.write_buffer)

    def read_write(self, rw_operator):
        rw_operator("vertex_count", "I")
        rw_operator("triangle_count", "I")
        rw_operator("unknown_coord_1", "fff")
        rw_operator("unknown_coord_2", "fff")
        rw_operator("triangles_offset", "Q")
        rw_operator("vertex_positions_offset", "Q")
        rw_operator("submesh_material_indices_offset", "Q")
        rw_operator("submesh_bone_indices_offset", "Q")

        self.assert_file_pointer_now_at(self.triangles_offset)
        rw_operator("triangle_indices", "I"*self.triangle_count*3)
        self.assert_file_pointer_now_at(self.vertex_positions_offset)
        rw_operator("vertex_positions", "f"*self.vertex_count*3)

        self.assert_file_pointer_now_at(self.submesh_material_indices_offset)
        rw_operator("submesh_material_indices", "h"*self.triangle_count)
        if (self.triangle_count % 2):
            rw_operator("submesh_material_indices_pad", "H")
            self.assert_equal("submesh_material_indices_pad", 0)

        self.assert_file_pointer_now_at(self.submesh_bone_indices_offset)
        rw_operator("submesh_bone_indices", "h"*self.triangle_count)
        if (self.triangle_count % 2):
            rw_operator("submesh_bone_indices_pad", "H")
            self.assert_equal("submesh_bone_indices_pad", 0)

    def interpret_mesh_collider_data(self):
        self.triangle_indices = self.chunk_list(self.triangle_indices, 3)
        self.vertex_positions = self.chunk_list(self.vertex_positions, 3)

    def reinterpret_mesh_collider_data(self):
        self.triangle_indices = self.flatten_list(self.triangle_indices)
        self.vertex_positions = self.flatten_list(self.vertex_positions)
