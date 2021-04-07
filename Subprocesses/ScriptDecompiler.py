import os

from PyQt5 import QtCore


class ScriptDecompilerWorkerThread(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    updateMessageLog = QtCore.pyqtSignal(str)
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()
    
    def __init__(self, source_folder, dump_folder, decompile_script, parent=None):
        super().__init__(parent)
        self.source_folder = source_folder
        self.dump_folder = dump_folder
        self.decompile_script = decompile_script
        
    def run(self):
        try:
            self.lockGui.emit()
            self.messageLog.emit(f"Extracting scripts in {self.source_folder} " 
                                 f"to {self.dump_folder}...")
            scripts = os.listdir(self.source_folder)
            n_scripts = len(scripts)
            self.messageLog.emit("")
            for i, script in enumerate(scripts):
                self.decompile_script(script, self.source_folder, self.dump_folder)
                self.updateMessageLog.emit(f"Decompiled script {i}/{n_scripts} [{script}]")
            self.messageLog.emit("Extraction successful.")
        except Exception as e:
            self.messageLog.emit(f"The following error occured when trying to decompile {script}: {e}")
            raise e
        finally:
            self.releaseGui.emit()
            self.finished.emit()

    
    
class ScriptDecompilerWorker:
    def __init__(self, origin, destination, decompile_script, threadpool,
                  lockGuiFunc, releaseGuiFunc, messageLogFunc, updateMessageLogFunc):
        self.origin = origin
        self.destination = destination
        self.decompile_script = decompile_script
        self.n_complete = 0
        self.n_jobs = 0
        self.threadpool = threadpool
        
        self.lockGuiFunc = lockGuiFunc
        self.releaseGuiFunc = releaseGuiFunc
        self.messageLogFunc = messageLogFunc
        self.updateMessageLogFunc = updateMessageLogFunc
        
        self.start = None

        
    def run(self):
        self.n_complete = 0
        self.messageLogFunc("")
        try:
            self.lockGuiFunc()
            scripts = os.listdir(self.origin)
            self.njobs = len(scripts)
            for script in scripts:
                job = ScriptDecompilerRunnable(self.decompile_script,
                                    script, self.origin, self.destination,
                                    self.update_messagelog,
                                    self.update_finished)
                self.threadpool.start(job)
                raise Exception
        except Exception as e:
            self.threadpool.waitForDone()
            self.messageLogFunc(f"Exception: {e}")
        
    def update_finished(self):
        if self.n_complete == self.njobs:
            self.releaseGuiFunc()

    def update_messagelog(self, message):
        self.n_complete += 1
        self.updateMessageLogFunc(f"Decompiled script {self.n_complete}/{self.njobs} [{message}]")


class ScriptDecompilerRunnable(QtCore.QRunnable):
    def __init__(self, decompile_script, script, origin, destination, update_messagelog, update_finished):
        super().__init__()
        self.decompile_script = decompile_script
        self.script = script
        self.origin = origin
        self.destination = destination
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        
    @QtCore.pyqtSlot()
    def run(self):
        self.decompile_script(self.script, self.origin, self.destination)
        self.update_messagelog(self.script)
        self.update_finished()
