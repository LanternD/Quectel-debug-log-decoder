import csv
import os
import time
from PyQt5.QtCore import *

class FileIOHandler(QThread):

    def __init__(self):
        super(FileIOHandler, self).__init__()
        # files
        self.debug_log_raw_file = None  # no csv
        self.debug_log_formatted_file = None
        self.current_file = None
        self.gps_file = None
        self.npusch_log_file = None
        self.rsrp_snr_log_file = None
        # csv writers
        self.debug_log_raw_writer = None  # no csv
        self.debug_log_formatted_writer = None
        self.current_writer = None
        self.gps_writer = None
        self.npusch_log_writer = None
        self.rsrp_snr_log_writer = None

        self.file_io_run_flag = True
        # self.reset_handler()

    def reset_handler(self):
        # Call this function when you want to start everything.
        self.start_time = time.time()
        self.folder_timestamp = time.strftime('%y%m%d_%H%M%S', time.localtime(self.start_time))
        self.output_foder_path = os.getcwd() + '/output_files/' + self.folder_timestamp + '/'

        if os.path.exists(self.output_foder_path):
            print('[ERROR] Destination folder is already exists')
        else:
            os.mkdir(self.output_foder_path)

        # Stop the files first
        self.stop_debug_log_file_recording()

        # Create files and their csv writers
        self.create_files_and_writers()

    def run(self):
        # Loop to wait for the incoming data.
        while self.file_io_run_flag:
            # Implement this if necessary
            pass

    def file_io_interface(self, input, writer_selection):

        if writer_selection == 'debug_log_raw':
            self.write_debug_log_raw(input)
        elif writer_selection == 'debug_log_formatted':
            self.write_debug_log_formatted(input)
        elif writer_selection == 'current':
            self.write_power_monitor_current(input)
        elif writer_selection == 'gps':
            self.write_gps_points(input)
        elif writer_selection == 'npusch':
            self.write_npusch_parameters(input)
        elif writer_selection == 'rsrp':
            self.write_rsrp_snr(input)

    def write_debug_log_raw(self, dbg_log_raw):
        if self.debug_log_raw_writer is not None:
            self.debug_log_raw_writer.writerow(dbg_log_raw)
        else:
            print('[ERROR] Raw debug log writer not found.')

    def write_debug_log_formatted(self, debug_log_formatted):
        if self.debug_log_formatted_writer is not None:
            self.debug_log_formatted_writer.writerow(debug_log_formatted)
        else:
            print('[ERROR] Formatted debug log writer not found.')

    def write_power_monitor_current(self, current_list):
        if self.current_writer is not None:
            self.current_writer.writerow(current_list)
        else:
            print('[ERROR] Power current file writer not found.')

    def write_npusch_parameters(self, param_list):
        if self.npusch_log_writer is not None:
            self.npusch_log_writer.writerow(param_list)
        else:
            print('[ERROR] NPUSCH log writer not found.')

    def write_gps_points(self, location):
        if self.gps_writer is not None:
            self.gps_writer.writerow(location)
        else:
            print('[ERROR] GPS writer not found.')

    def write_rsrp_snr(self, rsrp_snr_list):
        if self.rsrp_snr_log_writer is not None:
            self.rsrp_snr_log_writer.writerow(rsrp_snr_list)
        else:
            print('[ERROR] RSRP&SNR write not found.')

    def create_files_and_writers(self):
        self.debug_log_raw_file = open(self.output_foder_path + 'debug_log_raw.txt', 'w')
        self.debug_log_raw_writer = csv.writer(self.debug_log_raw_file)
        self.debug_log_formatted_file = open(self.output_foder_path + 'debug_log_formatted.csv', 'w')
        self.debug_log_formatted_writer = csv.writer(self.debug_log_formatted_file)
        self.current_file = open(self.output_foder_path + 'current.csv', 'w')
        self.current_writer = csv.writer(self.current_file)
        self.gps_file = open(self.output_foder_path + 'geolocatation.csv', 'w')
        self.gps_writer = csv.writer(self.gps_file)
        self.npusch_log_file = open(self.output_foder_path + 'npusch_parameters.csv', 'w')
        self.npusch_log_writer = csv.writer(self.npusch_log_file)
        self.rsrp_snr_log_file = open(self.output_foder_path + 'rsrp_snr.csv', 'w')
        self.rsrp_snr_log_writer = csv.writer(self.rsrp_snr_log_file)

    def stop_debug_log_file_recording(self):

        # Close the old stuff before restart.
        if self.debug_log_raw_file is not None:
            self.debug_log_raw_file.flush()
            self.debug_log_raw_file.close()
            self.debug_log_raw_file = None
            self.debug_log_raw_writer = None
        if self.debug_log_formatted_file is not None:
            self.debug_log_formatted_file.flush()
            self.debug_log_formatted_file.close()
            self.debug_log_formatted_file = None
            self.debug_log_formatted_writer = None
        if self.current_file is not None:
            self.current_file.flush()
            self.current_file.close()
            self.current_file = None
            self.current_writer = None
        if self.gps_file is not None:
            self.gps_file.flush()
            self.gps_file.close()
            self.gps_file = None
            self.gps_writer = None
        if self.npusch_log_file is not None:
            self.npusch_log_file.flush()
            self.npusch_log_file.close()
            self.npusch_log_file = None
            self.npusch_log_writer = None
        if self.rsrp_snr_log_file is not None:
            self.rsrp_snr_log_file.flush()
            self.rsrp_snr_log_file.close()
            self.rsrp_snr_log_file = None
            self.rsrp_snr_log_writer = None

