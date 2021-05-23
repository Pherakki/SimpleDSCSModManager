from PyQt5 import QtCore

class PoolChain(QtCore.QObject):
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    
    def __init__(self, *pools):
        super().__init__()
        self.pools = pools
        for pool_1, pool_2 in zip(self.pools, self.pools[1:]):
            pool_1.finished.connect(pool_2.run)
        self.pools[-1].finished.connect(self.finished.emit)
        
    def run(self):
        self.pools[0].run()
        self.lockGui.emit()
