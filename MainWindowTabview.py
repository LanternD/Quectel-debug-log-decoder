from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton
from LogDecoderTabview import LogDecoderTabview
from CurrentPlottingModule.CurrentLivePlotter import CurrentLivePlotter
from GpsQtGui import GPSTabview


class MainWindowTabview(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab1, 'Debug Log Decoder')
        self.tabs.addTab(self.tab2, 'Power Monitor')
        self.tabs.addTab(self.tab3, 'GPS')

        # Create debug_log tab
        self.main_view = LogDecoderTabview()
        self.tab1.layout = QVBoxLayout(self)
        self.tab1.layout.addWidget(self.main_view)
        self.tab1.setLayout(self.tab1.layout)

        # Create power_monitor tab
        self.power_monitor_view = CurrentLivePlotter()
        self.tab2.layout = QVBoxLayout(self)
        self.tab2.layout.addWidget(self.power_monitor_view)
        self.tab2.setLayout(self.tab2.layout)

        # Create gps_map tab
        self.gps_map = GPSTabview()
        self.tab3.layout = QVBoxLayout(self)
        self.tab3.layout.addWidget(self.gps_map)
        self.tab3.setLayout(self.tab3.layout)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
