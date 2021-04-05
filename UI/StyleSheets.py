import json


class MainStyleSheet:
    def __init__(self):
        self.text_colour = 'black'
        self.background_color = 'white'
        self.alternate_background_color = 'grey'
        self.border_color = 'grey'
        self.outline_colour = 'grey'
        
    def set_stylesheet_on(self, widget):
        stylesheet = f""" 
        QWidget 
        {{
            background-color: {self.background_color};
            alternate-background-color: {self.alternate_background_color};
            border-color: {self.border_color};
            color: {self.text_color};
            outline-color: {self.outline_colour};
        }}
        QTabBar {{background: {self.background_color};}}
        QTabBar::tab {{background: {self.background_color};}}
        QTabBar::tab:selected {{background: {self.alternate_background_color};}}
        QHeaderView::section 
        {{
            background-color: {self.alternate_background_color};
            color: {self.text_color};
            padding-left: 4px;
            border: 1px solid {self.border_color};
        }}
        """
        widget.setStyleSheet(stylesheet)
        
    def set_parameters(self, parameters):
        for param_name, param_value in parameters.items():
            setattr(self, param_name, param_value)
            
    def get_parameters(self):
        return vars(self)
    
    def to_json(self, filepath):
        with open(filepath, 'w') as F:
            json.dump(self.get_parameters(), F, indent=4)
            
    def from_json(self, filepath):
        with open(filepath, 'r') as F:
            self.set_parameters(json.load(F))
