import serial
import time
from PyQt5.QtCore import *
from LogDecoders import *


class UeAtController(object):

    def __init__(self, com, baudrate, enable_logging_flag=False, qt_flag=True):
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime((time.time())))
        print(current_time)
        # print("Connected to the UE via the serial port.")
        self.ser = serial.Serial(com, baudrate, timeout=2)
        print('UE serial connection established.')

        self.log_flag = enable_logging_flag
        self.qt_flag = qt_flag
        if self.log_flag:
            print('*** Message logging is enabled. ***')
            time_stamp = time.strftime('%Y%m%d_%H%M%S', time.localtime((time.time())))
            self.f_out = open('./local_output_data_buffer/' + time_stamp + '.log', 'w')

    def reconnect(self, com, baudrate):
        self.ser.close()
        self.ser = serial.Serial(com, baudrate, timeout=2)

    def at_write(self, msg):
        self.ser.write(self.encode_input(msg))

    def at_read(self):
        # end_flag = False
        # ret_msg = ''
        byte_flow = b''
        count = 0
        while count <= 500:
            # a simple AT return result parser
            new_char = self.ser.read(1)
            count += 1
            byte_flow += new_char
            # print(byte_flow)
            if len(byte_flow) >= 4 and byte_flow[-4:] == b'\r\nOK':
                break
            elif len(byte_flow) >= 7 and byte_flow[-7:] == b'\r\nERROR':
                break
        byte_flow += self.ser.read(2)
        return self.output_print(byte_flow)

    def at_read_has_server_msg(self):
        new_msg, msg_list = self.at_read()
        print(new_msg)
        sss = self.ser.read(2)
        print(sss)
        start_time = time.time()
        sonmi_msg = b''
        count = 0
        while count < 20:  # the maximum length is less than 20
            new_char = self.ser.read(1)
            count += 1
            if time.time() - start_time > 2:
                print('wait too long.')
                break
            sonmi_msg += new_char
            if len(sonmi_msg) >= 7 and sonmi_msg[-2:] == b'\r\n':
                break
            print(sonmi_msg)

    def encode_input(self, input_str):
        new_str = 'AT+' + input_str + '\r\n'
        print(new_str[0:80])
        if len(new_str) >= 80:
            new_str = new_str + '...'
        if self.log_flag:
            # log the msg to UE
            self.f_out.write(new_str)
        return new_str.encode('ascii')

    def output_print(self, byte_like):
        # Output formatting
        # print(byte_like)
        try:
            # new_msg = byte_like.decode('ascii')
            new_msg = byte_like.decode('utf-8')
        except UnicodeDecodeError:
            new_msg = '[ERROR] Unable to decode.\n'
        # print(new_msg)
        msg_list = new_msg.split('\r\n')
        msg_list = [x for x in msg_list if x != '']
        for item in msg_list:
            if len(item) <= 80:
                print(item)
            else:
                print(item[0:80], '...')
            if self.log_flag:
                self.f_out.write(item[0:80] + '\n')
        print('======')
        if self.log_flag:
            self.f_out.write('======\n')
        return new_msg, msg_list

    def create_udp_socket(self, local_port):
        # AT + NSOCR = DGRAM, 17, 8881, 1
        self.at_write('NSOCR=DGRAM,17,{0},1'.format(local_port))
        new_msg, msg_list = self.at_read()
        # print(new_msg, msg_list)
        if len(msg_list) == 2 and msg_list[1] == 'OK':
            print('UDP socket created successfully.')
        else:
            print('UDP socket already exists. Change a port if necessary.')
        return new_msg, msg_list

    def close_udp_socket(self, sock_num):
        self.at_write('NSOCL={0}'.format(sock_num))
        new_msg, msg_list = self.at_read()
        if msg_list[0] == 'OK':
            print('UDP socket closed successfully.')
        else:
            print('The requested UDP socket does not exist.')
        return new_msg, msg_list


