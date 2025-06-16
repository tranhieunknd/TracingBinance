from datetime import datetime

from binance_coin.enums.position_state import PositionState


class SellBuy:

    def __init__(self, coin_symbol , sell_time: datetime = None, sell_price: float = None, buy_time: datetime = None, buy_price: float = None):
        self.__coin_symbol = coin_symbol
        self.__sell_time = sell_time
        self.__sell_price = sell_price # Giá bán
        self.__buy_time = buy_time
        self.__buy_price = buy_price # Giá mua
        self.__position_active : PositionState = PositionState.KHONG_VI_THE
        self.__profit: float = 0

    def __str__(self):
        return (f"Sell at {self.__sell_time}, Price: {self.__sell_price}\n"
                f"Buy at {self.__buy_time}, Price: {self.__buy_price}")
    
    def is_buy(self) -> bool:
        return self.__buy_time is None
    
    def is_sell(self) -> bool:
        return self.__sell_time is None
    
    def buy(self, amount: float) -> None:
        self.__buy_price = amount
        self.__buy_time = datetime.now()
        self.__position_active = PositionState.CO_VI_THE
        
    def sell(self, amount: float) -> None:
        """ Cap nhat trang thai khi Ban COIN """
        self.__sell_price = amount
        self.__sell_time = datetime.now()
        self.__position_active = PositionState.KHONG_VI_THE
        self.__profit = self.__sell_price - self.__buy_price
    
    def compare_price(self) -> float:
        """ So sánh về giá khi không còn vị thế """
        return self.__profit
    
    def check_other_current_position(self, position_suggest: PositionState) -> bool:
        """ Truyền vào trạng thái tool suggest. Kiểm tra xem có khác vị the hiện tại không """
        return self.__position_active == position_suggest
    
    
    def get_position(self) -> PositionState:
        return self.__position_active

