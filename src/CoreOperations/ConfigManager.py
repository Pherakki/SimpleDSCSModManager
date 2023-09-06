import json
import os

from src.Utils.JSONHandler import JSONHandler


class ConfigManager:
    __slots__ = ("init", 
                 "__game_loc",
                 "__lang_pref", 
                 "__style_pref",
                 "__crash_pref", 
                 "__block_pref", 
                 "__first_time_launch",
                 "paths",
                 "ui")
    
    def __init__(self, ui):
        self.init = False
        self.ui = ui
        self.__game_loc = None
        self.__lang_pref = None
        self.__style_pref = None
        self.__crash_pref = 0
        self.__block_pref = 0
        self.__first_time_launch = False
        self.paths = None

    def get_style_pref(self):
        return self.__style_pref
    
    def set_style_pref(self, value):
        self.__style_pref = value
        if self.init: self.write_config()
    
    def get_game_loc(self):
        return self.__game_loc
    
    def set_game_loc(self, path):
        self.__game_loc = path
        self.paths._set_game_loc(self.__game_loc)
        self.ui.game_location_textbox.setText(self.paths.game_loc)
        if self.init: self.write_config()
        
    def get_lang_pref(self):
        return self.__lang_pref
        
    def set_lang_pref(self, pref):
        self.__lang_pref = pref
        if self.init: self.write_config()
        
    def set_crash_pref(self, pref):
        self.__crash_pref = pref
        if self.init: self.write_config()
        
    def get_crash_pref(self):
        return self.__crash_pref
        
    def set_block_pref(self, pref):
        self.__block_pref = pref
        if self.init: self.write_config()
        
    def get_block_pref(self):
        return self.__block_pref
    
    def get_first_time_launch(self):
        return self.__first_time_launch
    
    def set_first_time_launch(self, val):
        self.__first_time_launch = val
        
    def init_with_paths(self, paths):
        self.paths = paths  
        self.load_config()
        if self.__game_loc is not None:
            self.set_game_loc(self.__game_loc)
        
        self.init = True
        
    def load_config(self):
        try:
            self.read_config()
        except:
            self.__game_loc   = None
            self.__lang_pref  = None
            self.__style_pref = None
            self.__crash_pref = 0
            self.__block_pref = 0
            self.__first_time_launch = False
            
    def read_config(self):
        with JSONHandler(os.path.join(self.paths.config_loc, "config.json"), "Error reading 'config.json'") as config_data:
            self.__game_loc          = config_data.get("game_loc")
            self.__lang_pref         = config_data.get("language")
            self.__style_pref        = config_data.get("style")
            self.__crash_pref        = config_data.get("crash_pref", 0)
            self.__block_pref        = config_data.get("block_pref", 0)
            self.__first_time_launch = config_data.get("first_time_launch", False)
            
    def write_config(self):
        with open(os.path.join(self.paths.config_loc, "config.json"), 'w') as F:
            out_data = {
                'game_loc'         : self.__game_loc,
                'language'         : self.__lang_pref,
                'style'            : self.__style_pref,
                'crash_pref'       : self.__crash_pref,
                'block_pref'       : self.__block_pref,
                'first_time_launch': self.__first_time_launch
            }
            json.dump(out_data, F, indent=4)
