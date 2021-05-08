import os

from PyQt5 import QtCore
from tools.dscstools import DSCSTools
from .DSCSToolsArchiveWorker import ArchiveRunnable, ScriptHandlerError

# Make DumpArchiveWorker a subclass of this which passes the archive info to the file_list...
class DumpFileWorker(QtCore.QObject):
    updateMessageLog = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, file_list, destination, threadpool,
                 messageLog, updateMessageLog, lockGui, releaseGui):
        super().__init__()
        self.file_list = file_list
        self.destination = destination

        self.ncomplete = 0
        self.njobs = 0
        self.threadpool = threadpool
        self.messageLogFunc = messageLog
        self.updateMessageLogFunc = updateMessageLog
        self.lockGuiFunc = lockGui
        self.releaseGuiFunc = releaseGui
        
        self.updateMessageLog.connect(updateMessageLog)

    def run(self):
        self.ncomplete = 0
        self.messageLogFunc("")

        try:
            self.lockGuiFunc()

            self.njobs = len(self.file_list)
            for file, archive_path in self.file_list.items():
                job = ArchiveRunnable(archive_path, self.destination,
                                      file,
                                      self.update_messagelog,
                                      self.update_finished,
                                      self.raise_exception)
                job.signals.exception.connect(self.raise_exception)
                self.threadpool.start(job)
        except Exception as e:
            self.raise_exception(e)
            
    def update_finished(self):
        if self.ncomplete == self.njobs:
            self.releaseGuiFunc()
            self.finished.emit()
                
    def update_messagelog(self, message):
        self.ncomplete += 1
        self.updateMessageLog.emit(f"Extracting file {self.ncomplete}/{self.njobs} [{message}]")
        
    def raise_exception(self, exception):
        try:
            raise exception
        except ScriptHandlerError as e:
            self.threadpool.clear()
            self.threadpool.waitForDone()
            self.messageLogFunc(f"The following exception occured when extracting {e.args[1]}: {e.args[0]}")
            raise e.args[0]
        except Exception as e:
            self.threadpool.clear()
            self.threadpool.waitForDone()
            self.messageLogFunc(f"The following exception occured when extracting {self.archive}: {e}")
            raise e
        finally:
            self.releaseGuiFunc()
