# -*- coding: UTF-8 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import json
import os.path
from utils import YouAreSoQ


VERSION = '0.4 Alpha'
LAST_UPDATE = '2019.04.01'


class AboutMessageBox(QDialog):

    def __init__(self, parent=None):
        super(AboutMessageBox, self).__init__(parent)
        self.title = 'About Quectel UE Debug Log Analyzer'
        self.left = 400
        self.top = 400
        self.width = 560
        self.height = 280

        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon('./assets/about.png'))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top,
                         self.width, self.height)
        self.setFixedSize(self.width, self.height)

        info_label = QLabel('Quectel UE Debug Log Analyzer\n'
                            '  - A software we build for the NB-IoT field test.', self)
        info_label.move(50, 50)

        author_label = QLabel('Developer: \tDeliang Yang (LanternD), Xianghui Zhang, Liqian Shen', self)
        author_label.move(50, 110)

        version_label = QLabel('Version: \t' + VERSION, self)
        version_label.move(50, 150)

        update_date_label = QLabel('Last update: \t' + LAST_UPDATE, self)
        update_date_label.move(50, 190)


class ConfigurationEditor(QDialog):
    config_updated_trigger = pyqtSignal()

    def __init__(self):
        super(ConfigurationEditor, self).__init__()
        self.dlg_config = {}  # configs set in the Qdialog (subset of all the configs)
        g_q_style = YouAreSoQ()
        self.groupbox_stylesheet = g_q_style.groupbox_stylesheet
        self.lb_font = g_q_style.lb_font
        self.btn_font = g_q_style.large_btn_font

        self.initUI()
        self.add_tool_tips_dlg()

    def initUI(self):
        self.setWindowTitle('Configuration Editor')
        self.setFixedWidth(500)
        self.setMinimumHeight(550)
        self.setMaximumHeight(650)
        # cfg_editor_layout = QVBoxLayout()
        config_editor_dialog_v_layout = QVBoxLayout()

        self.exp_disp_gbox = QGroupBox('Export and Display Configurations')
        # self.exp_disp_gbox.setMaximumWidth(400)
        # self.exp_disp_gbox.setMinimumWidth(350)
        self.exp_disp_gbox.setStyleSheet(self.groupbox_stylesheet)

        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)

        config_v_layout = QVBoxLayout()

        misc_lb = QLabel('Miscellaneous')
        misc_lb.setFont(self.lb_font)
        # Socket configuration
        self.create_socket_cb = QCheckBox('Create socket at starting')
        self.create_socket_cb.setChecked(True)

        self.enable_power_monitor_cb = QCheckBox('Enable Monsoon power monitor module (Need restart)')
        self.enable_power_monitor_cb.setChecked(True)

        self.enable_gps_module_cb = QCheckBox('Enable GPS tracking module (Need restart)')
        self.enable_gps_module_cb.setChecked(True)


        # Export configuration
        export_lb = QLabel('Export')
        export_lb.setFont(self.lb_font)

        log_type_lb = QLabel('Choose export content')

        export_h_layout = QHBoxLayout()

        self.export_raw_cb = QCheckBox('Raw log')
        self.export_raw_cb.setChecked(True)

        self.export_decoded_cb = QCheckBox('Decoded log')
        self.export_decoded_cb.setChecked(True)

        self.keep_filtered_log_cb = QCheckBox('Keep filtered logs')

        export_h_layout.addWidget(self.export_raw_cb)
        export_h_layout.addWidget(self.export_decoded_cb)
        export_h_layout.addWidget(self.keep_filtered_log_cb)
        export_h_layout.addStretch()

        time_format_h_layout = QHBoxLayout()
        time_format_lb = QLabel('File name time format')
        self.time_format_input = QLineEdit('%y%m%d_%H%M%S')
        self.time_format_input.setMaximumWidth(200)
        time_format_h_layout.addWidget(time_format_lb)
        time_format_h_layout.addWidget(self.time_format_input)
        time_format_h_layout.addStretch(1)

        export_format_h_layout = QHBoxLayout()
        export_format_bg = QButtonGroup(export_format_h_layout)
        export_format_lb = QLabel('File format')
        self.export_format_rb_txt = QRadioButton('.txt')

        self.export_format_rb_csv = QRadioButton('.csv')
        self.export_format_rb_csv.setChecked(True)

        export_format_bg.addButton(self.export_format_rb_txt)
        export_format_bg.addButton(self.export_format_rb_csv)
        export_format_h_layout.addWidget(export_format_lb)
        # export_format_h_layout.addWidget(export_format_bg)
        export_format_h_layout.addWidget(self.export_format_rb_txt)
        export_format_h_layout.addWidget(self.export_format_rb_csv)
        export_format_h_layout.addStretch()

        disp_v_layout = QVBoxLayout()
        disp_time_format_bg = QButtonGroup(disp_v_layout)
        display_config_lb = QLabel('Display')
        display_config_lb.setFont(self.lb_font)

        self.disp_simplified_log_cb = QCheckBox('Simplify debug log display')
        self.disp_simplified_log_cb.setChecked(True)
        # self.disp_simplified_log_cb.stateChanged.connect(self.cbx_fn_simplify_option)

        # disp_time_format_lb = QLabel('Display time format')
        self.disp_time_format_rb_strf = QRadioButton('Local Time (e.g. 18-08-18 10:11:55.12353)')
        self.disp_time_format_rb_raw = QRadioButton('Raw time (e.g. 1534575622.4211376)')
        self.disp_time_format_rb_zero = QRadioButton('0-offset (e.g. 0.4211376)')
        self.disp_time_format_rb_zero.setChecked(True)

        disp_time_format_bg.addButton(self.disp_time_format_rb_strf)
        disp_time_format_bg.addButton(self.disp_time_format_rb_raw)
        disp_time_format_bg.addButton(self.disp_time_format_rb_zero)

        disp_v_layout.addWidget(display_config_lb)

        # disp_v_layout.addWidget(QLabel('Log verbosity'))
        disp_v_layout.addWidget(self.disp_simplified_log_cb)
        disp_v_layout.addWidget(QLabel('Time formatting'))
        disp_v_layout.addWidget(self.disp_time_format_rb_strf)
        disp_v_layout.addWidget(self.disp_time_format_rb_raw)
        disp_v_layout.addWidget(self.disp_time_format_rb_zero)

        # accept and cancel button
        decision_btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        decision_btn_box.accepted.connect(self.accept)
        decision_btn_box.rejected.connect(self.reject)

        self.accepted.connect(self.config_ok_btn_clicked)

        config_v_layout.addWidget(misc_lb)
        config_v_layout.addWidget(self.create_socket_cb)
        config_v_layout.addWidget(self.enable_power_monitor_cb)
        config_v_layout.addWidget(self.enable_gps_module_cb)
        config_v_layout.addWidget(export_lb)
        config_v_layout.addWidget(log_type_lb)
        config_v_layout.addLayout(export_h_layout)
        config_v_layout.addLayout(time_format_h_layout)
        config_v_layout.addLayout(export_format_h_layout)
        config_v_layout.addWidget(hline)
        config_v_layout.addLayout(disp_v_layout)
        config_v_layout.addStretch()

        self.exp_disp_gbox.setLayout(config_v_layout)

        config_editor_dialog_v_layout.addWidget(self.exp_disp_gbox)
        config_editor_dialog_v_layout.addWidget(decision_btn_box)
        self.setLayout(config_editor_dialog_v_layout)

    def load_previous_config_from_json(self, last_config):
        # Socket create config
        self.create_socket_cb.setChecked(last_config['Create socket at start'])
        self.enable_power_monitor_cb.setChecked(last_config['Enable power monitor module'])
        self.enable_gps_module_cb.setChecked(last_config['Enable GPS module'])

        # Export config
        self.export_raw_cb.setChecked(last_config['Export raw'])
        self.export_decoded_cb.setChecked(last_config['Export decoded'])
        self.keep_filtered_log_cb.setChecked(last_config['Keep filtered logs'])
        self.time_format_input.setText(last_config['Export filename time prefix'])
        if last_config['Export format'] == 'txt':
            self.export_format_rb_txt.setChecked(True)
        else:
            self.export_format_rb_csv.setChecked(True)

        # Display config
        disp_format = last_config['Display time format']
        if disp_format == 'local':
            self.disp_time_format_rb_strf.setChecked(True)
        elif disp_format == 'raw':
            self.disp_time_format_rb_raw.setChecked(True)
        elif disp_format == 'zero':
            self.disp_time_format_rb_zero.setChecked(True)


        self.dlg_config = last_config  # Sync everything to prevent KeyErrors.

    def set_availability_in_stop_mode_dlg(self):
        self.create_socket_cb.setEnabled(True)

        self.export_raw_cb.setEnabled(True)
        self.export_decoded_cb.setEnabled(True)
        self.keep_filtered_log_cb.setEnabled(True)
        self.export_format_rb_txt.setEnabled(True)
        self.export_format_rb_csv.setEnabled(True)

        self.time_format_input.setEnabled(True)
        self.disp_time_format_rb_strf.setEnabled(True)
        self.disp_time_format_rb_raw.setEnabled(True)
        self.disp_time_format_rb_zero.setEnabled(True)

    def set_availability_in_running_mode_dlg(self):
        self.create_socket_cb.setDisabled(True)

        self.export_raw_cb.setDisabled(True)
        self.export_decoded_cb.setDisabled(True)
        self.keep_filtered_log_cb.setDisabled(True)
        self.export_format_rb_txt.setDisabled(True)
        self.export_format_rb_csv.setDisabled(True)

        self.time_format_input.setDisabled(True)
        self.disp_time_format_rb_strf.setDisabled(True)
        self.disp_time_format_rb_raw.setDisabled(True)
        self.disp_time_format_rb_zero.setDisabled(True)

    def add_tool_tips_dlg(self):

        self.keep_filtered_log_cb.setToolTip(
            'If checked, all DECODED logs are saved, otherwise the filtered-out logs are discarded.')
        self.time_format_input.setToolTip('Tips: \n%y, %m, %d: year/month/date in two digits.\n'
                                          '%H, %M, %S: hour/minute/second in two digits\n'
                                          'For more info, check http://strftime.org/')
        self.export_decoded_cb.setToolTip('Whether to save decoded logs.')
        self.export_raw_cb.setToolTip('Raw HEX log is in \'.txt\' format. Filters will not be applied to raw log.\n'
                                      'Note: the raw log can be converted to UEMonitor compatible format.\n'
                                      '(Check \'RawLogFormatConvertor.py\' for more info.')
        self.disp_simplified_log_cb.setToolTip(
            'Do not display the decoded details of the log. This option will not '
            'change the exported log.')

    @pyqtSlot()
    def config_ok_btn_clicked(self):
        # Socket create config
        self.dlg_config['Create socket at start'] = self.create_socket_cb.isChecked()
        self.dlg_config['Enable power monitor module'] = self.enable_power_monitor_cb.isChecked()
        self.dlg_config['Enable GPS module'] = self.enable_gps_module_cb.isChecked()

        # Export config
        self.dlg_config['Export raw'] = self.export_raw_cb.isChecked()
        self.dlg_config['Export decoded'] = self.export_decoded_cb.isChecked()
        self.dlg_config['Keep filtered logs'] = self.keep_filtered_log_cb.isChecked()
        self.dlg_config['Export filename time prefix'] = self.time_format_input.text()
        if self.export_format_rb_txt.isChecked():
            self.dlg_config['Export format'] = 'txt'
        else:
            self.dlg_config['Export format'] = 'csv'

        # Dispaly config
        self.dlg_config['Simplify log'] = self.disp_simplified_log_cb.isChecked()
        if self.disp_time_format_rb_strf.isChecked():
            self.dlg_config['Display time format'] = 'local'
        elif self.disp_time_format_rb_raw.isChecked():
            self.dlg_config['Display time format'] = 'raw'
        elif self.disp_time_format_rb_zero.isChecked():
            self.dlg_config['Display time format'] = 'zero'

        self.config_updated_trigger.emit()



