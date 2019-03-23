'''
import array

from PyQt5 import QtGui

import Monsoon.HVPM as HVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
import pyqtgraph as pg

getted_num = 0
usb_data = []
Mon = HVPM.Monsoon()
Mon.setup_usb()



Mon.setVout(4.0)
engine = sampleEngine.SampleEngine(Mon)
engine.enableChannel(sampleEngine.channels.USBCurrent)
Mon.setUSBPassthroughMode(op.USB_Passthrough.On)
engine.disableCSVOutput()#enableCSVOutput('esssss.txt')
engine.ConsoleOutput(True)
numSamples = sampleEngine.triggers.SAMPLECOUNT_INFINITE
engine.startSampling(numSamples)  ##start sampling
'''