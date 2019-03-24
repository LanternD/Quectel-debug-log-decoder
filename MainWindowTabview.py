from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton
from LogDecoderTabview import LogDecoderTabview
from CurrentPlottingModule.CurrentLivePlotter import CurrentLivePlotter
from GpsTabview import GPSTabview


class MainWindowTabview(QWidget):
    def __init__(self, parent=None):
        super(MainWindowTabview, self).__init__(parent)
        main_layout = QVBoxLayout(self)

        # Initialize tab screen
        tabs = QTabWidget()
        tab1 = QWidget()
        tab2 = QWidget()
        tab3 = QWidget()
        tabs.resize(300, 200)

        # Add tabs
        tabs.addTab(tab1, 'Debug Log Decoder')
        tabs.addTab(tab2, 'Power Monitor')
        tabs.addTab(tab3, 'GPS')

        # Create debug_log tab
        main_view = LogDecoderTabview()
        tab1.layout = QVBoxLayout()
        tab1.layout.addWidget(main_view)
        tab1.setLayout(tab1.layout)

        # TODO: Add enable flags to the power monitor and GPS module.

        # Create power_monitor tab
        power_monitor_view = CurrentLivePlotter()
        tab2.layout = QVBoxLayout()
        tab2.layout.addWidget(power_monitor_view)
        tab2.setLayout(tab2.layout)

        # Create gps_map tab
        gps_map = GPSTabview()
        tab3.layout = QVBoxLayout()
        tab3.layout.addWidget(gps_map)
        tab3.setLayout(tab3.layout)

        # Add tabs to widget
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)
