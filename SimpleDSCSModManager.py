import ctypes
from datetime import datetime
import os
import platform
import stat
import sys
import traceback

from PyQt5 import QtCore, QtWidgets

from MainWindow import MainWindow

translate = QtCore.QCoreApplication.translate


def get_issue_tracker():
    return translate("Application", "{hyperlink_open}issue tracker{hyperlink_close}").format(hyperlink_open="<a href=\"https://github.com/Pherakki/SimpleDSCSModManager/issues\">", hyperlink_close="</a>")

def expectation_management_popup(win):
    msgBox = QtWidgets.QMessageBox(win)
    msgBox.setIcon(QtWidgets.QMessageBox.Information)
    msgBox.setWindowTitle(translate("Application::AlphaNotice", "Alpha Build Notice"))
    msgBox.setText(translate("Application::AlphaNotice", "This is an alpha build of SimpleDSCSModManager which has several incomplete features. You may run into bugs using some features of this program. If you encounter one, please check whether this bug is already an open issue at the {issue_tracker}, and if not, open a new issue.").format(issue_tracker=get_issue_tracker()),)

    msgBox.addButton(translate("Common", "OK"), QtWidgets.QMessageBox.AcceptRole)
    translate("Common", "Yes")
    translate("Common", "No")
    translate("Common", "Cancel")
    msgBox.exec_()
    
    
def warning_popup_UAC_error(win):
    msgBox = QtWidgets.QMessageBox(win)
    msgBox.setIcon(QtWidgets.QMessageBox.Warning)
    msgBox.setWindowTitle(translate("Application::UACPermissionsWarning", "Permissions Warning"))
    msgBox.setText(translate("Application::UACPermissionsWarning", "You are running SimpleDSCSModManager from<br><br>{path}<br><br>which appears to be a protected location. You may encounter errors when trying to install mods because of this. It is <b>highly recommended</b> to either <b>move SimpleDSCSModManager to a non-protected location</b>, or <b>run the program in Admin mode</b>.").format(path=win.directory))

    msgBox.addButton(translate("Common", "OK"), QtWidgets.QMessageBox.AcceptRole)
    translate("Common", "Yes")
    translate("Common", "No")
    translate("Common", "Cancel")
    msgBox.exec_()

def detect_savegames():
    # Make sure that %localappdata% expands correctly to the user's AppData/Local
    appdata_var = "%localappdata%"
    appdata_root = os.path.expandvars(appdata_var)
    if appdata_root == appdata_var:
        return None
    
    # Make sure the parent folder of the savegames directory exists
    root_path = os.path.join(appdata_root, 
                             "BANDAI NAMCO Entertainment", 
                             "Digimon Story Cyber Sleuth Complete Edition",
                             "Saved",
                             "SaveGames")
    if not os.path.isdir(root_path):
        return None
    
    # Name of the folder actually containing the gamedata seems to be non-constant...
    # So check that there is only one folder in the root_path that contains files with
    # the right names
    # First: Get all folders that have files with savegame names (only one should exist,
    # but maybe the user or a program has been fiddling around with the folder contents)
    subfolders = os.listdir(root_path)
    candidates = []
    for i, subfolder in enumerate(subfolders):
        if any(os.path.join(root_path, subfolder, binfile) for binfile in ["0000.bin", "slot_0000.bin",
                                                                           "0001.bin", "slot_0001.bin",
                                                                           "0002.bin", "slot_0002.bin"]):
            candidates.append(i)
            
    # If there is unambiguously only one potential savegame folder detected, return it
    if len(candidates) == 1:
        return os.path.join(root_path, subfolders[candidates[0]])
    else:
        return None
    
def check_windows_UAC_permissions(path):
    # Check if we're on Windows and if the User-Write permission is set on path
    if platform.system() == "Windows" and not (stat.S_IMODE(os.stat(path).st_mode) & stat.S_IWUSR):
        # Check if we're not an admin
        if not ctypes.windll.shell32.IsUserAnAdmin():
            # Might run into problems!
            return False
    return True

