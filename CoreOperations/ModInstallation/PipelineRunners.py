import json
import os
import sys

from PyQt5 import QtCore

from CoreOperations.PluginLoaders.FilePacksPluginLoader import get_filepack_plugins_dict
from CoreOperations.PluginLoaders.PatchersPluginLoader import get_patcher_plugins_dict
from Utils.Signals import StandardRunnableSignals

translate = QtCore.QCoreApplication.translate

patchers = get_patcher_plugins_dict()

class PipelineRunner(QtCore.QRunnable):
    __slots__ = ("softcodes", "target", "filepack", "path_prefix", "paths", "cache_index", "archive_postaction", "signals")
    
    def __init__(self, target, filepack, path_prefix, paths, cache_index, softcodes, archive_postaction):
        super().__init__()
        self.target = target
        self.filepack = filepack
        self.path_prefix = path_prefix
        self.paths = paths
        self.cache_index = cache_index
        self.softcodes = softcodes
        self.archive_postaction = archive_postaction
        
        self.signals = StandardRunnableSignals()
        
    def run(self):
        try:
            self.signals.started.emit(self.target)
            patcher = patchers[self.filepack.packgroup](self.filepack, self.paths, self.path_prefix, self.softcodes, post_action=self.archive_postaction)
            patcher.execute()
            for pack_target in self.filepack.get_pack_targets():
                self.cache_index[pack_target] = self.filepack.hash
            self.signals.finished.emit()
        except Exception as e:
            self.signals.raise_exception.emit(e)


class PipelineCollection(QtCore.QObject):
    __slots__ = ("softcodes", "threadpool", "path_prefix", "archive_postaction", "paths", "build_pipelines", "message", "cache_index")
    
    finished = QtCore.pyqtSignal()
    exiting = QtCore.pyqtSignal()
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    raise_exception = QtCore.pyqtSignal(Exception)
    
    def __init__(self, threadpool, path_prefix, archive_postaction, paths, build_pipelines, message, cache_index, softcodes, parent=None):
        super().__init__(parent)
        self.softcodes = softcodes
        self.threadpool = threadpool
        self.path_prefix = path_prefix
        self.archive_postaction = archive_postaction
        self.paths = paths
        self.build_pipelines = build_pipelines
        self.message = message
        self.cache_index = cache_index
        self.curJob = ""
        self.pre_message = ""
        
        self.n_jobs = len(build_pipelines)
        self.completed_jobs = 0
        
        self.finished.connect(self.exiting)
        self.raise_exception.connect(self.exiting)
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.logCurrentJob)
        self.exiting.connect(self.timer.stop)
        
    def setLogInfo(self, curStep, maxSteps, depth):
        self.pre_message = ">>"*depth + " " + translate("Common", "[Step {curStep}/{maxSteps}] ").format(curStep=curStep, maxSteps=maxSteps)
        
    @QtCore.pyqtSlot(str)
    def jobStarted(self, msg):
        self.curJob = msg
        
    @QtCore.pyqtSlot()
    def logCurrentJob(self):
        self.updateLog.emit(translate("ModInstall","{current_step_message}{main_message}... ").format(current_step_message=self.pre_message,main_message=self.message)+ f"[{self.completed_jobs+1}/{self.n_jobs}] [{self.curJob}]")
        
    @QtCore.pyqtSlot()
    def checkIfCompleted(self):
        self.completed_jobs += 1
        if self.completed_jobs == self.n_jobs:
            self.updateLog.emit(translate("ModInstall","{current_step_message}{main_message}... Done. ").format(current_step_message=self.pre_message,main_message=self.message)+ f"[{self.completed_jobs}/{self.n_jobs}]")
            self.finished.emit()
        
    @QtCore.pyqtSlot(Exception)
    def handleException(self, e):
        self.threadpool.clear()
        self.threadpool.waitForDone()
        self.raise_exception.emit(e)
        
    @QtCore.pyqtSlot()
    def execute(self):
        try:
            self.log.emit(translate("ModInstall::Debug", "---pipeline build log message---"))
            self.timer.start(100)
            for filepack_target, filepack in self.build_pipelines.items():
                job = PipelineRunner(filepack_target, filepack, self.path_prefix, self.paths, self.cache_index, self.softcodes, self.archive_postaction)
                
                job.signals.started.connect(self.jobStarted)
                job.signals.raise_exception.connect(self.handleException)
                job.signals.finished.connect(self.checkIfCompleted)
                job.setAutoDelete(True)
                self.threadpool.start(job)
        except Exception as e:
            self.handleException(e)

