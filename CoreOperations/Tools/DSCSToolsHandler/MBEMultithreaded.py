import os

from PyQt5 import QtCore

from CoreOperations.Tools.DSCSToolsHandler.Runnables import MBEUnpackerRunnable, MBEPackerRunnable

translate = QtCore.QCoreApplication.translate

class BaseMBERunner(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    raise_exception = QtCore.pyqtSignal(Exception)
    finished = QtCore.pyqtSignal()
    success = QtCore.pyqtSignal()
    
    def __init__(self, threadpool, ops, mbes_folder,  parent=None):
        super().__init__(parent)
        self.threadpool = threadpool
        self.ops = ops
        
        self.mbes_folder = mbes_folder
        self.pre_message = os.path.split(mbes_folder)[1]
        self.working_dir = os.path.join(mbes_folder, "working")
        
        self.completed_jobs = 0
        self.njobs = 0 
        self.curJob = ""
        
        self.success.connect(self.finished)
        #self.raise_exception.connect(self.finished)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.logCurrentJob)
        self.finished.connect(self.timer.stop)

    @QtCore.pyqtSlot(str)
    def jobStarted(self, msg):
        self.curJob = msg
        
    @QtCore.pyqtSlot()
    def logCurrentJob(self):
        self.updateLog.emit(translate("Tools::MBE", "{pack_or_extract_verb} MBEs from {filepath}... ").format(pack_or_extract_verb=self.packmsg,filepath=self.pre_message)+ f"[{self.completed_jobs+1}/{self.njobs}] [{self.curJob}]")
    
    @QtCore.pyqtSlot()
    def checkIfComplete(self):
        self.completed_jobs += 1
        if self.completed_jobs == self.njobs:
            self.updateLog.emit(translate("Tools::MBE", "{pack_or_extract_verb} MBEs from {filepath}... Done. ").format(pack_or_extract_verb=self.packmsg, filepath=self.pre_message)+ f"[{self.completed_jobs}/{self.njobs}]")
            self.success.emit()
            
    @QtCore.pyqtSlot(Exception)
    def clean_up_exception(self, e):
        self.threadpool.clear()
        self.threadpool.waitForDone()
        self.raise_exception.emit(e)

    @QtCore.pyqtSlot()
    def execute(self):
        try:
            if not os.path.isdir(self.mbes_folder):
                self.success.emit()
                return
            mbes = [file for file in os.listdir(self.mbes_folder) if ((os.path.splitext(file)[1] == ".mbe") and self.fcheck(file))]
            self.njobs = len(mbes)
            
            if self.njobs:
                self.log.emit(translate("Tools::MBE::Debug", "---MDB1 extractor message---"))
                os.makedirs(self.working_dir, exist_ok=True)
                self.finished.connect(lambda : os.rmdir(self.working_dir))
                self.timer.start(100)
                for mbe in mbes:
                    job = self.runnable(os.path.join(self.mbes_folder, mbe), self.working_dir)
                    job.signals.raise_exception.connect(self.clean_up_exception)
                    job.signals.started.connect(self.jobStarted)
                    job.signals.finished.connect(self.checkIfComplete)
                    self.threadpool.start(job)
            else:
                self.success.emit()
        except Exception as e:
            self.raise_exception.emit(e)

class MBEExtractor(BaseMBERunner):
    runnable = MBEUnpackerRunnable
    packmsg = translate("Tools::MBE::ExtractVerb", "Extracting")

    def fcheck(self, x):
        return os.path.isfile(os.path.join(self.mbes_folder, x))
    
class MBEPacker(BaseMBERunner):
    runnable = MBEPackerRunnable
    packmsg = translate("Tools::MBE::PackVerb", "Packing")
    
    def fcheck(self, x):
        return os.path.isdir(os.path.join(self.mbes_folder, x))