def CTD_popup(e, tb=None):
    # https://stackoverflow.com/a/16589622
    def full_stack():
        exc = sys.exc_info()[0]
        stack = traceback.extract_stack()[:-1]  # last one would be full_stack()
        if exc is not None:  # i.e. an exception is present
            del stack[-1]       # remove call of full_stack, the printed exception
                                # will contain the caught exception caller instead
        trc = 'Traceback (most recent call last):\n'
        stackstr = trc + ''.join(traceback.format_list(stack))
        if exc is not None:
             stackstr += '  ' + traceback.format_exc().lstrip(trc)
        return stackstr

    os.makedirs("logs", exist_ok=True)
    with open(os.path.join("logs", f"crashlog_{datetime.now().strftime('%Y_%m_%d-%H_%M_%S')}.txt"), "w") as F:
        if tb is None:
            F.write(full_stack())
        else:
            F.write(tb)
    buttons = QtWidgets.QMessageBox.Ok

    msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, 
                                   translate("Application::FatalErrorPopup", "Fatal Error"), 
                                   translate("Application::FatalErrorPopup", "SimpleDSCSModManager has encounted an issue and needs to close. The error is:<br><br>{error_message}<br><br>Please check whether this bug is already an open issue at the {issue_tracker}, and if not, open a new issue. Please include your crashlog.txt (found in the logs folder of SimpleDSCSModManager), and the <b><i>precise</i></b> step-by-step instructions required to reproduce the issue, alongside as much information as you can provide that may be relevant, including installed mods, and anything you have tried that <i>e.g.</i> prevents the bug or changes what happens. The more detail you can include, the easier it is to fix.").format(error_message=e, issue_tracker=get_issue_tracker()), buttons, None)
    msgBox.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.LinksAccessibleByMouse)
    msgBox.setTextFormat(QtCore.Qt.RichText)
    msgBox.exec_()
    
# Fix UI scaling for High DPI monitors
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    
if __name__ == '__main__':
    error_code = 0
    try:
        app = QtWidgets.QApplication([]) 
    
        app.setStyle("Fusion")
        win = MainWindow(app)
            
        def excepthook(exc_type, exc_value, exc_tb):
            win.close()
            tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            CTD_popup(exc_value, tb)
            QtWidgets.QApplication.quit()
            
        sys.excepthook = excepthook
        
        win.show()
        
        if not check_windows_UAC_permissions(win.directory):
            warning_popup_UAC_error(win)
            
        # Check for the exe in the most likely places
        recompute_paths = False
        if win.ops.paths.game_executable_loc is None:
            recompute_paths = True
        elif not os.path.isfile(win.ops.paths.game_executable_loc):
            recompute_paths = True
            
        if recompute_paths:
            success = False
            if os.path.isfile(os.path.join(gameroot := r"C:\Program Files (x86)\Steam\steamapps\common\Digimon Story Cyber Sleuth Complete Edition", r"app_digister\Digimon Story CS.exe")):
                win.ops.config_manager.set_game_loc(gameroot)
                success = True
            elif os.path.isfile(os.path.join(gameroot := r"C:\Games\steamapps\common\Digimon Story Cyber Sleuth Complete Edition", r"app_digister\Digimon Story CS.exe")):
                win.ops.config_manager.set_game_loc(gameroot)
                success = True
                
            if success:
                QtWidgets.QMessageBox.about(win, 
                                            translate("Application::GamePathDetectedPopup", "Game path detected"), 
                                            translate("Application::GamePathDetectedPopup", "Your game installation has been automatically detected at:\n\n{filepath}.").format(filepath=gameroot))

                
        win.ops.check_for_game_exe()
        #expectation_management_popup(win)
        error_code = app.exec_()
        
    except Exception as e:
        # raise e
        CTD_popup(e)
    finally:
        sys.exit(error_code)

       