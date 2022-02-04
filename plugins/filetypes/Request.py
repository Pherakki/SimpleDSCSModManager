import os

class RequestFile:
    group = 'request'
    default_rule = 'overwrite'
    enable_softcodes = True
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.splitext(filename)[-1] == '.request':
            return True
        else:
            return False
        
    @staticmethod
    def get_target(filepath):
        return filepath
    
    @classmethod
    def get_rule(cls, filepath):
        return cls.default_rule
    
    @staticmethod
    def get_pack_name(filepath):
        return os.path.splitext(filepath)[0]
        