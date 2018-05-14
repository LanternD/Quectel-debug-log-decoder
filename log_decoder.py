import csv
import xml.etree.cElementTree as ET
from collections import OrderedDict
import os.path

class DebugLogDecoder(object):

    def __init__(self, device_name):

        self.device_name = device_name.upper()
        self.decoder_dir = './decoders/'
        self.log_dir = './log_files/'
        self.decode_output_dir = './output_files/'

        if self.device_name == 'BC28':
            self.decoder_xml = 'messages_bc28.xml'
        elif self.device_name == 'BC95':
            self.decoder_xml = 'messages_bc95.xml'
        else:
            self.decoder_xml = None
        self.tag_name_prefix = '{http://tempuri.org/xmlDefinition.xsd}'
        self.message_dict = {}
        self.msg_buffer = []

        self.layer_dict = {0:'INVALID', 1:'DSP', 2:'LL1', 3:'L2_UL', 4:'L2_DL',
                           5:'MAC_DL', 6:'MAC_UL', 7:'RLC_UL', 8:'RLC_DL',
                           9:'PDCP_DL', 10:'PDCP_UL', 11:'RRC', 12:'EMMSM',
                           13:'MN', 14:'AT', 15:'PDH', 16:'LWIP', 17:'SIM',
                           18:'LOG', 19:'MONITOR', 20:'HOSTTEST_RF', 21:'HOSTTEST_TX',
                           22:'HOSTTEST_RX', 23:'NVCONFIG', 24:'NAS', 25:'IRMALLOC',
                           26:'PROTO', 27:'SMS', 28:'LPP', 29:'UICC', 30:'UE',
                           31:'NUM_STACK'}

    def xml_reader(self):
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

    def log_reader(self, log_path, is_from_log_viewer=True, save_to_file_flag=True):
        if not is_from_log_viewer:
            print('Unable to parse messages from QCOM yet.')
            return 0

        if save_to_file_flag:
            output_name = log_path[:-4]
            f_write = open(self.decode_output_dir + 'decoded_' + output_name + '.txt', 'w', newline='')

        with open(self.log_dir + log_path, 'r', encoding='utf-8') as log_file:
            header_list = ['Seq ID', 'Timestamp', 'Decimal ID', 'Msg ID', 'Source',
                           'Destination', 'Length', 'Formatted Output']
            header_print = '{0}\t{1}\t\t{3}({2})\t\t{4} -> {5}\t{6}\t{7}'.format(header_list[0], header_list[1],
                                                                                 header_list[2], header_list[3],
                                                                                 header_list[4], header_list[5],
                                                                                 header_list[6], header_list[7])
            if not save_to_file_flag:
                print(header_print)
            # print(header_list)
            count = 0
            for line in log_file:
                res = self.parse_one_msg(line)
                formatted_res = self.packet_output_formatting(res)
                if save_to_file_flag:
                    f_write.write(formatted_res + '\n')
                    count += 1
                    if count % 1000 == 0:
                        print('{0} messages are processed.'.format(count))
                else:
                    print(formatted_res)
            print('All messages are decoded.')

        if save_to_file_flag:
            f_write.flush()
            f_write.close()
            print('Results have been write to file.')
                # print(res)

    def hex_to_decimal(self, hex_list):
        # note that the string is LSB first, for example, 12-34-aa is 0xAA3412
        if type(hex_list) == str:
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

    def parse_one_msg(self, buf_line):
        if buf_line == '':
            return 0
        display_list = []
        line_temp = buf_line.split(';')
        # Structure:
        # 1 line = timestamp + data flow
        # data flow = msg header + msg payload
        # msg header = msg id + source + destination + length
        # msg payload are decoded based on the XML.

        time_stamp = line_temp[1]
        time_stamp = self.timestamp_parsing(time_stamp, is_beijing_time=True)


        data_flow = line_temp[2].split('-')
        first_field = data_flow[0:4]  # no idea what it is
        msg_counter_hex = data_flow[4:8]
        msg_counter = self.hex_to_decimal(msg_counter_hex)

        msg_header = data_flow[8:16]

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
        try:
            msg_dest = self.layer_dict[msg_dest_idx]
        except KeyError:
            msg_dest = 'Unknown'
        # print(msg_src, msg_dest, msg_length)

        decoded_msg = ''

        # Most important part: parse the payload
        if msg_length > 0 and msg_name != 'N/A':
            data_flow[-1] = data_flow[-1].replace('\n', '')
            payload_list = data_flow[16:]
            # print(self.message_dict[msg_id_dec][6].tag)
            if self.message_dict[msg_id_dec][6].tag == self.tag_name_prefix + 'Fields':
                decoded_msg = self.parse_fields(payload_list, self.message_dict[msg_id_dec][6])

        display_list += ['#{0}'.format(msg_counter), time_stamp, msg_id_dec, msg_name,
                         msg_src, msg_dest, msg_length, decoded_msg]
        return display_list

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
        header_list = info_list[:-1]
        header_print = '{0}\t{1}\t\t{3}({2})\t\t{4} -> {5}\t{6}'.format(header_list[0], header_list[1],
                                                                             header_list[2], header_list[3],
                                                                             header_list[4], header_list[5],
                                                                             header_list[6])
        ret_msg += header_print
        ret_msg += '\n'
        # The most important one
        msg_ordered_dict = info_list[-1]
        formatted_ordered_list = self.format_ordered_list(0, msg_ordered_dict)
        ret_msg += formatted_ordered_list
        return ret_msg

    def format_ordered_list(self, level, odict):
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
                another_dict = self.format_ordered_list(level+1, field_value)
                one_line = ' {0}{1}: \n{2}'.format(level*'\t', field_key, another_dict)
            else:
                one_line = '??????'
            if one_line[-1] != '\n':
                one_line += '\n'
            return_msg += one_line
        return return_msg
