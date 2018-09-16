from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import json
import os.path

VERSION = '0.2 Beta'
LAST_UPDATE = '2018.09.15'

class AboutMessageBox(QDialog):

    def __init__(self, parent=None):
        super(AboutMessageBox, self).__init__(parent)
        self.title = 'About Quectel UE Debug Log Assistant'
        self.left = 400
        self.top = 400
        self.width = 450
        self.height = 280

        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon('./assets/about.png'))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top,
                         self.width, self.height)
        self.setFixedSize(self.width, self.height)

        info_label = QLabel('NB-IOT Quectel UE Debug Log Assistant', self)
        info_label.move(70, 50)

        author_label = QLabel('Developer: \tDeliang Yang (LanternD), Xianghui Zhang, Liqian Shen', self)
        author_label.move(70, 90)

        version_label = QLabel('Version: \t' + VERSION, self)
        version_label.move(70, 130)

        update_date_label = QLabel('Last update: \t' + LAST_UPDATE, self)
        update_date_label.move(70, 170)
