import os

class SqMod:
    group = 'sqmod'
    default_rule = 'squirrel_modify'
    enable_softcodes = False
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1] == 'script64' and os.path.splitext(filename)[-1] == '.sqmod':
            return True
        else:
            return False
    
    @staticmethod
    def get_target(filepath):
        return os.path.splitext(filepath)[0] + ".txt"
    
    @classmethod
    def get_rule(cls, filepath):
        return cls.default_rule
    
    @classmethod
    def produce_index(cls, path, filename):
        return cls.group, os.path.join(path, filename), [filename]

    @staticmethod
    def get_pack_name(filepath):
        return filepath
