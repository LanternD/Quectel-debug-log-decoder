from log_decoder import DebugLogDecoder


def run():
    my_decoder = DebugLogDecoder('BC95')
    my_decoder.xml_reader()
    # If save_to_file_flag == False, the data will be printed in the console,
    # otherwise they are saved to files

    filter_out_set = {}  # add item to only one of them!!! To remove invalid message, use 'N/A'.
    filter_in_set = {'UICC_DBG_LOG_P0'}  # add item to only one of them!!!

    filter_dict = {'FO': filter_out_set, 'FI': filter_in_set}

    # my_decoder.log_reader('NB-IoT 2018-4-27 19-40-03_0.txt', is_from_log_viewer=True, save_to_file_flag=True)
    my_decoder.log_reader('20180427_short.txt', filter_dict,
                          is_from_log_viewer=True, save_to_file_flag=False)


if __name__ == '__main__':
    run()