import copy
import json
import os

from PyQt5 import QtCore, QtGui, QtWidgets

translate = QtCore.QCoreApplication.translate

class PaletteColour:
    __slots__ = ("c", "mirror_inactive")
    
    def __init__(self):
        self.c = None
        self.mirror_inactive = False
        
    @classmethod
    def from_dict(cls, dct):
        instance = cls()
        
        # COLOUR VALIDATION
        if "c" not in dct:
            raise Exception(translate("UI:StyleEngine", "No member 'c' found."))
        colour = dct["c"]
        if len(colour) != 3:
            raise Exception(translate("UI:StyleEngine", "Colour 'c' contains {n_elements} colours; 3 required")
                            .format(n_elements=len(colour)))
        try:
            instance.c = QtGui.QColor(*colour)
        except Exception as e:
            raise Exception(translate("UI:StyleEngine", "An unexpected error occurred when initialising colour: {error_msg}")
                            .format(error_msg=e))
            
        # mirror_inactive VALIDATION
        if "mirror_inactive" not in dct:
            raise Exception(translate("UI:StyleEngine", "No member 'mirror_inactive' found"))
            
        try:
            instance.mirror_inactive = bool(dct["mirror_inactive"])
        except Exception:
            raise Exception(translate("UI::StyleEngine", 
                                      "'mirror_inactive' value '{value}' cannot be converted to bool")
                            .format(value=dct["mirror_inactive"]))
        return instance
    
    def to_dict(self):
        return {
            "c": [self.c.red(), self.c.green(), self.c.blue()],
            "mirror_inactive": self.mirror_inactive
        }
    
class SubPalette:
    __slots__ = ("window", "base", "alt_base", "button", 
                 "bright_text", "text", "window_text", "button_text",
                 "link", "link_visited", 
                 "highlight", "highlighted_text",
                 "tooltip_base", "tooltip_text",
                 "light", "midlight", "mid", "dark", "shadow",
                 "unified_text")
    def __init__(self):
        self.window           = PaletteColour()
        self.base             = PaletteColour()
        self.alt_base         = PaletteColour()
        self.button           = PaletteColour()
        
        self.bright_text      = PaletteColour()
        self.text             = PaletteColour()
        self.window_text      = PaletteColour()
        self.button_text      = PaletteColour()
        
        self.link             = PaletteColour()
        self.link_visited     = PaletteColour()
        
        self.highlight        = PaletteColour()
        self.highlighted_text = PaletteColour()
        
        self.tooltip_base     = PaletteColour()
        self.tooltip_text     = PaletteColour()
        
        self.light            = PaletteColour()
        self.midlight         = PaletteColour()
        self.mid              = PaletteColour()
        self.dark             = PaletteColour()
        self.shadow           = PaletteColour()
        
        self.unified_text = False
          
    @classmethod
    def from_dict(cls, dct):
        instance = cls()
        for key in cls.__slots__:
            if key not in dct:
                raise ValueError(f"Dictionary contains no key '{key}':\n{dct}")
                
            if key == "unified_text":
                instance.unified_text = dct[key]
            else:
                try:
                    setattr(instance, key, PaletteColour.from_dict(dct[key]))
                except Exception as e:
                    raise Exception(translate("UI::StyleEngine", "colour definition '{name}': {error_msg}")
                                    .format(name=key, error_msg=e))
        return instance
    
    def to_dict(self):
        return {key: 
                getattr(self, key).to_dict() 
                if hasattr(getattr(self, key), "to_dict")
                else getattr(self, key)
                
                for key in self.__slots__}
      
