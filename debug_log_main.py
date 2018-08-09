from log_decoder import *


def run():
    my_decoder = DebugLogDecoder('BC95')
    my_decoder.xml_reader()
    # If save_to_file_flag == False, the data will be printed in the console,
    # otherwise they are saved to files

    filter_out_set = {}  # add item to only one of them!!! To remove invalid message, use 'N/A'.
    filter_in_set = {}  # add item to only one of them!!!

    filter_dict = {'FO': filter_out_set, 'FI': filter_in_set}

    # my_decoder.log_reader('NB-IoT 2018-4-27 19-40-03_0.txt', is_from_log_viewer=True, save_to_file_flag=True)
    my_decoder.log_reader('bc95_ul_packet_log.txt', filter_dict,  # bc95_reboot_log
                          is_from_log_viewer=True, save_to_file_flag=False)
    my_decoder.export_src_dest_pair('bc95_ul_packet_log')
    # my_decoder.export_stat_csv('bc95_reboot_log_')

def run_live():
    my_decoder = LiveUartLogDecoder('BC95', 'COM3')
    my_decoder.xml_reader()
    my_decoder.dbg_streaming()

if __name__ == '__main__':
    run_live()