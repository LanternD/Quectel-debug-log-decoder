# -*- coding: UTF-8 -*-
from collections import OrderedDict
import csv
from datetime import datetime
import os.path
import seaborn
import serial
import time
from PyQt5.QtCore import *
import xml.etree.cElementTree as ET


class DebugLogDecoder(QThread):
    # Load the XML file and then parse and format the logs.
    def __init__(self, device_name, filter_dict):

        super(DebugLogDecoder, self).__init__()
        self.device_name = device_name.upper()
        self.filter_dict = filter_dict
        self.filter_flag = self.filter_dict_checker()  # 0: no filter, 1: filter out enabled, 2: filter in enabled.

        self.decoder_dir = './decoders/'
        self.decode_output_dir = './output_files/'
        self.log_dir = './log_files/'

        if self.device_name == 'BC28':
            self.decoder_xml = 'messages_bc28.xml'
        elif self.device_name == 'BC95':
            self.decoder_xml = 'messages_bc95.xml'
        else:
            print('[ERROR] Unsupported device. Change the device or check the spell.')
            self.decoder_xml = None
        self.tag_name_prefix = '{http://tempuri.org/xmlDefinition.xsd}'
        self.message_dict = {}
        self.msg_buffer = []

        self.layer_dict = {0: 'INVALID', 1: 'DSP', 2: 'LL1', 3: 'L2_UL', 4: 'L2_DL',
                           5: 'MAC_DL', 6: 'MAC_UL', 7: 'RLC_UL', 8: 'RLC_DL',
                           9: 'PDCP_DL', 10: 'PDCP_UL', 11: 'RRC', 12: 'EMMSM',
                           13: 'MN', 14: 'AT', 15: 'PDH', 16: 'LWIP', 17: 'SIM',
                           18: 'LOG', 19: 'MONITOR', 20: 'HOSTTEST_RF', 21: 'HOSTTEST_TX',
                           22: 'HOSTTEST_RX', 23: 'NVCONFIG', 24: 'NAS', 25: 'IRMALLOC',
                           26: 'PROTO', 27: 'SMS', 28: 'LPP', 29: 'UICC', 30: 'UE',
                           31: 'NUM_STACK'}
        self.src_layer_stat = dict((v, 0) for k, v in self.layer_dict.items())
        self.src_layer_stat['Unknown'] = 0
        self.dest_layer_stat = self.src_layer_stat.copy()
        self.src_dest_pair_stat = {}
        # print(self.src_layer_stat, self.dest_layer_stat)

    def xml_loader(self):
        # Load the XML file for once.
        xml_path = self.decoder_dir + self.decoder_xml
        msg_tree = ET.parse(xml_path)
        root = msg_tree.getroot()
        type_set = {}
        if self.device_name == 'BC28':
            root = root[0]
        # print(root.tag, root.atrrib)
        for child in root:  # each child is a message item
            # msg_name = child[0].text
            msg_id = child[1].text
            if len(child) > 4:
                msg_size = child[4].text
            else:
                msg_size = 0
            if msg_size != 0:
                self.message_dict[msg_id] = child
            fields = child[6]
            for field in fields:
                msg_type = field[1].text
                msg_type_size = field[3].text
                # print(msg_type)
                type_set[msg_type] = msg_type_size
        print('[INFO] Message dict length:', len(self.message_dict))
        # print(type_set)
        print('[INFO] Available types:', len(type_set))

    def filter_dict_checker(self):

        if len(self.filter_dict['FO']) > 0 and len(self.filter_dict['FI']) > 0:
            raise ValueError('[ERROR] Invalid arguments in the filter dictionary! Check and rerun.')
        filter_flag = 0
        if len(self.filter_dict['FO']) > 0:
            filter_flag = 1
            print('[CONFIG] Filter-Out enabled.')
        elif len(self.filter_dict['FI']) > 0:
            filter_flag = 2
            print('[CONFIG] Filter-In enabled.')
        return filter_flag

    def hex_to_decimal(self, hex_list):
        # note that the string list is LSB first, for example, 12-34-aa is 0xAA3412
        if len(hex_list) == 0:
            # input an empty string or list
            print('[ERROR] Empty hex list.')
            return -1
        if type(hex_list) == str:
            # basically there is ONLY ONE byte.
            return int(hex_list, 16)
        hex_string = ''
        hex_list.reverse()
        for byte in hex_list:
            hex_string += byte
        try:
            return int(hex_string, 16)
        except ValueError:
            print(hex_string)
            return -1

    def hex_to_ascii(self, byte_list):
        byte_str = ''
        byte_list.reverse()
        for b_ascii in byte_list:
            if b_ascii != '00' or int(b_ascii, 16) < 127:
                byte_str += b_ascii
        # TODO: find a better way to prevent the decode error.
        try:
            return bytearray.fromhex(byte_str).decode()
        except UnicodeDecodeError:
            return ''

    def parse_one_msg_common(self, data_flow):
        result_list = []
        if len(data_flow) < 8:
            print('[ERROR] Insufficient message length. Missing information.')
            return result_list
        msg_header = data_flow[0:8]

        msg_id_hex = msg_header[0:4]
        msg_id_dec = str(self.hex_to_decimal(msg_id_hex))
        # print(msg_id_dec)

        if msg_id_dec in self.message_dict:
            msg_name = self.message_dict[msg_id_dec][0].text
        else:
            msg_name = 'N/A'  # not in the XML decoder

        # parse msg source and destination
        msg_src_idx = self.hex_to_decimal(msg_header[4])
        msg_dest_idx = self.hex_to_decimal(msg_header[5])
        msg_length_hex = msg_header[6:8]
        if '\n' in msg_length_hex[1]:
            msg_length = 0
        else:
            msg_length = self.hex_to_decimal(msg_length_hex)

        # FIXME: find out which part cause "Empty hex list" (return -1)
        try:
            msg_src = self.layer_dict[msg_src_idx]
        except KeyError:
            msg_src = 'Unknown'

        self.src_layer_stat[msg_src] += 1
        try:
            msg_dest = self.layer_dict[msg_dest_idx]
        except KeyError:
            msg_dest = 'Unknown'
        self.dest_layer_stat[msg_dest] += 1

        src_dest_pair = '{0}->{1}'.format(msg_src, msg_dest)
        if src_dest_pair not in self.src_dest_pair_stat:
            self.src_dest_pair_stat[src_dest_pair] = 1
        else:
            self.src_dest_pair_stat[src_dest_pair] += 1

        # print(msg_src, msg_dest, msg_length)

        decoded_msg = ''  # by default it is a str message, but it can be an ordered dict as well.

        # Most important part: parse the payload
        if msg_length > 0 and msg_name != 'N/A':
            data_flow[-1] = data_flow[-1].replace('\n', '')
            payload_list = data_flow[8:]  # actual data after the header field
            # print(self.message_dict[msg_id_dec][6].tag)
            if self.message_dict[msg_id_dec][6].tag == self.tag_name_prefix + 'Fields':
                decoded_msg = self.parse_fields(payload_list, self.message_dict[msg_id_dec][6])

        result_list += [msg_id_dec, msg_name,
                        msg_src, msg_dest, msg_length, decoded_msg]
        return result_list

    def parse_fields(self, data_flow, node):
        initial_point = 8  # constant
        payload_dict = OrderedDict()
        for item in node:
            if item[0].text == 'header' or item[0].text == 'msg_hdr':
                continue
            field_name = item[0].text
            field_type = item[1].text
            field_offset = int(item[2].text)
            field_size = int(item[3].text)
            field_length = int(item[4].text)
            # print(item)
            # print(field_name, field_offset, field_size, field_length)

            # parse any sub-structure
            try:
                sub_struct = item[5]
                # has_nested_structure = True
                # print(sub_struct.tag)
            except IndexError:
                sub_struct = None
                # has_nested_structure = False
                # just get the data from the flow.
            # payload_dict['Nested?'] = has_nested_structure
            info = ''
            # special case:
            if field_type == 'c_char':
                start = field_offset - initial_point
                my_chars = data_flow[start: start + field_length]
                my_str = self.hex_to_ascii(my_chars)
                payload_dict[field_name] = my_str

            else:
                if field_length == 1:
                    start = field_offset - initial_point
                    info = self.hex_to_decimal(data_flow[start: start + field_size])
                    if field_type == 'c_bool':
                        if info == 1:
                            info = True
                        else:
                            info = False
                        payload_dict[field_name] = info
                    # print(info)
                    elif field_type == 'c_short':
                        # signed int. eg: 65535 should be converted to -1
                        if info > 65536 // 2:
                            info -= 65536
                        payload_dict[field_name] = str(info)
                    else:
                        payload_dict[field_name] = str(info)
                if field_length > 1:
                    # print('>> More than one items here.')
                    # multiple_item_dict = OrderedDict()
                    temp_list = []
                    for i in range(field_length):
                        start = field_offset - initial_point + field_size * i
                        item_info = self.hex_to_decimal(data_flow[start: start + field_size])
                        temp_list.append(item_info)
                        # multiple_item_dict['{0}{1}'.format(field_name, i)](str(item_info))
                    payload_dict[field_name] = temp_list  # multiple_item_dict

                if sub_struct is not None:
                    # has substructure to parse
                    # print(sub_struct.tag)
                    if sub_struct.tag == self.tag_name_prefix + 'Enums':
                        payload_dict[field_name] = '{0}({1})'.format(str(info),
                                                                     self.find_enums(str(info), sub_struct))
                    elif sub_struct.tag == self.tag_name_prefix + 'Fields':
                        # print('do parse fields.')
                        another_fields_parse = self.parse_fields(data_flow, sub_struct)
                        payload_dict[field_name] = another_fields_parse
        return payload_dict

    def find_enums(self, data, node):
        # print('parse enums')
        for enum in node:
            if enum[1].text == data:
                return enum[0].text
        return 'Enum Not Found'

    def layer_indexing(self, decimal_enum):
        return self.layer_dict[decimal_enum]

    def timestamp_parsing(self, timestamp_str, is_beijing_time):
        date_time_buf = timestamp_str.split('T')
        # date = date_time_buf[0]
        timestamp = date_time_buf[1].split('+')[0]
        if is_beijing_time:
            hour = (int(timestamp.split(':')[0]) + 12) % 24
            timestamp = str(hour) + timestamp[2:]
        return timestamp  # the date is not important, just take a look into the log

    def packet_output_formatting(self, info_list):
        if len(info_list) < 4:
            print('[ERROR] Incomplete message for formatting.')
            return 'Incomplete Msg\n'
        if info_list[3] == 'N/A':
            return info_list[
                       0] + ' Invalid Msg\n'  # this is an invalid packet. Remove these two lines if you want them.
        ret_msg = ''

        # Deal with the header
        header_list = info_list[:-1]  # order: seq_num, time, time tick, msg_id_decimal,
        # msg name, src, dest, msg length
        header_print = '#{0}\t{1}\t{2}\t{4}({3})\t\t{5} -> {6}\t{7}'.format(header_list[0], header_list[1],
                                                                            header_list[2], header_list[3],
                                                                            header_list[4], header_list[5],
                                                                            header_list[6], header_list[7])
        ret_msg += header_print
        ret_msg += '\n'
        # The most important one
        msg_ordered_dict = info_list[-1]
        formatted_ordered_list = self.format_ordered_dict(0, msg_ordered_dict)
        ret_msg += formatted_ordered_list
        return ret_msg

    def format_ordered_dict(self, level, odict):
        return_msg = ''
        # print(odict)
        for element in odict:
            field_key = element
            field_value = odict[element]
            if type(field_value) == str or type(field_value) == bool:
                one_line = ' {0}{1}: {2}'.format(level * '\t', field_key, field_value)
            elif type(field_value) == list:
                counter = 0
                linefy = ''
                for item in field_value:
                    linefy += '{0}_{1}: {2} / '.format(field_key, counter, item)
                    counter += 1
                one_line = ' {0}{1}'.format(level * '\t', linefy)
            elif type(field_value) == OrderedDict:
                # print('>>> Ordered Dict.')
                another_dict = self.format_ordered_dict(level + 1, field_value)
                one_line = ' {0}{1}: \n{2}'.format(level * '\t', field_key, another_dict)
            else:
                one_line = '??????'
            if one_line[-1] != '\n':
                one_line += '\n'
            return_msg += one_line
        return return_msg

    def export_stat_csv(self, output_name_prefix):
        stat_mat = []
        ignored_layers = []  # ['LL1', 'UICC', 'DSP', '0 count']

        print('[INFO] Source Layer stats:')
        for key in sorted(self.src_layer_stat.keys()):
            val = self.src_layer_stat[key]
            if key in ignored_layers:
                continue
            if '0 count' in ignored_layers:
                if val == 0:
                    continue
            print('{0}: {1}'.format(key, val))
            stat_mat.append([key, val, 'src'])

        # print(my_decoder.src_layer_stat)
        print('======\nDestination Layer stats')
        # print(my_decoder.dest_layer_stat)
        for key in sorted(self.dest_layer_stat.keys()):
            val = self.dest_layer_stat[key]
            if key in ignored_layers:
                continue
            if '0 count' in ignored_layers:
                if val == 0:
                    continue
            print('{0}: {1}'.format(key, val))
            stat_mat.append([key, val, 'dest'])

        with open(self.decode_output_dir + output_name_prefix + '_msg_layer_stats.csv', 'w', newline='') as my_file:
            my_csv_writer = csv.writer(my_file)
            my_csv_writer.writerow(['layer_name', 'count', 'from'])
            for row in stat_mat:
                my_csv_writer.writerow(row)
            my_file.flush()
            my_file.close()

    def export_src_dest_pair(self, output_name_prefix):
        ignored_pairs = ['DSP->LL1', 'LL1->DSP', 'LL1->LL1', 'UICC->UICC']

        print('[INFO] Total number of available msg type:', len(self.src_dest_pair_stat))
        with open(self.decode_output_dir + output_name_prefix + '_pair_stats.csv', 'w', newline='') as my_file:
            my_csv_writer = csv.writer(my_file)
            my_csv_writer.writerow(['src->dest', 'count'])
            for key in sorted(self.src_dest_pair_stat.keys()):
                if key in ignored_pairs:
                    continue
                val = self.src_dest_pair_stat[key]
                print('{0}: {1}'.format(key, val))
                my_csv_writer.writerow([key, val])
            my_file.flush()
            my_file.close()


