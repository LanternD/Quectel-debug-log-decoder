# -*- coding: UTF-8 -*-
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton
from LogDecoderTabview import LogDecoderTabview
from CurrentPlottingModule.CurrentLivePlotter import CurrentLivePlotter
from GpsTabview import GpsTabview
from FileIOHandler import FileIOHandler
from PyQt5.QtCore import *


class MainWindowTabview(QWidget):
    def __init__(self, parent=None):
        super(MainWindowTabview, self).__init__(parent)

        main_layout = QVBoxLayout()

        enable_power_monitor_module = True
        enable_gps_module = True

        # Load the data
        import os, json
        json_path = './config.json'
        if os.path.exists(json_path):
            with open(json_path, 'r') as j_file:
                read_data = j_file.read()
                try:
                    json_data = json.loads(read_data)
                except json.decoder.JSONDecodeError:
                    print('[ERROR] Json file corrupted. No previous configs. Load default settings.')
                    j_file.close()
                    json_data = {}
                last_config = json_data
                j_file.close()
            try:
                enable_power_monitor_module = last_config['Enable power monitor module']
            except KeyError:
                pass
            try:
                enable_gps_module = last_config['Enable GPS module']
            except KeyError:
                pass

        file_io = FileIOHandler()
        print('[INFO] File IO handler created.')

        # Initialize tab screen
        tabs = QTabWidget()
        tabs.resize(300, 200)

        tab1, tab2, tab3 = None, None, None

        tab1 = QWidget()
        # Create debug_log tab
        log_decoder_tab_view = LogDecoderTabview(file_io)
        log_decoder_tab_view.signal_ecl_trigger.connect(self.update_ecl)
        tab1.layout = QVBoxLayout()
        tab1.layout.addWidget(log_decoder_tab_view)
        tab1.setLayout(tab1.layout)
        tabs.addTab(tab1, '&1 Debug Log Decoder')

        if enable_power_monitor_module:
            # Create power_monitor tab
            tab2 = QWidget()
            self.power_monitor_view = CurrentLivePlotter(file_io)
            tab2.layout = QVBoxLayout()
            tab2.layout.addWidget(self.power_monitor_view)
            tab2.setLayout(tab2.layout)
            tabs.addTab(tab2, '&2 Power Monitor')

        if enable_gps_module:
            # Create gps_map tab
            tab3 = QWidget()
            gps_map = GpsTabview(file_io)
            tab3.layout = QVBoxLayout()
            tab3.layout.addWidget(gps_map)
            tab3.setLayout(tab3.layout)
            tabs.addTab(tab3, '&3 GPS')

        # Add tabs to widget
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)

        #ecl_syn = ECL_Syn(log_decoder_tab_view, power_monitor_view)
        #ecl_syn.start()

    def update_ecl(self, mea_ecl):
        if mea_ecl.find('measure') != -1:
            self.power_monitor_view.volt_panel.display(mea_ecl[0] + '___0')
        elif mea_ecl.find('next') != -1:
            self.power_monitor_view.volt_panel.display(mea_ecl[0] + '___1')



    