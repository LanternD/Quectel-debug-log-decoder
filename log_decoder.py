import csv
import xml.etree.cElementTree as ET
from collections import OrderedDict
import serial
import time
import os.path
import seaborn


class DebugLogDecoder(object):
    # Load the XML file and then parse and format the logs.
    def __init__(self, device_name, filter_dict):

        self.device_name = device_name.upper()
        self.filter_dict = filter_dict
        self.filter_flag = self.filter_dict_checker()  # 0: no filter, 1: filter out enabled, 2: filter in enabled.

        self.decoder_dir = './decoders/'
        self.decode_output_dir = './output_files/'

        if self.device_name == 'BC28':
            self.decoder_xml = 'messages_bc28.xml'
        elif self.device_name == 'BC95':
            self.decoder_xml = 'messages_bc95.xml'
        else:
            print('Unsupported device. Change the device or check the spell.')
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
        print('Message dict length:', len(self.message_dict))
        # print(type_set)
        print('Available types:', len(type_set))

    def filter_dict_checker(self):

        if len(self.filter_dict['FO']) > 0 and len(self.filter_dict['FI']) > 0:
            raise ValueError('Invalid arguments in the filter dictionary! Check and rerun.')
        filter_flag = 0
        if len(self.filter_dict['FO']) > 0:
            filter_flag = 1
            print('Filter-Out enabled.')
        elif len(self.filter_dict['FI']) > 0:
            filter_flag = 2
            print('Filter-In enabled.')
        return filter_flag

    def hex_to_decimal(self, hex_list):
        # note that the string list is LSB first, for example, 12-34-aa is 0xAA3412
        if type(hex_list) == str:
            # basically there is ONLY ONE byte.
            return int(hex_list, 16)
        hex_string = ''
        hex_list.reverse()
        for byte in hex_list:
            hex_string += byte
        return int(hex_string, 16)

    def hex_to_ascii(self, byte_list):
        byte_str = ''
        byte_list.reverse()
        for b_ascii in byte_list:
            if b_ascii != '00':
                byte_str += b_ascii
        return bytearray.fromhex(byte_str).decode()

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

    def parse_one_msg_common(self, data_flow):
        result_list = []
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

        decoded_msg = ''

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
                        if info > 65536//2:
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
        if info_list[3] == 'N/A':
            return info_list[0] + ' Invalid Msg\n'  # this is an invalid packet. Remove these two lines if you want them.
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
                one_line = ' {0}{1}: {2}'.format(level*'\t', field_key, field_value)
            elif type(field_value) == list:
                counter = 0
                linefy = ''
                for item in field_value:
                    linefy += '{0}_{1}: {2} / '.format(field_key, counter, item)
                    counter += 1
                one_line = ' {0}{1}'.format(level*'\t', linefy)
            elif type(field_value) == OrderedDict:
                # print('>>> Ordered Dict.')
                another_dict = self.format_ordered_dict(level + 1, field_value)
                one_line = ' {0}{1}: \n{2}'.format(level*'\t', field_key, another_dict)
            else:
                one_line = '??????'
            if one_line[-1] != '\n':
                one_line += '\n'
            return_msg += one_line
        return return_msg

    def export_stat_csv(self, output_name_prefix):
        stat_mat = []
        ignored_layers = []  # ['LL1', 'UICC', 'DSP', '0 count']

        print('Source Layer stats:')
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

        print('Total number of available msg type:', len(self.src_dest_pair_stat))
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
        self.log_dir = './log_files/'

    def log_reader(self, log_path, save_to_file_flag=True):

        if save_to_file_flag:
            output_name = log_path[:-4]
            f_write = open(self.decode_output_dir + 'decoded_' + output_name + '.txt', 'w', newline='')

        with open(self.log_dir + log_path, 'r', encoding='utf-8') as log_file:
            # print or write the very first line.
            header_list = ['Seq ID', 'Timestamp', 'Time tick', 'Decimal ID', 'Msg ID', 'Source',
                           'Destination', 'Length', 'Formatted Output']
            header_print = '{0}\t{1}\t\t{3}({2})\t\t{4} -> {5}\t{6}\t{7}'.format(header_list[0], header_list[1],
                                                                                 header_list[2], header_list[3],
                                                                                 header_list[4], header_list[5],
                                                                                 header_list[6], header_list[7])
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
                        print('{0} messages are processed.'.format(count))
                else:
                    print(formatted_res)  # the actual meanings of each packet
            print('All messages are decoded.\n')
            if self.filter_flag == 1:
                print('Filter-out count:', filter_out_count)
            elif self.filter_flag == 2:
                print('Filter-in count:', count)

        if save_to_file_flag:
            f_write.flush()
            f_write.close()
            print('Results have been write to file.')
            # print(res)


