import os
import subprocess



class ScriptHandler:
    def __init__(self, nutcracker_location, compiler_location):
        self.nutcracker_location = nutcracker_location
        self.nutcracker_directory = os.path.split(nutcracker_location)[0]
        self.compiler_location = compiler_location
        self.compiler_directory = os.path.split(compiler_location)[0]
        
    def compile_script(self, file, origin, destination):
        filename = os.path.splitext(file)[0]
        p = subprocess.Popen([self.compiler_location, "-c", os.path.join(origin, file)], 
                             creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.compiler_directory,
                             shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        output = p.stdout.read()
        try:
            os.rename(f"{os.path.join(self.compiler_directory, 'out.cnut')}", 
                      f"{os.path.join(destination, filename + '.nut')}")
        except Exception as e:
            raise self.CompilationFailedError(e, output)
            
    def decompile_script(self, file, origin, destination):
        filename = os.path.splitext(file)[0]
        out_path = os.path.join(destination, filename) + '.txt'
        p = subprocess.Popen([self.nutcracker_location, f"{os.path.join(origin, file)} > {out_path}"], 
                             creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.nutcracker_directory,
                             shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
        output = p.stdout.read()
        if not os.path.exists(out_path):
            raise Exception(output)
            
    class CompilationFailedError(Exception):
        pass