class ArchivePipelineCollection(QtCore.QObject):
    __slots__ = ("archive", "ops", "ui", "softcodes", "threadpool", "pre_message", "cache_index")
    
    finished = QtCore.pyqtSignal()
    log = QtCore.pyqtSignal(str)
    updateLog = QtCore.pyqtSignal(str)
    raise_exception = QtCore.pyqtSignal(Exception)
    
    def __init__(self, threadpool, ops, ui, archive, softcodes, parent=None):
        super().__init__(parent)
        self.archive = archive
        self.ops = ops
        self.ui = ui
        self.softcodes = softcodes
        self.threadpool = threadpool
        self.cache_index = None
        self.pre_message = ""
    
    def setLogInfo(self, curStep, maxSteps, depth):
        self.pre_message = ">>"*depth + " " + translate("ModInstall", "[Step {curStep}/{maxSteps}] ").format(curStep=curStep, maxSteps=maxSteps)
    
    @QtCore.pyqtSlot()
    def execute(self):
        try:
            self.log.emit(translate("ModInstall", "{current_step_message}Building {archive_name} files...").format(current_step_message=self.pre_message, archive_name=self.archive.archive_name))
            self.cache_index = {}
            filepack_lookup = get_filepack_plugins_dict()
            
            graph = self.archive.build_graph
            
            group_pipes = []
            for group in list(graph.keys()):
                group_build_pipelines = graph[group]
                if not len(group_build_pipelines):
                    continue
                filepack = filepack_lookup[group]
                pcol = PipelineCollection(self.threadpool, sys.intern(self.archive.get_prefix()), self.archive.filepack_build_postaction, self.ops.paths, group_build_pipelines, filepack.get_build_message(), self.cache_index, self.softcodes, parent=self)
                pcol.log.connect(self.log)
                pcol.updateLog.connect(self.updateLog)
                pcol.raise_exception.connect(self.raise_exception.emit)
                group_pipes.append(pcol)
                
            n_gpipes = len(group_pipes)
            # Link the builders up to each other
            for i, (group_pipe, next_group_pipe) in enumerate(zip(group_pipes[:-1], group_pipes[1:])):
                def make_link(actor):
                    return lambda : actor.execute()
                group_pipe.finished.connect(make_link(next_group_pipe))
                group_pipe.raise_exception.connect(self.raise_exception)
                group_pipe.setLogInfo(i+1, n_gpipes, 2)
            group_pipes[-1].finished.connect(self.finalise_build)
            group_pipes[-1].raise_exception.connect(self.raise_exception)
            group_pipes[-1].setLogInfo(n_gpipes, n_gpipes, 2)
            
            # Start the pool; will signal this object when done
            group_pipes[0].execute()
        except Exception as e:
            self.raise_exception.emit(e)
            
    def finalise_build(self):
        with open(self.ops.paths.patch_cache_index_loc, 'r') as F:
            total_cache = json.load(F)
        for file, hashval in self.cache_index.items():
            total_cache[os.path.join(self.archive.get_prefix(), file)] = hashval
        with open(self.ops.paths.patch_cache_index_loc, 'w') as F:
            json.dump(total_cache, F, indent=2)

        self.finished.emit()