from log_decoder import *

# global setting
filter_out_set = {'N/A', 'UICC_DBG_LOG_P0', 'UICC_DBG_LOG_P1', 'UICC_DBG_LOG_P2'}  # add item to only one of them!!! E.g. to remove invalid message, use 'N/A'.
filter_in_set = {}  # add item to only one of them!!!
filter_dict = {'FO': filter_out_set, 'FI': filter_in_set}
is_from_log_viewer = False


def run_offline_ulv():

    my_decoder = UlvLogDecoder('BC95', filter_dict)  # UELogViewer debug log processing.
    my_decoder.xml_loader()
    my_decoder.log_reader('bc95_ul_packet_log.txt',  # bc95_reboot_log
                          save_to_file_flag=False)
    my_decoder.export_src_dest_pair('bc95_ul_packet_log')
    # my_decoder.export_stat_csv('bc95_reboot_log_')


def run_online_uart():
    config = {'Export to file': True,  # choose to export the decoded info. The raw log is mandatory.
              'Export filename time prefix': '%y%m%d_%H%M%S',
              'Export filtered logs': False,  # filtered logs will not be printed, but you can export them to file.
              'Time format': '%m-%d %H:%M:%S.%f',  # see time.strftime() for detail.
              'Export format': 'csv'}  # format: txt or csv, need to enable "export to file first".
    my_decoder = UartOnlineLogDecoder('BC95', 'COM3', filter_dict, config)
    my_decoder.xml_loader()
    my_decoder.dbg_streaming()


if __name__ == '__main__':
    # If save_to_file_flag == False, the data will be printed in the console,
    # otherwise they are saved to files
    if is_from_log_viewer:
        run_offline_ulv()
    else:
        run_online_uart()
