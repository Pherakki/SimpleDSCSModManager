import os
import platform
import subprocess
import sys

from PyQt5 import QtCore


class ProcLauncher(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    clean_up = QtCore.pyqtSignal()
    exiting = QtCore.pyqtSignal()
    raise_exception = QtCore.pyqtSignal(Exception)
    
    def __init__(self, ops, ui, parent=None):
        super().__init__(parent)
        self.ops = ops
        self.ui = ui
        self.thread = QtCore.QThread()

        # Link final step to the thread destructor
        self.exiting.connect(self.ui.enable_gui)
        self.finished.connect(self.clean_up.emit)
        self.raise_exception.connect(self.clean_up.emit)
        self.raise_exception.connect(parent.raise_exception.emit)
        self.clean_up.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.exiting.emit)
        
    def launch_game(self):
        try:
            self.ui.disable_gui()
            gl = GameLauncher(self.ops.paths, parent=self)
            gl.moveToThread(self.thread)
            gl.finished.connect(self.deleteLater)
            gl.finished.connect(self.finished.emit)
            gl.raise_exception.connect(self.raise_exception)
            gl.execute()
        except Exception as e:
            self.raise_exception.emit(e)

class GameLauncher(QtCore.QObject):
    success = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    raise_exception = QtCore.pyqtSignal(Exception)
    
    def __init__(self, paths, parent=None):
        super().__init__(parent)
        self.paths = paths  
        self.success.connect(self.finished.emit)
        self.raise_exception.connect(self.finished.emit)
    
    def execute(self):
        try:
            # https://stackoverflow.com/a/42499675
            kwargs = {}
            if platform.system() == 'Windows':
                kwargs.update(creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True)  
            elif sys.version_info < (3, 2):  # assume posix
                kwargs.update(preexec_fn=os.setsid)
            else:  # Python 3.2+ and Unix
                kwargs.update(start_new_session=True)
            
            subprocess.Popen([self.paths.game_executable_loc], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.paths.game_app_digister_loc, **kwargs)
            # Probably gonna need the version below if the manager is set to close on game launch
            # subprocess.Popen([self.game_executable_loc], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.game_app_digister_loc, **kwargs)

            self.success.emit()
        except Exception as e:
            self.raise_exception.emit(e)