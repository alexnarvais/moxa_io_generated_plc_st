from moxa_io import MoxaFileProc
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    read_file_path = r"moxa_config.csv"
    write_file_path = r"plc_structured_text.txt"
    moxa_io_file = MoxaFileProc(rd_file_path=read_file_path, wr_file_path=write_file_path)
    io = moxa_io_file.read_moxa_io_csv()
    moxa_io_file.wr_moxa_io_txt(io)




