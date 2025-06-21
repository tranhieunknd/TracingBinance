
import logging


class AsciiFilter(logging.Filter):
    def to_ascii(self, text: str) -> str:
        return str(text).encode('ascii', 'ignore').decode('ascii')
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self.to_ascii(record.msg)
        if record.args:
            record.args = tuple(self.to_ascii(arg) for arg in record.args)
        return True

# >>> BƯỚC 1: TẠO BỘ LỌC TÍN HIỆU <<<
class SignalFilter(logging.Filter):
    """
    Bộ lọc này chỉ cho phép các log record là tín hiệu Mua/Bán đi qua.
    Chúng ta nhận diện tín hiệu bằng các emoji đặc trưng.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        # Chuyển record.msg về string để xử lý an toàn
        msg_str = str(record.msg)
        # Chỉ cho phép các log chứa emoji tín hiệu hoặc dòng phân cách '==='
        return 'MUA' in msg_str or 'BAN' in msg_str or 'BUY' in msg_str or 'SELL' in msg_str  # or msg_str.startswith("=")
