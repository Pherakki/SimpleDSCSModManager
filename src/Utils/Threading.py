from PyQt5 import QtCore


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    raise_exception = QtCore.pyqtSignal(Exception)
    
    def __init__(self, func, args, kwargs):
        super().__init__(None)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    @QtCore.pyqtSlot()
    def execute(self):
        try:
            self.func(*self.args, **self.kwargs)
            self.finished.emit()
        except Exception as e:
            self.raise_exception.emit(e)


class ThreadRunner(QtCore.QObject):
    __slots__ = ("thread", "worker")
    def __init__(self, parent):
        super().__init__(parent)
    
    def runInThread(self, parent, final_action, func, *args, **kwargs):
        self.thread = QtCore.QThread()
        self.worker = Worker(func, args, kwargs)
        self.worker.moveToThread(self.thread)
        self.worker.raise_exception.connect(parent.raise_exception)
        self.worker.finished.connect(final_action)
        
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.started.connect(self.worker.execute)
        
        self.thread.start()

class UIAccessWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    raise_exception = QtCore.pyqtSignal(Exception)
    updateLog = QtCore.pyqtSignal(str)
    log = QtCore.pyqtSignal(str)
    enable_gui = QtCore.pyqtSignal()
    disable_gui = QtCore.pyqtSignal()
    
    def __init__(self, func, args, kwargs):
        super().__init__(None)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    @QtCore.pyqtSlot()
    def execute(self):
        try:
            self.func(self.log, self.updateLog, self.enable_gui, *self.args, **self.kwargs)
            self.finished.emit()
        except Exception as e:
            self.raise_exception.emit(e)


class UIAccessThreadRunner(QtCore.QObject):
    __slots__ = ("thread", "worker")
    def __init__(self, parent):
        super().__init__(parent)
    
    def runInThread(self, ui, parent, final_action, func, *args, **kwargs):
        self.thread = QtCore.QThread()
        self.worker = UIAccessWorker(func, args, kwargs)
        self.worker.moveToThread(self.thread)
        self.worker.raise_exception.connect(parent.raise_exception)
        self.worker.finished.connect(final_action)
        self.worker.log.connect(ui.log)
        self.worker.updateLog.connect(ui.updateLog)
        self.worker.enable_gui.connect(ui.enable_gui)
        self.worker.disable_gui.connect(ui.disable_gui)
        
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.started.connect(self.worker.execute)
        
        self.thread.start()