class UeAtParser(object):

    def __init__(self, ue_info_dict):

        self.ue_info_dict = ue_info_dict

    def interpret_nuestats_radio(self, msg_list):
        # results from AT+NUESTATS (default) or AT+NUESTATS=RADIO
        value_list = [x.split(':')[1] for x in msg_list[0:11] if x != '']
        # print(value_list)
        self.ue_info_dict['Signal power'] = value_list[0]
        self.ue_info_dict['Total power'] = value_list[1]
        self.ue_info_dict['TX power'] = value_list[2]
        self.ue_info_dict['TX Time'] = value_list[3]
        self.ue_info_dict['RX Time'] = value_list[4]
        self.ue_info_dict['Cell ID'] = value_list[5]
        self.ue_info_dict['Coverage Level'] = value_list[6]
        self.ue_info_dict['SNR'] = str(float(value_list[7]) / 10)
        self.ue_info_dict['EARFCN'] = value_list[8]
        self.ue_info_dict['PCI'] = value_list[9]
        self.ue_info_dict['RSRQ'] = str(float(value_list[10]) / 10)
        # update panel

        cell_freq = self.interpret_earfcn(self.ue_info_dict['EARFCN'])
        if cell_freq[0] != 'N/A':
            self.ue_info_dict['DL Freq'] = cell_freq[0]
            self.ue_info_dict['UL Freq'] = cell_freq[1]

    def interpret_nuestats_cell(self, msg_list):
        # result from AT+NUESTATS=CELL
        if msg_list[0] != 'OK':
            cell_info_buffer = msg_list[0].split(',')
            self.ue_info_dict['EARFCN'] = cell_info_buffer[1]
            self.ue_info_dict['PCI'] = cell_info_buffer[2]
            self.ue_info_dict['Primary Cell'] = cell_info_buffer[3]
            self.ue_info_dict['RSRP'] = str(float(cell_info_buffer[4]) / 10)
            self.ue_info_dict['RSRQ'] = str(float(cell_info_buffer[5]) / 10)
            self.ue_info_dict['RSSI'] = str(float(cell_info_buffer[6]) / 10)
            self.ue_info_dict['SNR'] = str(float(cell_info_buffer[7]) / 10)
            # update panel
            cell_freq = self.interpret_earfcn(self.ue_info_dict['EARFCN'])
            if cell_freq[0] != 'N/A':
                self.ue_info_dict['DL Freq'] = cell_freq[0]
                self.ue_info_dict['UL Freq'] = cell_freq[1]
        else:
            print('Error: Invalid cell stats.')

    def interpret_nuestats_thp(self, msg_list):
        # results from AT+NUESTATS=THP
        value_list = [x.split(',')[2] for x in msg_list[0:4]]
        # msg_list = [x[13:] for x in msg_list]  # remove prefix
        self.ue_info_dict['RLC UL THP'] = value_list[0]
        self.ue_info_dict['RLC DL THP'] = value_list[1]
        self.ue_info_dict['PHY UL THP'] = value_list[2]
        self.ue_info_dict['PHY DL THP'] = value_list[3]

    def interpret_nuestats_bler(self, msg_list):
        # msg_list = [x[14:] for x in msg_list]  # remove prefix
        value_list = [x.split(',')[2] for x in msg_list[0:10]]
        # print(value_list)
        self.ue_info_dict['RLC UL BLER'] = value_list[0]
        self.ue_info_dict['RLC DL BLER'] = value_list[1]
        self.ue_info_dict['PHY UL BLER'] = value_list[2]
        self.ue_info_dict['PHY DL BLER'] = value_list[3]
        self.ue_info_dict['Total TX bytes'] = value_list[4]
        self.ue_info_dict['Total RX bytes'] = value_list[5]
        self.ue_info_dict['Total TX blocks'] = value_list[6]
        self.ue_info_dict['Total TX blocks'] = value_list[7]
        self.ue_info_dict['Total RTX blocks'] = value_list[8]
        self.ue_info_dict['Total ACK/NACK RX'] = value_list[9]

    def interpret_earfcn(self, earfcn):
        # possible deployment band: 2, 3, 5, 8, 20, 28
        # print('run here')
        earfcn = int(earfcn)
        band_indicator = -1
        band_list = ['2', '3', '5', '8', '20', '28']
        f_dl_low = [1930, 1805, 869, 925, 791, 758]
        f_ul_low = [1850, 1710, 824, 880, 832, 703]
        n_dl_offs = [600, 1200, 2400, 3450, 6150, 9210]
        if 600 <= earfcn <= 1199:
            band_indicator = 0  # Band 2
        elif 1200 <= earfcn <= 1949:
            band_indicator = 1  # Band 3
        elif 2400 <= earfcn <= 2649:
            band_indicator = 2  # Band 5
        elif 3450 <= earfcn <= 3799:
            band_indicator = 3  # Band 8
        elif 6150 <= earfcn <= 6449:
            band_indicator = 4  # Band 20
        elif 9210 <= earfcn <= 9659:
            band_indicator = 5  # Band 28
        if band_indicator != -1:
            print('Deploy band:', band_list[band_indicator])
            freq_dl = f_dl_low[band_indicator] + 0.1 * (earfcn - n_dl_offs[band_indicator])
            freq_ul = f_ul_low[band_indicator] + 0.1 * (earfcn - n_dl_offs[band_indicator])
            return [str(freq_dl), str(freq_ul)]
        else:
            return ['N/A', 'N/A']


