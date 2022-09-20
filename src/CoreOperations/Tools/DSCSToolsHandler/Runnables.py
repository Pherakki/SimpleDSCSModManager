import os
import shutil

from PyQt5 import QtCore

from src.Utils.Signals import StandardRunnableSignals
from libs.dscstools import DSCSTools
from libs.nutcracker import NutCracker
from libs.squirrel import sq


class MDB1FileExtractorRunnable(QtCore.QRunnable):
    def __init__(self, archive, file, extract_method, postaction=None):
        super().__init__()
        self.archive = archive
        self.file = file
        self.extract_method = extract_method
        self.postaction = postaction
        self.signals = StandardRunnableSignals()
        
    def run(self):
        try:
            self.signals.started.emit(self.file)
            self.extract_method(self.archive, self.file)
            if self.postaction is not None:
                self.postaction(self.file)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.raise_exception.emit(e)

class MBEUnpackerRunnable(QtCore.QRunnable):
    def __init__(self, mbe_path, working_dir):
        super().__init__()
        self.mbe_path = mbe_path
        self.working_dir = working_dir
        self.signals = StandardRunnableSignals()
        
    def run(self):
        try:
            file = os.path.split(self.mbe_path)[1]
            self.signals.started.emit(file)
            DSCSTools.extractMBE(self.mbe_path, self.working_dir)
            os.remove(self.mbe_path)
            working_file = os.path.join(self.working_dir, file)
            shutil.move(working_file, self.mbe_path)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.raise_exception.emit(e)

class MBEPackerRunnable(QtCore.QRunnable):
    def __init__(self, mbe_path, working_dir):
        super().__init__()
        self.mbe_path = mbe_path
        self.working_dir = working_dir
        self.signals = StandardRunnableSignals()
        
    def run(self):
        try:
            file = os.path.split(self.mbe_path)[1]
            working_file = os.path.join(self.working_dir, file)
            self.signals.started.emit(file)
            DSCSTools.packMBE(self.mbe_path, working_file)
            shutil.rmtree(self.mbe_path)
            os.rename(working_file, self.mbe_path)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.raise_exception.emit(e)

class ScriptUnpackerRunnable(QtCore.QRunnable):
    def __init__(self, script_path, working_dir):
        super().__init__()
        self.script_path = script_path
        self.working_dir = working_dir
        self.signals = StandardRunnableSignals()
        
    def run(self):
        try:
            file = os.path.split(self.script_path)[1]
            working_file = os.path.join(self.working_dir, file)
            out_file = os.path.splitext(self.script_path)[0] + ".txt"
            self.signals.started.emit(file)
            os.rename(self.script_path, working_file)
            NutCracker.decompile(working_file, out_file)
            os.remove(working_file)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.raise_exception.emit(e)

class ScriptPackerRunnable(QtCore.QRunnable):
    def __init__(self, script_path, working_dir):
        super().__init__()
        self.script_path = script_path
        self.working_dir = working_dir
        self.signals = StandardRunnableSignals()
        
    def run(self):
        try:
            file = os.path.split(self.script_path)[1]
            working_file = os.path.join(self.working_dir, file)
            out_file = os.path.splitext(self.script_path)[0] + ".nut"
            self.signals.started.emit(file)
            os.rename(self.script_path, working_file)
            sq.compile(working_file, out_file)
            os.remove(working_file)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.raise_exception.emit(e)