class UlvLogDecoder(DebugLogDecoder):

    def __init__(self, dev_name, filter_dict):
        super(UlvLogDecoder, self).__init__(dev_name, filter_dict)

    def log_reader(self, log_path, save_to_file_flag=True):

        if save_to_file_flag:
            output_name = log_path[:-4]
            f_write = open(self.decode_output_dir + 'decoded_' + output_name + '.txt', 'w', newline='')

        with open(self.log_dir + log_path, 'r', encoding='utf-8') as log_file:
            # print or write the very first line.
            header_list = ['Seq ID', 'Timestamp', 'Time tick', 'Decimal ID', 'Msg ID', 'Source',
                           'Destination', 'Length', 'Formatted Output']
            header_print = '{0}\t{1}\t{2}\t{4}({3})\t\t{5} -> {6}\t{7}\t{8}'.format(header_list[0], header_list[1],
                                                                                    header_list[2], header_list[3],
                                                                                    header_list[4], header_list[5],
                                                                                    header_list[6], header_list[7],
                                                                                    header_list[8])
            if not save_to_file_flag:
                print(header_print)
            else:
                f_write.write(header_print)
            # print(header_list)
            count = 0
            filter_out_count = 0
            for line in log_file:
                res = self.parse_one_msg_ulv(line)

                if self.filter_flag == 1:  # filter out
                    if res[4] in self.filter_dict['FO']:  # message name
                        filter_out_count += 1
                        continue
                elif self.filter_flag == 2:  # filter in
                    if res[4] not in self.filter_dict['FI']:  # message in the set
                        continue

                count += 1
                formatted_res = self.packet_output_formatting(res)
                if save_to_file_flag:
                    f_write.write(formatted_res + '\n')
                    if count % 1000 == 0:
                        print('[INFO] {0} messages are processed.'.format(count))
                else:
                    print(formatted_res)  # the actual meanings of each packet
            print('[INFO] All messages are decoded.\n')
            if self.filter_flag == 1:
                print('Filter-out count:', filter_out_count)
            elif self.filter_flag == 2:
                print('[INFO] Filter-in count:', count)

        if save_to_file_flag:
            f_write.flush()
            f_write.close()
            print('[INFO] Results have been write to file.')
            # print(res)

    def parse_one_msg_ulv(self, buf_line):  # Message recorded by UELogViewer
        if buf_line == '':
            return 0
        line_temp = buf_line.split(';')
        # Structure:
        # 1 line = timestamp + data flow
        # data flow = msg header + msg payload
        # msg header = msg id + source + destination + length
        # msg payload are decoded based on the XML.

        time_stamp = line_temp[1]
        time_stamp = self.timestamp_parsing(time_stamp, is_beijing_time=True)

        data_flow = line_temp[2].split('-')

        display_list = []
        time_tick_hex = data_flow[0:4]  # time ticks, useless.
        time_tick = self.hex_to_decimal(time_tick_hex)
        msg_counter_hex = data_flow[4:8]
        msg_counter = self.hex_to_decimal(msg_counter_hex)

        display_list += [msg_counter, time_stamp, time_tick]
        meaning_list = self.parse_one_msg_common(data_flow[8:])  # remove the parsed field

        return display_list + meaning_list


