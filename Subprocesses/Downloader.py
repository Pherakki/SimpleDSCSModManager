import math
import os
import shutil
import urllib.request
import zipfile

from PyQt5 import QtCore

class DSCSToolsDownloader(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    emitTag = QtCore.pyqtSignal(str)
    messageLog = QtCore.pyqtSignal(str)
    updateMessageLog = QtCore.pyqtSignal(str)
    lockGui = QtCore.pyqtSignal()
    releaseGui = QtCore.pyqtSignal()
    
    
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.tag = None
        
    def run(self):
        try:
            self.lockGui.emit()
            containing_folder = os.path.join(*os.path.split(self.path)[:-1])
            for iter_item in os.listdir(containing_folder):
                item = os.path.join(containing_folder, iter_item)
                if os.path.isfile(item):
                    os.remove(item)
                elif os.path.isdir(item):
                    shutil.rmtree(item)
                else:
                    raise Exception("Encountered neither a file nor directory:", item)

            url, tag = self.get_dscstools_download_url()
            with urllib.request.urlopen(url) as req, open(self.path, 'ab') as f:
                chunk_size = 1024 * 256
                total_size = int(req.info()['Content-Length'])

                chunk = None
                total_read = 0
                num_packets = int(math.ceil(total_size / chunk_size))
                packet_number = 1
                self.messageLog.emit("")  # Set up an empty log entry to be overwritten
                #I think this should request 256kB packets?!
                while chunk != b'':
                    chunk = req.read(chunk_size)
                    f.write(chunk)
                    
                    progress = math.ceil(20 * packet_number / num_packets)

                    filled = '-'*(progress-1)
                    empty = '  '*(20-progress)
                    self.updateMessageLog.emit(f"Downloading DSCSTools... [{filled}|{empty}]")
                    
                    total_read += len(chunk)
                    packet_number += 1

                    
                    
            with zipfile.ZipFile(self.path, 'r') as f:
                f.extractall(containing_folder)
            
            self.messageLog.emit("DSCSTools downloaded successfully.")
            self.emitTag.emit(tag)
        except Exception as e:
            self.messageLog.emit(f"The following error occured when trying to download DSCSTools: {e}")
            raise e
        finally:
            self.releaseGui.emit()
            self.finished.emit()
            
    ################################
    # DSCSTools Download Functions #
    ################################
    @staticmethod
    def get_dscstools_tag():
        dscstools_url = r"https://github.com/SydMontague/DSCSTools/releases/latest"
        
        if dscstools_url[:19] != r"https://github.com/":
            raise ValueError("Download URL is not on GitHub.")
        url = urllib.request.urlopen(dscstools_url).geturl()
        return url.split('/')[-1]
        
    def get_dscstools_download_url(self):
        tag = self.get_dscstools_tag()
        return rf"https://github.com/SydMontague/DSCSTools/releases/download/{tag}/DSCSTools_{tag}-win64-shared.zip", tag

