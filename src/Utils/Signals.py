from PyQt5 import QtCore

            
class StandardRunnableSignals(QtCore.QObject):
    started = QtCore.pyqtSignal(str)
    raise_exception = QtCore.pyqtSignal(Exception)
    finished = QtCore.pyqtSignal()