class KeyLogConfigurator(QDialog):

    # TODO: move the key log configurator to a tab in the configuration window
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

        self.CB__RLC_UL_FILL_SRB1_TX_DATA = QCheckBox('RLC_UL_FILL_SRB1_TX_DATA')
        #self.CB__RLC_UL_FILL_SRB1_TX_DATA.setChecked(True)
        self.key_check_box_list.append(self.CB__RLC_UL_FILL_SRB1_TX_DATA)
        self.CB_NAS_DBG_NAS_MSG = QCheckBox('NAS_DBG_NAS_MSG')
        #self.CB_NAS_DBG_NAS_MSG.setChecked(True)
        self.key_check_box_list.append(self.CB_NAS_DBG_NAS_MSG)
        self.CB_ACK = QCheckBox('ACK')
        #self.CB_ACK.setChecked(True)
        self.key_check_box_list.append(self.CB_ACK)
        self.CB_LL1_DCI = QCheckBox('LL1_DCI')
        #self.CB_LL1_DCI.setChecked(True)
        self.key_check_box_list.append(self.CB_LL1_DCI)

        '''
        for item in self.key_log_selection_result:
            check_box_temp = QCheckBox(item)
            self.key_check_box_list.append(check_box_temp)
            check_box_temp.setChecked(True)
        '''
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

