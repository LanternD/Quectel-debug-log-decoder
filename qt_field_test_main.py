# -*- coding: UTF-8 -*-
import sys
import os
from LogDecoderTabview import LogDecoderTabview
from MainWindowTabview import MainWindowTabview
import qdarkstyle
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from SupportingWindows import AboutMessageBox
import getpass

VERSION = '0.4 Alpha'
LAST_UPDATE = '2019.03.23'


class QuectelDebugLogAnalyzer(QMainWindow):

    def __init__(self):
        super(QuectelDebugLogAnalyzer, self).__init__()
        self.version = VERSION
        self.title = 'Quectel UE Debug Log Analyzer ' + self.version
        self.left = 50
        self.top = 50
        self.width = 1480
        self.height = 940
        self.max_width = 1920
        self.max_height = 1440
        self.min_width = 980
        self.min_height = 750

        # small screen device rendering
        my_desktop = QDesktopWidget()
        screen = my_desktop.screenGeometry()
        screen_height = screen.height()
        print('[DEBUG] Screen resolution:', screen.width(), 'x', screen_height)
        self.small_screen_flag = False
        if screen_height < 1000:
            self.small_screen_flag = True

        self.init_ui()

    def init_ui(self):
        self.setWindowIcon(QIcon('./assets/img/mouse.png'))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top,
                         self.width, self.height)
        if self.small_screen_flag:
            self.setGeometry(20, 25, self.width, 738)

        self.setMaximumSize(self.max_width, self.max_height)
        self.setMinimumSize(self.min_width, self.min_height)

        # status bar
        self.statusBar().showMessage('Everything works well. A status bar makes a complete GUI software.')

        # menu bar
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu('File')
        help_menu = main_menu.addMenu('Help')

        # buttons in menu bar
        exit_button = QAction(QIcon('./assets/img/exit_button.png'), 'Exit', self)
        exit_button.setShortcut('Ctrl+Q')
        exit_button.setStatusTip('Exit Coverage Measurement Logger')
        exit_button.triggered.connect(self.close)
        file_menu.addAction(exit_button)

        about_button = QAction(QIcon('./assets/img/info.png'), 'About', self)
        about_button.triggered.connect(self.about_page)
        help_menu.addAction(about_button)

        # add tabView
        # self.main_view = LogDecoderTabview()
        # self.setCentralWidget(self.main_view)

        self.table_widget = MainWindowTabview()
        self.setCentralWidget(self.table_widget)

        self.show()

    @pyqtSlot(name='SHOW_ABOUT_DIALOG')
    def about_page(self):
        about_dialog = AboutMessageBox()
        about_dialog.exec_()


def run():
    # Do some system/computer specific settings
    my_name = getpass.getuser()
    print('[DEBUG] Username:', my_name)
    if my_name == 'lenovo':
        os.putenv('QT_SCALE_FACTOR', '1.0')
    elif my_name == 'SequoiaX':
        os.putenv('QT_SCALE_FACTOR', '1.0')
    # Create the app
    my_app = QApplication(sys.argv)

    # Change the fonts
    if sys.platform != 'linux':
        local_font = QFont('Segoe UI', 9)  # 'Segoe UI'
        my_app.setFont(local_font)
    # my_app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())  # dark mode. You need to run `pip install qdarkstyle` first.
    ex = QuectelDebugLogAnalyzer()
    sys.exit(my_app.exec_())


if __name__ == '__main__':
    run()
