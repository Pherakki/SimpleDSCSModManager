import os
import sys

from PyQt5 import QtCore

from src.CoreOperations.Tools.DSCSToolsHandler.Runnables import MDB1FileExtractorRunnable
from src.Utils.Backups import get_backed_up_filepath_if_exists, default_MBD1s
from libs.dscstools import DSCSTools

translate = QtCore.QCoreApplication.translate

class MDB1FilelistExtractor(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    raise_exception = QtCore.pyqtSignal(Exception)
    finished = QtCore.pyqtSignal()
    exiting = QtCore.pyqtSignal()
    
    def __init__(self, threadpool, ops, file_archive_pairs, filepack, parent=None):
        super().__init__(parent)
        if not len(file_archive_pairs):
            raise Exception(translate("Tools::MDB1", "No files were passed for extraction!"))
        self.threadpool = threadpool
        self.file_archive_pairs = file_archive_pairs
        self.filepack = filepack
        self.ops = ops
        self.game_resources_folder = sys.intern(ops.paths.game_resources_loc)
        self.backups_folder = sys.intern(ops.paths.backups_loc)
        self.sdmm_resources_folder = sys.intern(ops.paths.resources_loc)
        self.completed_jobs = 0
        self.pre_message = filepack.get_extraction_name()
        self.prepremessage = ""
        self.njobs = len(self.file_archive_pairs)
        self.work_dir = os.path.join(self.sdmm_resources_folder, "working")
        self.finished.connect(self.cleanup_function)
        self.curJob = ""
        
        self.finished.connect(self.exiting)
        self.raise_exception.connect(self.exiting)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.logCurrentJob)
        self.exiting.connect(self.timer.stop)
        
        self.archive_paths_lookup = {}
        for archive in default_MBD1s:
            game_source_file = os.path.join(self.game_resources_folder, f"{archive}.steam.mvgl")
            self.archive_paths_lookup[archive] = get_backed_up_filepath_if_exists(game_source_file, self.game_resources_folder, self.backups_folder)
                
    def setLogInfo(self, curStep, maxSteps, depth):
        self.prepremessage = depth*">>" + " " + translate("Common", "[Step {curStep}/{maxSteps}] ").format(curStep=curStep, maxSteps=maxSteps)

    @QtCore.pyqtSlot(str)
    def jobStarted(self, msg):
        self.curJob = msg
        
    @QtCore.pyqtSlot()
    def logCurrentJob(self):
        self.updateLog.emit(translate("Tools::MDB1", "{step_count_msg}Extracting {filename}... ").format(step_count_msg=self.prepremessage, filename=self.pre_message)+ f"[{self.completed_jobs+1}/{self.njobs}] [{self.curJob}]")
    
    @QtCore.pyqtSlot()
    def checkIfComplete(self):
        self.completed_jobs += 1
        if self.completed_jobs == self.njobs:
            self.updateLog.emit(translate("Tools::MDB1", "{step_count_msg}Extracting {filename}... Done. ").format(step_count_msg=self.prepremessage,filename=self.pre_message)+ f"[{self.completed_jobs}/{self.njobs}]")
            
            
            self.finished.emit()

    @QtCore.pyqtSlot(Exception)
    def handleException(self, e):
        self.threadpool.clear()
        self.threadpool.waitForDone()
        self.raise_exception.emit(e)

    @QtCore.pyqtSlot()
    def execute(self):
        try:
            self.log.emit(translate("Tools::MDB1::Debug", "---MDB1 filelist extractor message---"))
            os.makedirs(self.work_dir, exist_ok=True)
            self.timer.start(100)
            for archive, filepath in self.file_archive_pairs:
                job = MDB1FileExtractorRunnable(archive, filepath, self.__extract_function, self.__unpack_function)
                job.signals.started.connect(self.jobStarted)
                job.signals.raise_exception.connect(self.handleException)
                job.signals.finished.connect(self.checkIfComplete)
                self.threadpool.start(job)
        except Exception as e:
            self.handleException(e)

    def __extract_function(self, archive, filepath):
        archive_path = self.archive_paths_lookup[archive]
        destination_path = os.path.join(self.sdmm_resources_folder, "base_resources")

        DSCSTools.extractMDB1File(archive_path, destination_path, filepath, True)
        
    def __unpack_function(self, filepath):
        destination_path = os.path.join(self.sdmm_resources_folder, "base_resources", filepath)
        self.filepack.unpack(destination_path, self.work_dir)
        
    @QtCore.pyqtSlot()
    def cleanup_function(self):
        os.rmdir(self.work_dir)
        
class MDB1Extractor(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    raise_exception = QtCore.pyqtSignal(Exception)
    finished = QtCore.pyqtSignal()
    success = QtCore.pyqtSignal()
    
    def __init__(self, threadpool, ops, archive_path, extract_dir,  parent=None):
        super().__init__(parent)
        self.threadpool = threadpool
        self.ops = ops
        
        self.archive_path = archive_path
        self.pre_message = (os.path.split(archive_path)[1]).split('.')[0]
        self.extract_dir = os.path.join(extract_dir, self.pre_message)
        
        self.completed_jobs = 0
        self.njobs = 0 
        self.curJob = ""
        
        self.success.connect(self.finished)
        self.raise_exception.connect(self.finished)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.logCurrentJob)
        self.finished.connect(self.timer.stop)

    @QtCore.pyqtSlot(Exception)
    def clean_up_exception(self, e):
        self.threadpool.clear()
        self.threadpool.waitForDone()
        self.raise_exception.emit(e)
        
    @QtCore.pyqtSlot(str)
    def jobStarted(self, msg):
        self.curJob = msg
        
    @QtCore.pyqtSlot()
    def logCurrentJob(self):
        self.updateLog.emit(translate("Tools::MDB1", "Extracting {archive_name} to {filepath}... ").format(archive_name=self.pre_message,filepath=self.extract_dir)+ f"[{self.completed_jobs+1}/{self.njobs}] [{self.curJob}]")
    
    @QtCore.pyqtSlot()
    def checkIfComplete(self):
        self.completed_jobs += 1
        if self.completed_jobs == self.njobs:
            self.updateLog.emit(translate("Tools::MDB1", "Extracting {archive_name} to {filepath}... Done. ").format(archive_name=self.pre_message,filepath=self.extract_dir) + f"[{self.completed_jobs}/{self.njobs}] [{self.curJob}]")
            self.success.emit()

    @QtCore.pyqtSlot()
    def execute(self):
        try:
            # The first file is '.\x00\x00\x00\x00', which we don't want to process...
            fileinfos = DSCSTools.getArchiveInfo(self.archive_path).Files

            assert fileinfos[0].FileName == '.\x00\x00\x00\x00', f"First filename was not the expected value of \'.\\x00\\x00\\x00\\x00\', found {fileinfos[0].FileName}."
            fileinfos = fileinfos[1:]
            self.njobs = len(fileinfos)
            
            self.log.emit(translate("Tools::MDB1::Debug", "---MDB1 extractor message---"))
            os.makedirs(self.extract_dir, exist_ok=True)
            self.timer.start(100)
            for filepath in fileinfos:
                job = MDB1FileExtractorRunnable(self.archive_path, filepath.FileName, self.__extract_function)
                job.signals.raise_exception.connect(self.clean_up_exception)
                job.signals.started.connect(self.jobStarted)
                job.signals.finished.connect(self.checkIfComplete)
                self.threadpool.start(job)
        except Exception as e:
            self.clean_up_exception(e)

    def __extract_function(self, _, filepath):
        DSCSTools.extractMDB1File(self.archive_path, self.extract_dir, filepath, True)
