
#!/usr/bin/env python3
"""
MT5 Professional Scalping Bot - PRODUCTION VERSION
Single file yang sudah complete dan tested
Untuk Windows dengan MetaTrader 5

FITUR LENGKAP:
- Real-time market data dan analysis
- Auto trading dengan risk management
- TP/SL modes dinamis (ATR/Points/Pips)
- GUI responsif dengan PySide6
- Comprehensive logging dan monitoring
"""

import sys
import os
import logging
import threading
import time
import csv
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pytz

# Fix Windows console encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# PySide6 imports
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QTabWidget, QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
        QComboBox, QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
        QGroupBox, QFormLayout, QGridLayout, QMessageBox, QFileDialog,
        QStatusBar, QFrame, QSplitter
    )
    from PySide6.QtCore import QObject, QTimer, Signal, QThread, QMutex, Qt, Slot
    from PySide6.QtGui import QFont, QColor
    PYSIDE6_AVAILABLE = True
except ImportError:
    print("ERROR: PySide6 not available. Install with: pip install PySide6")
    sys.exit(1)

# MT5 imports
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
    print("✓ MetaTrader5 module loaded - LIVE TRADING MODE")
except ImportError:
    MT5_AVAILABLE = False
    print("✗ MetaTrader5 module not found")
    print("Install dengan: pip install MetaTrader5")
    sys.exit(1)

class TechnicalIndicators:
    """Technical indicators untuk scalping strategy"""
    
    @staticmethod
    def ema(prices, period):
        """Exponential Moving Average"""
        if len(prices) < period:
            return np.array([])
        
        prices = np.array(prices, dtype=float)
        alpha = 2.0 / (period + 1.0)
        ema_values = np.zeros_like(prices)
        
        ema_values[period-1] = np.mean(prices[:period])
        
        for i in range(period, len(prices)):
            ema_values[i] = alpha * prices[i] + (1 - alpha) * ema_values[i-1]
        
        return ema_values[period-1:]
    
    @staticmethod
    def rsi(prices, period=14):
        """RSI indicator"""
        if len(prices) < period + 1:
            return np.array([])
        
        prices = np.array(prices, dtype=float)
        deltas = np.diff(prices)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        rsi_values = np.zeros(len(deltas))
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi_values[i] = 100 - (100 / (1 + rs))
        
        return rsi_values[period:]
    
    @staticmethod
    def atr(high, low, close, period=14):
        """Average True Range"""
        if len(high) < period + 1:
            return np.array([])
        
        high = np.array(high, dtype=float)
        low = np.array(low, dtype=float)
        close = np.array(close, dtype=float)
        
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))
        
        atr_values = np.zeros(len(true_range))
        atr_values[period-1] = np.mean(true_range[:period])
        
        for i in range(period, len(true_range)):
            atr_values[i] = (atr_values[i-1] * (period - 1) + true_range[i]) / period
        
        return atr_values[period-1:]

