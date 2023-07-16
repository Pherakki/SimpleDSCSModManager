import json
import os

from PyQt5 import QtCore, QtWidgets

from src.UI.CustomWidgets import OnlyOneProfileNotification
from src.Utils.JSONHandler import JSONHandler

translate = QtCore.QCoreApplication.translate

profile_extension = ".profile"


class ProfileManager:
    def __init__(self, ui, paths):
        self.ui = ui
        self.profiles_loc = paths.profiles_loc
        self.mods = None
        self.modpath_to_id = None
        self.profile_selector = ui.profile_selector
        self.mods_display = ui.mods_display
        
        mod_categories_file = os.path.join(paths.config_loc, "modcategories.json")
        try:
            with JSONHandler(mod_categories_file, "Error loading 'modcategories.json'") as stream:
                self.mod_categories = set(stream)
        except:
            self.ui.log(translate("ProfileManager", "Failed to load mod categories from {filepath}").format(filepath=mod_categories_file))
            self.mod_categories = set()
        
        os.makedirs(self.profiles_loc, exist_ok=True)
        
    def update_mod_info(self, mods, modpath_to_id):
        self.mods = mods
        self.modpath_to_id = modpath_to_id
        
        key = "Custom:"
        for mod in self.mods:
            if mod.category[:len(key)] != key:
                if mod.category not in self.mod_categories:
                    mod.category = "-"
            else:
                mod.category = mod.category[len(key):]
        
    def profile_path(self, file):
        return os.path.join(self.profiles_loc, file) + profile_extension
    
    def new_profile(self):
        all_items = [self.profile_selector.itemText(idx) for idx in range(self.profile_selector.count())]
        current_idx = 1
        current_trial = translate("ProfileManager", "New Profile")
        while current_trial in all_items:
            current_idx += 1
            current_trial = translate("ProfileManager", "New Profile {number}").format(number=current_idx)
            
        self.profile_selector.addItem(current_trial)
        self.profile_selector.setCurrentIndex(self.profile_selector.count() - 1)
        self.save_profile()
        
    def rename_profile(self):
        current_index = self.profile_selector.currentIndex()
        current_text = self.profile_selector.itemText(current_index)
        name, dataEntered = QtWidgets.QInputDialog.getText(None, 
                                                           translate("ProfileManager", "Rename Profile"), 
                                                           translate("ProfileManager", "Profile name:"), 
                                                           text=current_text)  
        if dataEntered:
            self.profile_selector.setItemText(current_index, name)
            self.save_profile()
        if name != current_text:
            filepath = self.profile_path(current_text)
            os.remove(filepath)
            
    def apply_profile(self):
        current_index = self.profile_selector.currentIndex()
        current_text = self.profile_selector.itemText(current_index)
        if current_text == '' or self.modpath_to_id is None:
            return
        filepath = self.profile_path(current_text)
        if os.path.exists(filepath):
            try:
                with JSONHandler(filepath, f"Error reading '{current_text}'") as stream:
                    current_profile = stream
            except Exception as e:
                self.ui.log
                (
                    translate(
                        "ProfileManager",
                        "The following error occured when loading the profile {profile_name}: {error}"
                    ).format(profile_name=current_text, error=e)
                )
                current_profile = {}
            actives = {}
            for path, value in current_profile.items():
                if path in self.modpath_to_id:
                    modid = self.modpath_to_id[path]
                    actives[modid] = value
                
            id_to_order = {modid: i for i, modid in enumerate(actives)}
            ordered_mods = sorted([(i, mod) for i, mod in enumerate(self.mods)], 
                                  key=lambda x: (id_to_order.get(x[0]) is None, id_to_order.get(x[0])))
    
            self.mods_display.set_mods(ordered_mods)
            self.mods_display.set_mod_activation_states(actives)
    
    def save_profile(self):
        current_index = self.profile_selector.currentIndex()
        current_text = self.profile_selector.itemText(current_index)
        
        filepath = self.profile_path(current_text)
        with open(filepath, 'w', encoding="utf-8") as F:
            json.dump(self.profile_from_active_mods(), F, indent=4)

        
    def delete_profile(self):
        if self.profile_selector.count() == 1:
            notification = OnlyOneProfileNotification()
            notification.exec_()
            return
        current_index = self.profile_selector.currentIndex()
        current_text = self.profile_selector.itemText(current_index)
        filepath = self.profile_path(current_text)
        os.remove(filepath)
        self.profile_selector.removeItem(current_index)
    
    def get_active_mods(self):
        activation_states = self.mods_display.get_mod_activation_states()
        return [self.mods[int(idx)] for idx, state in activation_states.items() if state == 2]
        
    
    def profile_from_active_mods(self):
        activation_states = self.mods_display.get_mod_activation_states()
        return {self.mods[int(idx)].path: state for idx, state in activation_states.items()}
    
    def init_profiles(self):
        profiles = []
        for file in os.listdir(self.profiles_loc):
            filename, ext = os.path.splitext(file)
            if ext != profile_extension:
                continue
            profiles.append(filename)
        for profile_name in profiles:
            self.profile_selector.addItem(profile_name)
        if len(profiles) == 0:
            self.new_profile()