class PaletteMap:
    __slots__ = ("active", "inactive", "disabled")
    def __init__(self):
        self.active   = SubPalette()
        self.inactive = SubPalette()
        self.disabled = SubPalette()
        
    @classmethod
    def from_dict(cls, dct):
        instance = cls()
        for key in cls.__slots__:
            if key not in dct:
                raise ValueError(f"Dictionary contains no key '{key}':\n{dct}")
            try:
                setattr(instance, key, SubPalette.from_dict(dct[key]))
            except Exception as e:
                raise Exception(translate("UI::StyleEngine", "Attempted to load palette '{name}', {error_msg}")
                                .format(name=key, error_msg=e))
        return instance
    
    def to_dict(self):
        return {key: getattr(self, key).to_dict() for key in self.__slots__}

class StyleEngine:
    """
    Dark Colours from https://stackoverflow.com/a/56851493
    """
    def __init__(self, app_ref, paths, log, initial_style=None):
        self.__app = app_ref
        self.__paths = paths
        self.builtin_styles = {"Light": self.light_style, "Dark": self.dark_style}
        self.styles = {}
        self.active_style = None
        self.log = log
        
        for theme in sorted(os.listdir(self.__paths.themes_loc)):
            self.load_style(theme)
            
        if initial_style is None:
            initial_style = "Light"
        try:
            self.set_style(initial_style)
        except Exception:
            default_theme = "Light"
            self.log(translate("UI::StyleEngine", 
                               "Error: Failed to set style '{initial_style}.json'; defaulting to '{default_theme}'.")
                            .format(initial_style=initial_style, default_theme=default_theme))
            self.set_style(default_theme)

        
    @property
    def light_style(self):
        pmap = PaletteMap()
        
        c = QtGui.QColor
        pmap.active  .window.c = c(240, 240, 240)
        pmap.inactive.window.c = c(240, 240, 240)
        pmap.disabled.window.c = c(240, 240, 240)
        pmap.active  .window.mirror_inactive = True
        pmap.disabled.window.mirror_inactive = True
        
        pmap.active  .base.c   = c(255, 255, 255)
        pmap.inactive.base.c   = c(255, 255, 255)
        pmap.disabled.base.c   = c(240, 240, 240)
        pmap.active  .base.mirror_inactive = True
        pmap.disabled.base.mirror_inactive = False
        
        pmap.active  .alt_base.c   = c(233, 231, 227)
        pmap.inactive.alt_base.c   = c(233, 231, 227)
        pmap.disabled.alt_base.c   = c(247, 247, 247)
        pmap.active  .alt_base.mirror_inactive = True
        pmap.disabled.alt_base.mirror_inactive = False
        
        pmap.active  .button.c   = c(240, 240, 240)
        pmap.inactive.button.c   = c(240, 240, 240)
        pmap.disabled.button.c   = c(240, 240, 240)
        pmap.active  .button.mirror_inactive = True
        pmap.disabled.button.mirror_inactive = True
        
        pmap.active  .bright_text.c   = c(255, 255, 255)
        pmap.inactive.bright_text.c   = c(255, 255, 255)
        pmap.disabled.bright_text.c   = c(255, 255, 255)
        pmap.active  .bright_text.mirror_inactive = True
        pmap.disabled.bright_text.mirror_inactive = True
        
        pmap.active  .text.c   = c(  0,   0,   0)
        pmap.inactive.text.c   = c(  0,   0,   0)
        pmap.disabled.text.c   = c(120, 120, 120)
        pmap.active  .text.mirror_inactive = True
        pmap.disabled.text.mirror_inactive = False
        
        pmap.active  .button_text.c   = c(  0,   0,   0)
        pmap.inactive.button_text.c   = c(  0,   0,   0)
        pmap.disabled.button_text.c   = c(120, 120, 120)
        pmap.active  .button_text.mirror_inactive = True
        pmap.disabled.button_text.mirror_inactive = False
        
        pmap.active  .window_text.c   = c(  0,   0,   0)
        pmap.inactive.window_text.c   = c(  0,   0,   0)
        pmap.disabled.window_text.c   = c(120, 120, 120)
        pmap.active  .window_text.mirror_inactive = True
        pmap.disabled.window_text.mirror_inactive = False
        
        pmap.active  .link.c   = c(  0,   0, 255)
        pmap.inactive.link.c   = c(  0,   0, 255)
        pmap.disabled.link.c   = c(  0,   0, 255)
        pmap.active  .link.mirror_inactive = True
        pmap.disabled.link.mirror_inactive = True
        
        pmap.active  .link_visited.c   = c(255,   0, 255)
        pmap.inactive.link_visited.c   = c(255,   0, 255)
        pmap.disabled.link_visited.c   = c(255,   0, 255)
        pmap.active  .link_visited.mirror_inactive = True
        pmap.disabled.link_visited.mirror_inactive = True
        
        pmap.active  .highlight.c   = c(  0, 120, 215)
        pmap.inactive.highlight.c   = c(240, 240, 240)
        pmap.disabled.highlight.c   = c(  0, 120, 215)
        pmap.active  .highlight.mirror_inactive = False
        pmap.disabled.highlight.mirror_inactive = False
        
        pmap.active  .highlighted_text.c   = c(255, 255, 255)
        pmap.inactive.highlighted_text.c   = c(  0,   0,   0)
        pmap.disabled.highlighted_text.c   = c(255, 255, 255)
        pmap.active  .highlighted_text.mirror_inactive = False
        pmap.disabled.highlighted_text.mirror_inactive = False
        
        pmap.active  .tooltip_base.c   = c(255, 255, 220)
        pmap.inactive.tooltip_base.c   = c(255, 255, 220)
        pmap.disabled.tooltip_base.c   = c(255, 255, 220)
        pmap.active  .tooltip_base.mirror_inactive = True
        pmap.disabled.tooltip_base.mirror_inactive = True
        
        pmap.active  .tooltip_text.c   = c(  0,   0,   0)
        pmap.inactive.tooltip_text.c   = c(  0,   0,   0)
        pmap.disabled.tooltip_text.c   = c(  0,   0,   0)
        pmap.active  .tooltip_text.mirror_inactive = True
        pmap.disabled.tooltip_text.mirror_inactive = True
        
        pmap.active  .light.c   = c(255, 255, 255)
        pmap.inactive.light.c   = c(255, 255, 255)
        pmap.disabled.light.c   = c(255, 255, 255)
        pmap.active  .light.mirror_inactive = True
        pmap.disabled.light.mirror_inactive = True
        
        pmap.active  .midlight.c   = c(227, 227, 227)
        pmap.inactive.midlight.c   = c(227, 227, 227)
        pmap.disabled.midlight.c   = c(247, 247, 247)
        pmap.active  .midlight.mirror_inactive = True
        pmap.disabled.midlight.mirror_inactive = False
        
        pmap.active  .mid.c   = c(160, 160, 160)
        pmap.inactive.mid.c   = c(160, 160, 160)
        pmap.disabled.mid.c   = c(160, 160, 160)
        pmap.active  .mid.mirror_inactive = True
        pmap.disabled.mid.mirror_inactive = True
        
        pmap.active  .dark.c   = c(160, 160, 160)
        pmap.inactive.dark.c   = c(160, 160, 160)
        pmap.disabled.dark.c   = c(160, 160, 160)
        pmap.active  .dark.mirror_inactive = True
        pmap.disabled.dark.mirror_inactive = True
        
        pmap.active  .shadow.c   = c(105, 105, 105)
        pmap.inactive.shadow.c   = c(105, 105, 105)
        pmap.disabled.shadow.c   = c(  0,   0,   0)
        pmap.active  .shadow.mirror_inactive = True
        pmap.disabled.shadow.mirror_inactive = False
        
        return pmap

    @property
    def dark_style(self):
        pmap = PaletteMap()
        
        c = QtGui.QColor
        pmap.active  .window.c = c( 53,  53,  53)
        pmap.inactive.window.c = c( 53,  53,  53)
        pmap.disabled.window.c = c( 53,  53,  53)
        pmap.active  .window.mirror_inactive = True
        pmap.disabled.window.mirror_inactive = True
        
        pmap.active  .base.c   = c( 25,  25,  25)
        pmap.inactive.base.c   = c( 25,  25,  25)
        pmap.disabled.base.c   = c(240, 240, 240)
        pmap.active  .base.mirror_inactive = True
        pmap.disabled.base.mirror_inactive = False
        
        pmap.active  .alt_base.c   = c( 53,  53,  53)
        pmap.inactive.alt_base.c   = c( 53,  53,  53)
        pmap.disabled.alt_base.c   = c(247, 247, 247)
        pmap.active  .alt_base.mirror_inactive = True
        pmap.disabled.alt_base.mirror_inactive = False
        
        pmap.active  .button.c   = c( 53,  53,  53)
        pmap.inactive.button.c   = c( 53,  53,  53)
        pmap.disabled.button.c   = c( 53,  53,  53)
        pmap.active  .button.mirror_inactive = True
        pmap.disabled.button.mirror_inactive = True
        
        pmap.active  .bright_text.c   = c(255,   0,   0)
        pmap.inactive.bright_text.c   = c(255,   0,   0)
        pmap.disabled.bright_text.c   = c(255,   0,   0)
        pmap.active  .bright_text.mirror_inactive = True
        pmap.disabled.bright_text.mirror_inactive = True
        
        pmap.active  .text.c   = c(255, 255, 255)
        pmap.inactive.text.c   = c(255, 255, 255)
        pmap.disabled.text.c   = c(120, 120, 120)
        pmap.active  .text.mirror_inactive = True
        pmap.disabled.text.mirror_inactive = False
        
        pmap.active  .button_text.c   = c(255, 255, 255)
        pmap.inactive.button_text.c   = c(255, 255, 255)
        pmap.disabled.button_text.c   = c(120, 120, 120)
        pmap.active  .button_text.mirror_inactive = True
        pmap.disabled.button_text.mirror_inactive = False
        
        pmap.active  .window_text.c   = c(255, 255, 255)
        pmap.inactive.window_text.c   = c(255, 255, 255)
        pmap.disabled.window_text.c   = c(120, 120, 120)
        pmap.active  .window_text.mirror_inactive = True
        pmap.disabled.window_text.mirror_inactive = False
        
        pmap.active  .link.c   = c(  0,   0, 218)
        pmap.inactive.link.c   = c(  0,   0, 218)
        pmap.disabled.link.c   = c(  0,   0, 218)
        pmap.active  .link.mirror_inactive = True
        pmap.disabled.link.mirror_inactive = True
        
        pmap.active  .link_visited.c   = c(255,   0, 255)
        pmap.inactive.link_visited.c   = c(255,   0, 255)
        pmap.disabled.link_visited.c   = c(255,   0, 255)
        pmap.active  .link_visited.mirror_inactive = True
        pmap.disabled.link_visited.mirror_inactive = True
        
        pmap.active  .highlight.c   = c( 42, 130, 218)
        pmap.inactive.highlight.c   = c(240, 240, 240)
        pmap.disabled.highlight.c   = c( 42, 130, 218)
        pmap.active  .highlight.mirror_inactive = False
        pmap.disabled.highlight.mirror_inactive = False
        
        pmap.active  .highlighted_text.c   = c(  0,   0,   0)
        pmap.inactive.highlighted_text.c   = c(255, 255, 255)
        pmap.disabled.highlighted_text.c   = c(  0,   0,   0)
        pmap.active  .highlighted_text.mirror_inactive = False
        pmap.disabled.highlighted_text.mirror_inactive = False
        
        pmap.active  .tooltip_base.c   = c(  0,   0,   0)
        pmap.inactive.tooltip_base.c   = c(  0,   0,   0)
        pmap.disabled.tooltip_base.c   = c(  0,   0,   0)
        pmap.active  .tooltip_base.mirror_inactive = True
        pmap.disabled.tooltip_base.mirror_inactive = True
        
        pmap.active  .tooltip_text.c   = c(255, 255, 255)
        pmap.inactive.tooltip_text.c   = c(255, 255, 255)
        pmap.disabled.tooltip_text.c   = c(255, 255, 255)
        pmap.active  .tooltip_text.mirror_inactive = True
        pmap.disabled.tooltip_text.mirror_inactive = True
        
        pmap.active  .light.c   = c(255, 255, 255)
        pmap.inactive.light.c   = c(255, 255, 255)
        pmap.disabled.light.c   = c(255, 255, 255)
        pmap.active  .light.mirror_inactive = True
        pmap.disabled.light.mirror_inactive = True
        
        pmap.active  .midlight.c   = c(227, 227, 227)
        pmap.inactive.midlight.c   = c(227, 227, 227)
        pmap.disabled.midlight.c   = c(247, 247, 247)
        pmap.active  .midlight.mirror_inactive = True
        pmap.disabled.midlight.mirror_inactive = False
        
        pmap.active  .mid.c   = c(160, 160, 160)
        pmap.inactive.mid.c   = c(160, 160, 160)
        pmap.disabled.mid.c   = c(160, 160, 160)
        pmap.active  .mid.mirror_inactive = True
        pmap.disabled.mid.mirror_inactive = True
        
        pmap.active  .dark.c   = c(160, 160, 160)
        pmap.inactive.dark.c   = c(160, 160, 160)
        pmap.disabled.dark.c   = c(160, 160, 160)
        pmap.active  .dark.mirror_inactive = True
        pmap.disabled.dark.mirror_inactive = True
        
        pmap.active  .shadow.c   = c(105, 105, 105)
        pmap.inactive.shadow.c   = c(105, 105, 105)
        pmap.disabled.shadow.c   = c(  0,   0,   0)
        pmap.active  .shadow.mirror_inactive = True
        pmap.disabled.shadow.mirror_inactive = False
        
        return pmap
    
    def load_style(self, file):
        filepath = os.path.join(self.__paths.themes_loc, file)
        filename, ext = os.path.splitext(file)
        if os.path.isfile(filepath) and ext.lstrip(os.extsep) == "json":
            try:
                with open(filepath, 'r') as F:
                    style_def = json.load(F)
                name = filename
                self.styles[name] = PaletteMap.from_dict(style_def)
            except Exception as e:
                self.log(translate("UI::StyleEngine", 
                                   "WARNING: Failed to load style file '{name}.json'. Error is: {error_msg}.")
                         .format(name=filename, error_msg=e))
            
        
    def save_style(self, name):
        filepath = os.path.join(self.__paths.themes_loc, os.extsep.join((name, "json")))
        with open(filepath, 'w') as F:
            json.dump(self.styles[name].to_dict(), F, indent=4)
            
    def generate_style_name(self, name):
        stem, tail = name.rsplit(" ", 1)
        if tail.isdigit():
            number = int(tail)
            number += 1
            return stem + " " + str(number)
        else:
            return name + " 2"
        
    def generate_new_style_name(self, name):
        while name in self.styles or name in self.builtin_styles:
            name = self.generate_style_name(name)
        return name

    def new_style(self, from_name):
        return copy.deepcopy(self.styles[from_name])
    
    def delete_style(self, name):
        if name in self.styles:
            del self.styles[name]
        filepath = os.path.join(self.__paths.themes_loc, os.extsep.join((name, "json")))
        if os.path.isfile(filepath):
            os.remove(filepath)
        
    def set_style(self, name):
        if name in self.builtin_styles:
            self.apply_style(self.builtin_styles[name])
        else:
            self.apply_style(self.styles[name])
        self.active_style = name
        
    def apply_colour(self, palette, group, group_attr, element, accessor, colour_map):
        if accessor(group_attr).mirror_inactive:
            group_attr = colour_map.inactive
        palette.setColor(group, element, accessor(group_attr).c)
        
    def apply_style(self, colour_map):
        palette = QtWidgets.QApplication.palette()#QtGui.QPalette()
        for group, group_attr in ((QtGui.QPalette.Active,   colour_map.active  ),
                                  (QtGui.QPalette.Inactive, colour_map.inactive),
                                  (QtGui.QPalette.Disabled, colour_map.disabled)):
            
            def apply_colour(element, accessor):
                self.apply_colour(palette, group, group_attr, element, accessor, colour_map)
            
            apply_colour(QtGui.QPalette.Window,          lambda x: x.window)
            apply_colour(QtGui.QPalette.Base,            lambda x: x.base)
            apply_colour(QtGui.QPalette.AlternateBase,   lambda x: x.alt_base)
            apply_colour(QtGui.QPalette.Button,          lambda x: x.button)
            
            apply_colour(QtGui.QPalette.BrightText,      lambda x: x.bright_text)
            apply_colour(QtGui.QPalette.Text,            lambda x: x.text)
            apply_colour(QtGui.QPalette.WindowText,      lambda x: x.window_text)
            apply_colour(QtGui.QPalette.ButtonText,      lambda x: x.button_text)
            
            apply_colour(QtGui.QPalette.Link,            lambda x: x.link)
            apply_colour(QtGui.QPalette.LinkVisited,     lambda x: x.link_visited)
            
            apply_colour(QtGui.QPalette.Highlight,       lambda x: x.highlight)
            apply_colour(QtGui.QPalette.HighlightedText, lambda x: x.highlighted_text)
            
            apply_colour(QtGui.QPalette.ToolTipBase,     lambda x: x.tooltip_base)
            apply_colour(QtGui.QPalette.ToolTipText,     lambda x: x.tooltip_text)
            
            apply_colour(QtGui.QPalette.Light,           lambda x: x.light)
            apply_colour(QtGui.QPalette.Midlight,        lambda x: x.midlight)
            apply_colour(QtGui.QPalette.Mid,             lambda x: x.mid)
            apply_colour(QtGui.QPalette.Dark,            lambda x: x.dark)
            apply_colour(QtGui.QPalette.Shadow,          lambda x: x.shadow)
            
        self.__app.setPalette(palette)
        
    def get_active_style(self):
        if self.active_style in self.builtin_styles:
            return self.builtin_styles[self.active_style]
        else:
            return self.styles[self.active_style]
        
    # def __extract_style(self):
    #     palette = QtWidgets.QApplication.palette()
        
    #     style = {}
    #     style["window"]           = self.__extract_colour(palette.window())
    #     style["window text"]      = self.__extract_colour(palette.windowText())
    #     style["base"]             = self.__extract_colour(palette.base())
    #     style["alt base"]         = self.__extract_colour(palette.alternateBase())
    #     style["tooltip base"]     = self.__extract_colour(palette.toolTipBase())
    #     style["tooltip text"]     = self.__extract_colour(palette.toolTipText())
    #     style["text"]             = self.__extract_colour(palette.text())
    #     style["button"]           = self.__extract_colour(palette.button())
    #     style["button text"]      = self.__extract_colour(palette.buttonText())
    #     style["bright text"]      = self.__extract_colour(palette.brightText())
    #     style["link"]             = self.__extract_colour(palette.link())
    #     style["link visited"]     = self.__extract_colour(palette.linkVisited())
    #     style["highlight"]        = self.__extract_colour(palette.highlight())
    #     style["highlighted text"] = self.__extract_colour(palette.highlightedText())
    #     style["light"]            = self.__extract_colour(palette.light())
    #     style["midlight"]         = self.__extract_colour(palette.midlight())
    #     style["mid"]              = self.__extract_colour(palette.mid())
    #     style["dark"]             = self.__extract_colour(palette.dark())
    #     style["shadow"]           = self.__extract_colour(palette.shadow())
        
    #     return style
        
    # def __extract_colour(self, brush):
    #     bcol = brush.color()
    #     return [bcol.red(), bcol.green(), bcol.blue()]