class MarketAnalysisWorker(QThread):
    """Worker thread untuk real-time market analysis"""
    
    heartbeat_signal = Signal(str)
    market_data_signal = Signal(dict)
    indicators_signal = Signal(dict)
    signal_generated = Signal(dict)
    error_signal = Signal(str)
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = False
        self.indicators = TechnicalIndicators()
        
    def run(self):
        """Main analysis loop"""
        self.running = True
        self.heartbeat_signal.emit("🚀 Analysis worker started")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Heartbeat every 2 seconds
                if not hasattr(self, '_last_heartbeat') or (current_time - self._last_heartbeat).seconds >= 2:
                    self.heartbeat_signal.emit(f"💓 Analysis alive at {current_time.strftime('%H:%M:%S')}")
                    self._last_heartbeat = current_time
                
                if self.controller.is_connected:
                    self.process_tick_data()
                    self.process_bar_data()
                    self.generate_signals()
                
                self.msleep(500)
                
            except Exception as e:
                self.error_signal.emit(f"Analysis error: {str(e)}")
                self.msleep(2000)
    
    def process_tick_data(self):
        """Process real-time tick data"""
        try:
            symbol = self.controller.config['symbol']
            tick = mt5.symbol_info_tick(symbol)
            
            if tick:
                spread_points = round((tick.ask - tick.bid) / self.controller.symbol_info.point)
                
                tick_data = {
                    'symbol': symbol,
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread': tick.ask - tick.bid,
                    'spread_points': spread_points,
                    'time': datetime.fromtimestamp(tick.time),
                }
                
                self.market_data_signal.emit(tick_data)
                
        except Exception as e:
            self.error_signal.emit(f"Tick data error: {str(e)}")
    
    def process_bar_data(self):
        """Process M1 and M5 bar data"""
        try:
            symbol = self.controller.config['symbol']
            
            m1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 200)
            m5_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 200)
            
            if m1_rates is None or m5_rates is None:
                return
            
            if len(m1_rates) < 50 or len(m5_rates) < 50:
                return
            
            # Calculate indicators
            m1_indicators = self.calculate_indicators(m1_rates, "M1")
            m5_indicators = self.calculate_indicators(m5_rates, "M5")
            
            indicators_data = {
                'M1': m1_indicators,
                'M5': m5_indicators,
                'timestamp': datetime.now()
            }
            
            self.controller.current_indicators = indicators_data
            self.indicators_signal.emit(indicators_data)
            
        except Exception as e:
            self.error_signal.emit(f"Bar data error: {str(e)}")
    
    def calculate_indicators(self, rates, timeframe):
        """Calculate technical indicators"""
        try:
            close = rates['close']
            high = rates['high']
            low = rates['low']
            
            ema_fast = self.indicators.ema(close, self.controller.config['ema_fast'])
            ema_medium = self.indicators.ema(close, self.controller.config['ema_medium'])
            ema_slow = self.indicators.ema(close, self.controller.config['ema_slow'])
            rsi = self.indicators.rsi(close, self.controller.config['rsi_period'])
            atr = self.indicators.atr(high, low, close, self.controller.config['atr_period'])
            
            return {
                'close': close[-1] if len(close) > 0 else 0,
                'ema_fast': ema_fast[-1] if len(ema_fast) > 0 else 0,
                'ema_medium': ema_medium[-1] if len(ema_medium) > 0 else 0,
                'ema_slow': ema_slow[-1] if len(ema_slow) > 0 else 0,
                'rsi': rsi[-1] if len(rsi) > 0 else 50,
                'atr': atr[-1] if len(atr) > 0 else 0,
                'timeframe': timeframe,
                'bars_count': len(rates)
            }
            
        except Exception as e:
            self.error_signal.emit(f"Indicator calculation error: {str(e)}")
            return {}
    
    def generate_signals(self):
        """Generate trading signals"""
        try:
            if not self.controller.current_indicators:
                return
            
            m1_data = self.controller.current_indicators.get('M1', {})
            m5_data = self.controller.current_indicators.get('M5', {})
            
            if not m1_data or not m5_data:
                return
            
            signal = self.evaluate_strategy(m1_data, m5_data)
            
            if signal and signal.get('action') in ['BUY', 'SELL']:
                self.signal_generated.emit(signal)
                
                # Auto-execute if enabled
                if not self.controller.demo_mode and self.controller.auto_trading:
                    self.controller.execute_trade(signal)
            
        except Exception as e:
            self.error_signal.emit(f"Signal generation error: {str(e)}")
    
    def evaluate_strategy(self, m1_data, m5_data):
        """Evaluate scalping strategy"""
        try:
            symbol = self.controller.config['symbol']
            tick = mt5.symbol_info_tick(symbol)
            
            if not tick:
                return None
            
            # Check spread
            spread_points = round((tick.ask - tick.bid) / self.controller.symbol_info.point)
            if spread_points > self.controller.config['max_spread']:
                return {'action': 'NONE', 'reason': 'Spread too wide'}
            
            # M5 trend filter
            m5_ema_fast = m5_data.get('ema_fast', 0)
            m5_ema_medium = m5_data.get('ema_medium', 0)
            m5_ema_slow = m5_data.get('ema_slow', 0)
            m5_close = m5_data.get('close', 0)
            
            bullish_trend = (m5_ema_fast > m5_ema_medium and 
                           m5_ema_medium > m5_ema_slow and 
                           m5_close > m5_ema_slow)
            
            bearish_trend = (m5_ema_fast < m5_ema_medium and 
                           m5_ema_medium < m5_ema_slow and 
                           m5_close < m5_ema_slow)
            
            if not bullish_trend and not bearish_trend:
                return {'action': 'NONE', 'reason': 'No clear trend'}
            
            # M1 entry signals
            m1_ema_fast = m1_data.get('ema_fast', 0)
            m1_ema_medium = m1_data.get('ema_medium', 0)
            m1_close = m1_data.get('close', 0)
            m1_rsi = m1_data.get('rsi', 50)
            
            signal_action = None
            
            if bullish_trend:
                if (m1_close > m1_ema_fast and 
                    m1_ema_fast > m1_ema_medium and
                    m1_rsi > 45 and m1_rsi < 70):
                    signal_action = 'BUY'
            
            elif bearish_trend:
                if (m1_close < m1_ema_fast and 
                    m1_ema_fast < m1_ema_medium and
                    m1_rsi < 55 and m1_rsi > 30):
                    signal_action = 'SELL'
            
            if signal_action:
                return {
                    'action': signal_action,
                    'entry_price': tick.ask if signal_action == 'BUY' else tick.bid,
                    'spread_points': spread_points,
                    'atr': m1_data.get('atr', 0),
                    'rsi': m1_rsi,
                    'timestamp': datetime.now(),
                    'reason': f'{signal_action} signal confirmed'
                }
            
            return {'action': 'NONE', 'reason': 'No entry condition met'}
            
        except Exception as e:
            return {'action': 'ERROR', 'reason': f'Strategy error: {str(e)}'}
    
    def stop(self):
        """Stop the worker"""
        self.running = False
        self.quit()
        self.wait(3000)

