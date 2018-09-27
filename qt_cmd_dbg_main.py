import sys
import os
from main_view import MainView
import qdarkstyle
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from supporting_windows import AboutMessageBox
import getpass

VERSION = '0.2 Beta'
LAST_UPDATE = '2018.09.15'


class DebugLogAnalyzer(QMainWindow):

    def __init__(self):
        super(DebugLogAnalyzer, self).__init__()
        self.version = VERSION
        self.title = 'Quectel UE Debug Log Assistant ' + self.version
        self.left = 50
        self.top = 50
        self.width = 1380
        self.height = 940
        self.max_width = 1920
        self.max_height = 1440
        self.min_width = 980
        self.min_height = 750

        # small screen device rendering
        my_desktop = QDesktopWidget()
        screen = my_desktop.screenGeometry()
        screen_height = screen.height()
        print('Screen resolution:', screen.width(), 'x', screen_height)
        self.small_screen_flag = False
        if screen_height < 1000:
            self.small_screen_flag = True

        self.init_ui()

    def init_ui(self):
        self.setWindowIcon(QIcon('./assets/img/lol.jpg'))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top,
                         self.width, self.height)
        if self.small_screen_flag:
            self.setGeometry(20, 25, self.width, 738)

        self.setMaximumSize(self.max_width, self.max_height)
        self.setMinimumSize(self.min_width, self.min_height)

        # status bar
        self.statusBar().showMessage('Everything works well.')

        # logger configuration
        # self.config = StartupConfigurator()
        # self.config.exec_()

        # connect to UE
        # print('Configurations: ', self.config.config_results)

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
        self.main_view = MainView()

        self.setCentralWidget(self.main_view)

        self.show()

    @pyqtSlot(name='SHOW_ABOUT_DIALOG')
    def about_page(self):
        about_dialog = AboutMessageBox()
        about_dialog.exec_()

def run():
    # do some system/computer specific settings
    my_name = getpass.getuser()
    print('Username:', my_name)
    if my_name == 'lenovo':
        os.putenv('QT_SCALE_FACTOR', '1.0')
    elif my_name == 'SequoiaX':
        os.putenv('QT_SCALE_FACTOR', '1.0')
    # create the app
    my_app = QApplication(sys.argv)
    # change the fonts
    if my_name == 'lenovo':
        local_font = QFont('Microsoft Yahei', 8)  # 'Segoe UI'
        my_app.setFont(local_font)
    # my_app.setAttribute(Qt.AA_EnableHighDpiScaling)
    my_app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ex = DebugLogAnalyzer()
    sys.exit(my_app.exec_())


if __name__ == '__main__':
    run()