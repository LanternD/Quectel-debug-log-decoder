'''
Naming convention:
    Groupbox: xx_gbox
    PushButton: xx_btn
    PlanTextEdit: xx_monitor
'''

import csv
import json
import os.path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import time

from device_controller import UeAtController
from log_decoder import *
from run_test_scripts import *
from supporting_windows import *
from utils import *


class MainView(QWidget):

    def __init__(self, parent=None):
        super(MainView, self).__init__(parent)

        self.config = {}
        self.config['UDP local socket'] = 'X'

        # Minor elements
        self.lb_font = QFont("Helvetica", 9)
        self.lb_font.setBold(True)
        self.btn_font = QFont("Helvetica", 14)
        self.btn_font.setBold(True)
        self.groupbox_stylesheet = 'QGroupBox {font-size: 16px;' \
                                   'font-weight: bold;} ' \
                                   'Widget {font-weight: normal;}'

        main_layout = QHBoxLayout(self)
        left_section_layout = QVBoxLayout()
        left_section_layout.setStretch(2, 3)
        mid_section_layout = QVBoxLayout()
        mid_section_layout.setStretch(1, 1)
        right_section_layout = QVBoxLayout()
        right_section_layout.setStretch(1, 1)

        # Find available serial devices.
        available_serials = list_serial_ports()
        print('Available seiral ports:', available_serials)

        # Create main window layout
        self.create_serial_config_module(available_serials)  # self.serial_config_gbox is ready
        self.create_filter_config_module()  # self.filter_config_gbox is ready
        self.create_export_display_config_module()  # self.exp_disp_gbox is ready
        self.create_display_module()  # self.display_gbox is ready
        self.create_controller_module()  # self.controller_gbox is ready
        self.create_live_measurement_module()  # self.live_measurement_display_gbox is ready

        self.add_tool_tips()  # Put tool tips to the components.

        left_section_layout.addWidget(self.serial_config_gbox)
        left_section_layout.addWidget(self.filter_config_gbox)
        left_section_layout.addWidget(self.display_gbox)
        self.controller_gbox.setMaximumWidth(400)

        mid_section_layout.addWidget(self.exp_disp_gbox)
        mid_section_layout.addWidget(self.controller_gbox)

        right_section_layout.addWidget(self.key_info_display_gbox)

        main_layout.addLayout(left_section_layout)
        main_layout.addLayout(mid_section_layout)
        main_layout.addLayout(right_section_layout)
        self.setLayout(main_layout)

        self.set_availability_in_stop_mode()

        self.run_status = False  # Indicate whether it is running or not.
        # self.set_availability_in_running_mode()
        self.registered_configs = ('Device name', 'AT port', 'AT baudrate', 'Dbg port',
                                   'Run in Qt', 'Filter dict', 'Export raw', 'Export decoded',
                                   'Keep filtered logs', 'Export filename time prefix',
                                   'Export format', 'Display time format', 'Create socket at start',
                                   'UDP server IP', 'UDP server port', 'UDP local port',
                                   'AT command 1', 'AT command 2', 'AT command 3',
                                   'UL packet num', 'UL packet len', 'UL packet delay',
                                   'Simplify log', 'Enable live measurement', 'Key log list')
        self.load_config_from_json()

        # Measurement results
        self.main_log_text = ''  # Just a variable that store the txt in main monitor for reference.
        self.sys_log_text = ''  # Same as the above one.
        self.ue_info_dict = {}

        self.ul_mes_thread = None  # Initialization
        self.cm_recorder_thread = None
        self.cm_csv = None
        self.cm_count = 0

    # Create handlers
    def ue_serial_handler(self):
        com_str = self.config['AT port']
        ue_rate = int(self.config['AT baudrate'])
        print('UE:', com_str, ue_rate)
        self.ue_handler = UeAtController(com_str, ue_rate)
        # Close and open the UDP socket, just in case
        self.append_sys_log('Connected to AT UART.')
        if self.config['Create socket at start']:
            _, _ = self.ue_handler.close_udp_socket(0)
            _, _ = self.ue_handler.close_udp_socket(1)  # hope there are no more than 2 sockets
            _, msg_list = self.ue_handler.create_udp_socket(self.config['UDP local port'])
            self.config['UDP local socket'] = msg_list[0]
            print('Socket #:', self.config['UDP local socket'])

    def dbg_serial_handler(self):
        self.decoder = UartOnlineLogDecoder(self.config)
        self.decoder.xml_loader()
        self.decoder.start()
        self.decoder.dbg_uart_trigger.connect(self.dbg_fetch_log)
        self.append_sys_log('Debug decoder Streaming is started.')

    # Create UI zone
    def create_serial_config_module(self, avail_serials):  # The first tab
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
        at_label = QLabel('AT')
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
        dbg_label = QLabel('Debug')
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

        self.main_monitor = QPlainTextEdit()  # Important, display logs
        self.main_monitor.setPlaceholderText('Display AT command response and debug log.')
        self.main_monitor_cursor = self.main_monitor.textCursor()
        self.main_monitor.setFont(QFont('Courier New', 10))
        # self.main_monitor.setMaximumWidth(750)

        self.secondary_monitor = QPlainTextEdit()
        self.secondary_monitor.setPlaceholderText('Display system controlling information, if there is any.')
        self.secondary_monitor.setFixedHeight(100)
        self.secondary_monitor_cursor = self.secondary_monitor.textCursor()
        self.secondary_monitor.setFont(QFont('Courier New', 9))
        # self.secondary_monitor.setMaximumWidth(750)

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
        display_config_lb = QLabel('Display')
        display_config_lb.setFont(self.lb_font)

        self.disp_simplified_log_cb = QCheckBox('Simplify debug log display')
        self.disp_simplified_log_cb.setChecked(True)
        self.disp_simplified_log_cb.stateChanged.connect(self.cbx_fn_simplify_option)

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
        # Button area
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

        self.ping_server_btn.clicked.connect(self.btn_fn_ping_server)
        self.create_socket_btn.clicked.connect(lambda: self.btn_fn_udp_socket_control('create'))
        self.close_socket_btn.clicked.connect(lambda: self.btn_fn_udp_socket_control('close'))

        socket_btn_h_layout.addWidget(self.ping_server_btn)
        socket_btn_h_layout.addWidget(self.create_socket_btn)
        socket_btn_h_layout.addWidget(self.close_socket_btn)

        socket_v_layout.addWidget(socket_lb)
        socket_v_layout.addWidget(self.create_socket_cb)
        socket_v_layout.addLayout(socket_input_h_layout)
        socket_v_layout.addLayout(socket_btn_h_layout)

        # Uplink script control
        ul_script_v_layout = QVBoxLayout()
        ul_script_lb = QLabel('Uplink Script Packet Setting')
        ul_script_lb.setFont(self.lb_font)

        ul_script_v_sub_layout = QVBoxLayout()

        ul_input_h_layout = QHBoxLayout()
        self.ul_packet_num_input = QLineEdit('10')
        self.ul_packet_len_input = QLineEdit('512')
        self.ul_packet_delay_input = QLineEdit('380')

        self.ul_packet_num_input.setMaximumWidth(70)
        self.ul_packet_len_input.setMaximumWidth(50)
        self.ul_packet_delay_input.setMaximumWidth(100)

        self.ul_packet_num_input.setPlaceholderText('Int')
        self.ul_packet_len_input.setPlaceholderText('Int <=512')
        self.ul_packet_delay_input.setPlaceholderText('Int, ms')
        ul_input_h_layout.addWidget(QLabel('Num'))
        ul_input_h_layout.addWidget(self.ul_packet_num_input)
        ul_input_h_layout.addWidget(QLabel('Len (Byte)'))
        ul_input_h_layout.addWidget(self.ul_packet_len_input)
        ul_input_h_layout.addWidget(QLabel('Delay (ms)'))
        ul_input_h_layout.addWidget(self.ul_packet_delay_input)

        ul_ctrl_btn_h_layout = QHBoxLayout()
        self.start_ul_btn = QPushButton('Start UL')
        self.stop_ul_btn = QPushButton('Stop UL')
        # self.start_ul_btn.setMaximumWidth(150)
        # self.stop_ul_btn.setMaximumWidth(150)

        self.start_ul_btn.clicked.connect(lambda: self.btn_fn_ul_test('Start'))
        self.stop_ul_btn.clicked.connect(lambda: self.btn_fn_ul_test('Stop'))

        ul_ctrl_btn_h_layout.addWidget(self.start_ul_btn)
        ul_ctrl_btn_h_layout.addWidget(self.stop_ul_btn)

        ## Append everything to the layout
        ul_script_v_layout.addWidget(ul_script_lb)
        ul_script_v_sub_layout.addLayout(ul_input_h_layout)
        ul_script_v_sub_layout.addLayout(ul_ctrl_btn_h_layout)
        ul_script_v_layout.addLayout(ul_script_v_sub_layout)

        # Misc Ctrl Btn
        misc_btn_v_layout = QVBoxLayout()
        misc_btn_lb = QLabel('Other Buttons')
        misc_btn_lb.setFont(self.lb_font)
        misc_btn_h_sub_layout = QHBoxLayout()

        self.start_dl_btn = QPushButton('Start DL Test')
        self.start_customized_script_btn = QPushButton('Customized Script')

        misc_btn_h_sub_layout.addWidget(self.start_dl_btn)
        misc_btn_h_sub_layout.addWidget(self.start_customized_script_btn)

        misc_btn_v_layout.addWidget(misc_btn_lb)
        misc_btn_v_layout.addLayout(misc_btn_h_sub_layout)

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
        controller_v_layout.addLayout(ul_script_v_layout)
        controller_v_layout.addLayout(misc_btn_v_layout)
        controller_v_layout.addStretch()
        controller_v_layout.addLayout(at_command_v_layout)

        self.controller_gbox.setLayout(controller_v_layout)

    def create_live_measurement_module(self):
        # Live measurement result display + important log display
        self.key_info_display_gbox = QGroupBox('Key Info Display')
        self.key_info_display_gbox.setStyleSheet(self.groupbox_stylesheet)

        key_info_v_layout = QVBoxLayout()

        # Section 1 in key info module
        live_meansurement_lb = QLabel('Live Measurement Results')
        live_meansurement_lb.setFont(self.lb_font)
        self.live_measurement_monitor = QPlainTextEdit()  # The text display region
        self.live_measurement_monitor.setFixedHeight(150)
        self.live_measurement_monitor.setPlaceholderText('Start logging to measure and display the data.')
        # TODO: Find out the key log that contains the interesting measurement result, without reading from AT port

        self.enable_live_measurement_flag = True  # Indicate whether it is running or paused.
        self.pause_and_resume_lm_btn = QPushButton('Pause')
        self.pause_and_resume_lm_btn.clicked.connect(self.btn_fn_pause_or_resume_live_measurement)

        # Section 2 in key info module
        key_log_lb = QLabel('Key Log Display')
        key_log_lb.setFont(self.lb_font)

        self.key_log_options_dialog = KeyLogConfigurator()  # Create here for reference in the get_all_config() function.

        self.select_key_log_btn = QPushButton('Select Key Log to Display')
        self.select_key_log_btn.clicked.connect(self.btn_fn_select_key_log)

        self.key_log_monitor = QPlainTextEdit()
        self.key_log_monitor.setPlaceholderText('List the selected key logs in time order.')
        self.key_log_monitor_cursor = self.key_log_monitor.textCursor()
        self.clear_key_log_btn = QPushButton('Clear Key Logs')

        # Append everything to the layout
        key_info_v_layout.addWidget(live_meansurement_lb)
        key_info_v_layout.addWidget(self.live_measurement_monitor)
        key_info_v_layout.addWidget(self.pause_and_resume_lm_btn)

        key_info_v_layout.addWidget(key_log_lb)
        key_info_v_layout.addWidget(self.select_key_log_btn)
        key_info_v_layout.addWidget(self.key_log_monitor)
        key_info_v_layout.addWidget(self.clear_key_log_btn)

        # Set groupbox layout
        self.key_info_display_gbox.setLayout(key_info_v_layout)
        self.key_info_display_gbox.setMaximumWidth(400)

    # Button functions
    # # AT command buttons
    @pyqtSlot(name='BTN_RSP_SEND_AT_CMD')
    def btn_fn_send_at_command(self, idx):
        input_command = self.at_command_input_list[idx].text().upper()
        print('Send AT Command:', 'AT+' + input_command)
        self.qt_process_at_command(input_command)

    # # Session start/stop control
    @pyqtSlot(name='START_SESSION')
    def btn_fn_start(self):
        if self.get_all_config() == True:
            self.save_config_to_json()

            # Create UE AT handler
            self.ue_serial_handler()
            self.dbg_serial_handler()
            self.set_availability_in_running_mode()
            self.append_sys_log('Start program')
        else:
            # self.append_sys_log('Error in config setting detected.')
            print('Error in config setting detected.')

    @pyqtSlot(name='STOP_SESSION')
    def btn_fn_stop(self):
        # Close the device handlers
        self.ue_handler.ser.close()
        del self.ue_handler
        self.decoder.dbg_run_flag = False
        self.decoder.dbg_uart_handler.close()
        while self.decoder.isRunning():
            continue
        del self.decoder

        self.append_sys_log('Debug port stopped.')

        self.set_availability_in_stop_mode()

    # # Uplink measurement control
    @pyqtSlot(name='START_UL_SCRIPT')
    def btn_fn_ul_test(self, arg):
        if arg == 'Start':

            packet_length = self.ul_packet_len_input.text()
            packet_num = self.ul_packet_num_input.text()
            delay = self.ul_packet_delay_input.text()

            try:
                self.config['UL packet len'] = int(packet_length)
                self.config['UL packet num'] = int(packet_num)
                self.config['UL packet delay'] = int(delay)
            except ValueError:
                self.append_sys_log('[Error] Invalid argument in uplink test settings.')
                return -1

            print('Uplink test setting: num={0}, len={1}, delay={2}'.format(self.config['UL packet num'],
                                                                            self.config['UL packet len'],
                                                                            self.config['UL packet delay']))

            if self.ul_mes_thread is not None and self.ul_mes_thread.isRunning():
                self.append_sys_log('Another uplink test is running.')
            else:
                self.ul_mes_thread = UplinkMeasurement(self.ue_handler, self.config)
                self.ul_mes_thread.ul_trigger.connect(self.uplink_test_thread_processing)
                self.ul_mes_thread.finished.connect(self.uplink_test_thread_processing)
                self.ul_mes_thread.start()
                self.start_ul_btn.setDisabled(True)
                self.stop_ul_btn.setEnabled(True)
        elif arg == 'Stop':
            if self.ul_mes_thread is not None and self.ul_mes_thread.isRunning():
                self.ul_mes_thread.run_flag = False
                self.append_sys_log('Uplink test is terminated.')
            else:
                self.append_sys_log('There is nothing to stop.')
            self.start_ul_btn.setEnabled(True)
            self.stop_ul_btn.setDisabled(True)

    # # Start customized script btn func
    @pyqtSlot(name='BTN_RSP_CUSTOMIZED_SCRIPT')
    def btn_fn_run_customized_script(self):
        # Note: this will not start a new thread. So the UI may not response to your actions.
        # Prepare a .csv list of commands with delay in ms, load and run the script
        script_path = './customized_script.csv'
        if os.path.exists(script_path):
            with open(script_path, 'r') as script_file:
                script_reader = csv.reader(script_file)
                for cmd in script_reader:
                    cmd_buf = cmd[0].split('\t')
                    self.qt_process_at_command(cmd_buf[0])
                    time.sleep(int(cmd_buf[1]) / 1000)
                script_file.close()
        else:
            self.append_sys_log('Script file does not exist. (Name: customized.script.csv. '
                                'Separate command and delay with \\t.)')

    # # Downlink test start button.
    @pyqtSlot(name='BTN_RSP_DOWNLINK_TEST')
    def btn_fn_downlink_test(self):
        self.append_sys_log('Downlink test begins.')
        # Send a small packet to server to trigger the downlink packets transferring from the server.
        self.ue_handler.at_write('NSOST=0,{0},{1},8,FFFFDDDDEEEEAAAA'.format(self.config['UDP server IP'],
                                                                             self.config['UDP server port']))
        time.sleep(0.5)
        self.ue_handler.at_read_has_server_msg()
        # data_len = atc.ser.read(20)
        # print(data_len)
        count = 0
        success_count = 0
        receive_start_time = time.time()
        while count < 10:
            count += 1
            self.ue_handler.at_write('NSORF={0},512'.format(self.config['UDP local socket']))
            print('Packet #', count)
            new_msg, res = self.ue_handler.at_read()
            self.ue_log_text += new_msg
            time_lapse = time.time() - receive_start_time
            print('Timestamp: {0}'.format(time_lapse))
            if len(res) >= 3:
                success_count += 1
            time.sleep(2.9)  # This setting should be consistent with the server one.
            self.display_ue_log()
        print('Success:', success_count)
        self.append_sys_log('Downlink received success: {0}/{1}'.format(success_count, count))

    @pyqtSlot(name='SIMPLIFY_OPTION_CHANGED')
    def cbx_fn_simplify_option(self):
        current_state = self.disp_simplified_log_cb.checkState()
        if current_state:
            self.append_sys_log('Simplify option is set to True.')
        else:
            self.append_sys_log('Simplify option is set to False.')
        if current_state == 0:
            self.config['Simplify log'] = False
        elif current_state == 2:
            self.config['Simplify log'] = True
        else:
            print('Unknown simplify log option.')

    @pyqtSlot(name='PAUSE_OR_RESUME_LIVE_MEASUREMENT')
    def btn_fn_pause_or_resume_live_measurement(self):
        if self.config['Enable live measurement'] is True:
            self.pause_and_resume_lm_btn.setText('Resume')
            self.config['Enable live measurement'] = False  # Toggle the state
        elif self.config['Enable live measurement'] is False:
            self.pause_and_resume_lm_btn.setText('Pause')
            self.config['Enable live measurement'] = True
        else:
            print('Unknown condition occurs.')
        print('Live measurement is toggled. Now is {0}'.format(self.config['Enable live measurement']))

    @pyqtSlot(name='SELECT_KEY_LOG')
    def btn_fn_select_key_log(self):
        self.key_log_options_dialog.exec_()

    # TODO: Add ping server / create socket / close socket button functions

    # # UDP socket buttons
    @pyqtSlot(name='BTN_RSP_PING_SERVER')
    def btn_fn_ping_server(self):
        ip_addr = self.config['UDP server IP']  # '123.206.131.251'
        self.qt_process_at_command('NPING=' + ip_addr)

    @pyqtSlot(name='BTN_RSP_UDP_SOCKET_CONTROL')
    def btn_fn_udp_socket_control(self, arg):
        ip_addr = self.config['UDP server IP']  # '123.206.131.251'
        port = self.config['UDP server port']
        local_port = self.config['UDP local port']
        local_socket = self.config['UDP local socket']
        if arg == 'create':
            # self.qt_process_at_command('NSOCR=DGRAM,17,8889,1')
            new_msg, msg_list = self.ue_handler.create_udp_socket(local_port)
            self.main_log_text += new_msg
            self.display_ue_log(new_msg)
            if len(msg_list) == 2 and msg_list[1] == 'OK':
                self.append_sys_log('UDP socket created successfully.')
            else:
                self.append_sys_log('UDP socket already exists. Change a port if necessary.')
        elif arg == 'close':
            socket_num = self.config['UDP local socket']
            try:
                socket_num = int(socket_num)
            except ValueError:
                socket_num = 0
            new_msg, msg_list = self.ue_handler.close_udp_socket(socket_num)
            self.main_log_text += new_msg  # For reference only
            self.display_ue_log(new_msg)
            if msg_list[0] == 'OK':
                self.append_sys_log('UDP socket closed successfully.')
            else:
                self.append_sys_log('The requested UDP socket does not exist.')
        elif arg == 'send':
            data_to_send = self.socket_send_text.text()  # get texts from widget
            if data_to_send == '':
                self.append_sys_log('No data to send.')
            else:
                packet_length = len(data_to_send) // 2
                combined_command = 'NSOST={0},{1},{2},{3},{4}'.format(local_socket, ip_addr,
                                                                      port, packet_length,
                                                                      data_to_send)
                self.qt_process_at_command(combined_command)

    # Supporting function zone
    ## AT command processing
    def qt_process_at_command(self, input_command):
        # General read and write (special case: read data from server)
        self.append_sys_log('AT+' + input_command)  # Print only the first 50 chars
        self.ue_handler.at_write(input_command)
        msg_from_ue, msg_list = self.ue_handler.at_read()

        formatted_msg = '[AT] ' + msg_from_ue + '\n'
        # print('xxxx', msg_from_ue)
        # print(msg_list)
        self.main_log_text += formatted_msg
        self.display_ue_log(formatted_msg)
        # self.qt_update_ue_panel(msg_list, input_command)

    def display_ue_log(self, new_msg):
        # Put the raw UE feedback to the screen
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
        # Disable section
        self.stop_btn.setDisabled(True)
        self.send_btn_1.setDisabled(True)
        self.send_btn_2.setDisabled(True)
        self.send_btn_3.setDisabled(True)
        self.ping_server_btn.setDisabled(True)
        self.create_socket_btn.setDisabled(True)
        self.close_socket_btn.setDisabled(True)
        self.start_ul_btn.setDisabled(True)
        self.stop_ul_btn.setDisabled(True)
        self.start_customized_script_btn.setDisabled(True)
        self.start_dl_btn.setDisabled(True)
        self.pause_and_resume_lm_btn.setDisabled(True)
        # Enable section
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

        self.select_key_log_btn.setEnabled(True)

    def set_availability_in_running_mode(self):
        # Disable section
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
        self.stop_ul_btn.setDisabled(True)
        self.select_key_log_btn.setDisabled(True)
        # Enable section
        self.stop_btn.setEnabled(True)
        self.send_btn_1.setEnabled(True)
        self.send_btn_2.setEnabled(True)
        self.send_btn_3.setEnabled(True)
        self.ping_server_btn.setEnabled(True)
        self.create_socket_btn.setEnabled(True)
        self.close_socket_btn.setEnabled(True)
        self.start_ul_btn.setEnabled(True)
        self.start_customized_script_btn.setEnabled(True)
        self.start_dl_btn.setEnabled(True)
        self.pause_and_resume_lm_btn.setEnabled(True)
        self.pause_and_resume_lm_btn.setText('Pause')

        self.at_command_input_1.returnPressed.connect(lambda: self.btn_fn_send_at_command(0))
        self.at_command_input_2.returnPressed.connect(lambda: self.btn_fn_send_at_command(1))
        self.at_command_input_3.returnPressed.connect(lambda: self.btn_fn_send_at_command(2))

    def get_all_config(self):
        # Convention: the first letter in the key is capitalized.

        # Serial config
        self.config['Device name'] = self.dev_name_input.text()
        self.config['AT port'] = self.at_port_cbb.currentText()
        self.config['AT baudrate'] = self.at_baud_cbb.currentText()
        self.config['Dbg port'] = self.dbg_port_cbb.currentText()
        self.config['Run in Qt'] = True  # Tell the decoder class to prepare for the Qt env.

        # Check UART port conflicts
        if self.config['AT port'] == self.config['Dbg port']:
            self.append_sys_log('[Error] Cannot choose the same port for AT and Debug log at the same time!')
            return False
        if self.config['AT port'] == '':
            self.append_sys_log('[Error] Unknown AT serial port.')
            return False

        # Filter config
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

        # Export config
        self.config['Export raw'] = self.export_raw_cb.isChecked()
        self.config['Export decoded'] = self.export_decoded_cb.isChecked()
        self.config['Keep filtered logs'] = self.keep_filtered_log_cb.isChecked()
        self.config['Export filename time prefix'] = self.time_format_input.text()
        if self.export_format_rb_txt.isChecked():
            self.config['Export format'] = 'txt'
        else:
            self.config['Export format'] = 'csv'

        # Dispaly config
        self.config['Simplify log'] = self.disp_simplified_log_cb.isChecked()
        if self.disp_time_format_rb_strf.isChecked():
            self.config['Display time format'] = 'local'
        elif self.disp_time_format_rb_raw.isChecked():
            self.config['Display time format'] = 'raw'
        elif self.disp_time_format_rb_zero.isChecked():
            self.config['Display time format'] = 'zero'

        # Socket config
        self.config['Create socket at start'] = self.create_socket_cb.isChecked()
        self.config['UDP server IP'] = self.socket_ip_input.text()
        self.config['UDP server port'] = self.socket_port_input.text()
        self.config['UDP local port'] = self.local_port_input.text()

        # Keep the inputs to prevent typing next time.
        self.config['AT command 1'] = self.at_command_input_1.text()
        self.config['AT command 2'] = self.at_command_input_2.text()
        self.config['AT command 3'] = self.at_command_input_3.text()

        # Uplink packet config
        self.config['UL packet num'] = self.ul_packet_num_input.text()
        self.config['UL packet len'] = self.ul_packet_len_input.text()
        self.config['UL packet delay'] = self.ul_packet_delay_input.text()

        # Special config that is not in the UI:
        self.config['Enable live measurement'] = True
        self.config['Key log list'] = self.key_log_options_dialog.key_log_selection_result

        print('Your configurations:', self.config)
        return True

    def save_config_to_json(self):
        with open('config.json', 'w') as j_file:
            result_json = json.dumps(self.config)
            j_file.write(result_json)
            j_file.flush()
            j_file.close()
            print('All the configurations are saved to config.json.')

    def load_config_from_json(self):
        # Load the data
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

        # Check the integrity of the json file.
        for element in self.registered_configs:
            if element not in last_config:
                print('[Warning] Part of the configs are missing in the "config.json" file. Use default'
                                    'configs instead. Try to successfully start the logging for once to update '
                                    'the config.json file.')
                print('Missing element: \'{0}\''.format(element))
                return 0

        # If there is config data, update the display

        # Serial config
        self.dev_name_input.setText(last_config['Device name'])
        self.at_baud_cbb.setCurrentText(last_config['AT baudrate'])
        available_items = [self.at_port_cbb.itemText(i) for i in range(self.at_port_cbb.count())]
        print(available_items)
        if last_config['AT port'] in available_items:
            self.at_port_cbb.setCurrentText(last_config['AT port'])
        if last_config['Dbg port'] in available_items:
            self.dbg_port_cbb.setCurrentText(last_config['Dbg port'])

        # Filter config
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

        self.create_socket_cb.setChecked(last_config['Create socket at start'])

        # Previous AT command input.
        self.at_command_input_1.setText(last_config['AT command 1'])
        self.at_command_input_2.setText(last_config['AT command 2'])
        self.at_command_input_3.setText(last_config['AT command 3'])

    def add_tool_tips(self):

        self.dev_name_input.setToolTip('This is related to the .xml. '
                                       'Please rename your corresponding XML to '
                                       '"messages_YourDeviceName.xml" and put it '
                                       'in the "decoders" folder.\n'
                                       'If you are using devices other than BC95 and BC28, please update '
                                       'the DebugLogDecoder init() function in "log_decoder.py."')
        self.at_port_cbb.setToolTip('Make sure the port is correct, otherwise the program will crash.')
        self.dbg_port_cbb.setToolTip('Make sure the port is correct, otherwise the program will crash.')

        self.filter_no_rb.setToolTip('No filter, everything is logged.')
        self.filter_in_rb.setToolTip('Keep only the messages with EXACT names in the filter. Others are discarded.')
        self.filter_out_rb.setToolTip('Discard the unwanted logs in the filter. \n'
                                      'Note that this is for display purpose. You can check the "Keep filtered logs"'
                                      'on the right to export the not-showing logs to file.')
        self.filter_input.setToolTip('Separate multiple message names by comma ",".')
        self.keep_filtered_log_cb.setToolTip('If checked, everything is saved, otherwise the filtered-out logs are discarded.')
        self.time_format_input.setToolTip('Tips: \n%y, %m, %d: year/month/date in two digits.\n'
                                  '%H, %M, %S: hour/minute/second in two digits\n'
                                  'For more info, check http://strftime.org/')
        self.export_decoded_cb.setToolTip('Whether to save decoded logs.')
        self.export_raw_cb.setToolTip('Raw HEX log is in .txt format. No log will be discarded.')
        self.start_btn.setToolTip('Create AT and debug serial handler and start recording the logs.\n'
                                  'Every time you start will generate a new log file.')
        self.stop_btn.setToolTip('Stop the logging, delete the serial handlers.')
        self.at_command_input_1.setToolTip('You can also press Enter to send the command. The three input fields are equivalent')
        self.disp_simplified_log_cb.setToolTip('If checked, the details of the log is not displayed. This option will not'
                                               'change the exported log.')
        self.create_socket_btn.setToolTip('Only works when no socket exists.')
        self.close_socket_btn.setToolTip('Only works when sockets exist.')

    # Multithread signal processing
    # # Debug decoder signal slots
    @pyqtSlot(name='THREAD_FETCH_LOG')
    def dbg_fetch_log(self):
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

        # TODO: the following function is called everytime we enter the fetch log runtime. Add an update period to it if necessary.
        if self.config['Enable live measurement'] is True:
            # Update the live measurement monitor only this feature is enabled.
            msg = self.format_live_measurement_result(self.decoder.live_measurement_buf)
            self.live_measurement_monitor.setPlainText(msg)

    def format_live_measurement_result(self, mes_dict):
        # Format the result and display it in the top right PlainTextEdit
        # Order: ECL, CSQ, RSRP, SNR, Cell ID, Current state, last update time
        candidate_list = ['ECL', 'CSQ', 'RSRP', 'SNR', 'Cell ID', 'Current state', 'Last update']
        msg = ''
        for item in candidate_list:
            try:
                val = str(mes_dict[item])
            except KeyError:
                print('Key {0} is not in the given dictionary.'.format(item))
                val = 'N/A'
            msg += '{0}={1}\n'.format(item, val)
            if item == candidate_list[-2]:
                msg += '\n'  # Add a separate line between the last update timestamp.
        return msg

    # # Uplink test signal slots
    @pyqtSlot(name='THREAD_PROCESS_UPLINK_TEST')
    def uplink_test_thread_processing(self):
        fetched_data = self.ul_mes_thread.intermediate_output
        if fetched_data['System log list']:
            for items in fetched_data['System log list']:
                self.append_sys_log(items)
                if items == 'ULT: uplink test finished.\n':
                    self.start_ul_btn.setEnabled(True)  # the test finishes, swap the button availability.
                    self.stop_ul_btn.setDisabled(True)
            fetched_data['System log list'] = []
        if fetched_data['AT result'] != '':
            self.display_ue_log(fetched_data['AT result'])
            fetched_data['AT result'] = ''
