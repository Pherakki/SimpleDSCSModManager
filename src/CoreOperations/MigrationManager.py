import os
from PyQt5 import QtCore, QtGui, QtWidgets

translate = QtCore.QCoreApplication.translate

class PathCollection:
    __slots__ = ("mods_path",
                 "profiles_path",
                 "cache_path",
                 "themes_path",
                 "config_path")
    
    def __init__(self, mods_path, profiles_path, cache_paths, themes_path, config_path):
        self.mods_path = mods_path
        self.profiles_path = profiles_path
        self.cache_paths = cache_paths
        self.themes_path = themes_path
        self.config_path = config_path

VERSIONED_PATHS = {
    0.1: PathCollection
    (
        "mods", 
        "profiles",
        "output", 
        "themes", 
        os.path.join("config", os.path.extsep.join("config", "json"))
    ),
    0.2: PathCollection
    (
        os.path.join("data", "mods"), 
        os.path.join("data", "profiles"), 
        os.path.join("data", "output"), 
        os.path.join("data", "themes"),
        os.path.join("data", "config", os.path.extsep.join("config", "json"))
    )
}

class MigrationPopup(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Migrate Data")
        
        qbtn = QtWidgets.QDialogButtonBox.Yes | QtWidgets.QDialogButtonBox.No

        self.buttons = QtWidgets.QDialogButtonBox(qbtn)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        message = QtWidgets.QLabel(translate("UI::MigrationManager::MigrationPopup",
            "You appear to be launching this version of SimpleDSCSModManager for the first time.<br>"
            "<b>Do you want to migrate data from a previous version of SimpleDSCSModManager?</b><br>"
            "If you have mods active on your current save games, <br>"
            "not migrating carries a high risk of breaking your save games."))
        message.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)
        
def identify_version(directory, paths):
    source_file = os.path.join(paths.config_loc, "VERSION.txt")
    

def migrate_data_if_authorised():
    if (MigrationPopup().exec_()):
        pass