from enum import Enum, auto

class PositionState(Enum):
    """ Đang có vị thế (có coin) """
    CO_VI_THE = 1 # Đang có vị thế (có coin)
    KHONG_VI_THE = 2 # Không có vị thế (ko có coin)
    NONE = 3 # ko Action