class LiveUartLogDecoder(DebugLogDecoder):

    def __init__(self, dev_name, uart_port, filter_dict, config):
        super(LiveUartLogDecoder, self).__init__(dev_name, filter_dict)
        self.ue_dbg_port = uart_port
        self.dbg_port_handler = serial.Serial(self.ue_dbg_port, 921600)  # fixed baudrate
        self.dbg_run_flag = True
        self.config = config

    def read_byte(self, num):
        # read byte and format it.
        return self.dbg_port_handler.read(num).hex().upper()  # hex() converts byte to str.

    def dbg_streaming(self):
        states = {'UNKNOWN': 0, 'PREAMBLE': 1, 'COUNT': 2, 'TICK': 3,
                  'DATA': 5, 'LENGTH': 4, 'FINISHED': 6}  # UART state machine
        str_buf = []
        st = states['PREAMBLE']

        # initialize local variable to prevent warning.
        seq_num = 0
        time_tick = 0
        parsed_msg = ''
        time_stamp = .0
        payload_len = 1

        empty_msg_list = [0, 0, .0, []]  # order: seq_num, timestamp
        parsed_log_dict = empty_msg_list.copy()

        while self.dbg_run_flag:
            # run until the flag is set.
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
                        parsed_log_dict['Timestamp'] = time_stamp
                    else:
                        str_buf = []
                else:
                    str_buf = []  # empty the buf and restart
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
                    print('INFO: Inconsistent sequence number detected!')
                seq_num = num_temp
                parsed_log_dict['Sequence number'] = seq_num  # update the dict
                # print(str_buf, seq_num)
                str_buf = []
                st = states['TICK']
            elif st == states['TICK']:
                str_buf = []
                for i in range(4):
                    str_buf.append(self.read_byte(1))
                time_tick = self.hex_to_decimal(str_buf)
                parsed_log_dict['Time tick'] = time_tick  # update the dict
                dummy = self.read_byte(4)  # neglect the useless bytes.
                st = states['LENGTH']
            elif st == states['LENGTH']:
                str_buf = []
                for i in range(2):
                    str_buf.append(self.read_byte(1))
                payload_len = self.hex_to_decimal(str_buf)
                st = states['DATA']
            elif st == states['DATA']:
                str_buf = []
                for i in range(payload_len):
                    str_buf.append(self.read_byte(1))
                disp_list = self.parse_one_msg_common(str_buf)  # order: msg_id_dec, msg_name, msg_src, msg_dest, msg_length, decoded_msg
                parsed_log_dict['Display list'] = disp_list
                self.format_parsed_log_dict(parsed_log_dict)
                # print(parsed_log_dict)
                st = states['FINISHED']
            elif st == states['FINISHED']:
                parsed_log_dict = empty_msg_list.copy()
                st = states['PREAMBLE']  # recycle the UART state machine
            elif st == states['UNKNOWN']:
                print('Something wrong happens. Reset to PREAMBLE state.')
                st = states['PREAMBLE']

        str_pnt = ''
        for h in str_buf:
            str_pnt += h + ' '
        print(str_pnt)

    def format_parsed_log_dict(self, log_dict):
        # convert the dict to actual messages.
        timestamp = log_dict['Timestamp']
        ts_formatted = time.strftime(self.config['Time format'], time.localtime(timestamp))
        disp_list = log_dict['Display list']
        msg_id_dec = disp_list[0]
        msg_name = disp_list[1]
        msg_src = disp_list[2]
        msg_dest = disp_list[3]
        msg_len = disp_list[4]
        decoded_msg = disp_list[5]

        list_tmp = [log_dict['Sequence number'], ts_formatted, log_dict['Time tick'], msg_name, msg_id_dec, msg_src, msg_dest, msg_len]
        print(heading)
        print(decoded_msg)