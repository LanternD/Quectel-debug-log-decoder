"""
Convert the raw log expoerted by our Quectel Debug Log Decoder to UELogViewer compatible format,
so that one can import it into the UELogViewer or UEMonitor.
Created: 2019-04-01
"""
import csv
import os
import time
from utils import get_file_list

class RawLogFormatConvertor(object):

    def __init__(self):
        self.abs_work_dir = os.getcwd()
        self.output_dir = self.abs_work_dir + '/output_files/'
        self.dir_list = []
        self.prepare_dirs()

    def prepare_dirs(self):
        temp_list = os.listdir(self.output_dir)
        self.dir_list = [x for x in temp_list if '.' not in x]  # exclude the normal files
        # self.dir_list.sort()
        # print(self.dir_list)

    def convert_one_raw_file(self, folder_name):
        print('Project name:', folder_name)
        raw_log_file_name = self.output_dir + folder_name + '/debug_log_raw.txt'
        if os.path.exists(raw_log_file_name):
            debug_log_raw_uem = self.output_dir + folder_name + '/debug_log_raw_uem.txt'  # export_file
            if os.path.exists(debug_log_raw_uem):
                print('Already exported. Pass.')
                return False  # overwrite the existing UEM.txt files
            # The converted file does not exists, working on it.
            raw_log_file = open(raw_log_file_name, 'r')
            with open(debug_log_raw_uem, 'w', newline='') as f_out:
                for line in raw_log_file:
                    if len(line) > 2000:
                        print('Abnormal line', line[:100])
                        continue
                    line_buf = line.split(',')
                    # Assume it is UTC+8 time zone. Change accordingly
                    seq_num = line_buf[0]
                    seq_num_str = self.int_to_hex_bytes(int(seq_num))
                    # print(seq_num_str)
                    try:
                        second_frac = float(line_buf[1].split('.')[0])
                    except TypeError:
                        print('Not a time stamp.')
                        continue
                    if second_frac < 1500000000:
                        print('Error, continue')
                        continue
                    millisecond_frac = line_buf[1].split('.')[1]
                    time_stamp = time.strftime(';%Y-%m-%dT%H:%M:%S', time.localtime(float(second_frac)))
                    time_stamp += '.{0:.7s}+08:00;'.format(millisecond_frac)  # Assume it is UTC+8 time zone. Change accordingly
                    time_tick_hex = line_buf[2]
                    time_tick_str = self.int_to_hex_bytes(int(time_tick_hex))
                    # msg = time_stamp + line_buf[3]
                    byte_list = line_buf[3]
                    if byte_list == 'APPLICATION_REPORT':
                        byte_list = line_buf[4]
                        byte_list = '00-00-A0-7F-00-00-' + self.process_app_rep_log(byte_list)
                        # '00-00-A0-7F-00-00' is for APPLICATION_REPORT
                    f_out.write(time_stamp + time_tick_str + seq_num_str + byte_list)
                f_out.flush()
                f_out.close()
            raw_log_file.close()
            return True
        else:
            return False

    def process_app_rep_log(self, byte_list):
        byte_count = (len(byte_list) + 1)//3
        byte_count_hex = hex(byte_count)[2:].upper()
        prepend = ''
        if len(byte_count_hex) == 1:
            prepend = '0' + byte_count_hex + '-00-'
        elif len(byte_count_hex) == 2:
            prepend = byte_count_hex + '-00-'
        elif len(byte_count_hex) == 3:
            prepend = byte_count_hex[1:] + '-0' + byte_count_hex[1] + '-'
        else:
            print('[WARN] abnormal application report length.')
        return prepend + byte_list

    def int_to_hex_bytes(self, int_input):
        x = hex(int_input)[2:]
        # print(x)
        byte_list = []
        for i in range(len(x)//2):
            byte_list.append(x[-2:].upper())
            x = x[:-2]  # remove the tail bytes
        if len(x) == 1:
            byte_list.append('0' + x)
        # else:
        #     byte_list.append(x)
        # print(byte_list)
        while len(byte_list) < 4:
            byte_list.append('00')
        str_msg = ''
        for b in byte_list:
            str_msg += b + '-'
        # print(tick_msg)
        return str_msg

    def convert_all_files(self):
        success_list = []
        for dir in self.dir_list:
            if self.convert_one_raw_file(dir) == 1:
                success_list.append(dir)
        print('Successfully convert the raw log in these folders:', success_list)
        print('# of converted files:', len(success_list))


if __name__ == '__main__':
    my_rlfc = RawLogFormatConvertor()
    # my_rlfc.convert_one_raw_file('190329_233635')
    my_rlfc.convert_all_files()

