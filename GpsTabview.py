# -*- coding: UTF-8 -*-
import re
import threading
import time
import csv
from PyQt5.QtCore import QUrl
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import QLinearGradient, QColor, QFont
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from DeviceHandlers import GpsController
from utils import *


class GpsTabview(QWidget):

    def __init__(self, file_io, parent=None):

        super(GpsTabview, self).__init__(parent)
        self.file_io = file_io

        g_q_style = YouAreSoQ()
        self.groupbox_stylesheet = g_q_style.groupbox_stylesheet
        self.lb_font = g_q_style.lb_font
        self.middle_lb_font = g_q_style.middle_lb_font
        self.large_lb_font = g_q_style.large_lb_font

        self.btn_font = g_q_style.large_btn_font
        # GPS module specific style
        self.gps_text_edit_stylesheet = "QTextEdit {height: 18px;" \
                                        "width: 80px}"
        self.setStyleSheet(self.gps_text_edit_stylesheet)

        self.lat = '114.197574'  # Latitude
        self.long = '22.32383'  # Longitude

        self.last_lat = ''
        self.last_long = ''

        self.is_the_first_point = True  # no idea what is it...

        self.line_color_choice = 0  # switch between red and blue line.

        self.init_ui()  # prepare the self.x GUI elements
        # self.update_map()
        self.init_map()

        self.gps_handler = None  # init to prevent not found error
        self.gps_file_logger = open('./output_files/gps.csv', 'a')
        self.gps_csv_logger = csv.writer(self.gps_file_logger)

    def init_map(self):
        import os
        map_html_path = 'file://' + os.getcwd() + '/assets/baidu_map_interface.html'
        print('[INFO] GPS map:' + map_html_path)
        # map_html_path = 'http://www.qt.io/'
        self.map_viewer.load(QUrl(map_html_path))

    def init_ui(self):
        # Define layouts
        gps_main_layout = QVBoxLayout()  # the outer layout
        gps_bottom_h_layout = QHBoxLayout()
        gps_info_disp_v_layout = QVBoxLayout()
        gps_control_grid_layout = QGridLayout()
        geolocation_disp_layout = QGridLayout()

        gps_info_disp_gbox = QGroupBox('GPS Info Logs')
        gps_info_disp_gbox.setStyleSheet(self.groupbox_stylesheet)
        gps_info_disp_gbox.setMaximumHeight(200)

        self.map_viewer = QWebEngineView()
        gps_control_gbox = QGroupBox('GPS Control Panel')
        gps_control_gbox.setStyleSheet(self.groupbox_stylesheet)
        gps_control_gbox.setMaximumHeight(200)

        geolocation_disp_gbox = QGroupBox('Geolocation Display')
        geolocation_disp_gbox.setStyleSheet(self.groupbox_stylesheet)
        geolocation_disp_gbox.setMaximumHeight(200)

        # Define widgets
        self.gps_info_monitor = QPlainTextEdit()
        self.gps_info_monitor.setPlaceholderText('Display GPS module info')

        # Result display
        lat_lb = QLabel('Latitude')
        lat_lb.setFont(self.large_lb_font)
        long_lb = QLabel('Longitude')
        long_lb.setFont(self.large_lb_font)

        lat_raw_lb = QLabel('Raw Data')
        lat_raw_lb.setFont(self.lb_font)
        self.lat_raw_ted = QLineEdit('')
        lat_decimal_lb = QLabel('Decimal Degree')
        lat_decimal_lb.setFont(self.lb_font)
        self.lat_decimal_ted = QLineEdit('')
        lat_dms_lb = QLabel('DMS Format')
        lat_dms_lb.setFont(self.lb_font)
        self.lat_dms_ted = QLineEdit('')

        long_raw_lb = QLabel('Raw Data')
        long_raw_lb.setFont(self.lb_font)
        self.lon_raw_ted = QLineEdit('')
        long_decimal_lb = QLabel('Decimal Degree')
        long_decimal_lb.setFont(self.lb_font)
        self.lon_decimal_ted = QLineEdit('')
        long_dms_lb = QLabel('DMS Format')
        long_dms_lb.setFont(self.lb_font)
        self.long_dms_ted = QLineEdit('')

        gps_port_lb = QLabel('GPS Port')
        gps_port_lb.setFont(self.lb_font)

        self.gps_port_cmb = QComboBox()
        available_serials = list_serial_ports()
        self.gps_port_cmb.addItems(available_serials)

        baud_options = [4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        baud_options_str = [str(x) for x in baud_options]
        gps_baud_lb = QLabel('Baud Rate')
        gps_baud_lb.setFont(self.lb_font)

        self.gps_baud_cmb = QComboBox()
        self.gps_baud_cmb.addItems(baud_options_str)
        self.gps_baud_cmb.setCurrentIndex(baud_options_str.index('9600'))

        self.stop_gps_update_btn = QPushButton('Stop Update')
        self.stop_gps_update_btn.clicked.connect(self.btn_fn_stop_auto_update)

        self.start_gps_update_btn = QPushButton('Start Update')
        self.start_gps_update_btn.clicked.connect(self.btn_fn_start_map_update)

        self.auto_update_cb = QCheckBox('Auto Update')
        self.auto_update_cb.setChecked(True)

        self.map_viewer.show()  # display the map html

        gps_info_disp_v_layout.addWidget(self.gps_info_monitor)
        gps_info_disp_gbox.setLayout(gps_info_disp_v_layout)

        # bottom_container_layout.addWidget(self.gps_info_monitor, 0, 0, 4, 4)
        geolocation_disp_layout.addWidget(lat_lb, 0, 4, 1, 1)
        geolocation_disp_layout.addWidget(long_lb, 2, 4, 1, 1)

        geolocation_disp_layout.addWidget(lat_raw_lb, 1, 4, 1, 1)
        geolocation_disp_layout.addWidget(self.lat_raw_ted, 1, 5, 1, 1)
        geolocation_disp_layout.addWidget(lat_decimal_lb, 1, 6, 1, 1)
        geolocation_disp_layout.addWidget(self.lat_decimal_ted, 1, 7, 1, 1)
        geolocation_disp_layout.addWidget(lat_dms_lb, 1, 8, 1, 1)
        geolocation_disp_layout.addWidget(self.lat_dms_ted, 1, 9, 1, 1)

        geolocation_disp_layout.addWidget(long_raw_lb, 3, 4, 1, 1)
        geolocation_disp_layout.addWidget(self.lon_raw_ted, 3, 5, 1, 1)
        geolocation_disp_layout.addWidget(long_decimal_lb, 3, 6, 1, 1)
        geolocation_disp_layout.addWidget(self.lon_decimal_ted, 3, 7, 1, 1)
        geolocation_disp_layout.addWidget(long_dms_lb, 3, 8, 1, 1)
        geolocation_disp_layout.addWidget(self.long_dms_ted, 3, 9, 1, 1)

        gps_control_grid_layout.addWidget(self.auto_update_cb, 0, 1)
        gps_control_grid_layout.addWidget(gps_port_lb, 1, 0)
        gps_control_grid_layout.addWidget(self.gps_port_cmb, 1, 1)
        gps_control_grid_layout.addWidget(gps_baud_lb, 2, 0)
        gps_control_grid_layout.addWidget(self.gps_baud_cmb, 2, 1)
        gps_control_grid_layout.addWidget(self.start_gps_update_btn, 3, 0)
        gps_control_grid_layout.addWidget(self.stop_gps_update_btn, 3, 1)

        geolocation_disp_gbox.setLayout(geolocation_disp_layout)
        gps_control_gbox.setLayout(gps_control_grid_layout)

        gps_bottom_h_layout.addWidget(gps_info_disp_gbox)
        gps_bottom_h_layout.addWidget(geolocation_disp_gbox)
        gps_bottom_h_layout.addWidget(gps_control_gbox)

        # Set the outer layout
        gps_main_layout.addWidget(self.map_viewer)
        gps_main_layout.setStretchFactor(self.map_viewer, 5)
        gps_main_layout.addLayout(gps_bottom_h_layout)
        gps_main_layout.setStretchFactor(gps_bottom_h_layout, 2)

        self.setLayout(gps_main_layout)

    def refresh_map(self, lat, long):
        lat = str(float(lat[:-2]) + 0.011731)  # add a bias to make the map accurate
        long = str(float(long[:-2]) + 0.004051)
        # Lat =str(float(Lat[:-2]))
        # Lon =str(float(Lon[:-2]))

        if self.is_the_first_point:
            # Add point (the first point)
            self.map_viewer.page().runJavaScript('''add_point(''' + lat + ''',''' + long + ''');''')
            self.is_the_first_point = False
            self.last_lat = lat
            self.last_long = long
            self.append_text_to_gps_monitor('[INFO] Add a new Point.')
        else:
            # Add polyline
            if self.last_lat != lat or self.last_long != long:
                if self.line_color_choice == 0:
                    self.map_viewer.page().runJavaScript('''add_polyline(''' + self.last_lat + ''',''' + self.last_long + ''',''' + lat + ''',''' + long + ''',"red");''')
                    self.line_color_choice = 1
                else:
                    self.map_viewer.page().runJavaScript('''add_polyline(''' + self.last_lat + ''',''' + self.last_long + ''',''' + lat + ''',''' + long + '''',"blue");''')
                    self.line_color_choice = 0
                #self.map_viewer.page().runJavaScript('''add_point(''' + Lat + ''',''' + Lon + ''');''')
                self.append_text_to_gps_monitor('[INFO] Add a new point and a trace')
            else:
                self.append_text_to_gps_monitor('[INFO] Location not changed')
            self.last_lat = lat
            self.last_long = long

    @pyqtSlot(name='BTN_FN_START_GPS_UPDATE')
    def btn_fn_start_map_update(self):
        if self.gps_handler is None:
            # Objectify the GPS handler
            gps_com_port = self.gps_port_cmb.currentText()
            gps_baud = self.gps_baud_cmb.currentText()
            self.gps_handler = GpsController(gps_com_port, gps_baud)
            self.gps_handler.start()
            self.append_text_to_gps_monitor('[INFO] GPS streaming started.')
        else:
            # Already created, Check running
            if self.gps_handler.isRunning():
                self.append_text_to_gps_monitor('[WARN] GPS is already streaming.')
            else:
                # Run here only when the thread is stopped and restart.
                self.gps_handler.start()
                self.append_text_to_gps_monitor('[INFO] GPS streaming started.')

        # Make sure the GPS handler get started when run here.
        is_auto_update_chosen = self.auto_update_cb.checkState()  # manual or auto update
        # print('Auto update chosen:', is_auto_update_chosen)
        if is_auto_update_chosen:
            self.gps_handler.gps_trigger.connect(self.gps_finished_one_update)
        else:
            # Manual update
            try:
                self.gps_handler.gps_trigger.disconnect()
            except TypeError:
                # print('[ERROR] The GPS trigger is not connected to anything.')
                pass
            self.append_text_to_gps_monitor('[INFO] Manual update one point.')
            self.gps_finished_one_update()  # run this function for once.

    @pyqtSlot(name='STOP_AUTO_UPDATE')
    def btn_fn_stop_auto_update(self):
        # self.is_manual_update_flag = 0
        if self.gps_handler != None:
            if self.gps_handler.isRunning():
                self.gps_handler.terminate()
                try:
                    self.gps_handler.gps_trigger.disconnect()  # prevent update after termination.
                except TypeError:
                    print('[ERROR] The GPS trigger is not connected to anything.')
                    pass
                self.append_text_to_gps_monitor('[INFO] GPS streaming stopped.')
            else:
                self.append_text_to_gps_monitor('[INFO] There is nothing to stop.')
        else:
            self.append_text_to_gps_monitor('[INFO] GPS is not enabled.')

    @pyqtSlot(name='FETCH_DATA_FROM_GPS')
    def gps_finished_one_update(self):

        self.gps_live_data = self.gps_handler.gps_info_dict.copy()
        if self.gps_live_data['Latitude Deg'] != 'N/A' and self.gps_live_data['Longitude Deg'] != 'N/A':
            # This is a valid point
            print('[INFO] New point\tLat: {0}, Long: {1}'.format(self.gps_live_data['Latitude Deg'],
                                                          self.gps_live_data['Longitude Deg']))
            long = self.gps_live_data['Latitude Deg']
            lat = self.gps_live_data['Longitude Deg']
            # FIXME: gps file IO bookmark
            self.file_io.write_gps_points([time.time(), lat, long])
            self.refresh_map(lat, long)

        self.lat_raw_ted.setText(self.gps_live_data['Latitude Raw'])
        self.lat_decimal_ted.setText(self.gps_live_data['Latitude Deg'])
        self.lat_dms_ted.setText(self.gps_live_data['Latitude'])
        self.lon_raw_ted.setText(self.gps_live_data['Longitude Raw'])
        self.lon_decimal_ted.setText(self.gps_live_data['Longitude Deg'])
        self.long_dms_ted.setText(self.gps_live_data['Longitude'])

    def append_text_to_gps_monitor(self, msg):
        time_stamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        self.gps_info_monitor.appendPlainText(time_stamp + ' ' + msg)
