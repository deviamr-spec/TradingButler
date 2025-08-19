
"""
FIXED MT5 Scalping Bot Controller - PRODUCTION READY
Complete fixes for MT5 connection and auto-trading
"""

import sys
import logging
import threading
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import csv
import traceback
import pytz
import numpy as np

from PySide6.QtCore import QObject, QTimer, Signal, QThread, QMutex
from PySide6.QtWidgets import QMessageBox

# Import configuration
from config import *

# MANDATORY MT5 CONNECTION - NO MOCK FALLBACK
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    print("✅ MetaTrader5 module loaded successfully")
except ImportError:
    MT5_AVAILABLE = False
    print("❌ CRITICAL: MetaTrader5 module not installed!")
    print("❌ Install command: pip install MetaTrader5")
    print("❌ Real trading REQUIRES MetaTrader5 Python API")
    # NO MOCK IMPORT - Force real MT5 only

# Import indicators
from indicators import TechnicalIndicators

class AnalysisWorker(QThread):
    """Enhanced Analysis Worker for real-time trading signals"""

    # Signals
    heartbeat_signal = Signal(str)
    signal_ready = Signal(dict)
    indicators_ready = Signal(dict)
    tick_data_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = False
        self.indicators = TechnicalIndicators()
        self.last_m1_time = None
        self.logger = logging.getLogger(__name__)
        
        # Remove demo mode completely
        self.last_signal_time = 0
        self.signal_cooldown = 5  # 5 seconds between signals

    def run(self):
        """Main analysis loop dengan enhanced strategy"""
        self.running = True
        self.logger.info("[WORKER] Analysis thread starting for REAL trading...")

        try:
            while self.running:
                current_time = datetime.now(pytz.timezone('Asia/Jakarta'))

                # MANDATORY: Check MT5 connection first
                if not self.controller.is_connected or not MT5_AVAILABLE:
                    self.heartbeat_signal.emit(f"[HB] WAITING MT5 CONNECTION t={current_time.strftime('%H:%M:%S')}")
                    self.msleep(1000)
                    continue

                try:
                    # 1. Heartbeat with connection verification
                    if not self.verify_mt5_connection():
                        self.error_signal.emit("MT5 connection lost - attempting reconnect")
                        self.msleep(2000)
                        continue

                    # 2. Market data analysis
                    market_data = self.get_market_data()
                    if market_data:
                        self.tick_data_signal.emit(market_data)

                    # 3. Technical analysis
                    analysis_result = self.perform_technical_analysis()
                    if analysis_result:
                        self.indicators_ready.emit(analysis_result)

                    # 4. Signal generation
                    signal = self.generate_trading_signal(analysis_result)
                    if signal and signal.get('side'):
                        # Cooldown check
                        if (time.time() - self.last_signal_time) > self.signal_cooldown:
                            self.signal_ready.emit(signal)
                            self.last_signal_time = time.time()

                    # 5. Heartbeat log
                    spread = market_data.get('spread_points', 0) if market_data else 0
                    signal_status = signal.get('side', 'NONE') if signal else 'NONE'
                    self.heartbeat_signal.emit(
                        f"[HB] LIVE t={current_time.strftime('%H:%M:%S')} spread={spread}pts signal={signal_status}"
                    )

                except Exception as e:
                    error_msg = f"Analysis error: {e}"
                    self.error_signal.emit(error_msg)
                    self.logger.error(error_msg)

                self.msleep(1000)  # 1 second cycle

        except Exception as e:
            error_msg = f"Analysis worker fatal error: {e}\n{traceback.format_exc()}"
            self.error_signal.emit(error_msg)
            self.logger.error(error_msg)

    def verify_mt5_connection(self):
        """Verify MT5 connection is still active"""
        try:
            # Test connection with account info
            account_info = mt5.account_info()
            return account_info is not None
        except:
            return False

    def get_market_data(self):
        """Get current market data from MT5"""
        try:
            symbol = self.controller.config['symbol']
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None

            # Calculate spread
            point = getattr(self.controller.symbol_info, 'point', 0.01)
            spread_points = round((tick.ask - tick.bid) / point)

            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'spread_points': spread_points,
                'time': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Market data error: {e}")
            return None

    def perform_technical_analysis(self):
        """Perform comprehensive technical analysis"""
        try:
            symbol = self.controller.config['symbol']

            # Get M1 and M5 bars
            rates_m1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 200)
            rates_m5 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 200)

            if rates_m1 is None or rates_m5 is None or len(rates_m1) < 50:
                return None

            # M1 Analysis
            m1_analysis = self.analyze_timeframe(rates_m1, 'M1')
            
            # M5 Analysis  
            m5_analysis = self.analyze_timeframe(rates_m5, 'M5')

            # Update controller indicators
            self.controller.current_indicators = {
                'M1': m1_analysis,
                'M5': m5_analysis
            }

            return self.controller.current_indicators

        except Exception as e:
            self.logger.error(f"Technical analysis error: {e}")
            return None

    def analyze_timeframe(self, rates, timeframe):
        """Analyze single timeframe with all indicators"""
        try:
            close = rates['close']
            high = rates['high']
            low = rates['low']
            volume = rates['tick_volume']

            # Calculate indicators
            ema_fast = self.indicators.ema(close, self.controller.config['ema_periods']['fast'])
            ema_medium = self.indicators.ema(close, self.controller.config['ema_periods']['medium'])
            ema_slow = self.indicators.ema(close, self.controller.config['ema_periods']['slow'])
            rsi = self.indicators.rsi(close, self.controller.config['rsi_period'])
            atr = self.indicators.atr(high, low, close, self.controller.config['atr_period'])

            # Get latest values safely
            return {
                'ema_fast': ema_fast[-1] if len(ema_fast) > 0 and not np.isnan(ema_fast[-1]) else close[-1],
                'ema_medium': ema_medium[-1] if len(ema_medium) > 0 and not np.isnan(ema_medium[-1]) else close[-1],
                'ema_slow': ema_slow[-1] if len(ema_slow) > 0 and not np.isnan(ema_slow[-1]) else close[-1],
                'rsi': rsi[-1] if len(rsi) > 0 and not np.isnan(rsi[-1]) else 50,
                'atr': atr[-1] if len(atr) > 0 and not np.isnan(atr[-1]) else 0.01,
                'close': close[-1],
                'high': high[-1],
                'low': low[-1],
                'volume': volume[-1],
                'rates': rates,
                'timeframe': timeframe
            }

        except Exception as e:
            self.logger.error(f"Timeframe analysis error: {e}")
            return {}

    def generate_trading_signal(self, analysis):
        """Enhanced signal generation with professional scalping strategy"""
        try:
            if not analysis or 'M1' not in analysis or 'M5' not in analysis:
                return {'side': None, 'reason': 'insufficient_data'}

            m1 = analysis['M1']
            m5 = analysis['M5']

            # Get current market data
            symbol = self.controller.config['symbol']
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return {'side': None, 'reason': 'no_tick_data'}

            point = getattr(self.controller.symbol_info, 'point', 0.01)
            spread_points = round((tick.ask - tick.bid) / point)

            # ENHANCED SCALPING STRATEGY
            signal = self.evaluate_scalping_strategy(m1, m5, tick, spread_points, point)
            
            return signal

        except Exception as e:
            self.logger.error(f"Signal generation error: {e}")
            return {'side': None, 'reason': f'error: {e}'}

    def evaluate_scalping_strategy(self, m1, m5, tick, spread_points, point):
        """Professional scalping strategy implementation"""
        try:
            # 1. Spread filter (critical for scalping)
            max_spread = self.controller.config.get('max_spread_points', 30)
            if spread_points > max_spread:
                return {'side': None, 'reason': 'spread_too_wide', 'spread_points': spread_points}

            # 2. Session filter
            if not self.is_trading_session():
                return {'side': None, 'reason': 'outside_session'}

            # 3. Trend analysis (M5 timeframe)
            m5_trend = self.determine_trend(m5)
            if m5_trend == 'SIDEWAYS':
                return {'side': None, 'reason': 'sideways_market'}

            # 4. Entry conditions (M1 timeframe)
            entry_signal = self.check_entry_conditions(m1, m5_trend, tick)
            if not entry_signal:
                return {'side': None, 'reason': 'no_entry_signal'}

            # 5. Risk assessment
            atr_points = m1.get('atr', 0) / point
            if atr_points < 50:  # Minimum volatility for scalping
                return {'side': None, 'reason': 'low_volatility'}

            # 6. Final signal confirmation
            side = entry_signal['side']
            confidence = entry_signal['confidence']

            # Only high confidence signals
            if confidence < 0.75:
                return {'side': None, 'reason': 'low_confidence'}

            return {
                'side': side,
                'entry_price': tick.ask if side == 'BUY' else tick.bid,
                'confidence': confidence,
                'trend': m5_trend,
                'atr_points': atr_points,
                'spread_points': spread_points,
                'reason': 'scalping_signal_confirmed',
                'timestamp': datetime.now(),
                'm1_data': m1,
                'm5_data': m5
            }

        except Exception as e:
            return {'side': None, 'reason': f'strategy_error: {e}'}

    def determine_trend(self, data):
        """Determine market trend from M5 data"""
        try:
            ema_fast = data.get('ema_fast', 0)
            ema_medium = data.get('ema_medium', 0)
            ema_slow = data.get('ema_slow', 0)
            close = data.get('close', 0)

            # Strong uptrend
            if (ema_fast > ema_medium > ema_slow and 
                close > ema_fast and 
                (ema_fast - ema_slow) / ema_slow > 0.001):
                return 'BULLISH'

            # Strong downtrend
            if (ema_fast < ema_medium < ema_slow and 
                close < ema_fast and 
                (ema_slow - ema_fast) / ema_slow > 0.001):
                return 'BEARISH'

            return 'SIDEWAYS'

        except Exception as e:
            return 'SIDEWAYS'

    def check_entry_conditions(self, m1, trend, tick):
        """Check M1 entry conditions based on M5 trend"""
        try:
            ema_fast = m1.get('ema_fast', 0)
            ema_medium = m1.get('ema_medium', 0)
            close = m1.get('close', 0)
            rsi = m1.get('rsi', 50)

            if trend == 'BULLISH':
                # BUY conditions: Pullback to EMA and bounce
                if (close <= ema_medium and close > ema_fast and 
                    rsi > 30 and rsi < 70 and
                    tick.ask > ema_fast):
                    return {'side': 'BUY', 'confidence': 0.8}

            elif trend == 'BEARISH':
                # SELL conditions: Pullback to EMA and rejection
                if (close >= ema_medium and close < ema_fast and 
                    rsi < 70 and rsi > 30 and
                    tick.bid < ema_fast):
                    return {'side': 'SELL', 'confidence': 0.8}

            return None

        except Exception as e:
            return None

    def is_trading_session(self):
        """Check if current time is within trading session"""
        try:
            now = datetime.now(pytz.timezone('Asia/Jakarta'))
            current_hour = now.hour

            # London session: 15:00 - 18:00 Jakarta time
            # New York session: 20:00 - 00:00 Jakarta time
            return (15 <= current_hour <= 18) or (20 <= current_hour <= 23)

        except Exception as e:
            return True  # Default to allow trading

    def stop(self):
        """Stop the analysis worker"""
        self.running = False
        self.quit()
        self.wait(5000)

