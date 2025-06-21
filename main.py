
import sys
from binance_coin.services.trading_bot import TradingBot


def main():
    """
    Entry point chính
    """
    try:
        bot = TradingBot()
        bot.run()
        
    except Exception as e:
        print(f"❌ Lỗi khởi tạo bot: {e}")
        return 1
        
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)