class UartOnlineLogDecoder(DebugLogDecoder):
    dbg_uart_trigger = pyqtSignal()
    update_rsrp_snr_trigger = pyqtSignal()
    update_npusch_power_trigger = pyqtSignal()

    def __init__(self, config, file_io):

        dev_name = config['Device name']
        uart_port = config['Dbg port']
        filter_dict = config['Filter dict']

        super(UartOnlineLogDecoder, self).__init__(dev_name, filter_dict)
        self.ue_dbg_port = uart_port
        self.dbg_uart_handler = serial.Serial(self.ue_dbg_port, 921600)  # Fixed baudrate
        self.dbg_run_flag = True
        self.config = config

        self.file_io = file_io
        # self.f_raw = self.file_io.debug_log_raw_file
        # self.f_raw_csv_writer = self.file_io.debug_log_raw_writer
        # self.f_exp = self.file_io.debug_log_formatted_file  # None
        # self.f_exp_csv_writer = self.file_io.debug_log_formatted_writer  # None
        self.res = None  # decoded results.

        self.filter_out_count = 0  # Record the discarded log count
        self.filter_in_count = 0  # Record the kept log count

        file_time = time.strftime(self.config['Export filename time prefix'], time.localtime(time.time()))
        self.start_timestamp = time.time()  # This is the 0 offset of the rest timestamps.

        self.transfer_buf = []  # Transfer the decoded log
        self.sys_info_buf = []  # Transfer the system info
        # Transfer the incoming signal measurement to main thread.
        self.rsrp_snr_buf = {'ts': [], 'RSRP': [], 'SNR': []}
        self.npusch_power_buf = ['', '', '', '', '']  # ts, type, power db, repetition, iru number
        self.current_ecl = '-1'

        self.live_measurement_buf = {'ECL': -1, 'CSQ': -1, 'RSRP': -1, 'SNR': -1, 'Cell ID': -1,
                                     'Current state': -1,
                                     'Last update': -1}  # Transfer the live measurement results to the main thread
        # Live measurement order: ECL, CSQ, RSRP, SNR, Cell ID, Current state, last update time

        # Update: 20190327 Use FileIOHandler instead.
        '''
        if self.config['Export raw'] is True:
            # Create the raw log when this function is enabled.
            raw_log_path = '{0}{1}_{2}_raw.txt'.format(self.log_dir, file_time, self.device_name)
            self.f_raw = open(raw_log_path, 'w', newline='')
            self.f_raw_csv_writer = csv.writer(self.f_raw)  # It is a txt file, but use csv writer to handle it.
            self.sys_info_buf.append('Raw log created at: {0}.'.format(raw_log_path))

        if self.config['Export decoded']:
            # Create decoded output file when this function is enabled.
            if self.config['Export format'] not in {'txt', 'csv'}:
                # This unlikely happens.
                raise ValueError('Export file format unknown. \'txt\' and \'csv\' only.')

            file_path = '{0}{1}_{2}_{3}.{4}'.format(self.decode_output_dir, file_time,
                                                    self.device_name, 'OL', self.config['Export format'])
            self.f_exp = open(file_path, 'w', newline='')
            if self.config['Export format'] == 'csv':
                self.f_exp_csv_writer = csv.writer(self.f_exp)
            self.sys_info_buf.append('Decoded log file created at: {0}.'.format(file_path))
        '''

    def read_byte(self, num):
        # Read byte from debug UART and format it.
        try:
            msg = self.dbg_uart_handler.read(num).hex().upper()  # hex() converts byte to str.
        except serial.serialutil.SerialException:
            msg = ''
        return msg

    def run(self):
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

        self.dbg_run_flag = True
        while self.dbg_run_flag:
            # Run until the flag is set.
            if st == states['PREAMBLE']:
                new_byte = self.read_byte(1)
                # print(new_byte)
                if new_byte == '25':  # '%'
                    str_buf.append(new_byte)
                    new_byte = self.read_byte(4)
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
                str_buf = []
                for i in range(4):
                    str_buf.append(self.read_byte(1))
                num_temp = self.hex_to_decimal(str_buf)
                if num_temp - seq_num != 1:
                    missing_log_msg = '[Warning] Inconsistent sequence number detected! This: {0}, Prev: {1}'.format(
                        num_temp, seq_num)
                    print(missing_log_msg)
                    if self.config['Run in Qt']:
                        self.sys_info_buf.append(missing_log_msg)
                        self.dbg_uart_trigger.emit()
                seq_num = num_temp
                parsed_log_list[0] = seq_num  # Update the dict
                # print(str_buf, seq_num)
                str_buf = []
                st = states['TICK']
            elif st == states['TICK']:
                str_buf = []
                for i in range(4):
                    str_buf.append(self.read_byte(1))
                time_tick = self.hex_to_decimal(str_buf)
                parsed_log_list[2] = time_tick  # Update the dict
                dummy = self.read_byte(4)  # Neglect the useless bytes.
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
                    str_buf.append(self.read_byte(1))
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
                str_buf = []
                for i in range(payload_len):
                    str_buf.append(self.read_byte(1))
                raw_buf = parsed_log_list.copy()
                raw_buf.append(self.byte_concatenation(str_buf))

                if self.config['Export raw']:
                    # Export only if this feature is enabled.
                    # self.f_raw_csv_writer.writerow(raw_buf)
                    self.file_io.write_debug_log_raw(raw_buf)

                if app_rep_flag is True:
                    str_buf.reverse()  # There is another reverse in the hex to ascii function.
                    parsed_log_list.append(self.hex_to_ascii(str_buf))
                    self.application_report_export_processing(parsed_log_list)
                else:
                    disp_list = self.parse_one_msg_common(str_buf)
                    # Output order: msg_id_dec, msg_name, msg_src, msg_dest, msg_length, decoded_msg
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
                if self.config['Export decoded']:
                    # self.f_exp.flush()
                    self.file_io.debug_log_formatted_file.flush()
                st = states['PREAMBLE']  # Recycle the UART state machine
            elif st == states['UNKNOWN']:
                print('[ERROR] Something wrong happens. Reset to PREAMBLE state.')
                st = states['PREAMBLE']

    def display_export_processing(self, info_list):

        self.res = self.packet_output_formatting(info_list)

        if self.config['Simplify log'] is True:
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
            if self.config['Run in Qt']:
                res_disp_new = self.format_timestamp_in_qt(res_disp)
                # res_disp_new has formatted time according to the config.
                self.transfer_buf.append(res_disp_new)
                self.dbg_uart_trigger.emit()  # Tell the main thread to fetch data.
            else:
                # Note: if the GUI is enabled. The log will not be printed out in STDOUT (too messy).
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

    def format_timestamp_in_qt(self, log_detail):
        if self.config['Display time format'] == 'raw':
            return log_detail

        log_tmp = log_detail.split('\n')  # Separate each line, change the first line, and assemble them again.
        header = log_tmp[0]
        header_split = header.split('\t')
        try:
            timestamp_raw = float(header_split[1])
        except ValueError:
            print('[ERROR] Unknown timestamp value.')
            return log_detail

        time_new = timestamp_raw  # For initialization only
        if self.config['Display time format'] == 'local':
            time_new = datetime.fromtimestamp(timestamp_raw).strftime('%m-%d %H:%M:%S.%f')
            # Note: if you would like to see the year in the display, add "%y-" to the format in the above line.
        elif self.config['Display time format'] == 'zero':
            time_new = timestamp_raw - self.start_timestamp
        header_split[1] = str(time_new)

        # Assemble the split data
        header_new = ''
        for i in range(len(header_split)):
            header_new += header_split[i]
            if i != len(header_split) - 2:
                header_new += '\t'

        log_tmp[0] = header_new

        log_new = ''
        for row in log_tmp:
            log_new += row + '\n'

        return log_new

    def extract_info_from_log(self, decoded_list):
        # This is the entry of extracting important information from the log lively.
        # Currently we only implement the live measurement result update + important log display.
        # If there is any log processing code, append to this function.
        if len(decoded_list) == 0:
            print('[ERROR]: Empty decoded list.')
            return
        live_measurement_log_list = ['LL1_LOG_ECL_INFO', 'PROTO_LL1_SERVING_CELL_MEASUREMENT_IND']
        important_log_list = []
        msg_name = decoded_list[1]

        if msg_name in live_measurement_log_list:
            self.process_live_measurement_log(decoded_list)

        # Note: it is not elif here because a log may fall into both categories.
        if msg_name in important_log_list:
            self.process_important_log(decoded_list)

    def process_live_measurement_log(self, decoded_list):

        msg_name = decoded_list[1]
        if msg_name == 'LL1_LOG_ECL_INFO':
            print(decoded_list[-1])

    def dy_extract_rsrp_snr_from_log(self, complete_log_list):
        # list[1] is time stamp
        # list[-1] is ordered message list
        # list[-1][-1] is decoded msg.
        # list[4] is message name
        if len(complete_log_list) < 6:
            # Missing element. Not moving forward.
            return
        measurement_msg_name = 'LL1_NRS_MEASUREMENT_LOG'  # note that the following indexes only work for this log.

        msg_name = complete_log_list[4]
        if msg_name == measurement_msg_name:
            # print(complete_log_list)
            time_stamp = complete_log_list[1]
            msg_payload = complete_log_list[-1]
            incoming_rsrp = msg_payload['rsrp']
            incoming_snr = msg_payload['snr']
            self.rsrp_snr_buf['ts'].append(time_stamp)
            self.rsrp_snr_buf['RSRP'].append(incoming_rsrp)
            self.rsrp_snr_buf['SNR'].append(incoming_snr)

            self.update_rsrp_snr_trigger.emit()  # tell the LogDecoderTabview to fetch data.

    def extract_npusch_power_from_log(self, complete_log_list):
        # self.npusch_power_buf = {'ts': [], 'type': [], 'power_db': [], 'repetition': [], 'iru': []}
        if len(complete_log_list) < 6:
            return  # invalid packets
        npusch_msg = ['LL1_PUSCH_CALC_TX_POWER', 'LL1_DCI_FORMAT_N0', 'LL1_DCI_FORMAT_N1_NORMAL', 'LL1_RAR_UL_GRANT']
        ecl_msg_name = 'LL1_LOG_ECL_INFO'

        msg_name = complete_log_list[4]
        if msg_name == ecl_msg_name:
            ecl = complete_log_list[-1]['current_ecl']
            reason = complete_log_list[-1]['ecl_selected_by']
            # print(reason)
            if reason == '3(LL1_RACH_ECL_SELECTED_NEXT_COVERAGE_LEVEL)':
                reason = '(next)'
            elif reason == '2(LL1_RACH_ECL_SELECTED_BY_MEASUREMENT)':
                reason = '(measure)'
            else:
                reason = '(unknown)'
            self.current_ecl = '{0} {1}'.format(ecl, reason)

        if msg_name not in npusch_msg:
            return  # save computation resource
        else:
            time_stamp = complete_log_list[1]
            msg_payload = complete_log_list[-1]
            # Order: ts, type, power db, repetition, iru number
            self.npusch_power_buf[0] = time_stamp
            # print(time_stamp)
            if msg_name == 'LL1_DCI_FORMAT_N0':
                self.npusch_power_buf[1:] = ['DAT', ' ', msg_payload['dci_n0']['repetition_number'],
                                             msg_payload['dci_n0']['resource_assignment_iru']]
            elif msg_name == 'LL1_DCI_FORMAT_N1_NORMAL':
                # FIXME: decoder.xml has error: the "repetition_number" is "repetion_number". S**t happens.
                self.npusch_power_buf[1:] = ['UCI', ' ', msg_payload['dci_n1']['repetion_number'], ' ']
            elif msg_name == 'LL1_RAR_UL_GRANT':
                self.npusch_power_buf[1:] = ['MG3', ' ', msg_payload['rar_pdu']['repetition_number'], ' ']
            elif msg_name == 'LL1_PUSCH_CALC_TX_POWER':
                self.npusch_power_buf[1:] = ['PWR', msg_payload['tx_power_db'], ' ', ' ']
            else:
                print('[ERROR] Wrong place. Payload:', msg_payload)

            self.update_npusch_power_trigger.emit()



