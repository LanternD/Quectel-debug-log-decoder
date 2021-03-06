from LogDecoders import *


class McuLogDecoder(DebugLogDecoder):

    def __init__(self, dev_name, filter_dict, config):
        super(McuLogDecoder, self).__init__(dev_name, filter_dict)
        self.mcu_decode_output_folder = './mcu_log_files/'
        self.filter_out_count = 0  # Record the discarded log count
        self.filter_in_count = 0  # Record the kept log count
        self.config = config

    def load_one_file(self, file_name):
        # Input: do not include file extension in the filename
        with open(self.mcu_decode_output_folder + '{0}.txt'.format(file_name)) as f_t:
            one_row = f_t.readline()
            f_t.close()
        self.f_out = open(self.mcu_decode_output_folder + file_name + '_decoded.txt', 'w')  # output handler
        return one_row  # all the data in the file.

    def state_machine(self, row_all):

        states = {'UNKNOWN': 0, 'PREAMBLE': 1, 'COUNT': 2, 'TICK': 3,
                  'DATA': 5, 'LENGTH': 4, 'FINISHED': 6}  # UART state machine
        str_buf = []
        raw_buf = []
        st = states['PREAMBLE']

        # Initialize local variable to prevent warning.
        seq_num = 0
        time_tick = 0
        parsed_msg = ''
        time_stamp = .0
        payload_len = 1
        max_len = 0
        app_rep_flag = False

        empty_msg_list = [0, 0, .0]  # Order: seq_num, timestamp, time tick,
        parsed_log_list = empty_msg_list.copy()

        row_buf = row_all.split(' ')
        print('Message byte length:', len(row_buf))
        while len(row_buf) > 0:
            if st == states['PREAMBLE']:
                new_byte = row_buf.pop(0)
                # print(new_byte)
                if new_byte == '25':  # '%'
                    str_buf.append(new_byte)
                    # TODO: change read byte to traversing.
                    new_byte = ''
                    for i in range(4):
                        new_byte += row_buf.pop(0)
                    if new_byte == '4442473A':  # 'DBG:'
                        str_buf.append(new_byte)
                        st = states['COUNT']
                        time_stamp = time.time()
                        parsed_log_list[1] = time_stamp
                    else:
                        str_buf = []
                else:
                    str_buf = []  # Empty the buf and restart
                    # str_buf.append(new_byte)
                    # if len(str_buf) > 200:  # read
                    #     print('Read too m')
                    #     self.dbg_run_flag = False
            elif st == states['COUNT']:
                # 4 bytes' msg counter.
                str_buf = []
                for i in range(4):
                    str_buf.append(row_buf.pop(0))
                    num_temp = self.hex_to_decimal(str_buf)
                if num_temp - seq_num != 1:
                    missing_log_msg = '[Warning] Inconsistent sequence number detected! This: {0}, Prev: {1}'.format(num_temp, seq_num)
                    print(missing_log_msg)
                    seq_num = num_temp
                    parsed_log_list[0] = seq_num  # Update the dict
                str_buf = []
                st = states['TICK']
            elif st == states['TICK']:
                str_buf = []
                for i in range(4):
                    str_buf.append(row_buf.pop(0))
                    time_tick = self.hex_to_decimal(str_buf)
                    parsed_log_list[2] = time_tick  # Update the dict
                    for i in range(4):
                        dummy = row_buf.pop(0)  # Neglect the useless bytes.
                if len(dummy) == 0:
                    st = states['PREAMBLE']
                    continue
                if dummy[0] == 'A':  # This is an application report message
                    app_rep_flag = True
                    parsed_log_list.append('APPLICATION_REPORT')
                else:
                    app_rep_flag = False
                    st = states['LENGTH']
            elif st == states['LENGTH']:
                str_buf = []
                for i in range(2):
                    str_buf.append(row_buf.pop(0))
                    payload_len = self.hex_to_decimal(str_buf)
                    # if max_len < payload_len:
                    #     max_len = payload_len
                    #     print('[INFO]Max payload length:', max_len)
                if payload_len > 720:
                    st = states['UNKNOWN']
                    print('[ERROR] Found unbounded large payload length.')
                    continue
                st = states['DATA']
            elif st == states['DATA']:
                # Read in the data as the length field specified.
                str_buf = []
                for i in range(payload_len):
                    str_buf.append(row_buf.pop(0))
                    raw_buf = parsed_log_list.copy()
                    raw_buf.append(self.byte_concatenation(str_buf))

                print(str_buf)
                if app_rep_flag is True:
                    str_buf.reverse()  # There is another reverse in the hex to ascii function.
                    parsed_log_list.append(self.hex_to_ascii(str_buf))
                    self.application_report_export_processing(parsed_log_list)
                else:
                    disp_list = self.parse_one_msg_common(str_buf)
                    # Output order: msg_id_dec, msg_name, msg_src, msg_dest, msg_length, decoded_msg
                    disp_list = [str(x) for x in disp_list]
                    self.f_out.write('\t'.join(disp_list))
                    print(disp_list)
                    # TODO: Bookmarked. extract info from log.
                    # self.extract_info_from_log(disp_list)
                    parsed_log_list += disp_list  # parsed_log_list have time. disp_list only has message info.
                    self.display_export_processing(parsed_log_list)
                    if len(parsed_log_list) >= 6 and parsed_log_list[4] != 'N/A':  # msg name
                        self.dy_extract_rsrp_snr_from_log(parsed_log_list)
                        self.extract_npusch_power_from_log(parsed_log_list)
                        # print(parsed_log_dict)
                st = states['FINISHED']
            elif st == states['FINISHED']:
                parsed_log_list = empty_msg_list.copy()
                self.f_out.flush()
                st = states['PREAMBLE']  # Recycle the processing state machine
            elif st == states['UNKNOWN']:
                print('[ERROR] Something wrong happens. Reset to PREAMBLE state.')
                st = states['PREAMBLE']
        # All the bytes are processed.
        self.f_out.flush()
        self.f_close()

    def display_export_processing(self, info_list):
        # TODO: change this to txt friendly format.

        self.res = self.packet_output_formatting(info_list)

        if True:
            res_disp = self.res.split('\n')[0] + '\n'  # Truncate the result and keep only the first line.
        else:
            res_disp = self.res

        if len(info_list) <= 5:
            print('[ERROR] Missing element in Info List.')
        try:
            is_filtered = self.check_filters(info_list[4])
        except IndexError:
            is_filtered = True

        if is_filtered is False:
            print(res_disp)

        # Apply the filter, exporting
        if self.config['Export decoded']:
            if self.config['Keep filtered logs'] is True:
                # Means write every log
                is_filtered = False

            if is_filtered is False:
                # This log need to be export
                if self.config['Export format'] == 'txt':
                    # self.f_exp.write(self.res)
                    self.file_io.write_debug_log_formatted(info_list)
                elif self.config['Export format'] == 'csv':
                    # self.f_exp_csv_writer.writerow(info_list)
                    self.file_io.write_debug_log_formatted(info_list)

    def application_report_export_processing(self, info_list):
        first_line = '#{0}\t{1}\t{2}\t{3}\t\n'.format(info_list[0], info_list[1],
                                                      info_list[2], info_list[3])
        whole_app_rep = first_line + info_list[4] + '\n'  # The 4th element is the actual msg. add double \n
        # Check filter
        is_filtered = self.check_filters('APPLICATION_REPORT')
        if is_filtered is False:
            if self.config['Run in Qt']:
                self.transfer_buf.append(whole_app_rep)
                self.dbg_uart_trigger.emit()
            else:
                print(whole_app_rep)

        if self.config['Export decoded']:
            if self.config['Keep filtered logs'] is True:
                # Means write every log
                is_filtered = False

            if is_filtered is False:
                # This log need to be export
                if self.config['Export format'] == 'txt':
                    # self.f_exp.write(whole_app_rep)
                    self.file_io.write_debug_log_formatted(whole_app_rep)
                elif self.config['Export format'] == 'csv':
                    # self.f_exp_csv_writer.writerow(info_list)
                    self.file_io.write_debug_log_formatted(info_list)

    def check_filters(self, log_name):

        is_filtered_flag = False  # True: not wanted log; False: wanted log.
        # Apply the filter, printing
        if self.filter_flag == 1:  # Filter out
            if log_name in self.filter_dict['FO']:  # Message name
                is_filtered_flag = True
                self.filter_out_count += 1
            else:
                self.filter_in_count += 1  # The log that is kept.
        elif self.filter_flag == 2:  # Filter in
            if log_name in self.filter_dict['FI']:  # Message in the set
                self.filter_in_count += 1
            else:
                is_filtered_flag = True
                self.filter_out_count += 1

        if self.filter_out_count % 1000 == 0 and self.filter_out_count > 0:
            filter_out_count_msg = '[INFO] Excluded log count: {0}'.format(self.filter_out_count)
            print(filter_out_count_msg)
            if self.config['Run in Qt']:
                self.sys_info_buf.append(filter_out_count_msg)
                self.dbg_uart_trigger.emit()  # Tell the main thread to update the system info monitor.
        if self.filter_in_count % 500 == 0 and self.filter_in_count > 0:
            filter_in_count_msg = '[INFO] Included log count: {0}'.format(self.filter_in_count)
            print(filter_in_count_msg)
            if self.config['Run in Qt']:
                self.sys_info_buf.append(filter_in_count_msg)
                self.dbg_uart_trigger.emit()
        return is_filtered_flag

    def byte_concatenation(self, b_list):
        # Convert ['AA', '3E', '4F'] to 'AA-3E-4F'.
        ret = ''
        for i in range(len(b_list)):
            if i != len(b_list) - 1:
                ret += b_list[i] + '-'
            else:
                ret += b_list[i]
        return ret


filter_out_list = {'N/A', 'UICC_DBG_LOG_P0', 'UICC_DBG_LOG_P1', 'UICC_DBG_LOG_P2'}  # add item to only one of them!!! E.g. to remove invalid message, use 'N/A'.
filter_in_list = {}  # add item to only one of them!!!
filter_dict = {'FO': filter_out_list, 'FI': filter_in_list}

config = {'Device name': 'BC95',
            'Dbg port': 'COM3',
            'Filter dict': filter_dict,
            'Run in Qt': False,
          'Export decoded': True,
            'Export to file': True,  # choose to export the decoded info. The raw log is mandatory.
            'Export filename time prefix': '%y%m%d_%H%M%S',
            'Keep filtered logs': False,  # filtered logs will not be printed, but you can export them to file.
            'Time format': '%m-%d %H:%M:%S.%f',  # see time.strftime() for detail.
            'Export format': 'csv'}  # format: txt or csv, need to enable "export to file first".


mcu_decoder = McuLogDecoder('BC95', filter_dict, config)
mcu_decoder.state_machine(mcu_decoder.load_one_file('raw_dbg_log_short'))
