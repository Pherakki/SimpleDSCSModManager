from plugins.patchers import UniversalDataPack

class CSVDataPack(UniversalDataPack):
    __slots__ = ("csv_data", "id_len", "softcodes", "softcode_lookup", "encoding", "fill_value")
    