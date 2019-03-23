import threading
import Monsoon.HVPM as HVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op


class PowerMonitorHandler():
    def __init__(self):
        Mon = HVPM.Monsoon()
        Mon.setup_usb()
        Mon.setVout(4.0)
        self.engine = sampleEngine.SampleEngine(Mon)
        self.engine.enableChannel(sampleEngine.channels.USBCurrent)
        Mon.setUSBPassthroughMode(op.USB_Passthrough.On)
        self.engine.disableCSVOutput()
        #self.engine.enableCSVOutput('full_powwer_monitor_records.txt')
        self.engine.ConsoleOutput(False)
        self.numSamples = sampleEngine.triggers.SAMPLECOUNT_INFINITE
        self.engine.startSampling(self.numSamples)   ##start sampling



