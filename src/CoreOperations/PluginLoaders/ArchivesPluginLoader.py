import inspect
import os
import shutil

from PyQt5 import QtCore

from src.CoreOperations.PluginLoaders.PluginLoad import load_sorted_plugins_in

translate = QtCore.QCoreApplication.translate

def get_archivetype_plugins():
    plugin_dir = os.path.join('plugins', 'archives')
    
    return [patcher for patcher in [*load_sorted_plugins_in(plugin_dir, lambda x: issubclass(x, BaseArchiveType) if inspect.isclass(x) else False), LooseFiles]]


def get_archivetype_plugins_dict():
    return {archive_t.group: archive_t for archive_t in get_archivetype_plugins()}


class BaseArchiveType:
    __slots__ = ("log", "updateLog", "cached_pack_targets")
    
    def __init__(self):
        self.log = None
        self.updateLog = None
        self.cached_pack_targets = []
    
    def get_prefix(self):
        raise NotImplementedError()

    def filepack_build_postaction(self, src, dst):
        raise NotImplementedError()
    
    def pack(self, build_dir, cache_dir, dst):
        raise NotImplementedError()
        
    def setLogs(self, log, updateLog):
        self.log = log
        self.updateLog = updateLog

class LooseFiles(BaseArchiveType):
    __slots__ = ("archive_name", "backups", "build_graph", "build_files", "paths", "log", "updateLog")
    group = "LooseFiles"
    
    def __init__(self, archive_name, ops):
        super().__init__()
        self.archive_name = archive_name
        self.build_graph = {}
        self.build_files = []
        self.backups = ops.backups_manager
        self.paths = ops.paths
        self.log = None
        self.updateLog = None
        
    def get_prefix(self):
        return ""
    
    @staticmethod
    def filepack_build_postaction(src, dst):
        pass
    
    
    def __copy_pack_target(self, pack_target):
        cache_dir = self.paths.patch_cache_loc
        backup_dir = self.paths.backups_loc
        dst = os.path.join(self.paths.game_resources_loc, pack_target)
        file_target = os.path.join(cache_dir, pack_target)
        # Make backup if it's needed
        if pack_target in self.backups.default_misc_files:
            backup_target = os.path.join(backup_dir, pack_target)
            os.makedirs(os.path.split(backup_target)[0], exist_ok=True)
            shutil.copy2(dst, backup_target)
        os.makedirs(os.path.split(dst)[0], exist_ok=True)
        shutil.copy2(file_target, dst)
    
    def pack(self):
        """
        REPLACE COPIES WITH OS.LINK IF IT WORKS OK
        """
        self.log(translate("ArchiveTypes::LooseFiles", "Copying loose files..."))
        for pack_target in self.cached_pack_targets:
            self.__copy_pack_target(pack_target)
        for packtype, packtype_data in self.build_graph.items():
            for pack_name, pack in packtype_data.items():
                for pack_target in pack.get_pack_targets():
                    self.__copy_pack_target(pack_target)
