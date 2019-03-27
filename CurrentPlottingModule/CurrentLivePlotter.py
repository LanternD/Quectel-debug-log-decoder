import multiprocessing
import time
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
        self.flag = 0
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
        self.Start_btn.clicked.connect(self.Start_Monitor)
        self.Stop_btn = QPushButton('Stop Monitor')
        self.Stop_btn.clicked.connect(self.Stop_Monitor)
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

    def update_data(self):

        line = self.live_file.readline()
        if line:
            # print(line)
            if line != '':
                self.temp_data = float(line)
            self.data.append(self.temp_data)
            # self.p.setPos(self.idx-1000,self.idx+1000)
            self.w1.setRange(xRange=[self.idx - 2000, self.idx + 300])
            self.p.setData(self.data)
            self.usb_panel.display(self.temp_data)
            self.idx += 1
        else:
            self.data.append(self.temp_data)
            # self.p.setPos(self.idx - 1000, self.idx + 1000)
            self.w1.setRange(xRange=[self.idx - 2000, self.idx + 300])
            self.p.setData(self.data)
            self.usb_panel.display(self.temp_data)
            self.idx += 1
        # Write to file.
        # FIXME: File IO bookmark
        self.file_io.write_power_monitor_current([time.time(), self.temp_data])

    def Start_Monitor(self):
        if self.flag == 1:
            time.sleep(2)
            self.timer.start(0.001)
        else:
            self.timer = pg.QtCore.QTimer()
            self.timer.timeout.connect(lambda: self.update_data())
            ### start a new thread for power_monitor to sample
            self.t_monitor = multiprocessing.Process(target=PowerMonitorHandler)
            self.t_monitor.start()
            ###live animation process wait 3 seconds to plot the curve
            time.sleep(2)
            self.timer.start(0.001)

    def Stop_Monitor(self):
        self.timer.stop()
        self.flag = 1
        # self.t_monitor.terminate()
