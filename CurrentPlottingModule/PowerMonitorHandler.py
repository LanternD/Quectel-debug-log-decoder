import threading
import Monsoon.HVPM as HVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
from PyQt5.QtCore import *

# TODO: 20190327 inherit the sampleEngine class and re-implement the relevant parts.

class PowerMonitorHandler(QThread):
    samp_trigger = pyqtSignal(float)
    def __init__(self):
        super(PowerMonitorHandler, self).__init__()
        # super(PowerMonitorHandler, self).__init__()
    def run(self):
        Mon = HVPM.Monsoon()
        Mon.setup_usb()
        Mon.setVout(4.0)
        self.engine = sampleEngine.SampleEngine(Mon)
        self.engine.signal_samp_trigger.connect(self.pass_through)
        self.engine.enableChannel(sampleEngine.channels.USBCurrent)
        Mon.setUSBPassthroughMode(op.USB_Passthrough.On)
        self.engine.disableCSVOutput()
        #self.engine.enableCSVOutput('full_powwer_monitor_records.txt')
        self.engine.ConsoleOutput(False)
        self.numSamples = sampleEngine.triggers.SAMPLECOUNT_INFINITE
        self.engine.startSampling(self.numSamples)   ##start sampling
    def pass_through(self, sample):
        self.samp_trigger.emit(sample)



