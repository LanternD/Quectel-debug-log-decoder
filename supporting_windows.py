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

class KeyLogConfigurator(QDialog):

    def __init__(self):
        super(KeyLogConfigurator, self).__init__()
        self.title = 'Key Log Selection'
        self.width = 400
        self.height = 360

        self.key_log_selection_result = ['RLC_UL_FILL_SRB1_TX_DATA', 'NAS_DBG_NAS_MSG',
                                         'ACK', 'LL1_DCI']
        # Add the log directly into the list above. If some are unwanted, change them in the dialog.
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)

        self.setFixedSize(self.width, self.height)

        kl_dialog_v_layout = QVBoxLayout()

        key_log_selection_g_layout = QGridLayout()
        self.key_check_box_list = []
        for item in self.key_log_selection_result:
            check_box_temp = QCheckBox(item)
            self.key_check_box_list.append(check_box_temp)
            check_box_temp.setChecked(True)

        # self.key_check_box_list.append(QCheckBox('RLC_UL_FILL_SRB1_TX_DATA'))
        # self.key_check_box_list.append(QCheckBox('NAS_DBG_NAS_MSG'))
        # self.key_check_box_list.append(QCheckBox('ACK'))
        # self.key_check_box_list.append(QCheckBox('LL1_DCI'))

        cnt = 0
        for cb in self.key_check_box_list:
            key_log_selection_g_layout.addWidget(cb, cnt, 1)
            cnt += 1

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.accepted.connect(self.config_ok_clicked)
        # self.rejected.connect(self.config_cancel_clicked)

        kl_dialog_v_layout.addWidget(QLabel('Check the logs that you want to observe:'))
        kl_dialog_v_layout.addLayout(key_log_selection_g_layout)
        kl_dialog_v_layout.addStretch(1)
        kl_dialog_v_layout.addWidget(QLabel('Note: these options are not dumped to config.json. '))
        kl_dialog_v_layout.addWidget(button_box)
        self.setLayout(kl_dialog_v_layout)

    @pyqtSlot()
    def config_ok_clicked(self):
        self.key_log_selection_result = []
        for cb in self.key_check_box_list:
            if cb.isChecked():
                log_temp = str(cb.text())
                self.key_log_selection_result.append(log_temp)
