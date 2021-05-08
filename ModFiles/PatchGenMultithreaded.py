import csv
import os
import shutil

from PyQt5 import QtCore

from .ScriptPatching import patch_scripts
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
        for patcher in self.patchers:
            cul_jobs = 0
            for index in self.indices:
                group = patcher.group
                if group in index:
                    n_jobs = sum([len(index[group]) for index in self.indices if group in index])
                    subindex = index[group]
                    n_subjobs = len(subindex)
                    runner = patch_pool_runner(self.rules_dictionary, subindex, self.working_dir, self.resources_dir,
                                               patcher, self.threadpool, cul_jobs, n_jobs,
                                               self.lockGuiFunc, self.releaseGuiFunc,
                                               self.messageLogFunc, self.updateMessageLogFunc,
                                               patcher.singular_msg, patcher.plural_msg)
                    cul_jobs += n_subjobs
                    self.runners.append(runner)
            
        self.poolchain = PoolChain(*self.runners)
        self.poolchain.finished.connect(self.finished.emit)
        self.poolchain.run()

            
                    
class patch_pool_runner(QtCore.QObject):
    updateMessageLog = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    
    def __init__(self, rules_dictionary, subindex, working_dir, resources_dir, 
                 patcher,
                 threadpool, cml_job_count, total_jobs,
                 lockGuiFunc, releaseGuiFunc,
                 messageLogFunc, updateMessageLogFunc,
                 singmessage, plurmessage):
        super().__init__()
        self.subindex = subindex
        self.working_dir = working_dir
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
        
        
    @QtCore.pyqtSlot()   
    def run(self):
        try:
            self.lockGuiFunc()
            self.ncomplete = 0
            self.njobs = len(self.subindex)
            if not self.cml_job_count and self.njobs:
                self.messageLogFunc("")
            
            if not self.njobs:
                self.finished.emit()
                return
            
            for filepath, rules in self.subindex.items():
                job = self.patcher(self.rules_dictionary, self.working_dir, self.resources_dir, filepath, rules,
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
        
    def raise_exception(self, exception):
        try:
            raise exception
        # except ScriptHandlerError as e:
        #     self.threadpool.clear()
        #     self.threadpool.waitForDone()
        #     self.messageLogFunc(f"The following exception occured when {self.singmessage} {e.args[1]}: {e.args[0]}")
        #     raise e.args[0]
        except Exception as e:
            self.threadpool.clear()
            self.threadpool.waitForDone()
            self.messageLogFunc(f"The following exception occured when {self.plurmessage}: {e}")
            raise e
        finally:
            self.releaseGuiFunc()

