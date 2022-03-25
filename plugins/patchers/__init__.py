class BasePatcher:
    pass

class UniversalDataPack:
    __slots__ = ("source", "mod", "source_file", "target", "build_target", "backups_loc", "cache_loc", "archives_loc", "rule_args")
    
    def __init__(self):
        self.rule_args = []
        self.rule_args.clear()