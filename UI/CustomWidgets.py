from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

class DragDropTreeViewStyle(QtWidgets.QProxyStyle):
    """
    Assistance from https://apocalyptech.com/linux/qt/qtableview/
    """
    def __init__(self, key=None):
        super().__init__(key)
        self.top = 0
        self.width = 0
    
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == self.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
            option_new = QtWidgets.QStyleOption(option)
            option_new.rect.setLeft(0)
            option_new.rect.setTop(self.top)
            option_new.rect.setHeight(0)
            option_new.rect.setRight(self.width)
            option = option_new
            
        super().drawPrimitive(element, option, painter, widget)

def is_in_bottom_half(point, rect):
    posy = point.y()
    item_top = rect.top()
    item_height = rect.height()
    adjust = 2*(posy - item_top) - item_height
    clamped_adjust = min(max(adjust, -1), 1)
    clamped_adjust = int((clamped_adjust + 1) / 2)
    
    return clamped_adjust

class DragDropTreeView(QtWidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False) 
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove) 
        self.id_column = 4
        
        self.display_data = []
        self.dragdrop_startrow = None
        
        self.modid_to_order = None
        self.modorder_to_id = None
        
        self.register_mod_from_path = None
        
        self.style = DragDropTreeViewStyle()
        self.setStyle(self.style)
        
  
    def hook_registry_function(self, func):
        self.register_mod_from_path = func
        
    def update_style(self, pos, item_rect, row):
        bottom_is = is_in_bottom_half(pos, item_rect)
        top = (row + bottom_is)*item_rect.height() - bottom_is
        self.style.top = top
        self.style.width = self.width()
  
    #############
    # UI EVENTS #
    #############
    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        self.setDropIndicatorShown(False)
        if event.mimeData().hasUrls:
            index = self.indexAt(event.pos())
            item_rect = self.visualRect(index)
            self.update_style(event.pos(), item_rect, index.row())
            if len(event.mimeData().urls()) == 0:
                event.setDropAction(QtCore.Qt.MoveAction)
            else:
                event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, e):
        if e.mimeData().hasUrls:
            if len(e.mimeData().urls()) == 0:
                self.reorderElementsDropEvent(e)
            else:
                self.addModDropEvent(e)
            e.accept()
        else:
            e.ignore()
        
    def reorderElementsDropEvent(self, e):
        index = self.indexAt(e.pos())
        parent = index.parent()
        self.model().dropMimeData(e.mimeData(), e.dropAction(), index.row()+1, 0, parent)
        
        if index.row() > self.dragdrop_startrow:
            add = 0
        else:
            add = 1
        self.display_data.insert(index.row() + add, self.display_data.pop(self.dragdrop_startrow))
        
    def addModDropEvent(self, e):
        for url in e.mimeData().urls():
            self.register_mod_from_path(url.toLocalFile())
        
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragdrop_startrow = self.indexAt(e.pos()).row()
        super().mousePressEvent(e)
        
    #########
    # LOGIC #
    #########
    def set_mods(self, mods):
        self.model().removeRows(0, self.model().rowCount())
        self.display_data = []
        for i, mod in mods:
            name_item = QtGui.QStandardItem(mod.name)
            name_item.setCheckable(True)
            row = [name_item, *[QtGui.QStandardItem(elem) for elem in mod.metadata[1:]]]
            self.model().appendRow(row)
            self.display_data.append([*mod.metadata, i])

            
    def get_mod_activation_states(self):
        result = {}
        for ridx, display_row in zip(range(self.model().rowCount()), self.display_data):
            row = self.model().takeRow(ridx)
            self.model().insertRow(ridx, row)
            name_item = row[0]
            id_index = display_row[self.id_column]
            result[id_index] = name_item.checkState()
        return result
    
    def set_mod_activation_states(self, states):
        for mod_id, state in states.items():
            for ridx, display_row in zip(range(self.model().rowCount()), self.display_data):
                row = self.model().takeRow(ridx)
                self.model().insertRow(ridx, row)
                name_item = row[0]
                id_index = display_row[self.id_column]
                if id_index == mod_id:
                    name_item.setCheckState(state)
                    break
    
    def get_active_mods(self, mods):
        return [mods[idx] for idx, state in self.get_mod_activation_states().items() if state == 2]


class ClickEmitComboBox(QtWidgets.QComboBox):
    """
    Help from https://stackoverflow.com/questions/35932660/qcombobox-click-event
    """
    popupAboutToBeShown = QtCore.pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super().showPopup()
        
            
class OnlyOneProfileNotification(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Delete Profile")
        
        label = QtWidgets.QLabel("There is only one profile, will not delete.", self)
        
        okButton = QtWidgets.QPushButton("Ok")
        okButton.setFixedWidth(80)
        okButton.clicked.connect(self.accept)

        self.layout = QtWidgets.QGridLayout() 
        self.layout.addWidget(label, 0, 0)
        sublayout = QtWidgets.QGridLayout()
        sublayout.addWidget(okButton, 0, 0)
        self.layout.addLayout(sublayout, 1, 0)
        self.layout.setRowStretch(0, 1)
        self.setLayout(self.layout)
        
        
        self.setFixedSize(300, 100)
        
class ProgressDialog(QtWidgets.QDialog):
    def __init__(self, window_title, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle(window_title)
        
        self.label = QtWidgets.QLabel(self)
        
        self.progbar = QtWidgets.QProgressBar(self)

        self.layout = QtWidgets.QGridLayout() 
        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.progbar, 1, 0)
        self.setLayout(self.layout)
        
        self.setFixedSize(300, 100)
        
    def update_progbar(self, message, progress):
        self.label.setText(message)
        self.progbar.setValue(progress) 