class GpsController(QThread):
    gps_trigger = pyqtSignal()

    def __init__(self, com, rate):

        super(GpsController, self).__init__()
        self.com = com
        self.rate = rate
        self.ser = serial.Serial(com, rate, timeout=3)
        print('GPS serial connection established.')
        # when there is no signal, use the null dict.
        self.gps_info_null_dict = {'Latitude': 'N/A', 'Longitude': 'N/A',
                                   'Ground speed': '0', 'Available satellite': '0',
                                   'Latitude Deg': 'N/A', 'Longitude Deg': 'N/A',
                                   'UTC time': 'N/A', 'Ground speed mps': 'N/A',
                                   'Ground speed Knot': 'N/A', 'Height of geoid': 'N/A',
                                   'PDOP': '99', 'VDOP': '99', 'Latitude Raw': 'N/A',
                                   'Longitude Raw': 'N/A', 'Position type': '1',
                                   'HDOP': '99',
                                   'Sat_id_list': ['X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X'],
                                   'Sat_cnr_list': ['X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X']}
        self.gps_info_dict = self.gps_info_null_dict.copy()

    def run(self):
        # this must be called run(), it is a function in QThread
        while True:
            buf = self.read_gps(500)
            self.nmea_interpreter(buf)
            self.gps_trigger.emit()
            # time.sleep(0.5)

    def read_gps(self, amount):
        byte_buffer = self.ser.read(amount)
        info_buffer = byte_buffer.decode('utf-8')
        # print(info_buffer)
        return info_buffer.split('\r\n')
        # print(info_buffer.split('\r\n'))

    def nmea_interpreter(self, info_buffer):
        # print(info_buffer)
        latitude_raw = ''
        ns_indicator = ''
        longitude_raw = ''
        ew_indicator = ''
        for msg in info_buffer:
            msg_split = msg.split(',')
            if '*' in msg_split[-1]:
                # complete message, remove the checksum
                msg_split[-1] = msg_split[-1].split('*')[0]
                # begin to decode.
                if msg_split[0] == '$GPRMC' and len(msg_split) == 13:
                    # GPRMC message, check completeness
                    # print(msg_split)
                    self.gps_info_dict['UTC time'] = msg_split[1]
                    latitude_raw = msg_split[3]
                    ns_indicator = msg_split[4]  # north or south
                    longitude_raw = msg_split[5]
                    ew_indicator = msg_split[6]  # east or west
                elif msg_split[0] == '$GPVTG' and len(msg_split) == 10:
                    # GPVEG msg, complete
                    # print(msg_split)
                    if msg_split[7] != '':
                        self.gps_info_dict['Ground speed'] = msg_split[7]
                        self.gps_info_dict['Ground speed mps'] = '{0:5f}'.format(float(msg_split[7]) / 3.6)
                    else:
                        self.gps_info_dict['Ground speed'] = 'X'
                        self.gps_info_dict['Ground speed mps'] = 'X'
                    if msg_split[5] != '':
                        self.gps_info_dict['Ground speed Knot'] = msg_split[5]
                    else:
                        self.gps_info_dict['Ground speed Knot'] = 'X'
                    # print(msg_split)
                elif msg_split[0] == '$GPGGA' and len(msg_split) == 15:
                    # GPGGA msg, complete
                    self.gps_info_dict['UTC time'] = msg_split[1]
                    latitude_raw = msg_split[2]
                    ns_indicator = msg_split[3]  # north or south
                    longitude_raw = msg_split[4]
                    ew_indicator = msg_split[5]  # east or west
                    self.gps_info_dict['Available satellite'] = msg_split[7]
                    self.gps_info_dict['HDOP'] = msg_split[8]
                    self.gps_info_dict['Altitude'] = msg_split[9]
                    self.gps_info_dict['Height of geoid'] = msg_split[11]
                elif msg_split[0] == '$GPGSA' and len(msg_split) == 18:
                    # GPGSA msg, complete
                    self.gps_info_dict['Position type'] = msg_split[2]
                    self.gps_info_dict['PDOP'] = msg_split[15]
                    self.gps_info_dict['HDOP'] = msg_split[16]
                    self.gps_info_dict['VDOP'] = msg_split[17]
                elif msg_split[0] == '$GPGSV' and len(msg_split) % 4 == 0:
                    # GPGSV msg, most complicated one.
                    if msg_split[3] != '':
                        avail_sat = int(msg_split[3])
                        self.gps_info_dict['Available satellite'] = msg_split[3]
                    else:
                        self.gps_info_dict['Available satellite'] = '0'
                        continue
                    # first put everything into default null list
                    self.gps_info_dict['Sat_id_list'] = self.gps_info_null_dict['Sat_id_list']
                    self.gps_info_dict['Sat_cnr_list'] = self.gps_info_null_dict['Sat_cnr_list']
                    # print(msg_split)
                    if msg_split[2] == '1':
                        if avail_sat >= 1:
                            self.gps_info_dict['Sat_id_list'][0] = msg_split[4]
                            self.gps_info_dict['Sat_cnr_list'][0] = msg_split[7]
                        if avail_sat >= 2:
                            self.gps_info_dict['Sat_id_list'][1] = msg_split[8]
                            self.gps_info_dict['Sat_cnr_list'][1] = msg_split[11]
                        if avail_sat >= 3:
                            self.gps_info_dict['Sat_id_list'][2] = msg_split[12]
                            self.gps_info_dict['Sat_cnr_list'][2] = msg_split[15]
                        if avail_sat >= 4:
                            self.gps_info_dict['Sat_id_list'][3] = msg_split[16]
                            self.gps_info_dict['Sat_cnr_list'][3] = msg_split[19]
                    if msg_split[2] == '2':
                        if avail_sat >= 5:
                            self.gps_info_dict['Sat_id_list'][4] = msg_split[4]
                            self.gps_info_dict['Sat_cnr_list'][4] = msg_split[7]
                        if avail_sat >= 6:
                            self.gps_info_dict['Sat_id_list'][5] = msg_split[8]
                            self.gps_info_dict['Sat_cnr_list'][5] = msg_split[11]
                        if avail_sat >= 7:
                            self.gps_info_dict['Sat_id_list'][6] = msg_split[12]
                            self.gps_info_dict['Sat_cnr_list'][6] = msg_split[15]
                        if avail_sat >= 8:
                            self.gps_info_dict['Sat_id_list'][7] = msg_split[16]
                            self.gps_info_dict['Sat_cnr_list'][7] = msg_split[19]
                    if msg_split[2] == '3':
                        if avail_sat >= 9:
                            self.gps_info_dict['Sat_id_list'][8] = msg_split[4]
                            self.gps_info_dict['Sat_cnr_list'][8] = msg_split[7]
                        if avail_sat >= 10:
                            self.gps_info_dict['Sat_id_list'][9] = msg_split[8]
                            self.gps_info_dict['Sat_cnr_list'][9] = msg_split[11]
                        if avail_sat >= 11:
                            self.gps_info_dict['Sat_id_list'][10] = msg_split[12]
                            self.gps_info_dict['Sat_cnr_list'][10] = msg_split[15]
                        if avail_sat >= 12:
                            self.gps_info_dict['Sat_id_list'][11] = msg_split[16]
                            self.gps_info_dict['Sat_cnr_list'][11] = msg_split[19]
            else:
                # incomplete GPS message
                continue  # just a place holder.
            # print(msg_split)
        if latitude_raw != '':
            # make sure the buffer has the info we want
            self.gps_info_dict['Latitude Raw'] = latitude_raw
            self.gps_info_dict['Longitude Raw'] = longitude_raw
            self.gps_info_dict['Latitude'] = self.nmea_to_dms(latitude_raw) + ns_indicator
            self.gps_info_dict['Longitude'] = self.nmea_to_dms(longitude_raw) + ew_indicator
            self.gps_info_dict['Latitude Deg'] = self.nmea_to_decimal_deg(latitude_raw) + ns_indicator
            self.gps_info_dict['Longitude Deg'] = self.nmea_to_decimal_deg(longitude_raw) + ew_indicator
        else:
            self.gps_info_dict['Latitude Raw'] = 'N/A'
            self.gps_info_dict['Longitude Raw'] = 'N/A'
            self.gps_info_dict['Latitude'] = 'N/A'
            self.gps_info_dict['Longitude'] = 'N/A'
            self.gps_info_dict['Latitude Deg'] = 'N/A'
            self.gps_info_dict['Longitude Deg'] = 'N/A'

    def nmea_to_decimal_deg(self, lat_long_str):
        # convert to xxx.xxx deg
        if lat_long_str != '':
            divided = lat_long_str.split('.')
            first_part = divided[0][:-2]
            second_part = divided[0][-2:]
            third_part = divided[1][:4]
            float_num = float(first_part) + float(second_part) / 60 + float(third_part) / 600000
            # print(float_num)
            return '{0:4f}'.format(float_num)
        else:
            return 'N/A'

    def nmea_to_dms(self, lat_long_str):
        # convert to degree, minute, second format
        if lat_long_str != '':
            divided = lat_long_str.split('.')
            first_part = divided[0][:-2]
            second_part = divided[0][-2:]
            third_part = divided[1][:4]
            res = '{0}°{1}\'{2}\'\''.format(int(first_part),
                                            int(second_part),
                                            float(third_part) * 6 / 1000)
            # print(res)
            return res
        else:
            return 'N/A'