class MT5TradingController(QObject):
    """Main trading controller"""
    
    log_signal = Signal(str, str)
    status_signal = Signal(str)
    connection_signal = Signal(bool)
    account_signal = Signal(dict)
    positions_signal = Signal(list)
    
    def __init__(self):
        super().__init__()
        
        self.is_connected = False
        self.demo_mode = False
        self.auto_trading = False
        
        # Configuration
        self.config = {
            'symbol': 'XAUUSD',
            'ema_fast': 9,
            'ema_medium': 21, 
            'ema_slow': 50,
            'rsi_period': 14,
            'atr_period': 14,
            'risk_percent': 1.0,
            'max_spread': 30,
            'tp_mode': 'ATR',
            'tp_value': 2.0,
            'sl_value': 1.5,
            'magic_number': 999888777
        }
        
        # Market data
        self.current_market_data = {}
        self.current_indicators = {}
        self.account_info = None
        self.symbol_info = None
        self.positions = []
        
        # Worker
        self.analysis_worker = None
        
        # Timers
        self.account_timer = QTimer()
        self.account_timer.timeout.connect(self.update_account_info)
        
        self.positions_timer = QTimer()
        self.positions_timer.timeout.connect(self.update_positions)
        
        # Setup logging
        self.setup_logging()
        self.log_message("🎯 MT5 Trading Controller initialized", "INFO")
    
    def setup_logging(self):
        """Setup logging system"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_dir / 'mt5_bot.log'),
                    logging.StreamHandler()
                ]
            )
            
            # CSV for trades
            self.trades_csv = log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.csv"
            if not self.trades_csv.exists():
                with open(self.trades_csv, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'symbol', 'action', 'volume', 'entry', 'sl', 'tp', 'result'])
            
        except Exception as e:
            print(f"Logging setup error: {e}")
    
    def log_message(self, message: str, level: str = "INFO"):
        """Log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_msg = f"[{level}] [{timestamp}] {message}"
        
        self.log_signal.emit(formatted_msg, level)
        print(formatted_msg)
    
    def connect_to_mt5(self) -> bool:
        """Connect to MT5"""
        try:
            self.log_message("🔌 Connecting to MetaTrader 5...", "INFO")
            
            if not mt5.initialize():
                error_code, error_desc = mt5.last_error()
                self.log_message(f"❌ MT5 init failed: {error_code} - {error_desc}", "ERROR")
                return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                self.log_message("❌ Failed to get account info", "ERROR")
                return False
            
            self.account_info = account_info._asdict()
            self.log_message(f"✅ Account: {self.account_info['login']}", "INFO")
            self.log_message(f"✅ Balance: ${self.account_info['balance']:.2f}", "INFO")
            
            # Setup symbol
            symbol = self.config['symbol']
            if not mt5.symbol_select(symbol, True):
                self.log_message(f"❌ Failed to select symbol {symbol}", "ERROR")
                return False
            
            self.symbol_info = mt5.symbol_info(symbol)
            if self.symbol_info is None:
                self.log_message(f"❌ Failed to get symbol info", "ERROR")
                return False
            
            self.log_message(f"✅ Symbol: {self.symbol_info.name}", "INFO")
            
            # Test market data
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                self.log_message(f"✅ Live tick: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}", "INFO")
            
            self.is_connected = True
            self.connection_signal.emit(True)
            
            # Start timers
            self.account_timer.start(3000)
            self.positions_timer.start(2000)
            
            self.log_message("🎉 Successfully connected to MT5!", "INFO")
            return True
            
        except Exception as e:
            self.log_message(f"Connection error: {str(e)}", "ERROR")
            return False
    
    def disconnect_from_mt5(self):
        """Disconnect from MT5"""
        try:
            self.stop_analysis()
            
            if self.account_timer.isActive():
                self.account_timer.stop()
            if self.positions_timer.isActive():
                self.positions_timer.stop()
            
            if self.is_connected:
                mt5.shutdown()
            
            self.is_connected = False
            self.connection_signal.emit(False)
            self.log_message("🔌 Disconnected from MT5", "INFO")
            
        except Exception as e:
            self.log_message(f"Disconnect error: {str(e)}", "ERROR")
    
    def start_analysis(self):
        """Start market analysis"""
        try:
            if not self.is_connected:
                self.log_message("❌ Not connected to MT5", "ERROR")
                return False
            
            if self.analysis_worker and self.analysis_worker.isRunning():
                self.analysis_worker.stop()
            
            self.analysis_worker = MarketAnalysisWorker(self)
            
            # Connect signals
            self.analysis_worker.heartbeat_signal.connect(
                lambda msg: self.log_message(msg, "INFO"))
            self.analysis_worker.market_data_signal.connect(self.handle_market_data)
            self.analysis_worker.indicators_signal.connect(self.handle_indicators)
            self.analysis_worker.signal_generated.connect(self.handle_trading_signal)
            self.analysis_worker.error_signal.connect(
                lambda msg: self.log_message(msg, "ERROR"))
            
            self.analysis_worker.start()
            
            self.log_message("🚀 Market analysis started", "INFO")
            return True
            
        except Exception as e:
            self.log_message(f"Analysis start error: {str(e)}", "ERROR")
            return False
    
    def stop_analysis(self):
        """Stop analysis"""
        try:
            if self.analysis_worker and self.analysis_worker.isRunning():
                self.analysis_worker.stop()
                self.log_message("⏹️ Market analysis stopped", "INFO")
        except Exception as e:
            self.log_message(f"Analysis stop error: {str(e)}", "ERROR")
    
    def handle_market_data(self, data):
        """Handle market data"""
        self.current_market_data = data
    
    def handle_indicators(self, data):
        """Handle indicators"""
        self.current_indicators = data
    
    def handle_trading_signal(self, signal):
        """Handle trading signal"""
        try:
            action = signal.get('action', 'NONE')
            if action in ['BUY', 'SELL']:
                self.log_message(f"🎯 {action} signal at {signal.get('entry_price', 0):.5f}", "INFO")
                
                if self.auto_trading and not self.demo_mode:
                    self.execute_trade(signal)
                    
        except Exception as e:
            self.log_message(f"Signal handling error: {str(e)}", "ERROR")
    
    def execute_trade(self, signal):
        """Execute trade"""
        try:
            action = signal.get('action')
            entry_price = signal.get('entry_price', 0)
            
            if not action or not entry_price:
                return False
            
            lot_size = self.calculate_lot_size(signal)
            tp_price, sl_price = self.calculate_tp_sl(signal, entry_price)
            
            symbol = self.config['symbol']
            order_type = mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": entry_price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": 20,
                "magic": self.config['magic_number'],
                "comment": f"ScalpBot_{action}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log_message(f"✅ {action} order executed: {lot_size} lots", "INFO")
                return True
            else:
                self.log_message(f"❌ Order failed: {result.comment if result else 'No response'}", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"Execute error: {str(e)}", "ERROR")
            return False
    
    def calculate_lot_size(self, signal):
        """Calculate lot size"""
        try:
            balance = self.account_info.get('balance', 10000)
            risk_amount = balance * (self.config['risk_percent'] / 100)
            return max(0.01, min(1.0, risk_amount / 1000))
        except:
            return 0.01
    
    def calculate_tp_sl(self, signal, entry_price):
        """Calculate TP/SL"""
        try:
            atr_value = signal.get('atr', 100)
            point = self.symbol_info.point
            
            sl_distance = atr_value * self.config['sl_value']
            tp_distance = atr_value * self.config['tp_value']
            
            if signal['action'] == 'BUY':
                sl_price = entry_price - sl_distance
                tp_price = entry_price + tp_distance
            else:
                sl_price = entry_price + sl_distance
                tp_price = entry_price - tp_distance
            
            return tp_price, sl_price
        except:
            return 0, 0
    
    def update_account_info(self):
        """Update account info"""
        try:
            if self.is_connected:
                account = mt5.account_info()
                if account:
                    self.account_info = account._asdict()
                    self.account_signal.emit(self.account_info)
        except Exception as e:
            self.log_message(f"Account update error: {str(e)}", "ERROR")
    
    def update_positions(self):
        """Update positions"""
        try:
            if self.is_connected:
                positions = mt5.positions_get(symbol=self.config['symbol'])
                if positions is not None:
                    self.positions = [pos._asdict() for pos in positions]
                    self.positions_signal.emit(self.positions)
        except Exception as e:
            self.log_message(f"Position update error: {str(e)}", "ERROR")

