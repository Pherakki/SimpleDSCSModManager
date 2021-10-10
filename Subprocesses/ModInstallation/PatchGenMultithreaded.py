import csv
import os
import shutil

from PyQt5 import QtCore

from ModFiles.ScriptPatching import patch_scripts
from Utils.Multithreading import PoolChain
from Utils.Path import splitpath


class generate_patch_mt(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    
    def __init__(self, rules_dictionary, patchers, working_dir, resources_dir, threadpool, 
                 lockGuiFunc, releaseGuiFunc, messageLogFunc, updateMessageLogFunc):
        super().__init__()
        self.rules_dictionary = rules_dictionary
        self.patchers = patchers
        
        self.indices = None
        self.archives = None
        self.all_used_archives = None
        self.working_dir = working_dir
        self.resources_dir = resources_dir
        self.threadpool = threadpool

        self.lockGuiFunc = lockGuiFunc
        self.releaseGuiFunc = releaseGuiFunc
        self.messageLogFunc = messageLogFunc
        self.updateMessageLogFunc = updateMessageLogFunc
        
        self.runners = []

        
    def run(self):
        self.messageLogFunc("Generating patch...")
        
        for archive in self.all_used_archives:
            archive_patch_dir = os.path.relpath(os.path.join(self.working_dir, archive))
            if os.path.exists(archive_patch_dir):
                shutil.rmtree(archive_patch_dir)
            os.makedirs(archive_patch_dir)
            
        for patcher in self.patchers:
            cul_jobs = 0
            for index, archive_refs in zip(self.indices, self.archives):
                group = patcher.group
                if group in index:
                    n_jobs = sum([len(index[group]) for index in self.indices if group in index])
                    subindex = index[group]
                    n_subjobs = len(subindex)
                    runner = patch_pool_runner(self.rules_dictionary, subindex, self.working_dir, self.resources_dir,
                                               patcher, archive_refs,
                                               self.threadpool, cul_jobs, n_jobs,
                                               self.lockGuiFunc, self.releaseGuiFunc,
                                               self.messageLogFunc, self.updateMessageLogFunc,
                                               patcher.singular_msg, patcher.plural_msg)
                    cul_jobs += n_subjobs
                    self.runners.append(runner)
            
        self.poolchain = PoolChain(*self.runners)
        self.poolchain.finished.connect(self.finished.emit)
        self.poolchain.lockGui.connect(self.lockGuiFunc)
        self.poolchain.run()

            
                    
class patch_pool_runner(QtCore.QObject):
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()
    updateMessageLog = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    
    def __init__(self, rules_dictionary, subindex, working_dir, resources_dir, 
                 patcher, archives,
                 threadpool, cml_job_count, total_jobs,
                 lockGuiFunc, releaseGuiFunc,
                 messageLogFunc, updateMessageLogFunc,
                 singmessage, plurmessage):
        super().__init__()
        self.subindex = subindex
        self.working_dir = working_dir
        self.archives = archives
        self.resources_dir = resources_dir
        self.patcher = patcher
        self.threadpool = threadpool
        self.cml_job_count = cml_job_count
        self.total_jobs=total_jobs
        self.plurmessage = plurmessage
        self.singmessage = singmessage
        self.capsingmessage = singmessage[0].upper() + singmessage[1:]
        
        self.lockGuiFunc = lockGuiFunc
        self.releaseGuiFunc = releaseGuiFunc
        self.messageLogFunc = messageLogFunc
        self.updateMessageLogFunc = updateMessageLogFunc
        
        self.updateMessageLog.connect(self.updateMessageLogFunc)
        
        self.ncomplete = 0
        self.njobs = 0
        
        self.rules_dictionary = rules_dictionary
        
        
    def run(self):
        try:
            self.lockGui.emit()
            self.ncomplete = 0
            self.njobs = len(self.subindex)
            if not self.cml_job_count and self.njobs:
                self.messageLogFunc("")
            
            if not self.njobs:
                self.finished.emit()
                return
            
            for filepath, rules in self.subindex.items():
                used_archive = self.archives[filepath]
                job = self.patcher(self.rules_dictionary, os.path.join(self.working_dir, used_archive), 
                                   self.resources_dir, filepath, rules,
                                   self.update_messagelog, self.update_finished, self.raise_exception)
                self.threadpool.start(job)
            
        except Exception as e:
            self.raise_exception(e)
            
                
    def update_finished(self):
        if self.ncomplete == self.njobs:
            self.finished.emit()
                
    def update_messagelog(self, message):
        self.ncomplete += 1
        self.updateMessageLog.emit(f">>> {self.capsingmessage} {self.cml_job_count + self.ncomplete}/{self.total_jobs} [{message}]")
        
    def raise_exception(self, e):
        """
        THIS FUNCTION IS BUGGY
        MESSAGE FUNCTION DOESN'T WORK
        HANGS WHEN WAITING FOR THE THREADPOOL
        """
        self.threadpool.clear()
        self.updateMessageLog.emit(f"The following exception occured when {self.plurmessage}: {e}")
        self.threadpool.waitForDone()
        self.releaseGui.emit()

