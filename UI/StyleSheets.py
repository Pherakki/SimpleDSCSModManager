import json


class MainStyleSheet:
    def __init__(self):
        self.text_colour = '#dddddd'
        self.background_color = '#31363b'
        self.highlight_background_color = '#41464b'
        self.alternate_background_color = '#101520'
        self.border_color = '#1FD2DE'
        self.outline_colour = '#1FD2DE'
        
    def set_stylesheet_on(self, widget):
        stylesheet = f""" 
        QWidget 
        {{
            background-color: {self.background_color};
            alternate-background-color: {self.alternate_background_color};
            border-color: {self.border_color};
            color: {self.text_colour};
            outline-color: {self.outline_colour};
        }}

        QLabel 
        {{
            background-color: transparent;
        }}
        
        
        QPushButton 
        {{
            border-style: outset;
            border: 2px solid {self.border_color};
            border-radius: 20px;
            border-style: outset;
            background: {self.background_color};
            padding: 4px;
        }}
            
        QPushButton:hover 
        {{
            background: {self.highlight_background_color};
        }}
            
        QPushButton:pressed 
        {{
            border-style: inset;
            background: {self.alternate_background_color}
        }}
        
        QMenuBar 
        {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                              stop:0 lightgray, stop:1 darkgray);
        }}
        QMenuBar::item 
        {{
            spacing: 3px;           
            padding: 2px 10px;
            background-color: rgb(210,105,30);
            color: rgb(255,255,255);  
            border-radius: 5px;
        }}
        QMenuBar::item:selected 
        {{    
            background-color: rgb(244,164,96);
        }}
        QMenuBar::item:pressed 
        {{
            background: rgb(128,0,0);
        }}
        QMenu 
        {{
            background-color: #ABABAB;   
            border: 1px solid black;
            margin: 2px;
        }}
        QMenu::item 
        {{
            background-color: transparent;
        }}
        QMenu::item:selected 
        {{ 
            background-color: #654321;
            color: rgb(255,255,255);
        }}
        QTabBar {{background: {self.background_color};}}
        QTabBar::tab {{background: {self.background_color};}}
        QTabBar::tab:selected {{background: {self.alternate_background_color};}}
        QHeaderView::section 
        {{
            background-color: {self.alternate_background_color};
            color: {self.text_colour};
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
