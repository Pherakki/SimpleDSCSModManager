from PyQt5 import QtCore


class GenericThreadRunner(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    messageLog = QtCore.pyqtSignal(str)
    updateMessageLog = QtCore.pyqtSignal(str)
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()

    def __init__(self, func, initmessage, errormessage, parent=None):
        super().__init__(parent)
        self.func = func
        self.initmessage = initmessage
        self.errormessage = errormessage

    def run(self):
        try:
            self.lockGui.emit()
            self.messageLog.emit(self.initmessage)
            self.messageLog.emit("Operation successful.")
        except Exception as e:
            self.messageLog.emit(f"The following error occured when trying to {self.errormessage}: {e}")
            raise e
        finally:
            self.releaseGui.emit()
            self.finished.emit()
