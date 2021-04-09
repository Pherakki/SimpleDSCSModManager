import os
import shutil

from PyQt5 import QtCore


class MBEWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    
    def __init__(self, origin, destination, method, test, threadpool,
                 message_1, message_2,
                 messageLog, updateMessageLog, lockGui, releaseGui):
        super().__init__()
        
        self.origin = origin
        self.destination = destination
        self.replace_mode = origin == destination
        print(origin, destination, self.replace_mode)
        self.method = method
        self.test = test

        self.message_1 = message_1
        self.message_2 = message_2

        self.ncomplete = 0
        self.njobs = 0
        self.threadpool = threadpool
        self.messageLogFunc = messageLog
        self.updateMessageLogFunc = updateMessageLog
        self.lockGuiFunc = lockGui
        self.releaseGuiFunc = releaseGui

    def run(self):
        self.ncomplete = 0

        try:
            self.lockGuiFunc()
            if self.replace_mode:
                runnable = ReplaceMBERunnable
                os.makedirs(os.path.join(self.destination, 'temp'))
            else:
                runnable = MBERunnable
            files = [file for file in os.listdir(self.origin) if 
                     self.test(os.path.join(self.origin, file))]
            self.njobs = len(files)
            if self.njobs:
                self.messageLogFunc("")
            else:
                if self.replace_mode:
                    os.rmdir(os.path.join(self.destination, 'temp'))
                self.releaseGuiFunc()
                self.finished.emit()
                return
            
            for file in files:
                job = runnable(file, self.origin, self.destination,
                               self.method,
                               self.update_messagelog,
                               self.update_finished,
                               self.raise_exception)
                job.signals.exception.connect(self.raise_exception)
                self.threadpool.start(job)
        except Exception as e:
            self.raise_exception(e)
            
    def update_finished(self):
        if self.ncomplete == self.njobs:
            if self.replace_mode:
                os.rmdir(os.path.join(self.destination, 'temp'))
            self.releaseGuiFunc()
            self.finished.emit()
                
    def update_messagelog(self, message):
        self.ncomplete += 1
        self.updateMessageLogFunc(f"{self.message_1} MBE {self.ncomplete}/{self.njobs} [{message}]")
        
    def raise_exception(self, exception):
        try:
            raise exception
        except ScriptHandlerError as e:
            self.threadpool.clear()
            self.threadpool.waitForDone()
            self.messageLogFunc(f"The following exception occured when {self.message_2} {e.args[1]}: {e.args[0]}")
            raise e.args[0]
        except Exception as e:
            self.threadpool.clear()
            self.threadpool.waitForDone()
            self.messageLogFunc(f"The following exception occured when {self.message_2} MBEs: {e}")
            raise e
        finally:
            self.releaseGuiFunc()


class MBERunnable(QtCore.QRunnable):
    def __init__(self, archive, origin, destination, method, update_messagelog, update_finished, raise_exception):
        super().__init__()
        self.archive = archive
        self.origin = origin
        self.destination = destination
        self.method = method
        # Signals won't work for some reason unless there's a reference to the
        # functions that the signals are connected to in the runnable
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        self.signals = Signals()
        
    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.method(os.path.join(self.origin, self.archive),
                        os.path.join(self.destination, self.archive))
            # This should be a signal, but first you'll need to implement a
            # thread-safe messaging queue to prevent this overwriting the
            # error messages from the exception
            self.update_messagelog(self.filepath)
            self.update_finished()
        except Exception as e:
            self.signals.exception.emit(ScriptHandlerError(e, self.archive))


class ReplaceMBERunnable(QtCore.QRunnable):
    def __init__(self, archive, origin, destination, method, update_messagelog, update_finished, raise_exception):
        super().__init__()
        self.archive = archive
        self.origin = origin
        self.destination = destination
        self.method = method
        # Signals won't work for some reason unless there's a reference to the
        # functions that the signals are connected to in the runnable
        self.update_messagelog = update_messagelog
        self.update_finished = update_finished
        self.raise_exception = raise_exception
        self.signals = Signals()
        
    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.method(self.archive,
                        self.origin,
                        os.path.join(self.destination, 'temp'))
            rm_dir = os.path.join(self.origin, self.archive)
            if os.path.isdir(rm_dir):
                shutil.rmtree(rm_dir)
            else:
                os.remove(rm_dir)
            os.rename(os.path.join(self.destination, 'temp', self.archive),
                      os.path.join(self.destination, self.archive))
            # This should be a signal, but first you'll need to implement a
            # thread-safe messaging queue to prevent this overwriting the
            # error messages from the exception
            self.update_messagelog(self.archive)
            self.update_finished()
        except Exception as e:
            self.signals.exception.emit(ScriptHandlerError(e, self.archive))


class Signals(QtCore.QObject):
    exception = QtCore.pyqtSignal(Exception)
    update_messagelog = QtCore.pyqtSignal(str)
    update_finished = QtCore.pyqtSignal()


class ScriptHandlerError(Exception):
    pass
