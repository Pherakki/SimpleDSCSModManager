class LightSourceInterface:
    def __init__(self):
        self.bone_name_hash = None
        self.mode = None
        self.light_id = None
        self.intensity = None
        self.unknown_fog_param = None
        self.red = None
        self.blue = None
        self.green = None
        self.alpha = None

    @classmethod
    def from_subfile(cls, reader):
        instance = cls()
        instance.bone_name_hash = reader.bone_name_hash
        instance.mode = reader.mode
        instance.light_id = reader.light_id
        instance.intensity = reader.intensity
        instance.unknown_fog_param = reader.unknown_fog_param
        instance.red = reader.red
        instance.blue = reader.blue
        instance.green = reader.green
        instance.alpha = reader.alpha

        return instance

    def to_subfile(self, reader, virtual_pos):
        reader.bone_name_hash = self.bone_name_hash
        reader.mode = self.mode
        reader.light_id = self.light_id
        reader.intensity = self.intensity
        reader.unknown_fog_param = self.unknown_fog_param
        reader.red = self.red
        reader.blue = self.blue
        reader.green = self.green
        reader.alpha = self.alpha

        reader.unknown_0x20 = 0
        reader.unknown_0x24 = 0
        reader.unknown_0x28 = 0

        reader.padding_0x2C = 0
        reader.padding_0x30 = 0
        reader.padding_0x38 = 0

        return virtual_pos + 0x40

