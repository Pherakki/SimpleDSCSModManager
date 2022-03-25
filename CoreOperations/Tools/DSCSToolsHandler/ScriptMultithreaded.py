import os

from PyQt5 import QtCore

from CoreOperations.Tools.DSCSToolsHandler.Runnables import ScriptUnpackerRunnable, ScriptPackerRunnable

translate = QtCore.QCoreApplication.translate

class BaseScriptRunner(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    raise_exception = QtCore.pyqtSignal(Exception)
    finished = QtCore.pyqtSignal()
    success = QtCore.pyqtSignal()
    
    def __init__(self, threadpool, ops, scripts_folder,  parent=None):
        super().__init__(parent)
        self.threadpool = threadpool
        self.ops = ops
        
        self.scripts_folder = scripts_folder
        self.pre_message = os.path.split(scripts_folder)[1]
        self.working_dir = os.path.join(scripts_folder, "working")
        
        self.completed_jobs = 0
        self.njobs = 0 
        self.curJob = ""
        
        self.success.connect(self.finished)
        self.raise_exception.connect(self.finished)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.logCurrentJob)
        self.finished.connect(self.timer.stop)

    @QtCore.pyqtSlot(str)
    def jobStarted(self, msg):
        self.curJob = msg
        
    @QtCore.pyqtSlot()
    def logCurrentJob(self):
        self.updateLog.emit(translate("Tools::Scripts", "{compile_or_decompile_verb} scripts from {filepath}... ").format(compile_or_decompile_verb=self.packmsg, filepath=self.pre_message)+ f"[{self.completed_jobs+1}/{self.njobs}] [{self.curJob}]")
    
    @QtCore.pyqtSlot()
    def checkIfComplete(self):
        self.completed_jobs += 1
        if self.completed_jobs == self.njobs:
            self.updateLog.emit(translate("Tools::Scripts", "{compile_or_decompile_verb} scripts from {filepath}... Done. ").format(compile_or_decompile_verb=self.packmsg, filepath=self.pre_message) + f"[{self.completed_jobs+1}/{self.njobs}]")
            self.success.emit()
            
    @QtCore.pyqtSlot(Exception)
    def clean_up_exception(self, e):
        self.threadpool.clear()
        self.threadpool.waitForDone()
        self.raise_exception.emit(e)

    @QtCore.pyqtSlot()
    def execute(self):
        try:
            if not os.path.isdir(self.scripts_folder):
                self.success.emit()
                return
            scripts = [file for file in os.listdir(self.scripts_folder) if ((os.path.splitext(file)[1] == self.ext) and os.path.isfile(os.path.join(self.scripts_folder, file)))]
            self.njobs = len(scripts)
            
            if self.njobs:
                self.log.emit(translate("Tools::Scripts::Debug", "---script extractor message---"))
                os.makedirs(self.working_dir, exist_ok=True)
                self.finished.connect(lambda : os.rmdir(self.working_dir))
                self.timer.start(100)
                for script in scripts:
                    job = self.runnable(os.path.join(self.scripts_folder, script), self.working_dir)
                    job.signals.raise_exception.connect(self.clean_up_exception)
                    job.signals.started.connect(self.jobStarted)
                    job.signals.finished.connect(self.checkIfComplete)
                    self.threadpool.start(job)
            else:
                self.success.emit()
        except Exception as e:
            self.raise_exception.emit(e)

class ScriptExtractor(BaseScriptRunner):
    runnable = ScriptUnpackerRunnable
    packmsg = translate("Tools::Scripts::DecompileVerb", "Decompiling")
    ext = ".nut"
    
class ScriptPacker(BaseScriptRunner):
    runnable = ScriptPackerRunnable
    packmsg = translate("Tools::Scripts::CompileVerb", "Compiling")
    ext = ".txt"
