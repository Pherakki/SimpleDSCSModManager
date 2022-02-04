import os

class UncompiledScript:
    group = 'script_src'
    default_rule = 'squirrel_concat'
    enable_softcodes = True
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1] == 'script64' and os.path.splitext(filename)[-1] == '.txt':
            return True
        else:
            return False
        
    @staticmethod
    def get_target(filepath):
        return filepath
    
    @classmethod
    def get_rule(cls, filepath):
        return cls.default_rule
    
    @classmethod
    def produce_index(cls, path, filename):
        return cls.group, os.path.join(path, filename), [filename]
    
    @staticmethod
    def get_pack_name(filepath):
        return filepath
        