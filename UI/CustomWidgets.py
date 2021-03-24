from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

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
    
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
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
            print(url)
        
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dragdrop_startrow = self.indexAt(e.pos()).row()
        super().mousePressEvent(e)
        
    def set_mods(self, mods):
        self.model().removeRows(0, self.model().rowCount())
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


class ComboBox(QtWidgets.QComboBox):
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