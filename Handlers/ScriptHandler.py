import os
import subprocess

from .ScriptWorker import ScriptWorker

src_ext = '.txt'
comp_ext = '.nut'

class ScriptHandler:
    def __init__(self, nutcracker_location, compiler_location):
        self.nutcracker_location = nutcracker_location
        self.nutcracker_directory = os.path.split(nutcracker_location)[0]
        self.compiler_location = compiler_location
        self.compiler_directory = os.path.split(compiler_location)[0]
        
    def compile_script(self, file, origin, destination, remove_input=False):
        filename = os.path.splitext(file)[0]
        p = subprocess.Popen([self.compiler_location, "-o", os.path.join(destination, filename) + comp_ext, "-c", os.path.join(origin, file)], 
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.compiler_directory, close_fds=True)
        output = p.stdout.read()
        if len(output):
            raise Exception(output)
        if remove_input:
            os.remove(os.path.join(origin, file))
            
    def decompile_script(self, file, origin, destination, remove_input=False):
        filename = os.path.splitext(file)[0]
        out_path = os.path.join(destination, filename) + src_ext
        with open(out_path, "w") as out:
            p = subprocess.run([self.nutcracker_location, f"{os.path.join(origin, file)}"], 
                                  creationflags=subprocess.CREATE_NO_WINDOW, cwd=self.nutcracker_directory,
                                  stdout=out, close_fds=True)
            if remove_input:
                os.remove(os.path.join(origin, file))

    def generate_script_compiler(self, origin, destination, threadpool,
                                 lockGuiFunc, releaseGuiFunc, messageLogFunc, updateMessageLogFunc,
                                 remove_input=False):
        return ScriptWorker(origin, destination, self.compile_script, lambda file: os.path.splitext(file)[1] == src_ext,
                            threadpool, "compiling", "Compiled",
                            lockGuiFunc, releaseGuiFunc, messageLogFunc, updateMessageLogFunc,
                            remove_input=origin==destination)
    
    def generate_script_decompiler(self, origin, destination, threadpool,
                                 lockGuiFunc, releaseGuiFunc, messageLogFunc, updateMessageLogFunc,
                                 remove_input=False):
        return ScriptWorker(origin, destination, self.decompile_script, lambda file: os.path.splitext(file)[1] == comp_ext,
                            threadpool, "decompiling", "Decompiled",
                            lockGuiFunc, releaseGuiFunc, messageLogFunc, updateMessageLogFunc,
                            remove_input=origin==destination)
    