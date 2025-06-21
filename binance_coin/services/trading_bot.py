# -*- coding: utf-8 -*-
import os
import time
import sys
from typing import Optional, Tuple
from dotenv import load_dotenv
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Fix relative imports
from binance_coin.services.manager_coin import ManagementCoin
from binance_coin.models.sell_buy import SellBuy
from binance_coin.enums.position_state import PositionState
import binance_coin.utils.log_common as logCommon

# Fix console output buffering and encoding
sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
sys.stderr.reconfigure(line_buffering=True, encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

class TradingBot:
    """
    Trading Bot class để quản lý tất cả logic trading
    """
    
    def __init__(self):
        """Khởi tạo bot với cấu hình từ environment variables"""
        load_dotenv()
        
        # Setup logger
        self.logger = logCommon.getLog(__name__)
        
        # Load configuration
        self._load_config()
        
        # Initialize Binance client
        self._init_binance_client()
        
        # Bot state
        self.is_running = True

        # Khoi tao quan li coin
        self.management_coin = ManagementCoin(self.file_state)
        
    def _load_config(self):
        """Load configuration từ environment variables"""
        self.api_key = os.getenv('API_KEY')
        self.secret_key = os.getenv('SECRET_KEY')
        
        if not self.api_key or self.api_key == 'YOUR_API_KEY':
            raise ValueError("API_KEY chưa được cấu hình trong file .env")
            
        self.coin_symbol = os.getenv('COIN_SYMBOL', 'BTCUSDT')
        coin_symbol_list_str = os.getenv('LIST_COIN_SYMBOL', 'BTCUSDT')
        self.coin_symbol_list = [symbol.strip() for symbol in coin_symbol_list_str.split('|') if symbol.strip()]
        
        self.time_interval = os.getenv('TIME_INTERVAL', '15m')
        self.sleep_interval = int(os.getenv('SLEEP_INTERVAL_SECONDS', 60))
        
        self.logger.info(f"Cấu hình loaded: {len(self.coin_symbol_list)} coins, interval: {self.time_interval}")

        self.file_state = os.getenv('STATE_FILE', 'bot_state.json')
        
    def _init_binance_client(self):
        """Khởi tạo Binance client"""
        try:
            self.client = Client(self.api_key, self.secret_key)
            # self.client.API_URL = 'https://testnet.binance.vision/api'
            
            # Test connection
            account_info = self.client.get_account()
            self.logger.info("✅ Kết nối Binance API thành công!")
            self.logger.info(f"Account status: {account_info.get('accountType', 'Unknown')}")
            
        except (ValueError, BinanceAPIException) as e:
            self.logger.error(f"❌ Lỗi kết nối Binance API: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Lỗi Khong xác định khi kết nối API: {e}")
            raise

    def get_historical_data(self, symbol: str, interval: str, lookback: str = "5 days ago UTC") -> Optional[pd.DataFrame]:
        """
        Lấy dữ liệu lịch sử với error handling tốt hơn
        """
        try:
            self.logger.debug(f"📊 Đang tải dữ liệu lịch sử cho {symbol}...")
            
            klines = self.client.get_historical_klines(symbol, interval, lookback)
            
            if not klines:
                self.logger.warning(f"⚠️ Khong có dữ liệu cho {symbol}")
                return None
                
            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume', 
                'close_time', 'quote_asset_volume', 'number_of_trades', 
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Chỉ lấy các cột cần thiết
            df = df[['open_time', 'close']].copy()
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            
            # Remove any NaN values
            df.dropna(inplace=True)
            
            self.logger.debug(f"✅ Tải thành công {len(df)} dòng dữ liệu cho {symbol}")
            return df
            
        except BinanceAPIException as e:
            self.logger.error(f"❌ Lỗi Binance API cho {symbol}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Lỗi Khong xác định khi tải dữ liệu {symbol}: {e}")
            return None

    def calculate_moving_averages(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Tính toán các đường trung bình động
        """
        try:
            if len(df) < 25:
                self.logger.warning("⚠️ Khong đủ dữ liệu để tính MA25")
                return None
                
            df = df.copy()
            df['MA7'] = df['close'].rolling(window=7).mean()
            df['MA25'] = df['close'].rolling(window=25).mean()
            df.dropna(inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi tính MA: {e}")
            return None

    def analyze_and_signal(self, symbol: str, interval: str, current_position: PositionState) -> Tuple[PositionState, float]:
        """
        Phân tích kỹ thuật và đưa ra tín hiệu giao dịch
        """
        try:
            # Lấy dữ liệu
            df = self.get_historical_data(symbol, interval)
            if df is None:
                return PositionState.NONE, 0
                
            # Tính MA
            df = self.calculate_moving_averages(df)
            if df is None or len(df) < 3:
                self.logger.warning(f"⚠️ Khong đủ dữ liệu để phân tích {symbol}")
                return PositionState.NONE, 0
            
            
            # Lấy thông tin giá mới nhất
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            
            # Lấy dữ liệu candle cuối và trước đó
            last_candle = df.iloc[-1]
            previous_candle = df.iloc[-2]
            current_price = float(ticker['price'])
            
            # Log thong tin phan tich (English only)
            position_status = "HAS_POSITION" if current_position == PositionState.CO_VI_THE else "NO_POSITION"
            self.logger.info(f"Analysis {symbol} | Status: {position_status}")
            self.logger.info(f"Price: {current_price:.4f} | MA7: {last_candle['MA7']:.4f} | MA25: {last_candle['MA25']:.4f}")
            
            # Logic tín hiệu MUA
            ma_crossover_buy = (
                previous_candle['MA7'] < previous_candle['MA25'] and 
                last_candle['MA7'] > last_candle['MA25']
            )
            ma7_rising = last_candle['MA7'] > previous_candle['MA7'] and last_candle['MA7'] < current_price # giá hiện tại phải cao hơn đường MA7
            
            
            # Chi mua khi chua co vi the
            if ma_crossover_buy and ma7_rising and current_position != PositionState.CO_VI_THE:
                self.logger.info("=" * 60)
                self.logger.info(f"BUY SIGNAL: {symbol} | Price: {current_price:.4f}")
                self.logger.info(f"Reason: MA7 crosses above MA25 and MA7 rising")
                self.logger.info(f"Signal price: {current_price:.4f}")
                self.logger.info("=" * 60)
                
                # Force flush log
                sys.stdout.flush()
                return PositionState.CO_VI_THE, current_price
            
            # Logic tín hiệu BÁN
            ma_crossover_sell = (
                previous_candle['MA7'] > previous_candle['MA25'] and 
                last_candle['MA7'] < last_candle['MA25']
            )
            ma7_falling = last_candle['MA7'] < previous_candle['MA7']
            
            # Chi ban khi dang co vi the
            if ma_crossover_sell and ma7_falling and current_position == PositionState.CO_VI_THE:
                self.logger.info("=" * 60)
                self.logger.info(f"SELL SIGNAL: {symbol} | Price: {current_price:.4f} | Hieu quả: ")
                self.logger.info(f"Reason: MA7 crosses below MA25 and MA7 falling")
                self.logger.info(f"Signal price: {current_price:.4f}")
                self.logger.info("=" * 60)
                
                # Force flush log
                sys.stdout.flush()
                return PositionState.KHONG_VI_THE, current_price
            
            self.logger.info("No signal. Continue monitoring...")
            
            # Force flush immediately after each log
            self._force_flush_logs()
            
            return PositionState.NONE, 0
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi phân tích {symbol}: {e}")
            return PositionState.NONE, 0

    def process_signal(self, symbol: str, position_suggest: PositionState, price_suggest: float, item: SellBuy):
        """
        Xử lý tín hiệu giao dịch
        """
        try:
            if position_suggest == PositionState.CO_VI_THE:
                # Lấy thông tin giá mới nhất
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                # Định dạng giá có dấu phẩy ngăn cách hàng nghìn
                current_price = float(ticker['price'])
                current_price_str = f"{current_price:,.4f}"

                self.logger.warning(f"Executing BUY order for {symbol} at price suggest {price_suggest:.4f} and market value {current_price_str} ")
                item.buy(price_suggest)
                
            elif position_suggest == PositionState.KHONG_VI_THE:
                # Lấy thông tin giá mới nhất
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                # Định dạng giá có dấu phẩy ngăn cách hàng nghìn
                current_price_str = f"{current_price:,.4f}"
                current_price = float(ticker['price'])

                self.logger.warning(f"Executing SELL order for {symbol} at price {price_suggest:.4f} and market value {current_price_str} with effective {item.get_profit_price()} ")
                item.sell(price_suggest)  # Fix: should be sell, not buy
                
        except Exception as e:
            self.logger.error(f"Error processing signal for {symbol}: {e}")

    def run_single_cycle(self):
        """
        Chạy một chu kỳ phân tích
        """
        try:
            if not self.coin_symbol_list:
                self.logger.warning("⚠️ Danh sách coin trống!")
                return
                
            for symbol in self.coin_symbol_list:
                try:
                    # Lấy thông tin vị thế hiện tại
                    item: SellBuy = self.management_coin.get_item_coin(symbol)
                    current_position = item.get_position()
                    
                    # Phân tích và lấy tín hiệu
                    position_suggest, price_suggest = self.analyze_and_signal(
                        symbol, self.time_interval, current_position
                    )
                    
                    # Xử lý tín hiệu
                    if position_suggest != PositionState.NONE:
                        self.process_signal(symbol, position_suggest, price_suggest, item)
                        
                except Exception as e:
                    self.logger.error(f"❌ Lỗi khi xử lý {symbol}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"❌ Lỗi trong chu kỳ phân tích: {e}")

    def run(self):
        """
        Chạy bot chính
        """
        self.logger.info("=" * 50)
        self.logger.info("STARTING TRADING BOT")
        self.logger.info(f"Coin list: {', '.join(self.coin_symbol_list)}")
        self.logger.info(f"Time interval: {self.time_interval}")
        self.logger.info(f"Sleep cycle: {self.sleep_interval} seconds")
        self.logger.info("=" * 50)
        
        cycle_count = 0
        
        try:
            while self.is_running:
                cycle_count += 1
                self.logger.info(f"Cycle #{cycle_count} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Chay mot chu ky phan tich
                self.run_single_cycle()
                
                # Log va sleep
                self.logger.info(f"Waiting {self.sleep_interval} seconds for next cycle...")
                
                # Force flush tat ca logs
                self._force_flush_logs()
                
                self.management_coin.save_state()

                time.sleep(self.sleep_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Received stop signal (Ctrl+C). Shutting down.")
            self.is_running = False
            
        except Exception as e:
            self.logger.critical("Critical error in main loop!", exc_info=True)
            
        finally:
            self.logger.info("Trading Bot stopped.")
    
    def _force_flush_logs(self):
        """Force flush all output buffers"""
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            
            # Flush all logging handlers
            for handler in self.logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
                    
            # Also flush root logger handlers
            for handler in logCommon.logging.getLogger().handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
        except Exception as e:
            print(f"Error flushing logs: {e}")

    def stop(self):
        """
        Dừng bot
        """
        self.is_running = False
        self.management_coin.save_state()
        self.logger.info("🛑 Bot đang được dừng...")