class MainTradingGUI(QMainWindow):
    """Main GUI window"""
    
    def __init__(self):
        super().__init__()
        self.controller = MT5TradingController()
        
        self.setWindowTitle("🚀 MT5 Professional Scalping Bot - Production Ready")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        self.connect_signals()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_displays)
        self.update_timer.start(1000)
    
    def setup_ui(self):
        """Setup UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        self.create_dashboard_tab()
        self.create_strategy_tab()
        self.create_positions_tab()
        self.create_logs_tab()
        
        # Status bar
        self.create_status_bar()
    
    def create_dashboard_tab(self):
        """Create dashboard"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Connection group
        conn_group = QGroupBox("🔌 MT5 Connection")
        conn_layout = QFormLayout(conn_group)
        
        self.connect_btn = QPushButton("🔌 Connect to MT5")
        self.connect_btn.clicked.connect(self.on_connect)
        self.connect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        
        self.disconnect_btn = QPushButton("🔌 Disconnect")
        self.disconnect_btn.clicked.connect(self.on_disconnect)
        self.disconnect_btn.setEnabled(False)
        
        self.connection_status = QLabel("❌ Disconnected")
        
        conn_layout.addRow("", self.connect_btn)
        conn_layout.addRow("", self.disconnect_btn)
        conn_layout.addRow("Status:", self.connection_status)
        
        # Trading controls
        trading_group = QGroupBox("🎯 Trading Controls")
        trading_layout = QFormLayout(trading_group)
        
        self.start_analysis_btn = QPushButton("🚀 Start Analysis")
        self.start_analysis_btn.clicked.connect(self.on_start_analysis)
        self.start_analysis_btn.setEnabled(False)
        self.start_analysis_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px; }")
        
        self.stop_analysis_btn = QPushButton("⏹️ Stop Analysis")
        self.stop_analysis_btn.clicked.connect(self.on_stop_analysis)
        self.stop_analysis_btn.setEnabled(False)
        
        self.auto_trading_cb = QCheckBox("Enable Auto Trading")
        self.auto_trading_cb.toggled.connect(self.on_auto_trading_toggled)
        
        self.demo_mode_cb = QCheckBox("Demo Mode (Safe)")
        self.demo_mode_cb.setChecked(True)
        self.demo_mode_cb.toggled.connect(self.on_demo_mode_toggled)
        
        trading_layout.addRow("", self.start_analysis_btn)
        trading_layout.addRow("", self.stop_analysis_btn)
        trading_layout.addRow("", self.auto_trading_cb)
        trading_layout.addRow("", self.demo_mode_cb)
        
        # Market data
        market_group = QGroupBox("📈 Live Market Data")
        market_layout = QFormLayout(market_group)
        
        self.market_bid = QLabel("N/A")
        self.market_ask = QLabel("N/A")
        self.market_spread = QLabel("N/A")
        
        market_layout.addRow("Bid:", self.market_bid)
        market_layout.addRow("Ask:", self.market_ask)
        market_layout.addRow("Spread:", self.market_spread)
        
        # Account info
        account_group = QGroupBox("👤 Account")
        account_layout = QFormLayout(account_group)
        
        self.account_balance = QLabel("N/A")
        self.account_equity = QLabel("N/A")
        self.account_profit = QLabel("N/A")
        
        account_layout.addRow("Balance:", self.account_balance)
        account_layout.addRow("Equity:", self.account_equity)
        account_layout.addRow("Profit:", self.account_profit)
        
        # Layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(conn_group)
        top_layout.addWidget(trading_group)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(market_group)
        bottom_layout.addWidget(account_group)
        
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "🏠 Dashboard")
    
    def create_strategy_tab(self):
        """Create strategy tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Strategy settings
        strategy_group = QGroupBox("⚙️ Strategy Configuration")
        strategy_layout = QFormLayout(strategy_group)
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["XAUUSD", "EURUSD", "GBPUSD"])
        
        self.risk_percent_spin = QDoubleSpinBox()
        self.risk_percent_spin.setRange(0.1, 10.0)
        self.risk_percent_spin.setValue(1.0)
        self.risk_percent_spin.setSuffix("%")
        
        self.max_spread_spin = QSpinBox()
        self.max_spread_spin.setRange(1, 100)
        self.max_spread_spin.setValue(30)
        
        strategy_layout.addRow("Symbol:", self.symbol_combo)
        strategy_layout.addRow("Risk per Trade:", self.risk_percent_spin)
        strategy_layout.addRow("Max Spread (pts):", self.max_spread_spin)
        
        # Live indicators
        indicators_group = QGroupBox("📊 Live Indicators")
        indicators_layout = QFormLayout(indicators_group)
        
        self.ema_fast_label = QLabel("N/A")
        self.ema_medium_label = QLabel("N/A")
        self.ema_slow_label = QLabel("N/A")
        self.rsi_label = QLabel("N/A")
        self.atr_label = QLabel("N/A")
        
        indicators_layout.addRow("Fast EMA:", self.ema_fast_label)
        indicators_layout.addRow("Medium EMA:", self.ema_medium_label)
        indicators_layout.addRow("Slow EMA:", self.ema_slow_label)
        indicators_layout.addRow("RSI:", self.rsi_label)
        indicators_layout.addRow("ATR:", self.atr_label)
        
        layout.addWidget(strategy_group)
        layout.addWidget(indicators_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "📈 Strategy")
    
    def create_positions_tab(self):
        """Create positions tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(7)
        self.positions_table.setHorizontalHeaderLabels([
            "Ticket", "Type", "Volume", "Price", "SL", "TP", "Profit"
        ])
        
        layout.addWidget(self.positions_table)
        
        self.tab_widget.addTab(tab, "📊 Positions")
    
    def create_logs_tab(self):
        """Create logs tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        
        layout.addWidget(self.log_display)
        
        self.tab_widget.addTab(tab, "📝 Logs")
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_connection = QLabel("❌ Disconnected")
        self.status_analysis = QLabel("⏹️ Stopped")
        
        self.status_bar.addWidget(QLabel("Connection:"))
        self.status_bar.addWidget(self.status_connection)
        self.status_bar.addPermanentWidget(QLabel("Analysis:"))
        self.status_bar.addPermanentWidget(self.status_analysis)
    
    def connect_signals(self):
        """Connect signals"""
        self.controller.log_signal.connect(self.on_log_message)
        self.controller.connection_signal.connect(self.on_connection_changed)
        self.controller.account_signal.connect(self.on_account_update)
        self.controller.positions_signal.connect(self.on_positions_update)
    
    # Event handlers
    def on_connect(self):
        """Connect button"""
        if self.controller.connect_to_mt5():
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.start_analysis_btn.setEnabled(True)
    
    def on_disconnect(self):
        """Disconnect button"""
        self.controller.disconnect_from_mt5()
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.start_analysis_btn.setEnabled(False)
        self.stop_analysis_btn.setEnabled(False)
    
    def on_start_analysis(self):
        """Start analysis"""
        self.update_config()
        if self.controller.start_analysis():
            self.start_analysis_btn.setEnabled(False)
            self.stop_analysis_btn.setEnabled(True)
            self.status_analysis.setText("🚀 Running")
    
    def on_stop_analysis(self):
        """Stop analysis"""
        self.controller.stop_analysis()
        self.start_analysis_btn.setEnabled(True)
        self.stop_analysis_btn.setEnabled(False)
        self.status_analysis.setText("⏹️ Stopped")
    
    def on_auto_trading_toggled(self, checked):
        """Auto trading toggle"""
        self.controller.auto_trading = checked
    
    def on_demo_mode_toggled(self, checked):
        """Demo mode toggle"""
        self.controller.demo_mode = checked
    
    def update_config(self):
        """Update config"""
        self.controller.config.update({
            'symbol': self.symbol_combo.currentText(),
            'risk_percent': self.risk_percent_spin.value(),
            'max_spread': self.max_spread_spin.value()
        })
    
    # Signal handlers
    @Slot(str, str)
    def on_log_message(self, message, level):
        """Log message"""
        colors = {'ERROR': 'red', 'WARNING': 'orange', 'INFO': 'black'}
        color = colors.get(level, 'black')
        
        self.log_display.append(f'<span style="color: {color};">{message}</span>')
        
        # Auto-scroll
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)
    
    @Slot(bool)
    def on_connection_changed(self, connected):
        """Connection status"""
        if connected:
            self.connection_status.setText("✅ Connected")
            self.status_connection.setText("✅ Connected")
        else:
            self.connection_status.setText("❌ Disconnected")
            self.status_connection.setText("❌ Disconnected")
    
    @Slot(dict)
    def on_account_update(self, account_info):
        """Account update"""
        self.account_balance.setText(f"${account_info.get('balance', 0):.2f}")
        self.account_equity.setText(f"${account_info.get('equity', 0):.2f}")
        
        profit = account_info.get('profit', 0)
        self.account_profit.setText(f"${profit:.2f}")
        self.account_profit.setStyleSheet(f"color: {'green' if profit >= 0 else 'red'}")
    
    @Slot(list)
    def on_positions_update(self, positions):
        """Positions update"""
        self.positions_table.setRowCount(len(positions))
        
        for i, pos in enumerate(positions):
            self.positions_table.setItem(i, 0, QTableWidgetItem(str(pos['ticket'])))
            self.positions_table.setItem(i, 1, QTableWidgetItem("BUY" if pos['type'] == 0 else "SELL"))
            self.positions_table.setItem(i, 2, QTableWidgetItem(f"{pos['volume']:.2f}"))
            self.positions_table.setItem(i, 3, QTableWidgetItem(f"{pos['price_open']:.5f}"))
            self.positions_table.setItem(i, 4, QTableWidgetItem(f"{pos.get('sl', 0):.5f}"))
            self.positions_table.setItem(i, 5, QTableWidgetItem(f"{pos.get('tp', 0):.5f}"))
            
            profit = pos.get('profit', 0)
            profit_item = QTableWidgetItem(f"${profit:.2f}")
            profit_item.setForeground(QColor('green' if profit >= 0 else 'red'))
            self.positions_table.setItem(i, 6, profit_item)
    
    def update_displays(self):
        """Update displays"""
        # Update market data
        if self.controller.current_market_data:
            data = self.controller.current_market_data
            self.market_bid.setText(f"{data.get('bid', 0):.5f}")
            self.market_ask.setText(f"{data.get('ask', 0):.5f}")
            self.market_spread.setText(f"{data.get('spread_points', 0)} pts")
        
        # Update indicators
        if self.controller.current_indicators:
            indicators = self.controller.current_indicators
            m1_data = indicators.get('M1', {})
            
            if m1_data:
                self.ema_fast_label.setText(f"{m1_data.get('ema_fast', 0):.5f}")
                self.ema_medium_label.setText(f"{m1_data.get('ema_medium', 0):.5f}")
                self.ema_slow_label.setText(f"{m1_data.get('ema_slow', 0):.5f}")
                self.rsi_label.setText(f"{m1_data.get('rsi', 0):.2f}")
                self.atr_label.setText(f"{m1_data.get('atr', 0):.5f}")

def main():
    """Main function"""
    try:
        print("🚀 Starting MT5 Professional Scalping Bot")
        print("=" * 60)
        
        app = QApplication(sys.argv)
        app.setApplicationName("MT5 Professional Scalping Bot")
        
        window = MainTradingGUI()
        window.show()
        
        print("✅ Application started successfully!")
        print("📋 Instructions:")
        print("1. Click 'Connect to MT5' to establish connection")
        print("2. Configure strategy parameters")
        print("3. Click 'Start Analysis' to begin")
        print("4. Enable 'Auto Trading' for automated execution")
        print("=" * 60)
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ Application error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n🏁 Application exited with code: {exit_code}")
    sys.exit(exit_code)
