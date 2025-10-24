from PyQt5.QtWidgets import QStyledItemDelegate, QComboBox
from PyQt5.QtCore import Qt

class CapexComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = ["No", "Yes"]  # Opciones del combobox
    
    def createEditor(self, parent, option, index):
        """Crea el widget editor (combobox) para la celda"""
        editor = QComboBox(parent)
        editor.addItems(self.items)
        return editor
    
    def setEditorData(self, editor, index):
        """Establece el valor actual en el combobox"""
        current_value = index.model().data(index, Qt.EditRole)
        # Solo convertir booleano a texto para mostrar
        display_value = "Yes" if current_value else "No"
        editor.setCurrentText(display_value)
    
    def setModelData(self, editor, model, index):
        """Guarda el valor seleccionado del combobox al modelo"""
        value = editor.currentText()
        # Convertir a booleano para guardar
        boolean_value = True if value == "Yes" else False
        model.setData(index, boolean_value, Qt.EditRole)
    
    def updateEditorGeometry(self, editor, option, index):
        """Ajusta el tamaño del editor a la celda"""
        editor.setGeometry(option.rect)
