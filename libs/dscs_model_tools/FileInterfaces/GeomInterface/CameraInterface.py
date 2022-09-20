class CameraInterface:
    def __init__(self):
        self.bone_name_hash = None
        self.fov = None
        self.maybe_aspect_ratio = None
        self.zNear = None

        self.zFar = None
        self.orthographic_scale = None
        self.projection = None

    @classmethod
    def from_subfile(cls, reader):
        instance = cls()
        instance.bone_name_hash = reader.bone_name_hash
        instance.fov = reader.fov
        instance.maybe_aspect_ratio = reader.maybe_aspect_ratio
        instance.zNear = reader.zNear

        instance.zFar = reader.zFar
        instance.orthographic_scale = reader.orthographic_scale
        instance.projection = reader.projection

        return instance

    def to_subfile(self, reader, virtual_pos):
        reader.bone_name_hash = self.bone_name_hash
        reader.fov = self.fov
        reader.maybe_aspect_ratio = self.maybe_aspect_ratio
        reader.zNear = self.zNear

        reader.zFar = self.zFar
        reader.orthographic_scale = self.orthographic_scale
        reader.projection = self.projection
        reader.padding_0x1C = 0

        reader.padding_0x20 = 0
        reader.padding_0x28 = 0

        return virtual_pos + 0x30
