import os
import webbrowser

from PyQt5 import QtCore

translate = QtCore.QCoreApplication.translate

class PathManager:
    def __init__(self, modmanager_directory, config_manager):
        modmanager_directory = os.path.abspath(modmanager_directory)
        
        self.__game_loc = None
        self.__game_resources_loc    = None
        self.__game_plugins_loc      = None
        self.__game_app_digister_loc = None
        self.__game_executable_loc   = None
        self.__backups_loc           = None
                
        self.__modmanager_directory  = modmanager_directory
        
        self.__config_loc              = self.__clean_path(os.path.join(modmanager_directory, "config"))
        self.__localisations_loc       = os.path.normpath(os.path.join(modmanager_directory, "languages"))
        self.__localisations_names_loc = os.path.normpath(os.path.join(self.__localisations_loc, "LangNames.json"))
        self.__logs_loc                = self.__clean_path(os.path.join(modmanager_directory, "logs"))
        self.__mods_loc                = self.__clean_path(os.path.join(modmanager_directory, "mods"))
        self.__output_loc              = self.__clean_path(os.path.join(modmanager_directory, "output"))
        self.__profiles_loc            = self.__clean_path(os.path.join(modmanager_directory, "profiles"))
        self.__resources_loc           = self.__clean_path(os.path.join(modmanager_directory, "resources"))
        self.__softcodes_loc           = self.__clean_path(os.path.join(modmanager_directory, "softcodes"))
        self.__compiler_loc            = self.__clean_path(os.path.join(modmanager_directory, "tools", "squirrel"))

        self.__patch_build_loc         = self.__clean_path(os.path.join(self.__output_loc, "build"))
        self.__patch_cache_loc         = self.__clean_path(os.path.join(self.__output_loc, "cache"))
        self.__softcode_cache_loc      = self.__clean_path(os.path.join(self.__output_loc, "softcode_cache"))
        self.__patch_cache_index_loc   = self.__clean_path(os.path.join(self.__output_loc, "CACHE_INDEX.json"))
        self.__base_resources_loc      = self.__clean_path(os.path.join(self.__resources_loc, "base_resources"))
        
        
        config_manager.init_with_paths(self)

        os.makedirs(self.__config_loc, exist_ok=True)
        os.makedirs(self.__mods_loc, exist_ok=True)
        os.makedirs(self.__output_loc, exist_ok=True)
        os.makedirs(self.__profiles_loc, exist_ok=True)
        os.makedirs(self.__resources_loc, exist_ok=True)
        os.makedirs(self.__softcodes_loc, exist_ok=True)
        os.makedirs(self.__compiler_loc, exist_ok=True)
        
        os.makedirs(self.__patch_build_loc, exist_ok=True)
        os.makedirs(self.__patch_cache_loc, exist_ok=True)
        os.makedirs(self.__base_resources_loc, exist_ok=True)
        if not os.path.exists(self.__patch_cache_index_loc):
            with open(self.__patch_cache_index_loc, 'w') as F:
                F.write('{}')

    @staticmethod
    def __standard_error_message(msg):
        return translate("PathManager", "{path} does not exist!").format(path=msg)

    @property
    def syd_patreon(self):
        return r'https://www.patreon.com/sydmontague'
    
    def open_patreon(self):
        webbrowser.open_new_tab(self.syd_patreon)
    
    @property
    def discord_invite(self):
        return r'https://discord.gg/cb5AuxU6su'
    
    def _set_game_loc(self, path):
        self.__game_loc = path
        self.compute_game_paths()
        
    @staticmethod
    def __clean_path(path):
        return os.path.normpath(os.path.realpath(path))
        
    @staticmethod
    def __check_path_is_valid(path, root):
        assert path.startswith(root), translate("PathManager", "{path} is not a subitem of {root}!").format(path=path, root=root)
        
    def __safe_path_return(self, path, root):
        path = self.__clean_path(path)
        self.__check_path_is_valid(path, root)
        return path
        
    @property
    def mm_root(self):
        return self.__modmanager_directory
    
    @property
    def config_loc(self):
        return self.__safe_path_return(self.__config_loc, self.mm_root)
    
    @property
    def compiler_loc(self):
        return self.__safe_path_return(self.__compiler_loc, self.mm_root)
        
    @property
    def logs_loc(self):
        return self.__safe_path_return(self.__logs_loc, self.mm_root)
    
    @property
    def localisations_loc(self):
        return self.__safe_path_return(self.__localisations_loc, self.mm_root)
    
    @property
    def localisations_names_loc(self):
        return self.__safe_path_return(self.__localisations_names_loc, self.mm_root)
        
    @property
    def mods_loc(self):
        return self.__safe_path_return(self.__mods_loc, self.mm_root)
        
    @property
    def output_loc(self):
        return self.__safe_path_return(self.__output_loc, self.mm_root)
        
    @property
    def patch_build_loc(self):
        return self.__safe_path_return(self.__patch_build_loc, self.mm_root)
    
    @property
    def patch_cache_loc(self):
        return self.__safe_path_return(self.__patch_cache_loc, self.mm_root)
    
    @property
    def softcode_cache_loc(self):
        return self.__safe_path_return(self.__softcode_cache_loc, self.mm_root)
    
    @property
    def patch_cache_index_loc(self):
        return self.__safe_path_return(self.__patch_cache_index_loc, self.mm_root)
        
    @property
    def profiles_loc(self):
        return self.__safe_path_return(self.__profiles_loc, self.mm_root)
    
    @property
    def resources_loc(self):
        return self.__safe_path_return(self.__resources_loc, self.mm_root)
    
    @property
    def softcodes_loc(self):
        return self.__safe_path_return(self.__softcodes_loc, self.mm_root)
    
    @property
    def base_resources_loc(self):
        return self.__safe_path_return(self.__base_resources_loc, self.mm_root)
    
    @property
    def game_loc(self):
        assert os.path.isdir(self.__game_loc), self.__standard_error_message(self.__game_loc)
        return os.path.normpath(self.__game_loc)
    
    @property
    def game_resources_loc(self):
        assert os.path.isdir(self.__game_resources_loc), self.__standard_error_message(self.__game_resources_loc)
        return self.__safe_path_return(self.__game_resources_loc, self.game_loc)
    
    def game_resources_loc_is_valid(self):
        return not ((self.__game_resources_loc is None) or (not os.path.isdir(self.__game_resources_loc)))
    
    @property
    def game_plugins_loc(self):
        return self.__safe_path_return(self.__game_plugins_loc, self.game_loc)
    
    @property
    def game_app_digister_loc(self):
        assert os.path.isdir(self.__game_app_digister_loc), self.__standard_error_message(self.self.__game_app_digister_loc)
        return self.__safe_path_return(self.__game_app_digister_loc, self.game_loc)
    
    @property
    def game_executable_loc(self):
        if self.__game_executable_loc is None:
            return None
        assert os.path.isfile(self.__game_executable_loc), self.__standard_error_message(self.self.__game_executable_loc)
        return self.__safe_path_return(self.__game_executable_loc, self.game_loc)

    def game_executable_loc_is_valid(self):
        return not ((self.__game_executable_loc is None) or (not os.path.isfile(self.__game_executable_loc)))

    @property
    def backups_loc(self):
        return self.__safe_path_return(self.__backups_loc, self.game_loc)

    @property
    def index_file_name(self):
        return "INDEX.json"
    
    def compute_game_paths(self):
        self.__game_resources_loc    = self.__clean_path(os.path.join(self.__game_loc, "resources"))
        self.__game_plugins_loc      = self.__clean_path(os.path.join(self.__game_resources_loc, "plugins"))
        self.__game_app_digister_loc = self.__clean_path(os.path.join(self.__game_loc, "app_digister"))
        self.__game_executable_loc   = self.__clean_path(os.path.join(self.__game_app_digister_loc, "Digimon Story CS.exe"))
        self.__backups_loc           = self.__clean_path(os.path.join(self.__game_resources_loc, 'backup'))
        
        
        os.makedirs(self.__backups_loc, exist_ok=True)
        
        assert os.path.exists(self.__game_loc), self.__standard_error_message(self.__game_loc)
        assert os.path.exists(self.__game_resources_loc), self.__standard_error_message(self.__game_resources_loc)
        # assert os.path.exists(self.__game_plugins_loc), self.__standard_error_message(self.__game_plugins_loc)
        # assert os.path.exists(self.__game_app_digister_loc), self.__standard_error_message(self.__game_app_digister_loc)
        # assert os.path.exists(self.__game_executable_loc), self.__standard_error_message(self.__game_executable_loc)
        assert os.path.exists(self.__backups_loc), self.__standard_error_message(self.__backups_loc)
        
    def checkresources(self):
        return os.isdir(self.__game_resources_loc)