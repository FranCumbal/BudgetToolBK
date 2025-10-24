# main.py
import sys
from PyQt5.QtWidgets import QApplication
from controllers.main_controller import MainController
from views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    controller = MainController()
    window = MainWindow(controller)
    controller.set_view(window)
    
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
