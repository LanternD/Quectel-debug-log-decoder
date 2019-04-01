import threading
import time

import Monsoon.HVPM as HVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
from PyQt5.QtCore import *

# TODO: 20190327 inherit the sampleEngine class and re-implement the relevant parts.

class PowerMonitorHandler(QThread):
    def __init__(self, plot, plot_win, file_IO, USB_PANEL):
        self.p = plot
        self.w1 = plot_win
        self.file_io = file_IO
        self.data = []
        self.time_data = []
        self.temp_data = 0
        self.idx = 0
        self.is_start = True
        self.usb_panel = USB_PANEL
        super(PowerMonitorHandler, self).__init__()
        self.Mon = HVPM.Monsoon()
        self.Mon.setup_usb()
        self.Mon.setVout(4.0)
        self.engine = sampleEngine.SampleEngine(self.Mon)
        self.engine.signal_samp_trigger.connect(self.pass_through2)
        self.engine.enableChannel(sampleEngine.channels.USBCurrent)
        self.Mon.setUSBPassthroughMode(op.USB_Passthrough.On)
        self.engine.disableCSVOutput()
        self.engine.ConsoleOutput(False)
        self.numSamples = sampleEngine.triggers.SAMPLECOUNT_INFINITE

    def run(self):
        self.engine.startSampling(self.numSamples)  ##start sampling

    def pass_through2(self, sample):
        if sample and self.is_start:
            self.temp_data = sample
            if len(self.data) > 5000:
                self.data[:-1] = self.data[1:]  # shift data left
                self.data[-1] = self.temp_data
                self.time_data[:-1] = self.time_data[1:]
                self.time_data[-1] = self.idx
            else:
                self.data.append(self.temp_data)
                self.time_data.append(self.idx)
            if sample >55:
                self.p.setData(x=self.time_data, y=self.data)
                self.w1.setRange(xRange=[self.idx - 2000, self.idx + 50])
                self.usb_panel.display(self.temp_data)
            # Write to file.
            # FIXME: File IO bookmark
            self.file_io.write_power_monitor_current([time.time(), '{0:.4f}'.format(self.temp_data)])
            self.idx += 1

    def pass_through(self, sample):
        if sample and self.is_start:
            self.temp_data = sample
            if len(self.data) > 5000:
                self.data[:-1] = self.data[1:]  # shift data left
                self.data[-1] = self.temp_data
                self.time_data[:-1] = self.time_data[1:]
                self.time_data[-1] = self.idx
            else:
                self.data.append(self.temp_data)
                self.time_data.append(self.idx)

            self.p.setData(x=self.time_data , y=self.data)
            self.w1.setRange(xRange=[self.idx - 2000, self.idx + 50])
            self.usb_panel.display(self.temp_data)
            # Write to file.
            # FIXME: File IO bookmark
            self.file_io.write_power_monitor_current([time.time(), '{0:.4f}'.format(self.temp_data)])
            self.idx += 1
