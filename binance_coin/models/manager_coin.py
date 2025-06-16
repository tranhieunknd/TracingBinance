# manager_trading_coin
from binance_coin.models.sell_buy import SellBuy

manager_trading_coin = {}

class ManagementCoin(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ManagementCoin, cls).__new__(cls)
        return cls.instance
    
    # @staticmethod

    # @staticmethod
    def get_item_coin(coin_symbol) -> SellBuy:
        if not coin_symbol in manager_trading_coin:
            manager_trading_coin[coin_symbol] = SellBuy(coin_symbol=coin_symbol)
        return manager_trading_coin[coin_symbol]

def get_item_coin_global(coin_symbol) -> SellBuy:
    if not coin_symbol in manager_trading_coin:
        manager_trading_coin[coin_symbol] = SellBuy(coin_symbol=coin_symbol)
    return manager_trading_coin[coin_symbol]