import os

class UncompiledScript:
    @staticmethod
    def checkIfMatch(path, filename):
        if os.path.split(path)[-1] == 'script64' and os.path.splitext(filename)[-1] == '.txt':
            return True
        else:
            return False
        
    @staticmethod
    def produce_index(path, filename, rule):
        if rule is None:
            rule = 'squirrel_overwrite'
        return 'script_src', os.path.join(path, filename), {filename: rule}
