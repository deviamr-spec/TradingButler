
"""
Enhanced MT5 Scalping Bot Controller - LIVE TRADING FIXES
Addresses all critical issues:
1. Enhanced MT5 connection with retry logic
2. Fixed auto-execution of trades
3. Robust market data analysis
4. Comprehensive error handling and logging
"""

import sys
import logging
import threading
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import csv
import traceback
import time as time_module

from PySide6.QtCore import QObject, QTimer, Signal, QThread, QMutex
from PySide6.QtWidgets import QMessageBox

# Import configuration
from config import *

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("⚠️ MetaTrader5 not available - Running in demo mode")

# Import indicators
from indicators import TechnicalIndicators

class MarketDataWorker(QThread):
    """Enhanced worker thread for market data collection with error recovery"""
    data_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = False
        self.retry_count = 0
        self.max_retries = 3
        
    def run(self):
        """Enhanced market data collection loop with error recovery"""
        self.running = True
        while self.running:
            try:
                if self.controller.is_connected:
                    data = self.controller.get_market_data()
                    if data:
                        self.data_ready.emit(data)
                        self.retry_count = 0  # Reset on success
                    else:
                        self.retry_count += 1
                        if self.retry_count >= self.max_retries:
                            self.error_occurred.emit("Market data retrieval failed after retries")
                            self.retry_count = 0
                
                self.msleep(1000)  # Update every second
                
            except Exception as e:
                self.error_occurred.emit(f"Market data worker error: {e}")
                self.msleep(5000)  # Wait longer on error
    
    def stop(self):
        self.running = False

