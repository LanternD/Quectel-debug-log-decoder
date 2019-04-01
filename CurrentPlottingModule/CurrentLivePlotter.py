import multiprocessing
import time
import Monsoon.HVPM as HVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QLinearGradient, QColor, QFont
from PyQt5.QtWidgets import *
import pyqtgraph as pg
from CurrentPlottingModule.PowerMonitorHandler import PowerMonitorHandler
from utils import *


class CurrentLivePlotter(QWidget):

    def __init__(self, file_io, parent=None):

        super(CurrentLivePlotter, self).__init__(parent)
        self.is_start = True
        self.file_io = file_io
        self.live_file = open('./CurrentPlottingModule/usb_live.txt', 'r')
        self.temp_data = 0
        self.file_data = []
        self.data = []
        self.time_data = []
        self.idx = 0
        self.groupbox_stylesheet = 'QGroupBox {font-size: 16px;' \
                                   'font-weight: bold;} ' \
                                   'Widget {font-weight: normal;}'
        self.g_q_style = YouAreSoQ()
        power_main_layout = QVBoxLayout(self)
        self.Layout1 = QVBoxLayout()
        self.contral_panel = QGroupBox('Control the power monitor')
        self.contral_panel.setStyleSheet(self.groupbox_stylesheet)
        self.Layout2 = QHBoxLayout()
        self.w1 = pg.PlotWidget()

        ## add item to the layouts
        self.add_item2Layouts()
        self.contral_panel.setLayout(self.Layout2)
        power_main_layout.addLayout(self.Layout1)
        power_main_layout.setStretchFactor(self.Layout1, 2)
        power_main_layout.addWidget(self.contral_panel)
        power_main_layout.setStretchFactor(self.contral_panel, 1)
        self.setLayout(power_main_layout)
        self.init_plot()
        self.power_monitor = None
        # self.run()

    def add_item2Layouts(self):
        result_show_layout = QGridLayout()
        self.messages_show = QPlainTextEdit()
        self.messages_show.setPlaceholderText('Display some results.')

        usb_label = QLabel('USB Current (mA)')
        usb_label.setFont(self.g_q_style.middle_lb_font)
        self.usb_panel = QLCDNumber()
        volt_label = QLabel('USB Voltage (V)')
        volt_label.setFont(self.g_q_style.middle_lb_font)
        self.volt_panel = QLCDNumber()
        self.usb_panel.display('0__0')
        self.volt_panel.display('0__0')
        control_btn_box = QGroupBox('Control Box')
        control_btn_box.setStyleSheet(self.groupbox_stylesheet)
        control_btn_layout = QVBoxLayout()

        self.Start_btn = QPushButton('Start Monitor')
        self.Start_btn.clicked.connect(self.start_monitor)
        self.Stop_btn = QPushButton('Stop Monitor')
        self.Stop_btn.clicked.connect(self.stop_monitor)
        self.usb_cb = QCheckBox('Show Current')
        self.usb_cb.setChecked(True)
        self.volt_cb = QCheckBox('Show Voltage')

        control_btn_box.setLayout(control_btn_layout)

        self.Layout1.addWidget(self.w1)
        result_show_layout.addWidget(self.messages_show, 0, 0, 8, 7)
        result_show_layout.addWidget(usb_label, 0, 7, 1, 1)
        result_show_layout.addWidget(self.usb_panel, 1, 7, 3, 1)
        result_show_layout.addWidget(volt_label, 4, 7, 1, 1)
        result_show_layout.addWidget(self.volt_panel, 5, 7, 3, 1)

        control_btn_layout.addWidget(self.usb_cb)
        control_btn_layout.addWidget(self.volt_cb)
        control_btn_layout.addWidget(self.Start_btn)
        control_btn_layout.addWidget(self.Stop_btn)

        self.Layout2.addLayout(result_show_layout)
        self.Layout2.setStretchFactor(result_show_layout, 10)
        self.Layout2.addWidget(control_btn_box)
        self.Layout2.setStretchFactor(control_btn_box, 1)

    def init_plot(self):
        ###plot the animation for data
        self.p = self.w1.plot(pen='y', width='200')  # pen='y',width='100'
        self.w1.showGrid(x=True, y=True)
        self.w1.setRange(yRange=[-10, 350], padding=0)
        self.w1.setAutoPan(y=True)
        self.w1.setLabel(axis='left', text='USB_Current (mA)')
        self.w1.setLabel(axis='bottom', text='Samples Point')
        self.w1.setTitle('Power Monitor')
        # pg.mkPen('w', width=100, style=QtCore.Qt.DashLine)
        self.w1.setBackground(QColor(10, 50, 80))

### Please do not delete this part of codes
    #def update_data(self, sample):
        # if sample and self.is_start:
        #     self.temp_data = sample
        #     if len(self.data) > 5000:
        #         self.data[:-1] = self.data[1:]  # shift data left
        #         self.data[-1] = self.temp_data
        #         self.time_data[:-1] = self.time_data[1:]
        #         self.time_data[-1] = self.idx
        #     else:
        #         self.data.append(self.temp_data)
        #         self.time_data.append(self.idx)
        #     self.p.setData(x=self.time_data , y=self.data)
        #     self.w1.setRange(xRange=[self.idx - 2000, self.idx + 50])
        #     self.usb_panel.display(self.temp_data)
        #     # Write to file.
        #     # FIXME: File IO bookmark
        #     self.file_io.write_power_monitor_current([time.time(), '{0:.4f}'.format(self.temp_data)])
        #     self.idx += 1

    def start_monitor(self):
        self.Start_btn.setDisabled(True)
        self.Stop_btn.setEnabled(True)
        if self.power_monitor == None:
            self.power_monitor = PowerMonitorHandler(self.p, self.w1, self.file_io, self.usb_panel)
        if self.power_monitor.is_start == False:
            self.power_monitor.is_start = True
            self.power_monitor.start()
        else:
            self.power_monitor.start()

    def stop_monitor(self):
        #self.power_monitor.engine.monsoon.stopSampling()
        self.power_monitor.is_start = False
        self.Stop_btn.setDisabled(True)
        self.Start_btn.setEnabled(True)