class BotController(QObject):
    """Enhanced MT5 Scalping Bot Controller - REAL TRADING ONLY"""

    # Signals for GUI updates
    signal_log = Signal(str, str)
    signal_status = Signal(str)
    signal_market_data = Signal(dict)
    signal_trade_signal = Signal(dict)
    signal_position_update = Signal(list)
    signal_account_update = Signal(dict)
    signal_indicators_update = Signal(dict)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Bot state
        self.is_connected = False
        self.is_running = False
        self.shadow_mode = True  # Start in shadow mode for safety
        self.mt5_available = MT5_AVAILABLE

        # MANDATORY: Verify MT5 module
        if not MT5_AVAILABLE:
            self.log_message("❌ CRITICAL: MetaTrader5 module not installed!", "ERROR")
            self.log_message("❌ Real trading REQUIRES MT5 Python API", "ERROR")
            self.log_message("❌ Install command: pip install MetaTrader5", "ERROR")

        # Trading statistics
        self.execution_stats = {
            'signals_generated': 0,
            'signals_executed': 0,
            'execution_rate': 0.0,
            'last_execution': 'Never'
        }

        # Enhanced configuration
        self.config = {
            'symbol': 'XAUUSD',
            'risk_percent': 0.5,
            'max_daily_loss': 2.0,
            'max_trades_per_day': 10,
            'max_spread_points': 30,  # Tighter spread for scalping
            'min_sl_points': 100,
            'risk_multiple': 1.5,     # Conservative R:R for scalping
            'ema_periods': {'fast': 9, 'medium': 21, 'slow': 50},
            'rsi_period': 14,
            'atr_period': 14,
            'tp_sl_mode': 'ATR',
            'atr_multiplier': 1.5,    # Tighter SL for scalping
            'tp_percent': 1.0,
            'sl_percent': 0.5,
            'tp_points': 150,         # Scalping targets
            'sl_points': 75,
            'tp_pips': 15,
            'sl_pips': 7.5,
            'use_rsi_filter': True,
            'deviation': 5,           # Tight deviation for scalping
            'magic_number': 987654321
        }

        # Trading state
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.last_reset_date = datetime.now().date()

        # Market data
        self.current_market_data = {}
        self.current_signal = {}
        self.current_indicators = {'M1': {}, 'M5': {}}
        self.account_info = None
        self.positions = []
        self.symbol_info = None

        # Workers and timers
        self.analysis_worker = None
        self.data_mutex = QMutex()

        # Real-time timers
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_info)

        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_positions)

        # Initialize logging
        self.setup_logging()
        self.log_message("Enhanced controller initialized - REAL TRADING READY", "INFO")

    def setup_logging(self):
        """Setup comprehensive logging"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            # CSV trade logging
            self.csv_file = log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.csv"
            if not self.csv_file.exists():
                with open(self.csv_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'timestamp', 'side', 'entry', 'sl', 'tp', 'lot', 
                        'result', 'spread_pts', 'atr_pts', 'mode', 'reason'
                    ])

        except Exception as e:
            print(f"Logging setup error: {e}")

    def log_message(self, message: str, level: str = "INFO"):
        """Enhanced log message with threading safety"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            formatted_message = f"[{timestamp}] {message}"
            self.signal_log.emit(formatted_message, level)

            # Console logging for debugging
            print(f"[{level}] {formatted_message}")

        except Exception as e:
            print(f"Log emit error: {e}")

    def connect_mt5(self) -> bool:
        """Enhanced MT5 connection with multiple strategies"""
        try:
            if not MT5_AVAILABLE:
                self.log_message("❌ CANNOT CONNECT: MetaTrader5 module not installed", "ERROR")
                self.log_message("❌ Real trading REQUIRES: pip install MetaTrader5", "ERROR")
                return False

            self.log_message("🚀 CONNECTING TO REAL MT5 PLATFORM...", "INFO")

            # Enhanced connection strategies
            connection_successful = False
            last_error = None

            # Strategy 1: Simple initialization
            try:
                self.log_message("📡 Attempting direct MT5 connection...", "INFO")
                if mt5.initialize():
                    connection_successful = True
                    self.log_message("✅ Direct connection successful!", "INFO")
                else:
                    last_error = mt5.last_error()
                    self.log_message(f"❌ Direct connection failed: {last_error}", "WARNING")
            except Exception as e:
                self.log_message(f"❌ Direct connection exception: {e}", "WARNING")

            # Strategy 2: Path-based initialization
            if not connection_successful:
                self.log_message("🔄 Trying MT5 installation paths...", "INFO")
                mt5_paths = [
                    r"C:\Program Files\MetaTrader 5\terminal64.exe",
                    r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
                ]

                for path in mt5_paths:
                    try:
                        self.log_message(f"🔌 Testing path: {path}", "INFO")
                        if mt5.initialize(path=path):
                            connection_successful = True
                            self.log_message(f"✅ Connected via: {path}", "INFO")
                            break
                    except Exception as e:
                        continue

            # Strategy 3: Force reset and retry
            if not connection_successful:
                self.log_message("🔄 Force reset and final attempt...", "INFO")
                try:
                    mt5.shutdown()
                    import time
                    time.sleep(2)
                    
                    if mt5.initialize():
                        connection_successful = True
                        self.log_message("✅ Reset connection successful!", "INFO")
                except Exception as e:
                    self.log_message(f"❌ Reset connection failed: {e}", "ERROR")

            if not connection_successful:
                self.log_message("🚨 ALL CONNECTION ATTEMPTS FAILED!", "ERROR")
                self.log_message("📋 TROUBLESHOOTING REQUIRED:", "ERROR")
                self.log_message("1. ✅ Ensure MT5 terminal is RUNNING", "ERROR")
                self.log_message("2. ✅ LOGIN to your trading account", "ERROR")
                self.log_message("3. ✅ Enable 'Allow automated trading'", "ERROR")
                self.log_message("4. ✅ Check Tools → Options → Expert Advisors", "ERROR")
                self.log_message("5. ✅ 'Allow automated trading' must be checked", "ERROR")
                self.log_message("6. ✅ 'Allow imports of external experts' must be checked", "ERROR")
                return False

            # Verify account login
            account_info = mt5.account_info()
            if account_info is None:
                self.log_message("❌ MT5 connected but NO ACCOUNT LOGIN!", "ERROR")
                self.log_message("❌ Please login to your trading account in MT5", "ERROR")
                return False

            # Store account info
            self.account_info = account_info._asdict()
            self.log_message(f"✅ Account connected: {self.account_info['login']}", "INFO")
            self.log_message(f"✅ Live balance: ${self.account_info['balance']:.2f}", "INFO")
            
            # Validate symbol
            symbol = self.config['symbol']
            if not mt5.symbol_select(symbol, True):
                self.log_message(f"❌ Failed to select symbol: {symbol}", "ERROR")
                return False

            # Get symbol info
            self.symbol_info = mt5.symbol_info(symbol)
            if self.symbol_info is None:
                self.log_message(f"❌ Failed to get symbol info: {symbol}", "ERROR")
                return False

            # Verify trading permissions
            if self.symbol_info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL:
                self.log_message(f"❌ Symbol {symbol} not available for trading", "ERROR")
                return False

            # Log symbol specifications
            self.log_symbol_specs()

            # Connection successful
            self.is_connected = True
            self.log_message("🎉 MT5 CONNECTION SUCCESSFUL!", "INFO")

            # Start analysis worker
            self.start_analysis_worker()

            # Start monitoring timers
            self.account_timer.start(1000)   # 1 second
            self.position_timer.start(500)   # 0.5 seconds

            self.log_message("✅ REAL-TIME MONITORING ACTIVE", "INFO")
            return True

        except Exception as e:
            error_msg = f"MT5 connection critical error: {e}\n{traceback.format_exc()}"
            self.log_message(error_msg, "ERROR")
            return False

    def start_analysis_worker(self):
        """Start enhanced analysis worker"""
        try:
            # Stop existing worker
            if self.analysis_worker and self.analysis_worker.isRunning():
                self.analysis_worker.stop()
                self.analysis_worker.wait()

            # Create new worker
            self.analysis_worker = AnalysisWorker(self)

            # Connect signals
            self.analysis_worker.heartbeat_signal.connect(
                lambda msg: self.log_message(msg, "INFO"))
            self.analysis_worker.signal_ready.connect(self.handle_trading_signal)
            self.analysis_worker.indicators_ready.connect(self.handle_indicators_update)
            self.analysis_worker.tick_data_signal.connect(self.handle_tick_data)
            self.analysis_worker.error_signal.connect(
                lambda msg: self.log_message(msg, "ERROR"))

            # Start worker
            self.analysis_worker.start()
            self.log_message("✅ ENHANCED ANALYSIS WORKER STARTED", "INFO")

        except Exception as e:
            self.log_message(f"Analysis worker error: {e}", "ERROR")

    def handle_tick_data(self, tick_data):
        """Handle real-time tick data"""
        self.current_market_data = tick_data
        self.signal_market_data.emit(tick_data)

    def handle_indicators_update(self, indicators):
        """Handle technical indicators update"""
        self.current_indicators = indicators
        self.signal_indicators_update.emit(indicators)

    def handle_trading_signal(self, signal):
        """Handle trading signal with enhanced execution"""
        try:
            if not signal or not signal.get('side'):
                return

            self.execution_stats['signals_generated'] += 1
            signal_side = signal.get('side')
            entry_price = signal.get('entry_price', 0)
            confidence = signal.get('confidence', 0)

            self.log_message(f"🎯 [SIGNAL] {signal_side} @ {entry_price:.5f} confidence={confidence:.2f}", "INFO")
            self.current_signal = signal
            self.signal_trade_signal.emit(signal)

            # Risk management checks
            if not self.check_enhanced_risk_limits():
                self.log_message("🛡️ [BLOCKED] Signal blocked by risk management", "WARNING")
                return

            # Auto-execution for live mode
            if not self.shadow_mode and self.is_running:
                success = self.execute_enhanced_signal(signal)
                if success:
                    self.execution_stats['signals_executed'] += 1
                    self.execution_stats['last_execution'] = datetime.now().strftime('%H:%M:%S')
                    self.log_message(f"✅ [EXECUTED] {signal_side} order placed successfully", "INFO")
                else:
                    self.log_message(f"❌ [FAILED] {signal_side} execution failed", "ERROR")

                # Update execution rate
                if self.execution_stats['signals_generated'] > 0:
                    rate = (self.execution_stats['signals_executed'] / 
                           self.execution_stats['signals_generated']) * 100
                    self.execution_stats['execution_rate'] = rate

            else:
                self.log_message(f"🔒 [SHADOW] {signal_side} simulated - Live mode disabled", "INFO")

        except Exception as e:
            error_msg = f"Signal handling error: {e}\n{traceback.format_exc()}"
            self.log_message(error_msg, "ERROR")

    def execute_enhanced_signal(self, signal):
        """Execute real trading signal with enhanced order management"""
        try:
            if not self.is_connected or not MT5_AVAILABLE:
                self.log_message("❌ EXECUTION FAILED: MT5 not connected", "ERROR")
                return False

            symbol = self.config['symbol']
            side = signal.get('side')

            # Enhanced lot size calculation
            lot_size = self.calculate_enhanced_lot_size(signal)
            if lot_size <= 0:
                self.log_message("❌ EXECUTION FAILED: Invalid lot size", "ERROR")
                return False

            # Get fresh tick data
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                self.log_message("❌ EXECUTION FAILED: No tick data", "ERROR")
                return False

            # Calculate enhanced TP/SL
            tp_price, sl_price = self.calculate_enhanced_tp_sl(signal, tick)

            # Prepare order with enhanced parameters
            if side == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid

            # Enhanced order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": self.config.get('deviation', 5),
                "magic": self.config.get('magic_number', 987654321),
                "comment": f"SCALP_{side}_{signal.get('confidence', 0):.2f}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Execute with fallback filling
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                # Try FOK filling
                request["type_filling"] = mt5.ORDER_FILLING_FOK
                result = mt5.order_send(request)

            # Verify execution
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log_message(f"✅ REAL ORDER EXECUTED: {side} {lot_size} @ {price:.5f}", "INFO")
                self.log_message(f"✅ Ticket: {result.order} | SL: {sl_price:.5f} | TP: {tp_price:.5f}", "INFO")
                
                self.daily_trades += 1
                self.log_trade_to_csv(signal, result, lot_size, sl_price, tp_price)
                return True
            else:
                self.log_message(f"❌ ORDER FAILED: {result.retcode} - {result.comment}", "ERROR")
                return False

        except Exception as e:
            error_msg = f"Enhanced execution error: {e}"
            self.log_message(error_msg, "ERROR")
            return False

    def calculate_enhanced_lot_size(self, signal):
        """Calculate lot size with enhanced risk management"""
        try:
            if not self.account_info:
                return 0.01

            balance = self.account_info.get('balance', 10000)
            risk_percent = self.config.get('risk_percent', 0.5) / 100
            risk_amount = balance * risk_percent

            # Symbol constraints
            if not self.symbol_info:
                return 0.01

            # Enhanced SL calculation based on signal
            point = self.symbol_info.point
            atr_points = signal.get('atr_points', 100)
            
            # Adaptive SL based on volatility
            if atr_points > 200:
                sl_points = atr_points * 0.8  # Wider SL for high volatility
            else:
                sl_points = max(atr_points * 1.2, 75)  # Tighter SL for low volatility

            tick_value = getattr(self.symbol_info, 'trade_tick_value', 1.0)
            sl_amount = sl_points * point * tick_value

            if sl_amount <= 0:
                return 0.01

            lot_size = risk_amount / sl_amount

            # Apply symbol constraints
            min_lot = getattr(self.symbol_info, 'volume_min', 0.01)
            max_lot = getattr(self.symbol_info, 'volume_max', 100.0)
            step = getattr(self.symbol_info, 'volume_step', 0.01)

            lot_size = round(lot_size / step) * step
            lot_size = max(min_lot, min(lot_size, max_lot))

            self.log_message(f"💰 Enhanced lot: {lot_size} (Risk: ${risk_amount:.2f})", "INFO")
            return lot_size

        except Exception as e:
            self.log_message(f"Lot calculation error: {e}", "ERROR")
            return 0.01

    def calculate_enhanced_tp_sl(self, signal, tick):
        """Calculate TP/SL with enhanced scalping logic"""
        try:
            side = signal.get('side')
            mode = self.config.get('tp_sl_mode', 'ATR')

            if side == "BUY":
                entry_price = tick.ask
                multiplier = 1
            else:
                entry_price = tick.bid
                multiplier = -1

            point = self.symbol_info.point
            atr_points = signal.get('atr_points', 100)

            if mode == "ATR":
                # Enhanced ATR-based calculation
                confidence = signal.get('confidence', 0.5)
                
                # Adaptive multipliers based on confidence
                if confidence > 0.8:
                    sl_multiplier = 1.0   # Tighter SL for high confidence
                    tp_multiplier = 2.0   # Higher TP for high confidence
                else:
                    sl_multiplier = 1.5   # Wider SL for lower confidence
                    tp_multiplier = 1.5   # Conservative TP

                sl_distance = max(atr_points * sl_multiplier, 50)
                tp_distance = sl_distance * tp_multiplier

            elif mode == "Points":
                sl_distance = self.config.get('sl_points', 75)
                tp_distance = self.config.get('tp_points', 150)

            elif mode == "Pips":
                digits = getattr(self.symbol_info, 'digits', 5)
                pip_size = 10 if digits in [3, 5] else 1
                sl_distance = self.config.get('sl_pips', 7.5) * pip_size
                tp_distance = self.config.get('tp_pips', 15) * pip_size

            elif mode == "Balance%":
                balance = self.account_info.get('balance', 10000)
                tick_value = getattr(self.symbol_info, 'trade_tick_value', 1.0)
                
                sl_amount = balance * (self.config.get('sl_percent', 0.5) / 100)
                tp_amount = balance * (self.config.get('tp_percent', 1.0) / 100)
                
                sl_distance = sl_amount / (point * tick_value)
                tp_distance = tp_amount / (point * tick_value)

            # Calculate final prices
            sl_price = entry_price - (multiplier * sl_distance * point)
            tp_price = entry_price + (multiplier * tp_distance * point)

            self.log_message(f"🎯 Enhanced TP/SL: SL={sl_price:.5f} TP={tp_price:.5f}", "INFO")
            return tp_price, sl_price

        except Exception as e:
            self.log_message(f"TP/SL calculation error: {e}", "ERROR")
            # Fallback
            fallback_distance = 100 * point
            return (entry_price + (multiplier * fallback_distance * 2), 
                   entry_price - (multiplier * fallback_distance))

    def check_enhanced_risk_limits(self):
        """Enhanced risk management checks"""
        try:
            # Daily trade limit
            if self.daily_trades >= self.config['max_trades_per_day']:
                self.log_message(f"🛡️ Daily trade limit reached: {self.daily_trades}", "WARNING")
                return False

            # Consecutive losses limit
            if self.consecutive_losses >= 3:
                self.log_message(f"🛡️ Consecutive losses limit: {self.consecutive_losses}", "WARNING")
                return False

            # Account equity check
            if self.account_info:
                balance = self.account_info.get('balance', 0)
                equity = self.account_info.get('equity', 0)
                
                if balance > 0:
                    drawdown = ((balance - equity) / balance) * 100
                    if drawdown > 3.0:  # 3% max drawdown
                        self.log_message(f"🛡️ Drawdown limit exceeded: {drawdown:.1f}%", "WARNING")
                        return False

            return True

        except Exception as e:
            self.log_message(f"Risk check error: {e}", "ERROR")
            return True

    def log_trade_to_csv(self, signal, result, lot_size, sl, tp):
        """Enhanced trade logging"""
        try:
            trade_data = [
                datetime.now().isoformat(),
                signal.get('side'),
                result.price,
                sl,
                tp,
                lot_size,
                'EXECUTED',
                signal.get('spread_points', 0),
                signal.get('atr_points', 0),
                'REAL_ENHANCED',
                f"conf={signal.get('confidence', 0):.2f}"
            ]

            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(trade_data)

        except Exception as e:
            self.log_message(f"CSV logging error: {e}", "ERROR")

    def log_symbol_specs(self):
        """Log detailed symbol specifications"""
        try:
            if not self.symbol_info:
                return

            self.log_message(f"📊 Symbol: {self.symbol_info.name}", "INFO")
            self.log_message(f"📊 Point: {self.symbol_info.point}", "INFO")
            self.log_message(f"📊 Digits: {self.symbol_info.digits}", "INFO")
            self.log_message(f"📊 Min/Max Volume: {self.symbol_info.volume_min}/{self.symbol_info.volume_max}", "INFO")
            self.log_message(f"📊 Volume Step: {self.symbol_info.volume_step}", "INFO")
            self.log_message(f"📊 Trade Mode: {self.symbol_info.trade_mode}", "INFO")

        except Exception as e:
            self.log_message(f"Symbol specs error: {e}", "ERROR")

    # Additional methods for bot control...
    def start_bot(self) -> bool:
        """Start enhanced bot"""
        try:
            if not self.is_connected:
                self.log_message("❌ Cannot start: Not connected to MT5", "ERROR")
                return False

            if not self.analysis_worker or not self.analysis_worker.isRunning():
                self.start_analysis_worker()

            self.is_running = True
            self.log_message("🚀 [ENHANCED BOT STARTED] Real trading active", "INFO")
            return True

        except Exception as e:
            error_msg = f"Bot start error: {e}"
            self.log_message(error_msg, "ERROR")
            return False

    def stop_bot(self):
        """Stop enhanced bot"""
        try:
            self.is_running = False
            
            if self.analysis_worker and self.analysis_worker.isRunning():
                self.analysis_worker.stop()

            self.log_message("🛑 [BOT STOPPED] Analysis and trading halted", "INFO")

        except Exception as e:
            self.log_message(f"Bot stop error: {e}", "ERROR")

    def disconnect_mt5(self):
        """Enhanced MT5 disconnect"""
        try:
            self.stop_bot()

            if self.account_timer.isActive():
                self.account_timer.stop()
            if self.position_timer.isActive():
                self.position_timer.stop()

            if MT5_AVAILABLE:
                mt5.shutdown()

            self.is_connected = False
            self.log_message("🔌 Disconnected from MT5", "INFO")

        except Exception as e:
            self.log_message(f"Disconnect error: {e}", "ERROR")

    def update_account_info(self):
        """Enhanced account monitoring"""
        try:
            if not self.is_connected or not MT5_AVAILABLE:
                return

            account_info = mt5.account_info()
            if account_info is None:
                self.log_message("⚠️ Account info unavailable", "WARNING")
                return

            self.account_info = account_info._asdict()
            self.signal_account_update.emit(self.account_info)

            # Enhanced monitoring alerts
            margin_level = self.account_info.get('margin_level', 1000)
            if margin_level < 150:
                self.log_message(f"🚨 LOW MARGIN: {margin_level:.1f}%", "WARNING")

        except Exception as e:
            self.log_message(f"Account update error: {e}", "ERROR")

    def update_positions(self):
        """Enhanced position monitoring"""
        try:
            if not self.is_connected or not MT5_AVAILABLE:
                return

            positions = mt5.positions_get(symbol=self.config['symbol'])
            if positions is None:
                positions = []

            self.positions = []
            for pos in positions:
                pos_dict = {
                    'ticket': pos.ticket,
                    'type': pos.type,
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'price_current': pos.price_current,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'symbol': pos.symbol,
                    'comment': pos.comment,
                    'time': pos.time
                }
                self.positions.append(pos_dict)

            self.signal_position_update.emit(self.positions)

        except Exception as e:
            self.log_message(f"Position update error: {e}", "ERROR")

    def close_all_positions(self):
        """Enhanced emergency position closure"""
        try:
            if not MT5_AVAILABLE or not self.is_connected:
                self.log_message("❌ Cannot close: MT5 not connected", "ERROR")
                return

            symbol = self.config['symbol']
            positions = mt5.positions_get(symbol=symbol)

            if not positions:
                self.log_message("✅ No positions to close", "INFO")
                self.stop_bot()
                return

            closed_count = 0
            total_profit = 0.0

            for position in positions:
                try:
                    # Determine close parameters
                    if position.type == mt5.POSITION_TYPE_BUY:
                        order_type = mt5.ORDER_TYPE_SELL
                        price = mt5.symbol_info_tick(symbol).bid
                    else:
                        order_type = mt5.ORDER_TYPE_BUY
                        price = mt5.symbol_info_tick(symbol).ask

                    # Close order
                    close_request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": position.volume,
                        "type": order_type,
                        "position": position.ticket,
                        "price": price,
                        "deviation": 20,
                        "magic": self.config.get('magic_number', 987654321),
                        "comment": "EMERGENCY_CLOSE",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }

                    result = mt5.order_send(close_request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        closed_count += 1
                        total_profit += position.profit
                        self.log_message(f"✅ CLOSED: {position.ticket} P&L: ${position.profit:.2f}", "INFO")
                    else:
                        self.log_message(f"❌ FAILED: {position.ticket} - {result.comment}", "ERROR")

                except Exception as e:
                    self.log_message(f"Close error for {position.ticket}: {e}", "ERROR")

            self.log_message(f"🚨 EMERGENCY COMPLETE: {closed_count} closed, P&L: ${total_profit:.2f}", "WARNING")
            self.stop_bot()

        except Exception as e:
            self.log_message(f"Emergency close error: {e}", "ERROR")

    # Utility methods
    def get_execution_stats(self):
        """Get execution statistics"""
        return self.execution_stats.copy()

    def set_config(self, key, value):
        """Set configuration value"""
        self.config[key] = value

    def get_config(self, key):
        """Get configuration value"""
        return self.config.get(key)

    def export_logs(self, filename):
        """Export trading logs"""
        try:
            import shutil
            shutil.copy(self.csv_file, filename)
            self.log_message(f"📁 Logs exported to: {filename}", "INFO")
            return True
        except Exception as e:
            self.log_message(f"Export error: {e}", "ERROR")
            return False

    def diagnostic_check(self):
        """Run comprehensive diagnostics"""
        try:
            self.log_message("=== ENHANCED DIAGNOSTIC CHECK ===", "INFO")

            # MT5 module check
            self.log_message(f"MT5 Module: {'✅ Available' if MT5_AVAILABLE else '❌ Missing'}", "INFO")

            # Connection check
            self.log_message(f"Connection: {'✅ Connected' if self.is_connected else '❌ Disconnected'}", "INFO")

            # Account check
            if self.account_info:
                balance = self.account_info.get('balance', 0)
                self.log_message(f"Account: ✅ Balance ${balance:.2f}", "INFO")
            else:
                self.log_message("Account: ❌ No info", "ERROR")

            # Symbol check
            if self.symbol_info:
                self.log_message(f"Symbol: ✅ {self.symbol_info.name}", "INFO")
            else:
                self.log_message("Symbol: ❌ Not loaded", "ERROR")

            # Worker check
            if self.analysis_worker and self.analysis_worker.isRunning():
                self.log_message("Analysis: ✅ Running", "INFO")
            else:
                self.log_message("Analysis: ❌ Stopped", "WARNING")

            self.log_message("=== DIAGNOSTIC COMPLETE ===", "INFO")

        except Exception as e:
            self.log_message(f"Diagnostic error: {e}", "ERROR")

    def execute_manual_trade(self, side, lot_size):
        """Execute manual trade"""
        try:
            if not self.is_connected or not MT5_AVAILABLE:
                return {'success': False, 'error': 'MT5 not connected'}

            symbol = self.config['symbol']
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return {'success': False, 'error': 'No tick data'}

            if side == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "deviation": self.config.get('deviation', 5),
                "magic": self.config.get('magic_number', 987654321),
                "comment": f"MANUAL_{side}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                request["type_filling"] = mt5.ORDER_FILLING_FOK
                result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log_message(f"✅ MANUAL {side}: {lot_size} @ {price:.5f}", "INFO")
                self.daily_trades += 1
                return {'success': True, 'ticket': result.order, 'price': result.price}
            else:
                return {'success': False, 'error': f"{result.retcode} - {result.comment}"}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def close_position(self, ticket):
        """Close specific position"""
        try:
            if not MT5_AVAILABLE or not self.is_connected:
                return False

            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return False

            position = positions[0]
            symbol = position.symbol

            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask

            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": self.config.get('magic_number', 987654321),
                "comment": "MANUAL_CLOSE",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(close_request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log_message(f"✅ Position {ticket} closed", "INFO")
                return True
            else:
                self.log_message(f"❌ Close failed: {result.comment}", "ERROR")
                return False

        except Exception as e:
            self.log_message(f"Close position error: {e}", "ERROR")
            return False
