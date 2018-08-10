from log_decoder import *

# global setting

filter_out_set = {'N/A'}  # add item to only one of them!!! To remove invalid message, use 'N/A'.
filter_in_set = {}  # add item to only one of them!!!
filter_dict = {'FO': filter_out_set, 'FI': filter_in_set}
is_from_log_viewer = True


def run_offline_ulv():

    my_decoder = UlvLogDecoder('BC95', filter_dict)  # UELogViewer debug log processing.
    my_decoder.xml_loader()
    my_decoder.log_reader('bc95_ul_packet_log.txt',  # bc95_reboot_log
                          save_to_file_flag=False)
    my_decoder.export_src_dest_pair('bc95_ul_packet_log')
    # my_decoder.export_stat_csv('bc95_reboot_log_')


def run_live():
    # Note: filtered logs will not be printed, if you want to export them to file, specify it in the config.
    config = {'Export to file': True, 'Export filtered logs': False, 'Time format': '%m-%d %H:%M:%S'}
    my_decoder = LiveUartLogDecoder('BC95', 'COM3', filter_dict, config)
    my_decoder.xml_loader()
    my_decoder.dbg_streaming()


if __name__ == '__main__':
    # If save_to_file_flag == False, the data will be printed in the console,
    # otherwise they are saved to files
    if is_from_log_viewer:
        run_offline_ulv()
    else:
        run_live()
