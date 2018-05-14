from log_decoder import DebugLogDecoder


def run():
    my_decoder = DebugLogDecoder('BC95')
    my_decoder.xml_reader()
    
    # If save_to_file_flag == False, the data will be printed in the console,
    # otherwise they are saved to files
    my_decoder.log_reader('bc95_reboot_log.txt', is_from_log_viewer=True, save_to_file_flag=True)
    # my_decoder.log_reader('bc95_sending_packet_log.txt', is_from_log_viewer=True, save_to_file_flag=True)
   

if __name__ == '__main__':
    run()