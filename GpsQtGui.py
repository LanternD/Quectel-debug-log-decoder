# -*- coding: UTF-8 -*-
import re
import threading
import time
from PyQt5.QtCore import QUrl
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtCore import *
from PyQt5.QtGui import QLinearGradient, QColor, QFont
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from DeviceHandlers import GpsController
from utils import list_serial_ports


class GPSTabview(QWidget):

    def __init__(self, parent=None):

        super(GPSTabview, self).__init__(parent)

        self.Lat = '114.197574'  # Latitude
        self.Lon = '22.32383'  # Longitude

        self.Last_Lat = ''
        self.Last_Lon = ''

        self.flag = -1
        self.gps_flag = 0
        self.map_flag = 0
        self.line_color_flag = 0

        gps_main_layout = QVBoxLayout(self)
        available_serials = list_serial_ports()
        self.groupbox_stylesheet = 'QGroupBox {font-size: 16px;' \
                                   'font-weight: bold;} ' \
                                   'Widget {font-weight: normal;}'
        self.layout_map = QVBoxLayout()
        self.contral_panel = QGroupBox('GPS Informaiton')
        self.contral_panel.setStyleSheet(self.groupbox_stylesheet)
        self.map_viewer = QWebEngineView()
        self.init_ui(available_serials)
        # self.update_map()
        self.layout_map.addWidget(self.map_viewer)
        gps_main_layout.addLayout(self.layout_map)
        gps_main_layout.setStretchFactor(self.layout_map, 5)
        gps_main_layout.addWidget(self.contral_panel)
        gps_main_layout.setStretchFactor(self.contral_panel, 2)
        self.setLayout(gps_main_layout)
        self.init_map()

    def init_map(self):
        map_string = './assets/baidu_map_interface.html'
        self.map_viewer.load(QUrl(map_string))

    def init_ui(self, available_serials):
        contral_layout = QHBoxLayout()
        container_layout = QGridLayout()
        Lat_label = QtGui.QLabel('Latitude:')
        Lat_label.setFont(QFont('Arial', 14))
        Lon_label = QtGui.QLabel('Longitude:')
        Lon_label.setFont(QFont('Arial', 14))

        Lat_raw_data_label = QtGui.QLabel('Raw Data:')
        self.Lat_raw_data = QLineEdit('')
        Lat_decimal_label = QtGui.QLabel('Decimal Degree:')
        self.Lat_decimal = QLineEdit('')
        Lat_dms_label = QtGui.QLabel('DMS Format:')
        self.Lat_dms = QLineEdit('')

        Lon_raw_data_label = QtGui.QLabel('Raw Data:')
        self.Lon_raw_data = QLineEdit('')
        Lon_decimal_label = QtGui.QLabel('Decimal Degree:')
        self.Lon_decimal = QLineEdit('')
        Lon_dms_label = QtGui.QLabel('DMS Format:')
        self.Lon_dms = QLineEdit('')

        GPS_port_label = QLabel('GPS  Port:')
        GPS_port_label.setFont(QFont('Arial', 11))
        self.GPS_Port = QComboBox()
        self.GPS_Port.addItems(available_serials)

        baud_options = [4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        baud_options_str = [str(x) for x in baud_options]
        GPS_baud_label = QLabel('Baud  Rate:')
        GPS_baud_label.setFont(QFont('Arial', 11))
        self.GPS_baud = QComboBox()
        self.GPS_baud.addItems(baud_options_str)
        self.GPS_baud.setCurrentIndex(baud_options_str.index('115200'))

        self.stop_update_btn = QPushButton('Stop Update')
        self.stop_update_btn.clicked.connect(self.stop_update)

        self.update_geolog_btn = QPushButton('Start Update')
        self.update_geolog_btn.clicked.connect(self.update)

        self.auto_update_check = QCheckBox('Auto_Update')
        self.auto_update_check.setChecked(False)
        self.manual_update_check = QCheckBox('Manual_Update')
        self.manual_update_check.setChecked(True)

        self.gps_sys_info = QPlainTextEdit('Display important system information,'
                                           'if there is any.')

        container_layout.addWidget(self.gps_sys_info, 0, 0, 4, 4)
        container_layout.addWidget(Lat_label, 0, 4, 1, 1)
        container_layout.addWidget(Lon_label, 2, 4, 1, 1)

        container_layout.addWidget(Lat_raw_data_label, 1, 4, 1, 1)
        container_layout.addWidget(self.Lat_raw_data, 1, 5, 1, 1)
        container_layout.addWidget(Lat_decimal_label, 1, 6, 1, 1)
        container_layout.addWidget(self.Lat_decimal, 1, 7, 1, 1)
        container_layout.addWidget(Lat_dms_label, 1, 8, 1, 1)
        container_layout.addWidget(self.Lat_dms, 1, 9, 1, 1)

        container_layout.addWidget(Lon_raw_data_label, 3, 4, 1, 1)
        container_layout.addWidget(self.Lon_raw_data, 3, 5, 1, 1)
        container_layout.addWidget(Lon_decimal_label, 3, 6, 1, 1)
        container_layout.addWidget(self.Lon_decimal, 3, 7, 1, 1)
        container_layout.addWidget(Lon_dms_label, 3, 8, 1, 1)
        container_layout.addWidget(self.Lon_dms, 3, 9, 1, 1)

        container_layout.addWidget(self.auto_update_check, 0, 10, 1, 1)
        container_layout.addWidget(self.manual_update_check, 0, 11, 1, 1)
        container_layout.addWidget(GPS_port_label, 1, 10, 1, 1)
        container_layout.addWidget(self.GPS_Port, 1, 11, 1, 1)
        container_layout.addWidget(GPS_baud_label, 2, 10, 1, 1)
        container_layout.addWidget(self.GPS_baud, 2, 11, 1, 1)

        container_layout.addWidget(self.update_geolog_btn, 3, 10, 1, 1)
        container_layout.addWidget(self.stop_update_btn, 3, 11, 1, 1)
        contral_layout.addLayout(container_layout)
        self.contral_panel.setLayout(contral_layout)

    def update(self):
        if self.gps_flag == 0:
            GPS_com_port = self.GPS_Port.currentText()
            GPS_baud = self.GPS_baud.currentText()
            self.gps_handler = GpsController(GPS_com_port, GPS_baud)
            if self.manual_update_check.checkState():
                self.flag = 1
                self.update_gps_info()
            if self.auto_update_check.checkState():
                self.flag = 3
                self.update_gps_info()
            self.gps_flag = 1
        else:
            if self.manual_update_check.checkState():
                self.flag = 1
                self.update_gps_info()
            if self.auto_update_check.checkState():
                self.flag = 3
                self.update_gps_info()

    def load_map(self, Lat, Lon):
        if self.map_flag == 0:
            self.map_viewer.page().runJavaScript('''add_point(''' + Lat + ''',''' + Lon + ''');''')
            self.map_flag += 1
            self.Last_Lat = Lat
            self.Last_Lon = Lon
            self.gps_sys_info.appendPlainText('Logged a new Point')
        else:
            if self.Last_Lat != Lat or self.Last_Lon != Lon:
                if self.line_color_flag == 0:
                    self.map_viewer.page().runJavaScript('''add_polyline(''' + self.Last_Lat + ''',''' + \
                                                         self.Last_Lon + ''',''' + Lat + ''',''' + Lon + '''',red);''')
                    self.line_color_flag = 1
                else:
                    self.map_viewer.page().runJavaScript('''add_polyline(''' + self.Last_Lat + ''',''' + \
                                                         self.Last_Lon + ''',''' + Lat + ''',''' + Lon + '''',blue);''')
                    self.line_color_flag = 0
                self.map_viewer.page().runJavaScript('''add_point(''' + Lat + ''',''' + Lon + ''');''')
                self.map_flag += 1
                self.Last_Lat = Lat
                self.Last_Lon = Lon
                self.gps_sys_info.appendPlainText('Logged a new point and Plot a path')
            else:
                self.map_flag += 1
                self.Last_Lat = Lat
                self.Last_Lon = Lon
                self.gps_sys_info.appendPlainText('Loacation has not changed')

    def update_gps_info(self):
        if self.gps_handler != None:
            if self.gps_handler.isRunning():
                self.gps_sys_info.appendPlainText('GPS is already streaming-\nJust update the map')
            else:
                self.gps_handler.gps_trigger.connect(self.gps_finished_one_update)
                self.gps_handler.start()
                self.gps_sys_info.setPlainText('GPS Streaming is started.')
        else:
            self.gps_sys_info.appendPlainText('GPS is not enabled.')

    def stop_update(self):
        self.flag = 0
        if self.gps_handler != None:
            if self.gps_handler.isRunning():
                self.gps_handler.terminate()
                self.gps_sys_info.setPlainText('GPS streaming is stopped.')
            else:
                self.gps_sys_info.appendPlainText('There is nothing to stop.')
        else:
            self.gps_sys_info.appendPlainText('GPS is not enabled.')

    @pyqtSlot()
    def gps_finished_one_update(self):
        # print(self.gps_info_dict_buf)
        if self.flag >= 3:
            self.gps_live_data = self.gps_handler.gps_info_dict.copy()
            print(self.gps_live_data)
            # self.gps_live_data = self.gps_handler.gps_info_dict.copy()
            # self.Lat_raw_data.setText(self.gps_live_data['Latitude'])
            # self.Lat_decimal.setText(self.gps_live_data['Latitude Deg'])
            # self.Lat_dms.setText(self.gps_live_data['Latitude'])
            # self.Lon_raw_data.setText(self.gps_live_data['Longitude'])
            # self.Lon_decimal.setText(self.gps_live_data['Longitude Deg'])
            # self.Lon_dms.setText(self.gps_live_data['Longitude'])
            # self.Lat_raw_data.setText(self.Lat)
            # self.Lon_raw_data.setText(self.Lon)
            # print(self.gps_live_data['Latitude'])
            if self.gps_live_data['Latitude Deg'] != 'N/A' and self.gps_live_data['Longitude Deg'] != 'N/A':
                self.Lat_raw_data.setText(self.gps_live_data['Latitude'])
                self.Lat_decimal.setText(self.gps_live_data['Latitude Deg'])
                self.Lat_dms.setText(self.gps_live_data['Latitude'])
                self.Lon_raw_data.setText(self.gps_live_data['Longitude'])
                self.Lon_decimal.setText(self.gps_live_data['Longitude Deg'])
                self.Lon_dms.setText(self.gps_live_data['Longitude'])
                Lon = self.gps_live_data['Latitude Deg']
                Lat = self.gps_live_data['Longitude Deg']
                self.load_map(Lat, Lon)  # 更新地图
            else:
                self.Lat_raw_data.setText(self.gps_live_data['Latitude'])
                self.Lat_decimal.setText(self.gps_live_data['Latitude Deg'])
                self.Lat_dms.setText(self.gps_live_data['Latitude'])
                self.Lon_raw_data.setText(self.gps_live_data['Longitude'])
                self.Lon_decimal.setText(self.gps_live_data['Longitude Deg'])
                self.Lon_dms.setText(self.gps_live_data['Longitude'])
                self.load_map(self.Lat, self.Lon)
            self.flag += 1
        if self.flag == 1:
            self.gps_live_data = self.gps_handler.gps_info_dict.copy()
            print(self.gps_live_data)
            if self.gps_live_data['Latitude Deg'] != 'N/A' and self.gps_live_data['Longitude Deg'] != 'N/A':
                self.Lat_raw_data.setText(self.gps_live_data['Latitude'])
                self.Lat_decimal.setText(self.gps_live_data['Latitude Deg'])
                self.Lat_dms.setText(self.gps_live_data['Latitude'])
                self.Lon_raw_data.setText(self.gps_live_data['Longitude'])
                self.Lon_decimal.setText(self.gps_live_data['Longitude Deg'])
                self.Lon_dms.setText(self.gps_live_data['Longitude'])
                Lon = self.gps_live_data['Latitude Deg']
                Lat = self.gps_live_data['Longitude Deg']
                self.load_map(Lat, Lon)

            else:
                self.Lat_raw_data.setText(self.gps_live_data['Latitude'])
                self.Lat_decimal.setText(self.gps_live_data['Latitude Deg'])
                self.Lat_dms.setText(self.gps_live_data['Latitude'])
                self.Lon_raw_data.setText(self.gps_live_data['Longitude'])
                self.Lon_decimal.setText(self.gps_live_data['Longitude Deg'])
                self.Lon_dms.setText(self.gps_live_data['Longitude'])
                self.load_map(self.Lat, self.Lon)
            self.flag += 1
