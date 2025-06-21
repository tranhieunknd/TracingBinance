# manager_trading_coin
import json
import os
from pathlib import Path
from binance_coin.models.sell_buy import SellBuy
import binance_coin.utils.log_common as logCommon

manager_trading_coin = {}


class ManagementCoin(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ManagementCoin, cls).__new__(cls)
        return cls.instance

    def __init__(self, file_path: str = None) -> None:
        # Setup logger
        self.logger = logCommon.getLog(__name__)
        self.__file_path = file_path
        self.__manager_trading_coin = self.load_state()

    # @staticmethod
    def get_item_coin(self, coin_symbol) -> SellBuy:
        if not coin_symbol in self.__manager_trading_coin:
            self.__manager_trading_coin[coin_symbol] = SellBuy(
                coin_symbol=coin_symbol)
        return self.__manager_trading_coin[coin_symbol]

    # --- CÁC HÀM LƯU/TẢI TRẠNG THÁI (MỚI) ---
    def save_state(self):
        """Lưu từ điển trạng thái vào một file JSON."""
        self.logger.info(self.__file_path)
        if self.__file_path is None :
            return
        if not os.path.isfile(self.__file_path):
            # Tạo thư mục nếu chưa tồn tại
            Path(self.__file_path).touch(exist_ok=True)
            
        try:
            with open(self.__file_path, 'w', encoding='utf-8') as f:
                json.dump(self.__manager_trading_coin, f, indent=4)
            self.logger.info(f"Đã lưu trạng thái vào file: {self.__file_path}")
        except Exception as e:
            self.logger.error(f"Loi khi lưu trạng thái: {e}")

    def load_state(self) -> dict:
        """Tải trạng thái từ một file JSON. Nếu file không tồn tại, trả về trạng thái mặc định."""
        if self.__file_path is None:
            return {}

        try:
            if not os.path.isfile(self.__file_path) or os.path.getsize(self.__file_path) == 0:
                return {}

            with open(self.__file_path, 'r') as f:
                content = f.read().strip()
                # Kiểm tra file rỗng
                if not content:
                    return {}

                state_data = json.load(content)
                self.logger.info(
                    f"Da tai trang thai tu file: {self.__file_path} - Du lieu: {state_data}")
                return state_data
        except FileNotFoundError:
            self.logger.warning(
                f"Khong tim thay file trang thai. Bat dau voi trang thai mac dinh.")
            return {'position_active': False}
        except Exception as e:
            self.logger.error(
                f"Loi khi tai trang thai, su dung trang thai mac dinh: {e}")
            return {'position_active': False}
    def to_dict(self):
        return {
            "coin_symbol": self.__coin_symbol,
            "sell_time": self.__sell_time.isoformat() if self.__sell_time else None,
            "sell_price": self.__sell_price,
            "buy_time": self.__buy_time.isoformat() if self.__buy_time else None,
            "buy_price": self.__buy_price,
            "position_active": self.__position_active.name,
            "profit": self.__profit
        }


# def get_item_coin_global(coin_symbol) -> SellBuy:
#     if not coin_symbol in manager_trading_coin:
#         manager_trading_coin[coin_symbol] = SellBuy(coin_symbol=coin_symbol)
#     return manager_trading_coin[coin_symbol]
