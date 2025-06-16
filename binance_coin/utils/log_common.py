
# anh xạ chuoi cau hình sang cac hằng so cua thu vien
import logging
from logging.handlers import RotatingFileHandler
import os

from binance_coin.utils.common import AsciiFilter, SignalFilter


log_level_str = os.getenv('LOG_LEVEL', 'INFO')
log_filename = os.getenv('LOG_FILENAME', 'trading_bot.log')
# >>> THÊM TÊN FILE LOG CHO TÍN HIỆU <<<
signal_log_filename = os.getenv('SIGNAL_LOG_FILENAME', 'signals.log')

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
log_level = LOG_LEVELS.get(log_level_str.upper(), logging.INFO)

# logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

def getLog(name=None):
    # --- PHẦN 2: CaU HÌNH LOGGER (Su dụng gia tri từ file config) ---
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    ascii_filter = AsciiFilter()

    # --- Cấu hình handler chính (ghi mọi thứ vào trading_bot.log) ---
    file_handler = RotatingFileHandler(filename = log_filename, mode='w',
        backupCount=5,             # Số lượng file backup muốn giữ lại
        maxBytes=10 * 1024 * 1024, # Kích thước tối đa của file log (ví dụ: 10 MB)
        encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.addFilter(ascii_filter)

    # --- Cấu hình handler cho console ---
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)

    # --- Cấu hình handler phu ghi lai chot (ghi mọi thứ vào trading_bot.log) ---
    # Dùng mode 'a' (append) để lưu lại lịch sử các tín hiệu qua mỗi lần chạy
    signal_file_handler = logging.FileHandler(signal_log_filename, mode='a', encoding='utf-8')
    signal_file_handler.setLevel(logging.WARNING) # Chỉ quan tâm đến level WARNING trở lên
    # >>> BƯỚC 3: GẮN BỘ LỌC TÍN HIỆU VÀO HANDLER MỚI <<<
    signal_file_handler.addFilter(SignalFilter())
    signal_file_handler.addFilter(ascii_filter) # Tùy chọn: Dùng bộ lọc ASCII cho file signal


    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    signal_file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.addHandler(signal_file_handler)

    return logger
