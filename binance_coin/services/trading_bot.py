# -*- coding: utf-8 -*-
import os
import time
import schedule
from dotenv import load_dotenv
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
from ..models.manager_coin import ManagementCoin, get_item_coin_global

import binance_coin.utils.log_common as logCommon

from ..models.sell_buy import SellBuy
from ..enums.position_state import PositionState



# --- PHẦN 1: dỌC CaU HÌNH TỪ BIeN MoI TRuỜNG ---
# Tai cac bien từ file .env (neu có). Rat huu ich cho moi truờng dev.
# Trong moi truờng production, cac bien nay sẽ duợc dặt trực tiep.
load_dotenv()

# managementCoin: ManagementCoin = ManagementCoin()

# dọc cac bien, có the cung cap gia tri mặc dinh
api_key = os.getenv('API_KEY')
secret_key = os.getenv('SECRET_KEY')

coin_symbol = os.getenv('COIN_SYMBOL', 'BTCUSDT')
coin_symbol_list_str = os.getenv('LIST_COIN_SYMBOL', 'BTCUSDT')
coin_symbol_list = [symbol.strip() for symbol in coin_symbol_list_str.split('|') if symbol.strip()]

time_interval_str = os.getenv('TIME_INTERVAL', '15m')
sleep_interval = int(os.getenv('SLEEP_INTERVAL_SECONDS', 60))


logger = logCommon.getLog(__name__)

# --- PHẦN 3: KHỞI TẠO CLIENT Va LOGIC BOT (Khong thay dổi nhiều) ---
try:
    if not api_key or api_key == 'YOUR_API_KEY':
        raise ValueError("API_KEY chua duợc cau hình trong file config.ini")
    client = Client(api_key, secret_key)
    client.API_URL = 'https://testnet.binance.vision/api'
    client.get_account()
    logger.info("Ket noi den Binance API thanh cong!")
except (ValueError, BinanceAPIException) as e:
    logger.error(f"Loi ket noi hoặc cau hình: {e}")
    exit()

# Phần còn lại cua logic (get_historical_data, analyze_and_signal) giu nguyên nhu phiên ban truớc
# ... (dan code cac ham dó vao day) ...
# Luu ý: Sua ham analyze_and_signal de nó dùng bien global


