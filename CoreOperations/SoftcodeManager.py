import json
import os

from PyQt5 import QtCore

    
class SoftcodeManager:
    def __init__(self, paths):
        self.mutex = QtCore.QMutex()
        self.paths = paths
        self.softcodes = {}
        self.custom_softcodes = {}
        self.ID_prefixes = {}
        
        self.init_softcodes()
        
    def init_softcodes(self):
        for file in os.listdir(self.paths.softcodes_loc):
            if file == "__IDPrefix.json":
                with open(os.path.join(self.paths.softcodes_loc, file), 'r') as F:
                    self.ID_prefixes = json.load(F)
            category, ext = os.path.splitext(file)
            if ext == ".json":
                with open(os.path.join(self.paths.softcodes_loc, file), 'r') as F:
                    self.softcodes[category] = json.load(F)
                
        if not os.path.exists(self.paths.softcode_cache_loc):
            os.makedirs(self.paths.softcode_cache_loc)
        for file in os.listdir(self.paths.softcode_cache_loc):
            category, ext = os.path.splitext(file)
            if ext == ".json":
                with open(os.path.join(self.paths.softcode_cache_loc, file), 'r') as F:
                    self.custom_softcodes[category] = json.load(F)
                    self.softcodes[category] = {**self.softcodes.get(category, {}), **self.custom_softcodes[category]}
    
    def dump_cached_softcodes(self):
        for category, data in self.custom_softcodes.items():
            filename = os.path.join(self.paths.softcode_cache_loc, category + ".json")
            with open(filename, 'w') as F:
                json.dump(self.custom_softcodes[category], F, indent=2)
                    
    def get_next_slot(self, category):
        curSlot = 1
        for name, item in sorted(self.softcodes[category].items(), key=lambda x: x[1]):
            if item != curSlot:
                return curSlot
            curSlot += 1
                
    def add_category(self, category):
        locker = QtCore.QMutexLocker(self.mutex)
        if category not in self.softcodes:
            self.softcodes[category] = {}
            
        return self.softcodes[category]
    
    def add_softcode(self, category, key):
        locker = QtCore.QMutexLocker(self.mutex)
        if category not in self.custom_softcodes:
            self.custom_softcodes[category] = {}
        if key not in self.softcodes[category]:
            self.softcodes[category][key] = self.get_next_slot(category)
            self.custom_softcodes[category][key] = self.softcodes[category][key]
        return self.softcodes[category][key]     
           
            
    def get_softcode(self, category, key):
        cat = self.softcodes.get(category)
        if cat is None:
            if category[-2:] == 'ID' and category[-3].isdigit():
                return self.__handle_ID_manip(category[:-3], key, category[-3])
            else:
                cat = self.add_category(category)
        val = cat.get(key)
        if val is None:
            val = self.add_softcode(category, key)
        return val
    
    def __handle_ID_manip(self, category, key, N):
        val = self.get_softcode(category, key)
        prefix = self.ID_prefixes.get(category, {}).get(N, '0')
        val = str(prefix) + str(val).rjust(int(N)-1, '0')
        
        return val
    
    
