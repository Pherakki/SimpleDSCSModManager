import os

class UncompiledScript:
    group = 'script_src'
    enable_softcodes = True
    
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1] == 'script64' and os.path.splitext(filename)[-1] == '.txt':
            return True
        else:
            return False
        
    @classmethod
    def produce_index(cls, path, filename, rule):
        if rule is None:
            rule = 'squirrel_overwrite'
        return cls.group, os.path.join(path, filename), {filename: rule}