def get_historical_data(symbol: str, interval: str, lookback: str = "30 hours ago UTC") -> pd.DataFrame | None:
    # ... code ham nay giu nguyên ...
    try:
        logger.debug(f"dang tai du lieu lich su cho {symbol}...")
        klines = client.get_historical_klines(symbol, interval, lookback)
        df = pd.DataFrame(klines, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                          'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df = df[['open_time', 'close']]
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close'] = pd.to_numeric(df['close'])
        logger.debug(f"Tai thanh cong {len(df)} dòng du lieu.")
        return df
    except BinanceAPIException as e:
        logger.error(f"Loi API khi tai du lieu cho {symbol}: {e}")
        return None
    except Exception as e:
        logger.error(f"Loi khong xac dinh khi tai du lieu: {e}")
        return None

# >>> HÀM analyze_and_signal ĐƯỢC NÂNG CẤP ĐỂ QUẢN LÝ TRẠNG THÁI VÀ ĐẶT LỆNH <<<
def analyze_and_signal(symbol: str, interval: str, current_position_active: PositionState) -> tuple[PositionState, float]:
    """
    Phân tích và gợi ý quyết định.
    :param current_position_active: Trạng thái hiện tại của vị thế.
    :return: Trả về State Vào hay Ra
    """
    # ... code ham nay giu nguyên ...
    df = get_historical_data(symbol, interval)
    if df is None or len(df) < 11:
        logger.warning(
            "Khong du du lieu de tinh toan cac duờng MA. Bo qua chu ky nay.")
        return False
    df['MA7'] = df['close'].rolling(window=7).mean()
    df['MA25'] = df['close'].rolling(window=25).mean()
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    if len(df) < 3:
        logger.warning("Khong du du lieu sau khi tinh MA de so sanh.")
        return PositionState.NONE, 0
    
    last_closed_candle = df.iloc[-1]
    previous_candle = df.iloc[-2]
    
    logger.info(f"Phân tích {symbol} | Trạng thái: {'ĐANG CÓ VỊ THẾ' if current_position_active else 'KHÔNG CÓ VỊ THẾ'}")
    logger.info(f"Gia: {last_closed_candle['close']:.4f} | MA7: {last_closed_candle['MA7']:.4f} | MA25: {last_closed_candle['MA25']:.4f}")
    
    # --- Logic Tín hiệu MUA (Mới được thêm) ---
    ma_crossover_condition = (previous_candle['MA7'] < previous_candle['MA25']) and (
        last_closed_candle['MA7'] > last_closed_candle['MA25'])
    MA7_rising_condition = last_closed_candle['MA7'] > previous_candle['MA7']
    price = last_closed_candle['close']

    if ma_crossover_condition and MA7_rising_condition and current_position_active != PositionState.KHONG_VI_THE:

        
        logger.warning("="*50)
        logger.warning(f"✅ TIN HIEU HOP LE cho MUA: {symbol} | Giá: {price:.4f} ")
        logger.warning(f"Ly do: MA7 da cat len MA25 Va MA7 dang di len.")
        logger.warning(f"Gia tai thoi diem tin hieu: {price:.4f}")
        logger.warning("="*50)
        
        return PositionState.CO_VI_THE, price
        
    
    # --- Logic Tín hiệu BÁN (Mới được thêm) ---
    sell_crossover = (previous_candle['MA7'] > previous_candle['MA25']) and \
                     (last_closed_candle['MA7'] < last_closed_candle['MA25'])
    MA7_is_falling = last_closed_candle['MA7'] < previous_candle['MA7']

    if sell_crossover and MA7_is_falling and  current_position_active == PositionState.CO_VI_THE:
        logger.warning("="*50)
        logger.warning(f"🔻 TIN HIEU HOP LE cho BAN: {symbol} | Giá: {price:.4f}")
        logger.warning(f"Lý do: MA7 da cat xuong MA25 và MA7 đang đi xuống.")
        logger.warning(f"Gia tai thoi diem tin hieu: {price:.4f}")
        logger.warning("="*50)
        # Tại đây bạn có thể thêm logic đặt lệnh BÁN
        return PositionState.KHONG_VI_THE, price
    
    logger.info("Khong co tin hieu mua. Tiep tuc theo doi...")
    return PositionState.NONE, 0


# Vòng lặp chinh
if __name__ == '__main__':
    logger.info("="*30)
    logger.info(
        "Bat dau chuong trinh theo doi tin hieu giao dich ")
    logger.info(f"Cap tien: {coin_symbol}")
    logger.info(f"Khung thoi gian: {time_interval_str}")
    logger.info("="*30)

    while True:
        try:
            if coin_symbol_list: # Kiểm tra xem danh sách có rỗng không
                for symbol in coin_symbol_list: # for danh sach cac coin
                    # TODO: kiểm tra không tồn tại cần khởi tạo item cho dict (chi khoi tao tren  duong MUA)

                    item: SellBuy =  get_item_coin_global(symbol)
                    position_suggest: PositionState = None
                    position_suggest, price_suggest  = analyze_and_signal(symbol, time_interval_str, item.get_position())

                    if position_suggest == PositionState.CO_VI_THE:
                        item.buy(price_suggest)
                    elif position_suggest == PositionState.KHONG_VI_THE:
                        item.buy(price_suggest)
                    
            logger.info(f"Cho {sleep_interval} giay cho chu ky phan tich tiep theo...")
            time.sleep(sleep_interval)
        
        except KeyboardInterrupt:
            logger.info(
                "da nhan tin hieu dung (Ctrl+C). Ket thuc chuơng trinh.")
            break 
        except Exception as e:
            logger.critical(
                "Vong lap chinh gap loi nghiem trong!", exc_info=True)
            time.sleep(sleep_interval)
    # while True:
    #     schedule.run_pending()  # Kiểm tra và thực thi các job đến hạn
    #     time.sleep(1)  # Chờ 1 giây để tránh tốn tài nguyên CPU
