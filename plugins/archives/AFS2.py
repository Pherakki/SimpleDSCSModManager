import os
import shutil

from PyQt5 import QtCore

from CoreOperations.PluginLoaders.ArchivesPluginLoader import BaseArchiveType
from sdmmlib.dscstools import DSCSTools

translate = QtCore.QCoreApplication.translate
    
class AFS2(BaseArchiveType):
    __slots__ = ("archive_name", "backups", "build_graph", "build_files", "paths", "log", "updateLog")
    group = "AFS2"
    
    def __init__(self, archive_name, ops):
        super().__init__()
        self.archive_name = archive_name
        self.backups = ops.backups_manager
        self.paths = ops.paths
        self.build_graph = {}
        self.build_files = []
        self.log = None
        self.updateLog = None
        
    def get_prefix(self):
        return self.archive_name
    
    @staticmethod
    def filepack_build_postaction(src, dst):
        pass
    
    def get_resource_archive(self, build_dir):
        self.updateLog(translate("ArchiveTypes::AFS2", "Packing AFS2 {archive_name}... unpacking base archive to build directory...").format(archive_name=self.archive_name))
        
        build_loc = os.path.join(build_dir, self.archive_name)
        game_source_file = os.path.join(self.paths.game_resources_loc, f"{self.archive_name}.steam.mvgl")
        game_source_file = self.backups.get_backed_up_filepath_if_exists(game_source_file, self.paths.game_resources_loc, self.paths.backups_loc)

        DSCSTools.extractAFS2(game_source_file, build_loc, False)

        
    def pack(self):
        build_dir = self.paths.patch_build_loc
        cache_dir = self.paths.patch_cache_loc
        dst = os.path.join(self.paths.game_resources_loc, f"{self.archive_name}.steam.mvgl")
        
        archive_build_dir = os.path.join(build_dir, self.archive_name)
        archive_cache_dir = os.path.join(cache_dir, self.archive_name)
        
        self.log(translate("ArchiveTypes::AFS2", "Packing AFS2 {archive_name}...").format(archive_name=self.archive_name))
        self.get_resource_archive(archive_build_dir)
        
        self.updateLog(translate("ArchiveTypes::AFS2", "Packing AFS2 {archive_name}... copying mod files to build directory...").format(archive_name=self.archive_name))
        for pack_target in self.cached_pack_targets:
                pack_loc = os.path.join(archive_cache_dir, pack_target)
                build_pack_loc = os.path.join(archive_build_dir, pack_target)
                os.makedirs(os.path.split(build_pack_loc)[0], exist_ok=True)
                shutil.copy2(pack_loc, build_pack_loc) # os.link?
        for packtype, packtype_data in self.build_graph.items():
            for pack_name, pack in packtype_data.items():
                for pack_target in pack.get_pack_targets():
                    pack_loc = os.path.join(archive_cache_dir, pack_target)
                    build_pack_loc = os.path.join(archive_build_dir, pack_target)
                    os.makedirs(os.path.split(build_pack_loc)[0], exist_ok=True)
                    shutil.copy2(pack_loc, build_pack_loc) # os.link?
                    
        if self.archive_name in self.backups.default_AFS2s:
            self.updateLog(translate("ArchiveTypes::AFS2", "Backing up AFS2 {archive_name}...").format(archive_name=self.archive_name))
            self.backups.try_back_up_file(dst, self.paths.game_resources_loc, self.paths.backups_loc)
        self.updateLog(translate("ArchiveTypes::AFS2", "Packing AFS2 {archive_name}...").format(archive_name=self.archive_name))
        DSCSTools.packAFS2(archive_build_dir, dst)
        # Check that something unexpected and terrible didn't happen to the archive_build_dir path
        assert (os.path.split(archive_build_dir)[1] == self.archive_name) and (len(self.archive_name) > 1), translate("ArchiveTypes::AFS2", "Something critically bad happened to the archive packing directory - aborting.")
        shutil.rmtree(archive_build_dir)
        self.updateLog(translate("ArchiveTypes::AFS2", "Packing AFS2 {archive_name}... Done.").format(archive_name=self.archive_name))