class BotController(QObject):
    """Enhanced MT5 Scalping Bot Controller with comprehensive fixes"""
    
    # Enhanced signals
    signal_log = Signal(str, str)
    signal_status = Signal(str)
    signal_market_data = Signal(dict)
    signal_trade_signal = Signal(dict)
    signal_position_update = Signal(list)
    signal_account_update = Signal(dict)
    signal_indicators_update = Signal(dict)
    signal_analysis_update = Signal(dict)
    signal_connection_status = Signal(bool)
    signal_execution_result = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Enhanced bot state
        self.is_connected = False
        self.is_running = False
        self.shadow_mode = True
        self.mt5_available = MT5_AVAILABLE
        
        # Configuration with enhanced defaults
        self.config = {
            'symbol': 'XAUUSD',
            'risk_percent': 0.5,
            'max_daily_loss': 2.0,
            'max_trades_per_day': 15,
            'max_spread_points': 30,
            'min_sl_points': 150,
            'risk_multiple': 2.0,
            'ema_periods': {'fast': 8, 'medium': 21, 'slow': 50},
            'rsi_period': 14,
            'atr_period': 14,
            'tp_sl_mode': 'ATR',
            'tp_percent': 1.0,
            'sl_percent': 0.5,
            'tp_points': 200,
            'sl_points': 100,
            'tp_pips': 20,
            'sl_pips': 10,
            'deviation': 20,
            'magic_number': 987654321
        }
        
        # Enhanced trading state
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        self.consecutive_losses = 0
        self.last_signal_time = None
        self.signal_cooldown = 30  # seconds
        
        # Market data and analysis
        self.current_market_data = {}
        self.current_signal = {}
        self.current_indicators = {'M1': {}, 'M5': {}}
        self.account_info = None
        self.positions = []
        self.symbol_info = None
        
        # Enhanced workers and timers
        self.market_worker = None
        self.data_mutex = QMutex()
        
        # Indicators calculator
        self.indicators = TechnicalIndicators()
        
        # Account and position timers
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_info)
        
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_positions_display)
        
        # Enhanced logging setup
        self.setup_logging()
        
        self.log_message("Enhanced bot controller initialized", "INFO")
    
    def setup_logging(self):
        """Enhanced logging setup with detailed trade tracking"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Enhanced CSV logging
            self.csv_file = log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.csv"
            
            if not self.csv_file.exists():
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'timestamp', 'type', 'entry', 'sl', 'tp', 'lot', 
                        'result', 'spread', 'reason', 'profit'
                    ])
                    
        except Exception as e:
            print(f"Enhanced logging setup error: {e}")
    
    def log_message(self, message: str, level: str = "INFO"):
        """Enhanced log message emission with timestamp"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            formatted_message = f"[{timestamp}] {message}"
            self.signal_log.emit(formatted_message, level)
            
            # Also log to file
            if level == "ERROR":
                self.logger.error(message)
            elif level == "WARNING":
                self.logger.warning(message)
            else:
                self.logger.info(message)
                
        except Exception as e:
            print(f"Log emit error: {e}")
    
    def connect_mt5(self) -> bool:
        """Enhanced MT5 connection with comprehensive error handling"""
        try:
            self.log_message("🔌 Attempting MT5 connection...", "INFO")
            
            if not MT5_AVAILABLE:
                self.log_message("❌ MetaTrader5 module not available", "ERROR")
                return False
            
            # Enhanced initialization with retry logic
            init_success = False
            attempts = 0
            max_attempts = 3
            
            while not init_success and attempts < max_attempts:
                attempts += 1
                self.log_message(f"Connection attempt {attempts}/{max_attempts}", "INFO")
                
                try:
                    # Try simple initialization first
                    if mt5.initialize():
                        init_success = True
                        break
                    else:
                        error_code, error_desc = mt5.last_error()
                        self.log_message(f"Init failed: {error_code} - {error_desc}", "WARNING")
                        
                except Exception as e:
                    self.log_message(f"Init exception: {e}", "WARNING")
                
                if not init_success and attempts < max_attempts:
                    time_module.sleep(2)  # Wait before retry
            
            if not init_success:
                self.log_message("❌ MT5 initialization failed after all attempts", "ERROR")
                return False
            
            # Verify terminal connection
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                self.log_message("❌ Cannot get terminal info - Check MT5 login", "ERROR")
                mt5.shutdown()
                return False
            
            # Verify account connection
            account_info = mt5.account_info()
            if account_info is None:
                self.log_message("❌ Cannot get account info - Check MT5 login", "ERROR")
                mt5.shutdown()
                return False
            
            # Check trading permissions
            if not terminal_info.trade_allowed:
                self.log_message("❌ Trading not allowed in MT5 settings", "ERROR")
                mt5.shutdown()
                return False
            
            # Enhanced symbol validation
            symbol = self.config['symbol']
            if not self.validate_symbol(symbol):
                mt5.shutdown()
                return False
            
            # Store connection data
            self.account_info = account_info
            self.symbol_info = mt5.symbol_info(symbol)
            self.is_connected = True
            
            # Start enhanced data collection
            self.start_market_worker()
            self.account_timer.start(5000)
            self.position_timer.start(3000)
            
            self.log_message(f"✅ Connected to MT5 - Account: {account_info.login}", "INFO")
            self.log_message(f"✅ Balance: ${account_info.balance:.2f}", "INFO")
            self.signal_connection_status.emit(True)
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ MT5 connection error: {e}", "ERROR")
            self.log_message(f"Traceback: {traceback.format_exc()}", "ERROR")
            return False
    
    def validate_symbol(self, symbol: str) -> bool:
        """Enhanced symbol validation with detailed checks"""
        try:
            # Select symbol in Market Watch
            if not mt5.symbol_select(symbol, True):
                self.log_message(f"❌ Cannot select symbol {symbol} - Add to Market Watch", "ERROR")
                return False
            
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.log_message(f"❌ Cannot get symbol info for {symbol}", "ERROR")
                return False
            
            # Check if symbol is tradeable
            if symbol_info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL:
                self.log_message(f"❌ Symbol {symbol} not available for trading", "ERROR")
                return False
            
            # Check minimum volume
            if symbol_info.volume_min <= 0:
                self.log_message(f"❌ Invalid minimum volume for {symbol}", "ERROR")
                return False
            
            self.log_message(f"✅ Symbol {symbol} validated successfully", "INFO")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Symbol validation error: {e}", "ERROR")
            return False
    
    def start_market_worker(self):
        """Enhanced market data worker with error handling"""
        try:
            if self.market_worker is not None:
                self.market_worker.stop()
                self.market_worker.wait()
            
            self.market_worker = MarketDataWorker(self)
            self.market_worker.data_ready.connect(self.process_market_data)
            self.market_worker.error_occurred.connect(self.handle_market_error)
            self.market_worker.start()
            
            self.log_message("✅ Market data worker started", "INFO")
            
        except Exception as e:
            self.log_message(f"❌ Market worker start error: {e}", "ERROR")
    
    def handle_market_error(self, error_message: str):
        """Handle market data errors"""
        self.log_message(f"📊 Market data error: {error_message}", "WARNING")
    
    def get_market_data(self) -> Optional[Dict]:
        """Enhanced market data retrieval with comprehensive checks"""
        try:
            if not self.is_connected or not MT5_AVAILABLE:
                return None
            
            symbol = self.config['symbol']
            
            # Get current tick with retry logic
            tick = None
            for attempt in range(3):
                tick = mt5.symbol_info_tick(symbol)
                if tick is not None:
                    break
                time_module.sleep(0.1)
            
            if tick is None:
                self.log_message(f"⚠️ Cannot get tick data for {symbol}", "WARNING")
                return None
            
            # Calculate spread
            spread_points = int((tick.ask - tick.bid) / self.symbol_info.point) if self.symbol_info else 0
            
            # Get enhanced indicator data
            indicators_m1 = self.calculate_indicators(symbol, mt5.TIMEFRAME_M1)
            indicators_m5 = self.calculate_indicators(symbol, mt5.TIMEFRAME_M5)
            
            return {
                'symbol': symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': spread_points,
                'time': datetime.fromtimestamp(tick.time),
                'indicators_m1': indicators_m1,
                'indicators_m5': indicators_m5,
                'tick_volume': tick.volume
            }
            
        except Exception as e:
            self.log_message(f"Market data error: {e}", "ERROR")
            return None
    
    def calculate_indicators(self, symbol: str, timeframe) -> Optional[Dict]:
        """Enhanced indicator calculation with error handling"""
        try:
            # Get sufficient price data
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 200)
            if rates is None or len(rates) < 100:
                return None
            
            closes = [r['close'] for r in rates]
            highs = [r['high'] for r in rates]
            lows = [r['low'] for r in rates]
            
            # Calculate enhanced indicators
            ema_fast = self.indicators.calculate_ema(closes, self.config['ema_periods']['fast'])
            ema_medium = self.indicators.calculate_ema(closes, self.config['ema_periods']['medium'])
            ema_slow = self.indicators.calculate_ema(closes, self.config['ema_periods']['slow'])
            rsi = self.indicators.calculate_rsi(closes, self.config['rsi_period'])
            atr = self.indicators.calculate_atr(highs, lows, closes, self.config['atr_period'])
            
            return {
                'ema_fast': ema_fast,
                'ema_medium': ema_medium,
                'ema_slow': ema_slow,
                'rsi': rsi,
                'atr': atr,
                'bars_count': len(rates)
            }
            
        except Exception as e:
            self.log_message(f"Indicator calculation error: {e}", "ERROR")
            return None
    
    def process_market_data(self, data: Dict):
        """Enhanced market data processing with signal generation"""
        try:
            self.data_mutex.lock()
            self.current_market_data = data
            
            # Update indicators for GUI
            if 'indicators_m1' in data and 'indicators_m5' in data:
                self.current_indicators = {
                    'M1': data['indicators_m1'] or {},
                    'M5': data['indicators_m5'] or {}
                }
                self.signal_indicators_update.emit(self.current_indicators)
            
            self.data_mutex.unlock()
            
            # Emit to GUI
            self.signal_market_data.emit(data)
            
            # Enhanced signal generation with cooldown
            if self.is_running and self.should_analyze_signal():
                signal = self.generate_signal(data)
                if signal and signal.get('type') != 'None':
                    self.current_signal = signal
                    self.last_signal_time = datetime.now()
                    self.signal_trade_signal.emit(signal)
                    
                    self.log_message(f"🎯 SIGNAL: {signal['type']} at {signal['entry_price']:.5f}", "INFO")
                    
                    # Enhanced auto-execution with validation
                    if not self.shadow_mode and self.validate_execution_conditions(signal):
                        self.log_message("🚀 AUTO EXECUTION STARTING", "INFO")
                        QTimer.singleShot(500, lambda: self.execute_signal(signal))
                    else:
                        mode = "Shadow mode" if self.shadow_mode else "Validation failed"
                        self.log_message(f"🛡️ {mode} - Signal logged only", "INFO")
            
        except Exception as e:
            self.log_message(f"Market data processing error: {e}", "ERROR")
        finally:
            if self.data_mutex.tryLock():
                self.data_mutex.unlock()
    
    def should_analyze_signal(self) -> bool:
        """Check if enough time has passed since last signal"""
        if self.last_signal_time is None:
            return True
        
        time_since_last = (datetime.now() - self.last_signal_time).total_seconds()
        return time_since_last >= self.signal_cooldown
    
    def validate_execution_conditions(self, signal: Dict) -> bool:
        """Enhanced validation before trade execution"""
        try:
            # Check daily limits
            if self.daily_trades >= self.config['max_trades_per_day']:
                self.log_message("❌ Daily trade limit reached", "WARNING")
                return False
            
            # Check spread
            if signal.get('spread', 0) > self.config['max_spread_points']:
                self.log_message("❌ Spread too wide for execution", "WARNING")
                return False
            
            # Check account balance
            if not self.account_info or self.account_info.balance <= 0:
                self.log_message("❌ Invalid account balance", "ERROR")
                return False
            
            # Check consecutive losses
            if self.consecutive_losses >= 3:
                self.log_message("❌ Too many consecutive losses", "WARNING")
                return False
            
            # Check trading session
            if not self.is_trading_session():
                self.log_message("❌ Outside trading session", "WARNING")
                return False
            
            return True
            
        except Exception as e:
            self.log_message(f"Execution validation error: {e}", "ERROR")
            return False
    
    def is_trading_session(self) -> bool:
        """Check if current time is within trading session"""
        try:
            # Simple session check - can be enhanced
            current_hour = datetime.now().hour
            return 8 <= current_hour <= 22  # 8 AM to 10 PM
            
        except Exception:
            return True  # Default to allow trading
    
    def generate_signal(self, data: Dict) -> Optional[Dict]:
        """Enhanced signal generation with comprehensive analysis"""
        try:
            self.signal_analysis_update.emit({
                'status': 'analyzing',
                'next_analysis': datetime.now().strftime("%H:%M:%S")
            })
            
            m1_indicators = data.get('indicators_m1', {})
            m5_indicators = data.get('indicators_m5', {})
            
            if not m1_indicators or not m5_indicators:
                return None
            
            # Enhanced signal logic
            current_price = data['ask']
            spread = data.get('spread', 0)
            
            # Get indicator values safely
            m1_ema_fast = m1_indicators.get('ema_fast')
            m1_ema_medium = m1_indicators.get('ema_medium')
            m5_ema_fast = m5_indicators.get('ema_fast')
            m5_ema_medium = m5_indicators.get('ema_medium')
            m1_rsi = m1_indicators.get('rsi', 50)
            m1_atr = m1_indicators.get('atr', 0.001)
            
            if any(x is None for x in [m1_ema_fast, m1_ema_medium, m5_ema_fast, m5_ema_medium]):
                return None
            
            # Enhanced signal logic
            signal_type = None
            confidence = 0
            
            # M5 trend filter + M1 entry
            m5_bullish = m5_ema_fast > m5_ema_medium
            m5_bearish = m5_ema_fast < m5_ema_medium
            m1_bullish = m1_ema_fast > m1_ema_medium
            m1_bearish = m1_ema_fast < m1_ema_medium
            
            # BUY signal
            if m5_bullish and m1_bullish and m1_rsi > 40 and m1_rsi < 70:
                signal_type = "BUY"
                confidence = 75
                if current_price > m1_ema_fast:
                    confidence += 10
            
            # SELL signal
            elif m5_bearish and m1_bearish and m1_rsi < 60 and m1_rsi > 30:
                signal_type = "SELL"
                confidence = 75
                if current_price < m1_ema_fast:
                    confidence += 10
            
            if signal_type and confidence >= 70:
                # Calculate TP/SL
                sl_price, tp_price = self.calculate_sl_tp(signal_type, current_price, m1_atr)
                lot_size = self.calculate_lot_size(abs(current_price - sl_price))
                
                return {
                    'type': signal_type,
                    'entry_price': current_price,
                    'sl_price': sl_price,
                    'tp_price': tp_price,
                    'lot_size': lot_size,
                    'confidence': confidence,
                    'timestamp': datetime.now(),
                    'spread': spread,
                    'atr': m1_atr
                }
            
            return None
            
        except Exception as e:
            self.log_message(f"Signal generation error: {e}", "ERROR")
            return None
    
    def calculate_sl_tp(self, signal_type: str, entry_price: float, atr_value: float) -> Tuple[Optional[float], Optional[float]]:
        """Enhanced TP/SL calculation based on mode"""
        try:
            mode = self.config['tp_sl_mode']
            
            if mode == 'ATR':
                atr_points = max(self.config['min_sl_points'], int(atr_value * 100000 * 1.5))
                sl_distance = atr_points / 100000
                tp_distance = sl_distance * self.config['risk_multiple']
                
            elif mode == 'Points':
                sl_distance = self.config['sl_points'] / 100000
                tp_distance = self.config['tp_points'] / 100000
                
            elif mode == 'Pips':
                pip_multiplier = 10 if self.symbol_info and self.symbol_info.digits == 5 else 1
                sl_distance = (self.config['sl_pips'] * pip_multiplier) / 100000
                tp_distance = (self.config['tp_pips'] * pip_multiplier) / 100000
                
            else:  # Percent mode
                if not self.account_info:
                    return None, None
                balance = self.account_info.balance
                sl_usd = balance * (self.config['sl_percent'] / 100)
                tp_usd = balance * (self.config['tp_percent'] / 100)
                
                # Simplified conversion
                sl_distance = sl_usd / 10000  # Rough conversion
                tp_distance = tp_usd / 10000
            
            # Apply direction
            if signal_type == "BUY":
                sl_price = entry_price - sl_distance
                tp_price = entry_price + tp_distance
            else:  # SELL
                sl_price = entry_price + sl_distance
                tp_price = entry_price - tp_distance
            
            return sl_price, tp_price
            
        except Exception as e:
            self.log_message(f"TP/SL calculation error: {e}", "ERROR")
            return None, None
    
    def calculate_lot_size(self, sl_distance: float) -> float:
        """Enhanced lot size calculation"""
        try:
            if not self.account_info or not self.symbol_info:
                return 0.01
            
            risk_amount = self.account_info.balance * (self.config['risk_percent'] / 100)
            pip_value = 10  # For XAUUSD
            risk_pips = sl_distance * 100000
            
            if risk_pips > 0:
                lot_size = risk_amount / (risk_pips * pip_value)
                # Normalize to symbol requirements
                min_lot = getattr(self.symbol_info, 'volume_min', 0.01)
                max_lot = getattr(self.symbol_info, 'volume_max', 1.0)
                step = getattr(self.symbol_info, 'volume_step', 0.01)
                
                lot_size = max(min_lot, min(max_lot, round(lot_size / step) * step))
                return lot_size
            
            return 0.01
            
        except Exception as e:
            self.log_message(f"Lot calculation error: {e}", "ERROR")
            return 0.01
    
    def execute_signal(self, signal: Dict):
        """Enhanced signal execution with comprehensive error handling"""
        try:
            if not MT5_AVAILABLE or not self.is_connected:
                self.log_message("❌ Cannot execute - MT5 not available", "ERROR")
                return
            
            signal_type = signal['type']
            lot_size = signal['lot_size']
            entry_price = signal['entry_price']
            sl_price = signal['sl_price']
            tp_price = signal['tp_price']
            
            self.log_message(f"🚀 EXECUTING {signal_type} ORDER", "INFO")
            self.log_message(f"📊 Entry: {entry_price:.5f}, SL: {sl_price:.5f}, TP: {tp_price:.5f}", "INFO")
            self.log_message(f"📦 Lot Size: {lot_size}", "INFO")
            
            # Prepare enhanced order request
            symbol = self.config['symbol']
            order_type = mt5.ORDER_TYPE_BUY if signal_type == 'BUY' else mt5.ORDER_TYPE_SELL
            
            # Get current price for execution
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                self.log_message("❌ Cannot get current price", "ERROR")
                return
            
            price = tick.ask if signal_type == 'BUY' else tick.bid
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": self.config['deviation'],
                "magic": self.config['magic_number'],
                "comment": f"AutoBot_{signal_type}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Enhanced order execution with retry
            result = None
            for attempt in range(3):
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    break
                elif result:
                    self.log_message(f"Order attempt {attempt + 1} failed: {result.comment}", "WARNING")
                    if attempt < 2:
                        time_module.sleep(0.5)
            
            # Process result
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.daily_trades += 1
                self.consecutive_losses = 0  # Reset on successful execution
                
                self.log_message(f"✅ ORDER EXECUTED: Ticket {result.order}", "INFO")
                self.log_message(f"✅ {signal_type} {lot_size} lots at {price:.5f}", "INFO")
                
                # Log to CSV
                self.log_trade_to_csv(signal_type, price, sl_price, tp_price, lot_size, "EXECUTED", signal.get('spread', 0))
                
                # Emit execution result
                self.signal_execution_result.emit({
                    'success': True,
                    'ticket': result.order,
                    'type': signal_type,
                    'price': price,
                    'message': 'Order executed successfully'
                })
                
            else:
                error_msg = result.comment if result else "Unknown error"
                self.log_message(f"❌ ORDER FAILED: {error_msg}", "ERROR")
                
                self.signal_execution_result.emit({
                    'success': False,
                    'type': signal_type,
                    'price': price,
                    'message': error_msg
                })
            
        except Exception as e:
            self.log_message(f"Signal execution error: {e}", "ERROR")
            self.log_message(f"Traceback: {traceback.format_exc()}", "ERROR")
    
    def log_trade_to_csv(self, trade_type: str, entry: float, sl: float, tp: float, lot: float, result: str, spread: int):
        """Enhanced CSV trade logging"""
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    trade_type, entry, sl, tp, lot, result, spread,
                    "auto_signal", 0.0  # profit will be updated on close
                ])
        except Exception as e:
            self.log_message(f"CSV logging error: {e}", "ERROR")
    
    def start_bot(self) -> bool:
        """Enhanced bot start with comprehensive validation"""
        try:
            if not self.is_connected:
                self.log_message("❌ Cannot start bot - Not connected to MT5", "ERROR")
                return False
            
            # Reset daily counters if needed
            current_date = datetime.now().date()
            if current_date != self.last_reset_date:
                self.daily_trades = 0
                self.daily_pnl = 0.0
                self.consecutive_losses = 0
                self.last_reset_date = current_date
                self.log_message("📅 Daily counters reset", "INFO")
            
            self.is_running = True
            mode = "SHADOW MODE" if self.shadow_mode else "🚨 LIVE TRADING"
            self.log_message(f"🚀 Trading bot started in {mode}", "INFO")
            
            self.signal_status.emit("Running")
            return True
            
        except Exception as e:
            self.log_message(f"Bot start error: {e}", "ERROR")
            return False
    
    def stop_bot(self):
        """Enhanced bot stop"""
        try:
            self.is_running = False
            self.signal_status.emit("Stopped")
            self.log_message("🛑 Trading bot stopped", "INFO")
            
        except Exception as e:
            self.log_message(f"Bot stop error: {e}", "ERROR")
    
    def disconnect_mt5(self):
        """Enhanced MT5 disconnection"""
        try:
            self.stop_bot()
            
            # Stop workers
            if self.market_worker:
                self.market_worker.stop()
                self.market_worker.wait()
            
            # Stop timers
            self.account_timer.stop()
            self.position_timer.stop()
            
            # Shutdown MT5
            if MT5_AVAILABLE and self.is_connected:
                mt5.shutdown()
            
            self.is_connected = False
            self.signal_connection_status.emit(False)
            self.signal_status.emit("Disconnected")
            self.log_message("🔌 Disconnected from MT5", "INFO")
            
        except Exception as e:
            self.log_message(f"Disconnect error: {e}", "ERROR")
    
    def get_positions(self) -> List[Dict]:
        """Enhanced position retrieval"""
        try:
            if not self.is_connected or not MT5_AVAILABLE:
                return []
            
            positions = mt5.positions_get(symbol=self.config['symbol'])
            if positions is None:
                return []
            
            position_list = []
            for pos in positions:
                position_list.append({
                    'ticket': pos.ticket,
                    'type': 'BUY' if pos.type == 0 else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'comment': pos.comment
                })
            
            return position_list
            
        except Exception as e:
            self.log_message(f"Get positions error: {e}", "ERROR")
            return []
    
    def update_positions_display(self):
        """Enhanced position display update"""
        try:
            positions = self.get_positions()
            self.signal_position_update.emit(positions)
            
            # Update daily P&L
            total_profit = sum(pos.get('profit', 0) for pos in positions)
            self.daily_pnl = total_profit
            
        except Exception as e:
            self.log_message(f"Position update error: {e}", "ERROR")
    
    def update_account_info(self):
        """Enhanced account info update"""
        try:
            if not self.is_connected or not MT5_AVAILABLE:
                return
            
            account_info = mt5.account_info()
            if account_info:
                self.account_info = account_info
                
                account_data = {
                    'balance': account_info.balance,
                    'equity': account_info.equity,
                    'margin': getattr(account_info, 'margin', 0),
                    'profit': getattr(account_info, 'profit', 0),
                    'margin_free': getattr(account_info, 'margin_free', 0)
                }
                self.signal_account_update.emit(account_data)
            
        except Exception as e:
            self.log_message(f"Account update error: {e}", "ERROR")
    
    def close_all_positions(self):
        """Enhanced close all positions with error handling"""
        try:
            positions = self.get_positions()
            if not positions:
                self.log_message("No positions to close", "INFO")
                return
            
            self.log_message(f"🚨 Closing {len(positions)} positions...", "INFO")
            
            for position in positions:
                try:
                    ticket = position['ticket']
                    volume = position['volume']
                    pos_type = position['type']
                    
                    # Prepare close request
                    close_type = mt5.ORDER_TYPE_SELL if pos_type == 'BUY' else mt5.ORDER_TYPE_BUY
                    
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": self.config['symbol'],
                        "volume": volume,
                        "type": close_type,
                        "position": ticket,
                        "deviation": 20,
                        "magic": self.config['magic_number'],
                        "comment": "Emergency_Close",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    
                    result = mt5.order_send(request)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        self.log_message(f"✅ Position {ticket} closed", "INFO")
                    else:
                        error_msg = result.comment if result else "Unknown error"
                        self.log_message(f"❌ Failed to close {ticket}: {error_msg}", "ERROR")
                        
                except Exception as e:
                    self.log_message(f"Error closing position: {e}", "ERROR")
            
            # Stop bot after closing all positions
            self.stop_bot()
            
        except Exception as e:
            self.log_message(f"Close all positions error: {e}", "ERROR")
    
    def toggle_shadow_mode(self, enabled: bool):
        """Enhanced shadow mode toggle"""
        try:
            self.shadow_mode = enabled
            mode = "Shadow Mode (Safe)" if enabled else "🚨 LIVE TRADING MODE"
            self.log_message(f"⚙️ Switched to {mode}", "INFO")
            
            if not enabled:
                self.log_message("⚠️ WARNING: Live trading enabled - Real money at risk!", "WARNING")
            
        except Exception as e:
            self.log_message(f"Shadow mode toggle error: {e}", "ERROR")
    
    def update_config(self, config: Dict):
        """Enhanced configuration update with validation"""
        try:
            # Validate critical parameters
            if 'risk_percent' in config:
                if config['risk_percent'] <= 0 or config['risk_percent'] > 10:
                    self.log_message("❌ Invalid risk percent - must be 0.1-10%", "ERROR")
                    return
            
            if 'max_spread_points' in config:
                if config['max_spread_points'] <= 0:
                    self.log_message("❌ Invalid max spread - must be positive", "ERROR")
                    return
            
            # Update configuration
            self.config.update(config)
            self.log_message("✅ Configuration updated successfully", "INFO")
            
            # Log important changes
            if 'tp_sl_mode' in config:
                self.log_message(f"📊 TP/SL Mode: {config['tp_sl_mode']}", "INFO")
            
            if 'risk_percent' in config:
                self.log_message(f"💰 Risk per trade: {config['risk_percent']}%", "INFO")
            
        except Exception as e:
            self.log_message(f"Config update error: {e}", "ERROR")
