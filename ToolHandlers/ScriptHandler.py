import os
import subprocess



class ScriptHandler:
    def __init__(self, nutcracker_location, compiler_location):
        self.nutcracker_location = nutcracker_location
        self.nutcracker_directory = os.path.split(nutcracker_location)[0]
        self.compiler_location = compiler_location
        self.compiler_directory = os.path.split(compiler_location)[0]
        
    def compile_script(self, file, origin, destination, remove_input=False):
        filename = os.path.splitext(file)[0]
        p = subprocess.run([self.compiler_location, "-o", os.path.join(destination, filename) + '.nut', "-c", os.path.join(origin, file)], 
                             creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.compiler_directory, close_fds=True)
        if remove_input:
            os.remove(os.path.join(origin, file))
            
    def decompile_script(self, file, origin, destination, remove_input=False):
        filename = os.path.splitext(file)[0]
        out_path = os.path.join(destination, filename) + '.txt'
        with open(out_path, "w") as out:
            p = subprocess.run([self.nutcracker_location, f"{os.path.join(origin, file)}"], 
                                  creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.nutcracker_directory,
                                  stdout=out, close_fds=True)
            if remove_input:
                os.remove(os.path.join(origin, file))
