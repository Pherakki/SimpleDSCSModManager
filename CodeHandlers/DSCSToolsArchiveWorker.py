import os

from PyQt5 import QtCore
from tools.dscstools import DSCSTools


class DumpArchiveWorkerThread(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    updateMessageLog = QtCore.pyqtSignal(str)
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()
    
    def __init__(self, archive, source_folder, dump_folder, dscstools_handler, extract_method, parent=None):
        super().__init__(parent)
        self.archive = archive
        self.source_folder = source_folder
        self.dump_folder = dump_folder
        self.dscstools_handler = dscstools_handler
        self.extract_method = extract_method
        
    def run(self):
        try:
            self.lockGui.emit()
            self.messageLog.emit(f"Extracting {self.dscstools_handler.base_archive_name(self.archive)} to {self.dump_folder}...")
            self.extract_method(self.archive, self.source_folder, self.dump_folder)
            self.messageLog.emit("Extraction successful.")
        except Exception as e:
            self.messageLog.emit(f"The following error occured when trying to extract {self.dscstools_handler.base_archive_name(self.archive)}: {e}")
            raise e
        finally:
            self.releaseGui.emit()
            self.finished.emit()


class DumpArchiveWorker(QtCore.QObject):
    updateMessageLog = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, origin, destination, threadpool,
                 messageLog, updateMessageLog, lockGui, releaseGui):
        super().__init__()
        self.archive = os.path.split(origin)[-1]
        self.origin = origin
        self.destination = destination

        self.ncomplete = 0
        self.njobs = 0
        self.threadpool = threadpool
        self.messageLogFunc = messageLog
        self.lockGuiFunc = lockGui
        self.releaseGuiFunc = releaseGui
        
        self.updateMessageLog.connect(updateMessageLog)

    def run(self):
        self.ncomplete = 0
        self.messageLogFunc("")

        try:
            self.lockGuiFunc()
            # The first file is '.\x00\x00\x00\x00', which we don't want to process...
            fileinfos = DSCSTools.getArchiveInfo(self.origin).Files

            assert fileinfos[0].FileName == '.\x00\x00\x00\x00', "First filename was not the expected value of \'.\\x00\\x00\\x00\\x00\'."
            fileinfos = fileinfos[1:]
            self.njobs = len(fileinfos)
            for file in fileinfos:
                job = ArchiveRunnable(self.origin, self.destination,
                                     file.FileName,
                                     self.update_messagelog,
                                     self.update_finished,
                                     self.raise_exception)
                job.signals.exception.connect(self.raise_exception)
                job.signals.update_messagelog.connect(self.update_messagelog)
                job.signals.update_finished.connect(self.update_finished)
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


class ArchiveRunnable(QtCore.QRunnable):
    def __init__(self, origin, destination, filepath, update_messagelog, update_finished, raise_exception):
        super().__init__()
        self.archive = os.path.split(origin)[-1]
        self.origin = origin
        self.destination = destination
        self.filepath = filepath
        # Signals won't work for some reason unless there's a reference to the
        # functions that the signals are connected to in the runnable
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        self.signals = Signals()
        
    @QtCore.pyqtSlot()
    def run(self):
        try:
            DSCSTools.extractMDB1File(self.origin, self.destination, self.filepath)
            # This should be a signal, but first you'll need to implement a
            # thread-safe messaging queue to prevent this overwriting the
            # error messages from the exception
            self.update_messagelog(self.filepath)
            self.update_finished()
        except Exception as e:
            self.signals.exception.emit(ScriptHandlerError(e, self.archive))


class Signals(QtCore.QObject):
    exception = QtCore.pyqtSignal(Exception)
    update_messagelog = QtCore.pyqtSignal(str)
    update_finished = QtCore.pyqtSignal()


class ScriptHandlerError(Exception):
    pass
