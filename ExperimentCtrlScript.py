# -*- coding: UTF-8 -*-
from PyQt5.QtCore import *
import os
import random
import time
from DeviceHandlers import UeAtParser
import csv


class UplinkMeasurement(QThread):
    ul_trigger = pyqtSignal()

    def __init__(self, ue_handler, config):
        super(UplinkMeasurement, self).__init__()
        self.intermediate_output = {'System log list': [], 'Sent notice': '',
                                    'AT result': ''}

        self.test_string = 256 * 'FF'  # default test string

        self.config = config
        self.ue_handler = ue_handler
        self.packet_length = self.config['UL packet len']
        self.packet_num = self.config['UL packet num']
        self.delay_ms = self.config['UL packet delay']

        if self.file_handler() == 0:
            print('Run UL test with the default buffer.')

        self.run_flag = True

    def run(self):
        self.run_flag = True
        random_data = random.randint(100, 999)  # every time the random number is different to differentiate tests.
        history = []
        count = 0
        if self.config['UDP local socket'] == 'X':  # change to True to enable.
            # try to open the UDP socket again, in case there is some error.
            local_port = self.config['UDP local port']
            _, _ = self.ue_handler.create_udp_socket(local_port)
            self.intermediate_output['System log list'].append('Try to create UDP socket again.')

        self.intermediate_output['System log list'].append('ULT: uplink test begins.')
        while count < self.packet_num and self.run_flag:
            print(self.fetch_packet_text(count))
            # add a header to each package
            count += 1
            # packet = '//Package index: {0:4d}//'.format(count)
            packet = '{0:03d}/{1:03d}/{2:03d}/'.format(count, self.packet_num, random_data)
            packet += self.test_string[0:self.packet_length - 12]  # 12 is the header length
            # print(len(packet))
            packet2msg = packet.encode('utf-8').hex()  # type: str
            # print(len(packet2msg))
            self.ue_handler.at_write('NSOST={0},{1},{2},{3},{4}'.format(self.config['UDP local socket'],
                                                                        self.config['UDP server IP'],
                                                                        self.config['UDP server port'],
                                                                        len(packet2msg) // 2,
                                                                        packet2msg))
            self.intermediate_output['System log list'].append(
                'Packet sent: {0:03d}/{1:03d}'.format(count, self.packet_num))

            print('[INFO] Packet count: {0:3d}/{1:3d}'.format(count, self.packet_num))
            new_msg, msg_list = self.ue_handler.at_read()
            self.intermediate_output['AT result'] += new_msg
            self.ul_trigger.emit()

            if len(msg_list) == 2:
                history.append(1)  # success
            else:
                history.append(0)  # failure
            self.msleep(self.delay_ms)
            # time.sleep(self.delay_ms/1000)
            # self.display_ue_log()
        res_str = ''
        for res in history:
            res_str += str(res)
        self.intermediate_output['System log list'].append('Result overview: {0}'.format(res_str))
        self.intermediate_output['System log list'].append('ULT: uplink test finished.\n')

    def file_handler(self):
        # Read the file from folder as buffer.
        test_file_path = './assets/Lorem Ipsum.txt'
        if os.path.exists(test_file_path):
            with open(test_file_path, 'r') as f_tx:
                self.test_string = ''
                for lines in f_tx:
                    self.test_string += lines
            f_tx.close()
            print('Length of text string: {0}'.format(len(self.test_string)))
            return 1
        else:
            self.intermediate_output['System log list'].append(
                '[Error] Lorem Ipsum.txt does not exist. Create one in the "assets" folder, '
                'add some texts (at least 1024 Bytes) and retry.')
            return 0

    def fetch_packet_text(self, packet_count):
        if self.packet_length * packet_count > len(self.test_string):
            ret_msg = self.test_string[len(self.test_string) - self.packet_length * packet_count:]
            ret_msg += self.test_string[0:self.packet_length - len(ret_msg)]
        else:
            ret_msg = self.test_string[self.packet_length * packet_count: self.packet_length * (packet_count + 1)]
        return len(ret_msg)


class DownlinkMeasurement(QThread):

    def __init__(self, ue_handler, config):
        super(DownlinkMeasurement, self).__init__()

        self.ue_handler = ue_handler
        self.config = config

    def run(self):
        pass
        # TODO: Add the downlink measurement test details.
