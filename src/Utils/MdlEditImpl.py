import json

from src.Utils.Settings import default_encoding
from src.Utils.Softcodes import replace_softcodes


class MdlEdit:
    ops = ["editNPC"]
    __slots__ = tuple(ops)
    
    def __init__(self):
        for op in MdlEdit.ops:
            setattr(self, op, [])
            
    @classmethod
    def init_from_data(cls, dataset):
        instance = cls()
        for op, data in dataset:
            instance.add_element(op, data)
        return instance
    
    @classmethod
    def init_from_file(cls, filepath, softcodes, softcode_lookup):
        with open(filepath, 'rb') as F:
            data = replace_softcodes(F.read(), softcodes, softcode_lookup)
            return cls.init_from_data(json.loads(data.decode(encoding=default_encoding), object_pairs_hook=lambda x: x))
            
    def add_element(self, op, data):
        try:
            opdata = getattr(self, op)
        except AttributeError as e:
            raise AttributeError(f"\'{op}\' is not a valid ModelEdit command.") from e
        opdata.append({k: v for k, v in data})


def parse_mdledit(filepath, softcodes, softcode_lookup):
    return MdlEdit.init_from_file(filepath, softcodes, softcode_lookup)
