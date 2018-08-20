from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import time
import csv
import json
import os.path
from device_controller import UeAtController
from log_decoder import *
from utils import *

class MainView(QWidget):

    def __init__(self, parent=None):
        super(MainView, self).__init__(parent)

        self.config = {}

        # minor elements
        self.lb_font = QFont("Helvetica", 9)
        self.lb_font.setBold(True)
        self.btn_font = QFont("Helvetica", 14)
        self.btn_font.setBold(True)
        self.groupbox_stylesheet = 'QGroupBox {font-size: 16px;' \
                                   'font-weight: bold;} ' \
                                   'Widget {font-weight: normal;}'

        # Create device handler
        # self.ue_serial_handler()

        main_layout = QHBoxLayout(self)
        left_section_layout = QVBoxLayout()
        left_section_layout.setStretch(2, 2)
        right_section_layout = QVBoxLayout()
        right_section_layout.setStretch(1, 1)

        # find available serial devices.
        available_serials = list_serial_ports()
        print('Available seiral ports:', available_serials)

        # create main window layout
        self.create_serial_config_module(available_serials)
        self.create_filter_config_module()
        self.create_export_display_config_module()
        self.create_display_module()
        self.create_controller_module()

        left_section_layout.addWidget(self.serial_config_gbox)
        left_section_layout.addWidget(self.filter_config_gbox)
        left_section_layout.addWidget(self.display_gbox)
        self.controller_gbox.setMaximumWidth(400)

        right_section_layout.addWidget(self.exp_disp_gbox)
        right_section_layout.addWidget(self.controller_gbox)
        main_layout.addLayout(left_section_layout)
        main_layout.addLayout(right_section_layout)
        self.setLayout(main_layout)

        self.set_availability_in_stop_mode()

        self.run_status = False  # indicate whether it is running or not.
        # self.set_availability_in_running_mode()

        self.load_config_from_json()

        # measurement results
        self.main_log_text = ''
        self.sys_log_text = ''
        self.ue_info_dict = {}
        self.gps_live_data = {}

        self.ul_mes_thread = None  # initialization
        self.cm_recorder_thread = None
        self.cm_csv = None
        self.cm_count = 0

    # Create handlers
    def ue_serial_handler(self):
        com_str = self.config['AT port']
        ue_rate = int(self.config['AT baudrate'])
        print('UE:', com_str, ue_rate)
        self.ue_handler = UeAtController(com_str, ue_rate)
        # close and open the UDP socket, just in case
        self.append_sys_log('Connected to AT UART.')
        if self.config['Create socket at start']:
            _, _ = self.ue_handler.close_udp_socket(0)
            _, _ = self.ue_handler.close_udp_socket(1)
            _, msg_list = self.ue_handler.create_udp_socket(self.config['UDP local port'])
            self.config['Local UDP socket'] = msg_list[0]
            print('Socket #:', self.config['Local UDP socket'])

    def dbg_serial_handler(self):
        self.decoder = UartOnlineLogDecoder(self.config)
        self.decoder.xml_loader()
        self.decoder.start()
        self.decoder.dbg_uart_trigger.connect(self.dbg_fetch_log)
        self.append_sys_log('Debug decoder Streaming is started.')

    # Create UI zone
    def create_serial_config_module(self, avail_serials):  # the first tab
        self.serial_config_gbox = QGroupBox('Serial Configuration')
        self.serial_config_gbox.setStyleSheet(self.groupbox_stylesheet)
        config_h_layout = QHBoxLayout()

        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setFrameShadow(QFrame.Sunken)

        vline1 = QFrame()
        vline1.setFrameShape(QFrame.VLine)
        vline1.setFrameShadow(QFrame.Sunken)

        # Device name
        dev_name_lb = QLabel('Device Name')
        dev_name_lb.setFont(self.lb_font)
        self.dev_name_input = QLineEdit('BC95')
        self.dev_name_input.setMaximumWidth(50)

        # AT command port
        at_label = QLabel('AT UART')
        at_label.setFont(self.lb_font)
        at_port_label = QLabel('Port')
        self.at_port_cbb = QComboBox()
        self.at_port_cbb.addItems(avail_serials)
        self.at_port_cbb.setCurrentIndex(1)

        baud_options = [4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        baud_options_str = [str(x) for x in baud_options]
        at_baud_label = QLabel('Baud')
        self.at_baud_cbb = QComboBox()
        self.at_baud_cbb.addItems(baud_options_str)
        self.at_baud_cbb.setCurrentIndex(baud_options_str.index('9600'))

        # Debug info output config
        dbg_label = QLabel('Debug UART')
        dbg_label.setFont(self.lb_font)
        dbg_port_label = QLabel('Port')
        self.dbg_port_cbb = QComboBox()
        self.dbg_port_cbb.addItems(avail_serials)
        self.dbg_port_cbb.setCurrentIndex(avail_serials.index(avail_serials[-1]))
        dbg_baud_info = QLabel('Baud: 921600')

        # Layout loading
        config_h_layout.addWidget(dev_name_lb)
        config_h_layout.addWidget(self.dev_name_input)
        config_h_layout.addWidget(vline)
        config_h_layout.addWidget(at_label)
        config_h_layout.addWidget(at_port_label)
        config_h_layout.addWidget(self.at_port_cbb)
        config_h_layout.addWidget(at_baud_label)
        config_h_layout.addWidget(self.at_baud_cbb)
        config_h_layout.addWidget(vline1)

        config_h_layout.addWidget(dbg_label)
        config_h_layout.addWidget(dbg_port_label)
        config_h_layout.addWidget(self.dbg_port_cbb)
        config_h_layout.addWidget(dbg_baud_info)

        config_h_layout.addStretch()

        self.serial_config_gbox.setLayout(config_h_layout)

    def create_filter_config_module(self):
        self.filter_config_gbox = QGroupBox('Filter Settings')
        self.filter_config_gbox.setStyleSheet(self.groupbox_stylesheet)

        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setFrameShadow(QFrame.Sunken)

        filter_h_layout = QHBoxLayout()

        filter_choice_lb = QLabel('Filter Type')
        filter_choice_lb.setFont(self.lb_font)

        self.filter_no_rb = QRadioButton('No Filter')
        self.filter_no_rb.setChecked(True)
        self.filter_in_rb = QRadioButton('Filter-In')
        self.filter_out_rb = QRadioButton('Filter-Out')
        filter_text_lb = QLabel('Filter')
        filter_text_lb.setFont(self.lb_font)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText('e.g. APPLICATION_REPORT')
        self.filter_input.setMinimumWidth(180)

        filter_h_layout.addWidget(filter_choice_lb)
        filter_h_layout.addWidget(self.filter_no_rb)
        filter_h_layout.addWidget(self.filter_in_rb)
        filter_h_layout.addWidget(self.filter_out_rb)
        filter_h_layout.addWidget(vline)
        filter_h_layout.addWidget(filter_text_lb)
        filter_h_layout.addWidget(self.filter_input)
        # filter_h_layout.addStretch()

        self.filter_config_gbox.setLayout(filter_h_layout)

    def create_display_module(self):

        self.display_gbox = QGroupBox('AT and Debug Info Display')
        self.display_gbox.setStyleSheet(self.groupbox_stylesheet)

        disp_v_layout = QVBoxLayout()
        disp_v_layout.setStretch(1, 1)

        self.main_monitor = QPlainTextEdit()  # important, display logs
        self.main_monitor.setPlaceholderText('Display AT command response and debug log.')
        self.main_monitor_cursor = self.main_monitor.textCursor()
        self.main_monitor.setFont(QFont('Courier New', 10))

        self.secondary_monitor = QPlainTextEdit()
        self.secondary_monitor.setPlaceholderText('Display system controlling information, if there is any.')
        self.secondary_monitor.setFixedHeight(100)
        self.secondary_monitor_cursor = self.secondary_monitor.textCursor()
        self.secondary_monitor.setFont(QFont('Courier New', 9))

        disp_v_layout.addWidget(self.main_monitor)
        disp_v_layout.addWidget(self.secondary_monitor)

        self.display_gbox.setLayout(disp_v_layout)

    def create_export_display_config_module(self):
        self.exp_disp_gbox = QGroupBox('Export and Display Configurations')
        self.exp_disp_gbox.setMaximumWidth(400)
        self.exp_disp_gbox.setMinimumWidth(350)
        self.exp_disp_gbox.setStyleSheet(self.groupbox_stylesheet)

        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)

        config_v_layout = QVBoxLayout()

        # Export configuration
        export_lb = QLabel('Export')
        export_lb.setFont(self.lb_font)

        log_type_lb = QLabel('Choose export content')

        export_h_layout = QHBoxLayout()

        self.export_raw_cb = QCheckBox('Raw log')
        self.export_raw_cb.setChecked(True)
        self.export_raw_cb.setToolTip('Raw log is in .txt format. It will record everything.')

        self.export_decoded_cb = QCheckBox('Decoded log')
        self.export_decoded_cb.setChecked(True)
        self.export_decoded_cb.setToolTip('Whether to save decoded logs.')

        self.keep_filtered_log_cb = QCheckBox('Keep filtered logs')
        self.keep_filtered_log_cb.setToolTip(
            'If checked, everything is saved, otherwise the filtered logs are discarded.')

        export_h_layout.addWidget(self.export_raw_cb)
        export_h_layout.addWidget(self.export_decoded_cb)
        export_h_layout.addWidget(self.keep_filtered_log_cb)
        export_h_layout.addStretch()

        time_format_h_layout = QHBoxLayout()
        time_format_lb = QLabel('File name time format')
        time_format_lb.setToolTip('Tips: \n%y, %m, %d: year/month/date in two digits.\n'
                                  '%H, %M, %S: hour/minute/second in two digits\n'
                                  'For more info, check http://strftime.org/')
        self.time_format_input = QLineEdit('%y%m%d_%H%M%S')
        self.time_format_input.setMaximumWidth(200)
        time_format_h_layout.addWidget(time_format_lb)
        time_format_h_layout.addWidget(self.time_format_input)
        time_format_h_layout.addStretch(1)

        export_format_h_layout = QHBoxLayout()
        export_format_bg = QButtonGroup(export_format_h_layout)
        export_format_lb = QLabel('File format')
        self.export_format_rb_txt = QRadioButton('txt')

        self.export_format_rb_csv = QRadioButton('csv')
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
        display_config_lb = QLabel('Time Display Configuration')
        display_config_lb.setFont(self.lb_font)
        # disp_time_format_lb = QLabel('Display time format')
        self.disp_time_format_rb_strf = QRadioButton('Local Time (e.g. 18-08-18 10:11:55.12353)')
        self.disp_time_format_rb_raw = QRadioButton('Raw time (e.g. 1534575622.4211376')
        self.disp_time_format_rb_zero = QRadioButton('0-offset (e.g. 0.4211376)')
        self.disp_time_format_rb_zero.setChecked(True)

        disp_time_format_bg.addButton(self.disp_time_format_rb_strf)
        disp_time_format_bg.addButton(self.disp_time_format_rb_raw)
        disp_time_format_bg.addButton(self.disp_time_format_rb_zero)

        disp_v_layout.addWidget(display_config_lb)
        disp_v_layout.addWidget(self.disp_time_format_rb_strf)
        disp_v_layout.addWidget(self.disp_time_format_rb_raw)
        disp_v_layout.addWidget(self.disp_time_format_rb_zero)

        config_v_layout.addWidget(export_lb)
        config_v_layout.addWidget(log_type_lb)
        config_v_layout.addLayout(export_h_layout)
        config_v_layout.addLayout(time_format_h_layout)
        config_v_layout.addLayout(export_format_h_layout)
        config_v_layout.addWidget(hline)
        config_v_layout.addLayout(disp_v_layout)

        self.exp_disp_gbox.setLayout(config_v_layout)

    def create_controller_module(self):
        self.controller_gbox = QGroupBox('Controller Panel')
        self.controller_gbox.setStyleSheet(self.groupbox_stylesheet)
        self.controller_gbox.setMaximumWidth(400)
        self.controller_gbox.setMinimumWidth(350)

        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        hline.setFrameShadow(QFrame.Sunken)

        controller_v_layout = QVBoxLayout()
        # button area
        button_h_layout = QHBoxLayout()

        self.start_btn = QPushButton('Start')
        self.start_btn.setFont(self.btn_font)
        self.start_btn.setMinimumWidth(80)
        self.start_btn.setMinimumHeight(50)

        self.stop_btn = QPushButton('Stop')
        self.stop_btn.setFont(self.btn_font)

        self.stop_btn.setMinimumWidth(80)
        self.stop_btn.setMinimumHeight(50)

        self.start_btn.clicked.connect(self.btn_fn_start)
        self.stop_btn.clicked.connect(self.btn_fn_stop)

        button_h_layout.addWidget(self.start_btn)
        button_h_layout.addWidget(self.stop_btn)

        socket_v_layout = QVBoxLayout()
        socket_lb = QLabel('Socket Actions')
        socket_lb.setFont(self.lb_font)
        socket_input_h_layout = QHBoxLayout()
        self.create_socket_cb = QCheckBox('Create socket at starting')
        self.create_socket_cb.setChecked(True)
        socket_ip_lb = QLabel('Server IP')
        self.socket_ip_input = QLineEdit('123.206.131.251')
        socket_port_lb = QLabel('Port')
        self.socket_port_input = QLineEdit('59986')
        self.socket_port_input.setMaximumWidth(45)
        local_port_lb = QLabel('Local port')
        self.local_port_input = QLineEdit('8889')
        self.local_port_input.setMaximumWidth(40)

        socket_input_h_layout.addWidget(socket_ip_lb)
        socket_input_h_layout.addWidget(self.socket_ip_input)
        socket_input_h_layout.addWidget(socket_port_lb)
        socket_input_h_layout.addWidget(self.socket_port_input)
        socket_input_h_layout.addWidget(local_port_lb)
        socket_input_h_layout.addWidget(self.local_port_input)

        socket_btn_h_layout = QHBoxLayout()
        self.ping_server_btn = QPushButton('Ping server')
        self.create_socket_btn = QPushButton('Create socket')
        self.close_socket_btn = QPushButton('Close socket')

        socket_btn_h_layout.addWidget(self.ping_server_btn)
        socket_btn_h_layout.addWidget(self.create_socket_btn)
        socket_btn_h_layout.addWidget(self.close_socket_btn)

        socket_v_layout.addWidget(socket_lb)
        socket_v_layout.addWidget(self.create_socket_cb)
        socket_v_layout.addLayout(socket_input_h_layout)
        socket_v_layout.addLayout(socket_btn_h_layout)

        # AT command inputs
        at_command_v_layout = QVBoxLayout()

        at_lb = QLabel('AT Command Input')
        at_lb.setFont(self.lb_font)
        input_row_1 = QHBoxLayout()
        input_row_2 = QHBoxLayout()
        input_row_3 = QHBoxLayout()
        alert_row = QHBoxLayout()
        # at_command_gbox.setMaximumWidth(500)
        at_command_v_layout.setStretch(1, 1)

        self.at_command_input_1 = QLineEdit('CSQ')
        self.at_command_input_2 = QLineEdit('NUESTATS=CELL')
        self.at_command_input_3 = QLineEdit('NUESTATS=RADIO')

        self.at_command_input_1.returnPressed.connect(lambda: self.btn_fn_send_at_command(0))
        self.at_command_input_2.returnPressed.connect(lambda: self.btn_fn_send_at_command(1))
        self.at_command_input_3.returnPressed.connect(lambda: self.btn_fn_send_at_command(2))

        input_row_1.addWidget(self.at_command_input_1)
        input_row_2.addWidget(self.at_command_input_2)
        input_row_3.addWidget(self.at_command_input_3)

        self.at_command_input_list = [self.at_command_input_1,
                                      self.at_command_input_2,
                                      self.at_command_input_3]

        self.send_btn_1 = QPushButton('Send')
        self.send_btn_2 = QPushButton('Send')
        self.send_btn_3 = QPushButton('Send')

        self.send_btn_1.clicked.connect(lambda: self.btn_fn_send_at_command(0))
        self.send_btn_2.clicked.connect(lambda: self.btn_fn_send_at_command(1))
        self.send_btn_3.clicked.connect(lambda: self.btn_fn_send_at_command(2))

        input_row_1.addWidget(self.send_btn_1)
        input_row_2.addWidget(self.send_btn_2)
        input_row_3.addWidget(self.send_btn_3)

        self.at_command_label = QLabel('Note: don\'t need to add \'AT+\' in the input.')
        alert_row.addWidget(self.at_command_label)

        at_command_v_layout.addWidget(at_lb)
        at_command_v_layout.addLayout(input_row_1)
        at_command_v_layout.addLayout(input_row_2)
        at_command_v_layout.addLayout(input_row_3)
        at_command_v_layout.addLayout(alert_row)

        controller_v_layout.addLayout(button_h_layout)
        controller_v_layout.addWidget(hline)
        controller_v_layout.addLayout(socket_v_layout)
        controller_v_layout.addStretch()
        controller_v_layout.addLayout(at_command_v_layout)

        self.controller_gbox.setLayout(controller_v_layout)

    # # at command buttons
    @pyqtSlot(name='BTN_RSP_SEND_AT_CMD')
    def btn_fn_send_at_command(self, idx):
        input_command = self.at_command_input_list[idx].text().upper()
        print('Send AT Command:', 'AT+' + input_command)
        self.qt_process_at_command(input_command)

    @pyqtSlot(name='START_SESSION')
    def btn_fn_start(self):
        self.get_all_config()
        self.save_config_to_json()

        # create UE AT handler
        self.ue_serial_handler()
        self.dbg_serial_handler()
        self.set_availability_in_running_mode()
        self.append_sys_log('Start program')


    @pyqtSlot(name='STOP_SESSION')
    def btn_fn_stop(self):
        # close the device handlers
        self.ue_handler.ser.close()
        del self.ue_handler
        self.decoder.dbg_run_flag = False
        self.decoder.dbg_uart_handler.close()
        while self.decoder.isRunning():
            continue
        del self.decoder

        self.append_sys_log('Debug port stopped.')

        self.set_availability_in_stop_mode()
    # '''
    # Supporting function zone
    # '''
    # AT command processing zone
    def qt_process_at_command(self, input_command):
        # general read and write (special case: read data from server)
        self.append_sys_log('AT+' + input_command)  # print only the first 50 chars
        self.ue_handler.at_write(input_command)
        msg_from_ue, msg_list = self.ue_handler.at_read()
        # print('xxxx', msg_from_ue)
        # print(msg_list)
        self.main_log_text += msg_from_ue
        self.display_ue_log(msg_from_ue)
        # self.qt_update_ue_panel(msg_list, input_command)

    def display_ue_log(self, new_msg):
        # put the raw UE feedback to the screen
        # self.main_monitor.setPlainText(self.main_log_text)
        self.main_monitor.insertPlainText(new_msg)
        self.main_monitor_cursor.movePosition(QTextCursor.End)
        self.main_monitor.setTextCursor(self.main_monitor_cursor)

    def append_sys_log(self, text_to_append):
        self.sys_log_text += text_to_append + '\n'
        self.secondary_monitor.insertPlainText(text_to_append + '\n')
        self.secondary_monitor_cursor.movePosition(QTextCursor.End)
        self.secondary_monitor.setTextCursor(self.secondary_monitor_cursor)

    def set_availability_in_stop_mode(self):
        # disable section
        self.stop_btn.setDisabled(True)
        self.send_btn_1.setDisabled(True)
        self.send_btn_2.setDisabled(True)
        self.send_btn_3.setDisabled(True)
        self.ping_server_btn.setDisabled(True)
        self.create_socket_btn.setDisabled(True)
        self.close_socket_btn.setDisabled(True)
        # enable section
        self.dev_name_input.setEnabled(True)
        self.at_port_cbb.setEnabled(True)
        self.at_baud_cbb.setEnabled(True)
        self.dbg_port_cbb.setEnabled(True)
        self.export_raw_cb.setEnabled(True)
        self.export_decoded_cb.setEnabled(True)
        self.keep_filtered_log_cb.setEnabled(True)
        self.export_format_rb_txt.setEnabled(True)
        self.export_format_rb_csv.setEnabled(True)
        self.time_format_input.setEnabled(True)
        self.disp_time_format_rb_strf.setEnabled(True)
        self.disp_time_format_rb_raw.setEnabled(True)
        self.disp_time_format_rb_zero.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.create_socket_cb.setEnabled(True)

        self.filter_no_rb.setEnabled(True)
        self.filter_in_rb.setEnabled(True)
        self.filter_out_rb.setEnabled(True)
        self.filter_input.setEnabled(True)

        self.at_command_input_1.returnPressed.disconnect()
        self.at_command_input_2.returnPressed.disconnect()
        self.at_command_input_3.returnPressed.disconnect()

    def set_availability_in_running_mode(self):
        # disable section
        self.dev_name_input.setDisabled(True)
        self.at_port_cbb.setDisabled(True)
        self.at_baud_cbb.setDisabled(True)
        self.dbg_port_cbb.setDisabled(True)
        self.export_raw_cb.setDisabled(True)
        self.export_decoded_cb.setDisabled(True)
        self.keep_filtered_log_cb.setDisabled(True)
        self.export_format_rb_txt.setDisabled(True)
        self.export_format_rb_csv.setDisabled(True)
        self.time_format_input.setDisabled(True)
        self.disp_time_format_rb_strf.setDisabled(True)
        self.disp_time_format_rb_raw.setDisabled(True)
        self.disp_time_format_rb_zero.setDisabled(True)
        self.start_btn.setDisabled(True)
        self.create_socket_cb.setDisabled(True)
        self.filter_no_rb.setDisabled(True)
        self.filter_in_rb.setDisabled(True)
        self.filter_out_rb.setDisabled(True)
        self.filter_input.setDisabled(True)
        # enable section
        self.stop_btn.setEnabled(True)
        self.send_btn_1.setEnabled(True)
        self.send_btn_2.setEnabled(True)
        self.send_btn_3.setEnabled(True)
        self.ping_server_btn.setEnabled(True)
        self.create_socket_btn.setEnabled(True)
        self.close_socket_btn.setEnabled(True)

        self.at_command_input_1.returnPressed.connect(lambda: self.btn_fn_send_at_command(0))
        self.at_command_input_2.returnPressed.connect(lambda: self.btn_fn_send_at_command(1))
        self.at_command_input_3.returnPressed.connect(lambda: self.btn_fn_send_at_command(2))

    def get_all_config(self):
        # Convention: the first letter in the key is capitalized.

        # serial config
        self.config['Device name'] = self.dev_name_input.text()
        self.config['AT port'] = self.at_port_cbb.currentText()
        self.config['AT baudrate'] = self.at_baud_cbb.currentText()
        self.config['Dbg port'] = self.dbg_port_cbb.currentText()
        self.config['Run in Qt'] = True  # tell the decoder class to prepare for the Qt env.

        # filter config
        self.config['Filter dict'] = {'FO': [], 'FI': []}
        if self.filter_no_rb.isChecked() is False:
            filter_str = self.filter_input.text()
            filter_list = string_to_list(filter_str)
            if self.filter_in_rb.isChecked():
                self.config['Filter dict']['FI'] = filter_list
            else:
                self.config['Filter dict']['FO'] = filter_list
        else:
            self.config['Filter dict']['FO'] = []
            self.config['Filter dict']['FI'] = []

        # export config
        self.config['Export raw'] = self.export_raw_cb.isChecked()
        self.config['Export decoded'] = self.export_decoded_cb.isChecked()
        self.config['Keep filtered logs'] = self.keep_filtered_log_cb.isChecked()
        self.config['Export filename time prefix'] = self.time_format_input.text()
        if self.export_format_rb_txt.isChecked():
            self.config['Export format'] = 'txt'
        else:
            self.config['Export format'] = 'csv'

        # dispaly config
        if self.disp_time_format_rb_strf.isChecked():
            self.config['Display time format'] = 'local'
        elif self.disp_time_format_rb_raw.isChecked():
            self.config['Display time format'] = 'raw'
        elif self.disp_time_format_rb_zero.isChecked():
            self.config['Display time format'] = 'zero'

        # socket config
        self.config['Create socket at start'] = self.create_socket_cb.isChecked()
        self.config['UDP server IP'] = self.socket_ip_input.text()
        self.config['UDP server port'] = self.socket_port_input.text()
        self.config['UDP local port'] = self.local_port_input.text()

        print(self.config)

    def save_config_to_json(self):
        with open('config.json', 'w') as j_file:
            result_json = json.dumps(self.config)
            j_file.write(result_json)
            j_file.flush()
            j_file.close()
            print('All the configurations are saved to config.json.')

    def load_config_from_json(self):
        # load the data
        json_path = './config.json'
        if os.path.exists(json_path):
            with open(json_path, 'r') as j_file:
                read_data = j_file.read()
                try:
                    json_data = json.loads(read_data)
                except json.decoder.JSONDecodeError:
                    print('Json file corrupted. No previous configs. Load default settings.')
                    j_file.close()
                    return 0
                # print(json_data)
                last_config = json_data
                j_file.close()
        else:
            print('config.json does not exist.')
            return 0

        # if there is config data, update the display

        # serial config
        self.dev_name_input.setText(last_config['Device name'])
        self.at_baud_cbb.setCurrentText(last_config['AT baudrate'])
        available_items = [self.at_port_cbb.itemText(i) for i in range(self.at_port_cbb.count())]
        print(available_items)
        if last_config['AT port'] in available_items:
            self.at_port_cbb.setCurrentText(last_config['AT port'])
        if last_config['Dbg port'] in available_items:
            self.dbg_port_cbb.setCurrentText(last_config['Dbg port'])

        # filter config
        if last_config['Filter dict']['FO'] != []:
            my_set = last_config['Filter dict']['FO']
            self.filter_out_rb.setChecked(True)
        elif last_config['Filter dict']['FI'] != []:
            my_set = last_config['Filter dict']['FI']
            self.filter_in_rb.setChecked(True)
        else:
            my_set = {}
            self.filter_no_rb.setChecked(True)
        filter_str = list_to_string(my_set)
        self.filter_input.setText(filter_str)

        # export config
        self.export_raw_cb.setChecked(last_config['Export raw'])
        self.export_decoded_cb.setChecked(last_config['Export decoded'])
        self.keep_filtered_log_cb.setChecked(last_config['Keep filtered logs'])
        self.time_format_input.setText(last_config['Export filename time prefix'])
        if last_config['Export format'] == 'txt':
            self.export_format_rb_txt.setChecked(True)
        else:
            self.export_format_rb_csv.setChecked(True)

        # display config
        disp_format = last_config['Display time format']
        if disp_format == 'local':
            self.disp_time_format_rb_strf.setChecked(True)
        elif disp_format == 'raw':
            self.disp_time_format_rb_raw.setChecked(True)
        elif disp_format == 'zero':
            self.disp_time_format_rb_zero.setChecked(True)

        self.create_socket_cb.setChecked(last_config['Create socket at start'])

    # Multithread signal processing
    # # debug decoder signal slots
    @pyqtSlot(name='THREAD_PROCESS_GPS')
    def dbg_fetch_log(self):
        # print(self.gps_info_dict_buf)
        new_log = self.decoder.transfer_buf.copy()
        self.decoder.transfer_buf = []
        if new_log != []:
            for log in new_log:
                self.main_log_text += log
                self.display_ue_log(log)

        new_sys_info = self.decoder.sys_info_buf.copy()
        self.decoder.sys_info_buf = []
        if new_sys_info != []:
            for sys_info in new_sys_info:
                self.append_sys_log(sys_info)