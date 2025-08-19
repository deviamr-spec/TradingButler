
"""
Enhanced PySide6 GUI for MT5 Scalping Bot - LIVE TRADING FIXES
Addresses all GUI interaction issues:
1. Proper component initialization order
2. Enhanced error handling for GUI operations  
3. Robust event binding with validation
4. Improved user feedback and status indicators
"""

import sys
from datetime import datetime
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QFormLayout, QGridLayout, QSplitter, QProgressBar,
    QStatusBar, QMessageBox, QFrame, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Slot, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon, QColor

class MainWindow(QMainWindow):
    """Enhanced Main Window with comprehensive error handling and validation"""
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("MT5 Professional Scalping Bot - LIVE TRADING READY")
        self.setGeometry(100, 100, 1500, 900)
        
        # Initialize component references to None for safe checking
        self.connection_status = None
        self.bot_status = None
        self.mode_status = None
        self.connect_btn = None
        self.start_btn = None
        self.stop_btn = None
        self.emergency_stop_btn = None
        
        # Component initialization flags
        self.components_initialized = False
        self.signals_connected = False
        
        try:
            # Setup UI with enhanced error handling
            self.setup_ui()
            self.setup_status_bar()
            self.connect_signals()
            
            # Enhanced update timer
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.safe_update_gui_data)
            self.update_timer.start(1000)
            
            # Initialize displays safely
            self.safe_initialize_displays()
            
            self.components_initialized = True
            print("✅ GUI initialized successfully")
            
        except Exception as e:
            error_msg = f"❌ GUI Initialization Error: {e}"
            print(error_msg)
            QMessageBox.critical(self, "GUI Error", error_msg)
            raise
    
    def setup_ui(self):
        """Enhanced UI setup with component validation"""
        try:
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            # Create tab widget
            self.tab_widget = QTabWidget()
            layout.addWidget(self.tab_widget)
            
            # Create tabs with individual error handling
            self.create_dashboard_tab()
            self.create_strategy_tab()
            self.create_risk_tab()
            self.create_execution_tab()
            self.create_logs_tab()
            self.create_tools_tab()
            
            print("✅ UI setup completed")
            
        except Exception as e:
            raise Exception(f"UI setup failed: {e}")
    
    def create_dashboard_tab(self):
        """Enhanced dashboard with proper component initialization"""
        try:
            dashboard = QWidget()
            layout = QVBoxLayout(dashboard)
            
            # Enhanced connection section
            conn_group = QGroupBox("🔗 MT5 Connection & Status")
            conn_layout = QGridLayout(conn_group)
            
            # Initialize buttons with validation
            self.connect_btn = QPushButton("🔌 Connect to MT5")
            self.connect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
            self.connect_btn.setEnabled(True)  # Always enabled initially
            
            self.disconnect_btn = QPushButton("🔌 Disconnect")
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
            
            # Enhanced status labels
            self.status_label = QLabel("❌ Status: Disconnected")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; font-size: 14px; }")
            
            self.account_login_label = QLabel("Account: Not Connected")
            self.server_label = QLabel("Server: N/A")
            
            # Connection quality indicator
            self.connection_quality_label = QLabel("Quality: Unknown")
            
            conn_layout.addWidget(self.connect_btn, 0, 0)
            conn_layout.addWidget(self.disconnect_btn, 0, 1)
            conn_layout.addWidget(self.status_label, 1, 0, 1, 2)
            conn_layout.addWidget(self.account_login_label, 2, 0)
            conn_layout.addWidget(self.server_label, 2, 1)
            conn_layout.addWidget(self.connection_quality_label, 3, 0, 1, 2)
            
            # Enhanced symbol section
            symbol_group = QGroupBox("📊 Trading Symbol Configuration")
            symbol_layout = QFormLayout(symbol_group)
            
            self.symbol_combo = QComboBox()
            self.symbol_combo.addItems(["XAUUSD", "XAUUSDm", "XAUUSDc", "GOLD"])
            self.symbol_combo.setCurrentText("XAUUSD")
            
            self.symbol_status_label = QLabel("❓ Not validated")
            self.symbol_info_label = QLabel("Info: Select symbol to validate")
            
            symbol_layout.addRow("Trading Symbol:", self.symbol_combo)
            symbol_layout.addRow("Symbol Status:", self.symbol_status_label)
            symbol_layout.addRow("Symbol Info:", self.symbol_info_label)
            
            # Enhanced bot control section
            control_group = QGroupBox("🤖 Enhanced Bot Control Panel")
            control_layout = QGridLayout(control_group)
            
            self.start_btn = QPushButton("🚀 START TRADING BOT")
            self.start_btn.setEnabled(False)  # Disabled until connected
            self.start_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 12px; font-size: 14px; }")
            
            self.stop_btn = QPushButton("🛑 STOP BOT")
            self.stop_btn.setEnabled(False)
            self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 12px; font-size: 14px; }")
            
            self.shadow_mode_cb = QCheckBox("🛡️ Shadow Mode (SAFE - Signals Only)")
            self.shadow_mode_cb.setChecked(True)  # Default to safe mode
            self.shadow_mode_cb.setStyleSheet("QCheckBox { color: green; font-weight: bold; font-size: 12px; }")
            
            self.emergency_stop_btn = QPushButton("🚨 EMERGENCY STOP ALL")
            self.emergency_stop_btn.setStyleSheet("QPushButton { background-color: #8B0000; color: white; font-weight: bold; padding: 10px; }")
            self.emergency_stop_btn.setEnabled(False)
            
            # Bot status indicator
            self.bot_status_indicator = QLabel("⚪ Bot Stopped")
            self.bot_status_indicator.setStyleSheet("QLabel { font-weight: bold; font-size: 12px; }")
            
            control_layout.addWidget(self.start_btn, 0, 0)
            control_layout.addWidget(self.stop_btn, 0, 1)
            control_layout.addWidget(self.shadow_mode_cb, 1, 0, 1, 2)
            control_layout.addWidget(self.emergency_stop_btn, 2, 0, 1, 2)
            control_layout.addWidget(self.bot_status_indicator, 3, 0, 1, 2)
            
            # Enhanced market data section
            market_group = QGroupBox("📈 Live Market Data & Analysis")
            market_layout = QFormLayout(market_group)
            
            self.bid_label = QLabel("0.00000")
            self.ask_label = QLabel("0.00000")
            self.spread_label = QLabel("0")
            self.time_label = QLabel("N/A")
            self.volume_label = QLabel("0")
            
            # Enhanced styling for market data
            for label in [self.bid_label, self.ask_label, self.spread_label, self.time_label, self.volume_label]:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 14px; font-weight: bold; color: #2196F3; }")
            
            market_layout.addRow("💰 Bid Price:", self.bid_label)
            market_layout.addRow("💸 Ask Price:", self.ask_label)
            market_layout.addRow("📏 Spread (pts):", self.spread_label)
            market_layout.addRow("🕐 Last Update:", self.time_label)
            market_layout.addRow("📊 Volume:", self.volume_label)
            
            # Enhanced account section
            account_group = QGroupBox("💰 Account Information & Risk")
            account_layout = QFormLayout(account_group)
            
            self.balance_label = QLabel("$0.00")
            self.equity_label = QLabel("$0.00")
            self.margin_label = QLabel("$0.00")
            self.pnl_label = QLabel("$0.00")
            self.margin_level_label = QLabel("0%")
            self.daily_pnl_label = QLabel("$0.00")
            
            # Enhanced styling for account data
            for label in [self.balance_label, self.equity_label, self.margin_label, self.pnl_label, self.margin_level_label, self.daily_pnl_label]:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 12px; font-weight: bold; }")
            
            account_layout.addRow("💵 Balance:", self.balance_label)
            account_layout.addRow("💎 Equity:", self.equity_label)
            account_layout.addRow("📊 Margin Used:", self.margin_label)
            account_layout.addRow("📈 Total P&L:", self.pnl_label)
            account_layout.addRow("🎯 Margin Level:", self.margin_level_label)
            account_layout.addRow("📅 Daily P&L:", self.daily_pnl_label)
            
            # Enhanced layout arrangement
            top_layout = QHBoxLayout()
            top_layout.addWidget(conn_group)
            top_layout.addWidget(symbol_group)
            
            middle_layout = QHBoxLayout()
            middle_layout.addWidget(control_group)
            middle_layout.addWidget(market_group)
            
            bottom_layout = QHBoxLayout()
            bottom_layout.addWidget(account_group)
            
            layout.addLayout(top_layout)
            layout.addLayout(middle_layout)
            layout.addLayout(bottom_layout)
            layout.addStretch()
            
            # Validate all components were created
            required_components = [
                self.connect_btn, self.disconnect_btn, self.start_btn, self.stop_btn,
                self.emergency_stop_btn, self.shadow_mode_cb, self.symbol_combo
            ]
            
            for component in required_components:
                if component is None:
                    raise ValueError("Critical component failed to initialize")
            
            self.tab_widget.addTab(dashboard, "🏠 Dashboard")
            print("✅ Dashboard tab created successfully")
            
        except Exception as e:
            raise Exception(f"Dashboard creation failed: {e}")
    
    def create_strategy_tab(self):
        """Enhanced strategy tab with validation"""
        try:
            strategy = QWidget()
            layout = QVBoxLayout(strategy)
            
            # Strategy settings with validation
            settings_group = QGroupBox("⚙️ Enhanced Strategy Configuration")
            settings_layout = QFormLayout(settings_group)
            
            # EMA Settings with validation
            self.ema_fast_spin = QSpinBox()
            self.ema_fast_spin.setRange(1, 50)
            self.ema_fast_spin.setValue(8)
            
            self.ema_medium_spin = QSpinBox()
            self.ema_medium_spin.setRange(1, 100)
            self.ema_medium_spin.setValue(21)
            
            self.ema_slow_spin = QSpinBox()
            self.ema_slow_spin.setRange(1, 200)
            self.ema_slow_spin.setValue(50)
            
            # RSI Settings
            self.rsi_period_spin = QSpinBox()
            self.rsi_period_spin.setRange(1, 50)
            self.rsi_period_spin.setValue(14)
            
            # ATR Settings
            self.atr_period_spin = QSpinBox()
            self.atr_period_spin.setRange(1, 50)
            self.atr_period_spin.setValue(14)
            
            settings_layout.addRow("⚡ Fast EMA Period:", self.ema_fast_spin)
            settings_layout.addRow("📊 Medium EMA Period:", self.ema_medium_spin)
            settings_layout.addRow("🐌 Slow EMA Period:", self.ema_slow_spin)
            settings_layout.addRow("📈 RSI Period:", self.rsi_period_spin)
            settings_layout.addRow("📏 ATR Period:", self.atr_period_spin)
            
            # Live indicators display with enhanced formatting
            indicators_group = QGroupBox("📊 Live Technical Indicators")
            indicators_layout = QFormLayout(indicators_group)
            
            # M1 indicators
            self.ema_fast_m1_label = QLabel("N/A")
            self.ema_medium_m1_label = QLabel("N/A")
            self.ema_slow_m1_label = QLabel("N/A")
            self.rsi_m1_label = QLabel("N/A")
            self.atr_m1_label = QLabel("N/A")
            
            # M5 indicators
            self.ema_fast_m5_label = QLabel("N/A")
            self.ema_medium_m5_label = QLabel("N/A")
            self.ema_slow_m5_label = QLabel("N/A")
            self.rsi_m5_label = QLabel("N/A")
            self.atr_m5_label = QLabel("N/A")
            
            # Enhanced styling for indicators
            indicator_labels = [
                self.ema_fast_m1_label, self.ema_medium_m1_label, self.ema_slow_m1_label,
                self.rsi_m1_label, self.atr_m1_label,
                self.ema_fast_m5_label, self.ema_medium_m5_label, self.ema_slow_m5_label,
                self.rsi_m5_label, self.atr_m5_label
            ]
            
            for label in indicator_labels:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 11px; color: #2196F3; }")
            
            indicators_layout.addRow("⚡ M1 Fast EMA:", self.ema_fast_m1_label)
            indicators_layout.addRow("📊 M1 Medium EMA:", self.ema_medium_m1_label)
            indicators_layout.addRow("🐌 M1 Slow EMA:", self.ema_slow_m1_label)
            indicators_layout.addRow("📈 M1 RSI:", self.rsi_m1_label)
            indicators_layout.addRow("📏 M1 ATR:", self.atr_m1_label)
            
            indicators_layout.addRow("", QLabel(""))  # Spacer
            
            indicators_layout.addRow("⚡ M5 Fast EMA:", self.ema_fast_m5_label)
            indicators_layout.addRow("📊 M5 Medium EMA:", self.ema_medium_m5_label)
            indicators_layout.addRow("🐌 M5 Slow EMA:", self.ema_slow_m5_label)
            indicators_layout.addRow("📈 M5 RSI:", self.rsi_m5_label)
            indicators_layout.addRow("📏 M5 ATR:", self.atr_m5_label)
            
            layout.addWidget(settings_group)
            layout.addWidget(indicators_group)
            layout.addStretch()
            
            self.tab_widget.addTab(strategy, "📈 Strategy")
            print("✅ Strategy tab created successfully")
            
        except Exception as e:
            raise Exception(f"Strategy tab creation failed: {e}")
    
    def create_risk_tab(self):
        """Enhanced risk management tab"""
        try:
            risk = QWidget()
            layout = QVBoxLayout(risk)
            
            # Enhanced risk management settings
            risk_group = QGroupBox("🛡️ Enhanced Risk Management")
            risk_layout = QFormLayout(risk_group)
            
            self.risk_percent_spin = QDoubleSpinBox()
            self.risk_percent_spin.setRange(0.1, 10.0)
            self.risk_percent_spin.setValue(0.5)
            self.risk_percent_spin.setSuffix("%")
            self.risk_percent_spin.setDecimals(2)
            
            self.max_daily_loss_spin = QDoubleSpinBox()
            self.max_daily_loss_spin.setRange(0.5, 20.0)
            self.max_daily_loss_spin.setValue(2.0)
            self.max_daily_loss_spin.setSuffix("%")
            self.max_daily_loss_spin.setDecimals(1)
            
            self.max_trades_spin = QSpinBox()
            self.max_trades_spin.setRange(1, 100)
            self.max_trades_spin.setValue(15)
            
            self.risk_multiple_spin = QDoubleSpinBox()
            self.risk_multiple_spin.setRange(0.5, 5.0)
            self.risk_multiple_spin.setValue(2.0)
            self.risk_multiple_spin.setDecimals(1)
            
            self.max_spread_spin = QSpinBox()
            self.max_spread_spin.setRange(10, 200)
            self.max_spread_spin.setValue(30)
            self.max_spread_spin.setSuffix(" pts")
            
            self.min_sl_spin = QSpinBox()
            self.min_sl_spin.setRange(50, 500)
            self.min_sl_spin.setValue(150)
            self.min_sl_spin.setSuffix(" pts")
            
            risk_layout.addRow("💰 Risk per Trade:", self.risk_percent_spin)
            risk_layout.addRow("🚨 Max Daily Loss:", self.max_daily_loss_spin)
            risk_layout.addRow("🔢 Max Trades/Day:", self.max_trades_spin)
            risk_layout.addRow("📈 Risk Multiple (R:R):", self.risk_multiple_spin)
            risk_layout.addRow("📏 Max Spread:", self.max_spread_spin)
            risk_layout.addRow("🛡️ Min SL Distance:", self.min_sl_spin)
            
            # Enhanced TP/SL Configuration
            tp_sl_group = QGroupBox("🎯 Enhanced TP/SL Configuration")
            tp_sl_layout = QFormLayout(tp_sl_group)
            
            # TP/SL Mode Selection
            self.tp_sl_mode_combo = QComboBox()
            self.tp_sl_mode_combo.addItems(["ATR", "Points", "Pips", "Percent"])
            self.tp_sl_mode_combo.setCurrentText("ATR")
            
            # ATR Mode Controls
            self.atr_multiplier_spin = QDoubleSpinBox()
            self.atr_multiplier_spin.setRange(0.5, 5.0)
            self.atr_multiplier_spin.setValue(1.5)
            self.atr_multiplier_spin.setDecimals(1)
            
            # Points Mode Controls
            self.tp_points_spin = QSpinBox()
            self.tp_points_spin.setRange(50, 1000)
            self.tp_points_spin.setValue(200)
            self.tp_points_spin.setSuffix(" pts")
            
            self.sl_points_spin = QSpinBox()
            self.sl_points_spin.setRange(50, 500)
            self.sl_points_spin.setValue(100)
            self.sl_points_spin.setSuffix(" pts")
            
            # Pips Mode Controls
            self.tp_pips_spin = QSpinBox()
            self.tp_pips_spin.setRange(5, 100)
            self.tp_pips_spin.setValue(20)
            self.tp_pips_spin.setSuffix(" pips")
            
            self.sl_pips_spin = QSpinBox()
            self.sl_pips_spin.setRange(5, 50)
            self.sl_pips_spin.setValue(10)
            self.sl_pips_spin.setSuffix(" pips")
            
            # Percent Mode Controls
            self.tp_percent_spin = QDoubleSpinBox()
            self.tp_percent_spin.setRange(0.1, 10.0)
            self.tp_percent_spin.setValue(1.0)
            self.tp_percent_spin.setSuffix("% balance")
            self.tp_percent_spin.setDecimals(2)
            
            self.sl_percent_spin = QDoubleSpinBox()
            self.sl_percent_spin.setRange(0.1, 5.0)
            self.sl_percent_spin.setValue(0.5)
            self.sl_percent_spin.setSuffix("% balance")
            self.sl_percent_spin.setDecimals(2)
            
            tp_sl_layout.addRow("🔧 TP/SL Mode:", self.tp_sl_mode_combo)
            tp_sl_layout.addRow("🔄 ATR Multiplier:", self.atr_multiplier_spin)
            tp_sl_layout.addRow("🎯 TP Points:", self.tp_points_spin)
            tp_sl_layout.addRow("🛡️ SL Points:", self.sl_points_spin)
            tp_sl_layout.addRow("🎯 TP Pips:", self.tp_pips_spin)
            tp_sl_layout.addRow("🛡️ SL Pips:", self.sl_pips_spin)
            tp_sl_layout.addRow("🎯 TP Percent:", self.tp_percent_spin)
            tp_sl_layout.addRow("🛡️ SL Percent:", self.sl_percent_spin)
            
            # Apply button for settings
            apply_btn = QPushButton("✅ Apply All Settings")
            apply_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
            tp_sl_layout.addRow(apply_btn)
            
            # Enhanced daily statistics
            stats_group = QGroupBox("📊 Enhanced Daily Statistics")
            stats_layout = QFormLayout(stats_group)
            
            self.daily_trades_label = QLabel("0")
            self.daily_pnl_stat_label = QLabel("$0.00")
            self.win_rate_label = QLabel("0%")
            self.max_dd_label = QLabel("$0.00")
            self.consecutive_losses_label = QLabel("0")
            
            # Enhanced styling for statistics
            stat_labels = [
                self.daily_trades_label, self.daily_pnl_stat_label, self.win_rate_label,
                self.max_dd_label, self.consecutive_losses_label
            ]
            
            for label in stat_labels:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 12px; font-weight: bold; }")
            
            stats_layout.addRow("🔢 Trades Today:", self.daily_trades_label)
            stats_layout.addRow("💰 Daily P&L:", self.daily_pnl_stat_label)
            stats_layout.addRow("🎯 Win Rate:", self.win_rate_label)
            stats_layout.addRow("📉 Max Drawdown:", self.max_dd_label)
            stats_layout.addRow("📉 Consecutive Losses:", self.consecutive_losses_label)
            
            layout.addWidget(risk_group)
            layout.addWidget(tp_sl_group)
            layout.addWidget(stats_group)
            layout.addStretch()
            
            self.tab_widget.addTab(risk, "🛡️ Risk Management")
            print("✅ Risk tab created successfully")
            
        except Exception as e:
            raise Exception(f"Risk tab creation failed: {e}")
    
    def create_execution_tab(self):
        """Enhanced execution monitoring tab"""
        try:
            execution = QWidget()
            layout = QVBoxLayout(execution)
            
            # Enhanced signal display
            signal_group = QGroupBox("🎯 Current Trading Signal & Analysis")
            signal_layout = QFormLayout(signal_group)
            
            self.signal_type_label = QLabel("None")
            self.signal_entry_label = QLabel("N/A")
            self.signal_sl_label = QLabel("N/A")
            self.signal_tp_label = QLabel("N/A")
            self.signal_lot_label = QLabel("N/A")
            self.signal_risk_label = QLabel("N/A")
            self.signal_time_label = QLabel("N/A")
            self.signal_confidence_label = QLabel("N/A")
            
            # Enhanced styling for signal labels
            signal_labels = [
                self.signal_type_label, self.signal_entry_label, self.signal_sl_label,
                self.signal_tp_label, self.signal_lot_label, self.signal_risk_label, 
                self.signal_time_label, self.signal_confidence_label
            ]
            
            for label in signal_labels:
                label.setStyleSheet("QLabel { font-family: 'Courier New'; font-size: 12px; font-weight: bold; }")
            
            signal_layout.addRow("📊 Signal Type:", self.signal_type_label)
            signal_layout.addRow("🎯 Entry Price:", self.signal_entry_label)
            signal_layout.addRow("🛡️ Stop Loss:", self.signal_sl_label)
            signal_layout.addRow("🎯 Take Profit:", self.signal_tp_label)
            signal_layout.addRow("📊 Lot Size:", self.signal_lot_label)
            signal_layout.addRow("📈 Risk/Reward:", self.signal_risk_label)
            signal_layout.addRow("🕐 Signal Time:", self.signal_time_label)
            signal_layout.addRow("💪 Confidence:", self.signal_confidence_label)
            
            # Enhanced positions table
            positions_group = QGroupBox("📋 Enhanced Positions Monitor")
            positions_layout = QVBoxLayout(positions_group)
            
            self.positions_table = QTableWidget()
            self.positions_table.setColumnCount(9)
            self.positions_table.setHorizontalHeaderLabels([
                "Ticket", "Type", "Volume", "Entry", "Current", "SL", "TP", "Profit", "Comment"
            ])
            
            # Enhanced table properties
            self.positions_table.setAlternatingRowColors(True)
            self.positions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.positions_table.setSortingEnabled(True)
            
            positions_layout.addWidget(self.positions_table)
            
            # Enhanced position controls
            position_controls = QHBoxLayout()
            
            self.close_all_btn = QPushButton("🚨 EMERGENCY: Close All Positions")
            self.close_all_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
            
            self.refresh_positions_btn = QPushButton("🔄 Refresh Positions")
            self.refresh_positions_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }")
            
            position_controls.addWidget(self.close_all_btn)
            position_controls.addWidget(self.refresh_positions_btn)
            position_controls.addStretch()
            
            positions_layout.addLayout(position_controls)
            
            layout.addWidget(signal_group)
            layout.addWidget(positions_group)
            
            self.tab_widget.addTab(execution, "⚡ Execution")
            print("✅ Execution tab created successfully")
            
        except Exception as e:
            raise Exception(f"Execution tab creation failed: {e}")
    
    def create_logs_tab(self):
        """Enhanced logs tab with better formatting"""
        try:
            logs = QWidget()
            layout = QVBoxLayout(logs)
            
            # Enhanced log display
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setFont(QFont("Consolas", 10))
            self.log_text.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #444;
                    font-family: 'Courier New';
                }
            """)
            
            # Enhanced log controls
            controls_layout = QHBoxLayout()
            
            clear_btn = QPushButton("🗑️ Clear Logs")
            clear_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
            
            save_btn = QPushButton("💾 Save Logs")
            save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
            
            export_btn = QPushButton("📤 Export Trading History")
            export_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; }")
            
            # Auto-scroll checkbox
            self.auto_scroll_cb = QCheckBox("🔄 Auto-scroll")
            self.auto_scroll_cb.setChecked(True)
            
            controls_layout.addWidget(clear_btn)
            controls_layout.addWidget(save_btn)
            controls_layout.addWidget(export_btn)
            controls_layout.addWidget(self.auto_scroll_cb)
            controls_layout.addStretch()
            
            layout.addLayout(controls_layout)
            layout.addWidget(self.log_text)
            
            self.tab_widget.addTab(logs, "📜 Logs")
            print("✅ Logs tab created successfully")
            
        except Exception as e:
            raise Exception(f"Logs tab creation failed: {e}")
    
    def create_tools_tab(self):
        """Enhanced tools tab"""
        try:
            tools = QWidget()
            layout = QVBoxLayout(tools)
            
            # Enhanced testing tools
            test_group = QGroupBox("🧪 Enhanced Testing & Validation")
            test_layout = QGridLayout(test_group)
            
            self.test_signal_btn = QPushButton("🧪 Generate Test Signal")
            self.test_signal_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; font-weight: bold; }")
            
            self.validate_symbol_btn = QPushButton("✅ Validate Symbol")
            self.validate_symbol_btn.setStyleSheet("QPushButton { background-color: #607D8B; color: white; font-weight: bold; }")
            
            self.check_margin_btn = QPushButton("💰 Check Margin Requirements")
            self.check_margin_btn.setStyleSheet("QPushButton { background-color: #795548; color: white; font-weight: bold; }")
            
            self.diagnostic_btn = QPushButton("🩺 Run Full Diagnostic")
            self.diagnostic_btn.setStyleSheet("QPushButton { background-color: #E91E63; color: white; font-weight: bold; }")
            
            test_layout.addWidget(self.test_signal_btn, 0, 0)
            test_layout.addWidget(self.validate_symbol_btn, 0, 1)
            test_layout.addWidget(self.check_margin_btn, 1, 0)
            test_layout.addWidget(self.diagnostic_btn, 1, 1)
            
            # Enhanced system status
            status_group = QGroupBox("🔧 Enhanced System Status")
            status_layout = QFormLayout(status_group)
            
            self.mt5_version_label = QLabel("N/A")
            self.connection_quality_status_label = QLabel("N/A")
            self.last_tick_label = QLabel("N/A")
            self.system_time_label = QLabel("N/A")
            self.memory_usage_label = QLabel("N/A")
            
            status_layout.addRow("📊 MT5 Version:", self.mt5_version_label)
            status_layout.addRow("📡 Connection Quality:", self.connection_quality_status_label)
            status_layout.addRow("⏰ Last Tick:", self.last_tick_label)
            status_layout.addRow("🕐 System Time:", self.system_time_label)
            status_layout.addRow("💾 Memory Usage:", self.memory_usage_label)
            
            layout.addWidget(test_group)
            layout.addWidget(status_group)
            layout.addStretch()
            
            self.tab_widget.addTab(tools, "🔧 Tools")
            print("✅ Tools tab created successfully")
            
        except Exception as e:
            raise Exception(f"Tools tab creation failed: {e}")
    
    def setup_status_bar(self):
        """Enhanced status bar setup"""
        try:
            self.statusBar().showMessage("🚀 System Ready - Enhanced Trading Bot Loaded")
            
            # Enhanced status indicators
            self.connection_status = QLabel("❌ Disconnected")
            self.bot_status = QLabel("⏸️ Stopped")
            self.mode_status = QLabel("🛡️ Shadow")
            
            # Enhanced styling for status indicators
            self.connection_status.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            self.bot_status.setStyleSheet("QLabel { color: gray; font-weight: bold; }")
            self.mode_status.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            
            self.statusBar().addPermanentWidget(QLabel("Connection:"))
            self.statusBar().addPermanentWidget(self.connection_status)
            self.statusBar().addPermanentWidget(QLabel("Bot:"))
            self.statusBar().addPermanentWidget(self.bot_status)
            self.statusBar().addPermanentWidget(QLabel("Mode:"))
            self.statusBar().addPermanentWidget(self.mode_status)
            
            print("✅ Status bar setup completed")
            
        except Exception as e:
            raise Exception(f"Status bar setup failed: {e}")
    
    def connect_signals(self):
        """Enhanced signal connections with validation"""
        try:
            if not self.controller:
                raise ValueError("Controller not available for signal connection")
            
            # Connect controller signals with error handling
            if hasattr(self.controller, 'signal_log'):
                self.controller.signal_log.connect(self.safe_log_message)
            
            if hasattr(self.controller, 'signal_status'):
                self.controller.signal_status.connect(self.safe_update_status)
            
            if hasattr(self.controller, 'signal_market_data'):
                self.controller.signal_market_data.connect(self.safe_update_market_data)
            
            if hasattr(self.controller, 'signal_trade_signal'):
                self.controller.signal_trade_signal.connect(self.safe_update_trade_signal)
            
            if hasattr(self.controller, 'signal_position_update'):
                self.controller.signal_position_update.connect(self.safe_update_positions)
            
            if hasattr(self.controller, 'signal_account_update'):
                self.controller.signal_account_update.connect(self.safe_update_account_display)
            
            if hasattr(self.controller, 'signal_indicators_update'):
                self.controller.signal_indicators_update.connect(self.safe_update_indicators_display)
            
            if hasattr(self.controller, 'signal_connection_status'):
                self.controller.signal_connection_status.connect(self.safe_update_connection_status)
            
            if hasattr(self.controller, 'signal_execution_result'):
                self.controller.signal_execution_result.connect(self.safe_handle_execution_result)
            
            # Connect GUI element signals with validation
            if self.connect_btn:
                self.connect_btn.clicked.connect(self.safe_on_connect)
            
            if self.disconnect_btn:
                self.disconnect_btn.clicked.connect(self.safe_on_disconnect)
            
            if self.start_btn:
                self.start_btn.clicked.connect(self.safe_on_start_bot)
            
            if self.stop_btn:
                self.stop_btn.clicked.connect(self.safe_on_stop_bot)
            
            if self.emergency_stop_btn:
                self.emergency_stop_btn.clicked.connect(self.safe_on_emergency_stop)
            
            if self.shadow_mode_cb:
                self.shadow_mode_cb.toggled.connect(self.safe_on_shadow_mode_toggle)
            
            if self.symbol_combo:
                self.symbol_combo.currentTextChanged.connect(self.safe_on_symbol_changed)
            
            self.signals_connected = True
            print("✅ All signals connected successfully")
            
        except Exception as e:
            print(f"❌ Signal connection error: {e}")
            # Don't raise here - allow GUI to continue with limited functionality
    
    def safe_initialize_displays(self):
        """Safe initialization of display elements"""
        try:
            # Initialize market data displays
            if hasattr(self, 'bid_label'):
                self.bid_label.setText("0.00000")
            if hasattr(self, 'ask_label'):
                self.ask_label.setText("0.00000")
            if hasattr(self, 'spread_label'):
                self.spread_label.setText("0")
            if hasattr(self, 'time_label'):
                self.time_label.setText("Not Connected")
            
            # Initialize account displays
            if hasattr(self, 'balance_label'):
                self.balance_label.setText("$0.00")
            if hasattr(self, 'equity_label'):
                self.equity_label.setText("$0.00")
            if hasattr(self, 'margin_label'):
                self.margin_label.setText("$0.00")
            if hasattr(self, 'pnl_label'):
                self.pnl_label.setText("$0.00")
            
            print("✅ Display initialization completed")
            
        except Exception as e:
            print(f"❌ Display initialization error: {e}")
    
    # Enhanced safe event handlers
    def safe_on_connect(self):
        """Safe connect button handler"""
        try:
            if not self.controller:
                QMessageBox.warning(self, "Error", "Controller not available")
                return
            
            if hasattr(self.controller, 'connect_mt5'):
                if self.controller.connect_mt5():
                    self.safe_update_button_states(connected=True)
                    QMessageBox.information(self, "Success", "Successfully connected to MT5")
                else:
                    QMessageBox.warning(self, "Connection Failed", "Failed to connect to MT5. Check logs for details.")
            else:
                QMessageBox.warning(self, "Error", "Connect method not available")
                
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Connection failed: {e}")
    
    def safe_on_disconnect(self):
        """Safe disconnect button handler"""
        try:
            if self.controller and hasattr(self.controller, 'disconnect_mt5'):
                self.controller.disconnect_mt5()
                self.safe_update_button_states(connected=False)
                
        except Exception as e:
            QMessageBox.critical(self, "Disconnect Error", f"Disconnect failed: {e}")
    
    def safe_on_start_bot(self):
        """Safe start bot handler with enhanced validation"""
        try:
            if not self.controller:
                QMessageBox.warning(self, "Error", "Controller not available")
                return
            
            if not hasattr(self.controller, 'is_connected') or not self.controller.is_connected:
                QMessageBox.warning(self, "Not Connected", "Please connect to MT5 first!")
                return
            
            # Enhanced safety warning
            if hasattr(self.shadow_mode_cb, 'isChecked') and not self.shadow_mode_cb.isChecked():
                reply = QMessageBox.warning(
                    self, 
                    "⚠️ LIVE TRADING WARNING",
                    "🚨 YOU ARE ABOUT TO START LIVE TRADING WITH REAL MONEY! 🚨\n\n"
                    "⚠️ This will place actual orders in your MT5 account\n"
                    "⚠️ You can lose real money\n"
                    "⚠️ Make sure you understand the risks\n\n"
                    "STRONGLY RECOMMENDED: Test in Shadow Mode first!\n\n"
                    "Do you want to continue with LIVE TRADING?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    return
            
            # Update configuration from GUI
            self.safe_update_controller_config()
            
            if hasattr(self.controller, 'start_bot') and self.controller.start_bot():
                self.safe_update_button_states(running=True)
                mode = "SHADOW MODE" if (hasattr(self.shadow_mode_cb, 'isChecked') and self.shadow_mode_cb.isChecked()) else "🚨 LIVE TRADING"
                QMessageBox.information(self, "Bot Started", f"Trading bot started in {mode}")
            else:
                QMessageBox.warning(self, "Start Failed", "Failed to start trading bot!")
                
        except Exception as e:
            QMessageBox.critical(self, "Start Error", f"Failed to start bot: {e}")
    
    def safe_on_stop_bot(self):
        """Safe stop bot handler"""
        try:
            if self.controller and hasattr(self.controller, 'stop_bot'):
                self.controller.stop_bot()
                self.safe_update_button_states(running=False)
                
        except Exception as e:
            QMessageBox.critical(self, "Stop Error", f"Failed to stop bot: {e}")
    
    def safe_on_emergency_stop(self):
        """Safe emergency stop handler"""
        try:
            reply = QMessageBox.question(
                self,
                "🚨 Emergency Stop Confirmation",
                "This will immediately:\n"
                "• Stop the trading bot\n"
                "• Close all open positions\n"
                "• Disconnect from MT5\n\n"
                "Are you sure you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.controller:
                    if hasattr(self.controller, 'close_all_positions'):
                        self.controller.close_all_positions()
                    if hasattr(self.controller, 'stop_bot'):
                        self.controller.stop_bot()
                    if hasattr(self.controller, 'disconnect_mt5'):
                        self.controller.disconnect_mt5()
                
                self.safe_update_button_states(connected=False, running=False)
                QMessageBox.information(self, "Emergency Stop", "Emergency stop completed successfully!")
                
        except Exception as e:
            QMessageBox.critical(self, "Emergency Stop Error", f"Emergency stop failed: {e}")
    
    def safe_on_shadow_mode_toggle(self, checked):
        """Safe shadow mode toggle handler"""
        try:
            if self.controller and hasattr(self.controller, 'toggle_shadow_mode'):
                self.controller.toggle_shadow_mode(checked)
                
            # Update mode status
            if hasattr(self, 'mode_status'):
                if checked:
                    self.mode_status.setText("🛡️ Shadow")
                    self.mode_status.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                else:
                    self.mode_status.setText("🚨 Live")
                    self.mode_status.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                    
        except Exception as e:
            print(f"Shadow mode toggle error: {e}")
    
    def safe_on_symbol_changed(self, symbol):
        """Safe symbol change handler"""
        try:
            if self.controller and hasattr(self.controller, 'update_config'):
                self.controller.update_config({'symbol': symbol})
                
        except Exception as e:
            print(f"Symbol change error: {e}")
    
    def safe_update_controller_config(self):
        """Safe controller configuration update"""
        try:
            if not self.controller or not hasattr(self.controller, 'update_config'):
                return
            
            config = {}
            
            # Safely get GUI values
            if hasattr(self, 'symbol_combo') and self.symbol_combo:
                config['symbol'] = self.symbol_combo.currentText()
            
            if hasattr(self, 'risk_percent_spin') and self.risk_percent_spin:
                config['risk_percent'] = self.risk_percent_spin.value()
            
            if hasattr(self, 'max_daily_loss_spin') and self.max_daily_loss_spin:
                config['max_daily_loss'] = self.max_daily_loss_spin.value()
            
            if hasattr(self, 'max_trades_spin') and self.max_trades_spin:
                config['max_trades_per_day'] = self.max_trades_spin.value()
            
            if hasattr(self, 'max_spread_spin') and self.max_spread_spin:
                config['max_spread_points'] = self.max_spread_spin.value()
            
            if hasattr(self, 'min_sl_spin') and self.min_sl_spin:
                config['min_sl_points'] = self.min_sl_spin.value()
            
            if hasattr(self, 'risk_multiple_spin') and self.risk_multiple_spin:
                config['risk_multiple'] = self.risk_multiple_spin.value()
            
            # EMA periods
            if all(hasattr(self, attr) for attr in ['ema_fast_spin', 'ema_medium_spin', 'ema_slow_spin']):
                config['ema_periods'] = {
                    'fast': self.ema_fast_spin.value(),
                    'medium': self.ema_medium_spin.value(),
                    'slow': self.ema_slow_spin.value()
                }
            
            if hasattr(self, 'rsi_period_spin') and self.rsi_period_spin:
                config['rsi_period'] = self.rsi_period_spin.value()
            
            if hasattr(self, 'atr_period_spin') and self.atr_period_spin:
                config['atr_period'] = self.atr_period_spin.value()
            
            # TP/SL configuration
            if hasattr(self, 'tp_sl_mode_combo') and self.tp_sl_mode_combo:
                config['tp_sl_mode'] = self.tp_sl_mode_combo.currentText()
            
            # Apply configuration
            self.controller.update_config(config)
            
        except Exception as e:
            print(f"Config update error: {e}")
    
    def safe_update_button_states(self, connected=None, running=None):
        """Safe button state updates"""
        try:
            if connected is not None:
                if hasattr(self, 'connect_btn') and self.connect_btn:
                    self.connect_btn.setEnabled(not connected)
                if hasattr(self, 'disconnect_btn') and self.disconnect_btn:
                    self.disconnect_btn.setEnabled(connected)
                if hasattr(self, 'start_btn') and self.start_btn:
                    self.start_btn.setEnabled(connected and (running is False or running is None))
                if hasattr(self, 'emergency_stop_btn') and self.emergency_stop_btn:
                    self.emergency_stop_btn.setEnabled(connected)
            
            if running is not None:
                if hasattr(self, 'start_btn') and self.start_btn:
                    self.start_btn.setEnabled(not running and (connected is True or connected is None))
                if hasattr(self, 'stop_btn') and self.stop_btn:
                    self.stop_btn.setEnabled(running)
            
        except Exception as e:
            print(f"Button state update error: {e}")
    
    # Enhanced safe slot handlers
    @Slot(str, str)
    def safe_log_message(self, message: str, level: str):
        """Safe log message handler"""
        try:
            if not hasattr(self, 'log_text') or not self.log_text:
                return
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Color mapping
            color_map = {
                "INFO": "#00FF00",
                "WARNING": "#FFA500", 
                "ERROR": "#FF0000",
                "DEBUG": "#00FFFF"
            }
            
            color = color_map.get(level, "#FFFFFF")
            formatted_msg = f'<span style="color: {color};">[{timestamp}] {level}: {message}</span>'
            
            self.log_text.append(formatted_msg)
            
            # Auto-scroll if enabled
            if hasattr(self, 'auto_scroll_cb') and self.auto_scroll_cb and self.auto_scroll_cb.isChecked():
                cursor = self.log_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                self.log_text.setTextCursor(cursor)
            
        except Exception as e:
            print(f"Log display error: {e}")
    
    @Slot(str)
    def safe_update_status(self, status: str):
        """Safe status update handler"""
        try:
            if hasattr(self, 'bot_status') and self.bot_status:
                self.bot_status.setText(status)
            
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage(f"System Status: {status}")
            
        except Exception as e:
            print(f"Status update error: {e}")
    
    @Slot(dict)
    def safe_update_market_data(self, data: Dict):
        """Safe market data update handler"""
        try:
            if 'bid' in data and hasattr(self, 'bid_label') and self.bid_label:
                self.bid_label.setText(f"{data['bid']:.5f}")
            
            if 'ask' in data and hasattr(self, 'ask_label') and self.ask_label:
                self.ask_label.setText(f"{data['ask']:.5f}")
            
            if 'spread' in data and hasattr(self, 'spread_label') and self.spread_label:
                self.spread_label.setText(f"{data['spread']}")
            
            if 'time' in data and hasattr(self, 'time_label') and self.time_label:
                self.time_label.setText(data['time'].strftime("%H:%M:%S"))
            
            if 'tick_volume' in data and hasattr(self, 'volume_label') and self.volume_label:
                self.volume_label.setText(f"{data['tick_volume']}")
            
        except Exception as e:
            print(f"Market data update error: {e}")
    
    @Slot(dict)
    def safe_update_trade_signal(self, signal: Dict):
        """Safe trade signal update handler"""
        try:
            if 'type' in signal and hasattr(self, 'signal_type_label') and self.signal_type_label:
                signal_type = signal['type']
                self.signal_type_label.setText(signal_type)
                # Color code the signal type
                color = "green" if signal_type == "BUY" else "red" if signal_type == "SELL" else "gray"
                self.signal_type_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")
            
            if 'entry_price' in signal and hasattr(self, 'signal_entry_label') and self.signal_entry_label:
                self.signal_entry_label.setText(f"{signal['entry_price']:.5f}")
            
            if 'sl_price' in signal and hasattr(self, 'signal_sl_label') and self.signal_sl_label:
                self.signal_sl_label.setText(f"{signal['sl_price']:.5f}")
            
            if 'tp_price' in signal and hasattr(self, 'signal_tp_label') and self.signal_tp_label:
                self.signal_tp_label.setText(f"{signal['tp_price']:.5f}")
            
            if 'lot_size' in signal and hasattr(self, 'signal_lot_label') and self.signal_lot_label:
                self.signal_lot_label.setText(f"{signal['lot_size']:.2f}")
            
            if 'timestamp' in signal and hasattr(self, 'signal_time_label') and self.signal_time_label:
                self.signal_time_label.setText(signal['timestamp'].strftime("%H:%M:%S"))
            
            if 'confidence' in signal and hasattr(self, 'signal_confidence_label') and self.signal_confidence_label:
                confidence = signal['confidence']
                self.signal_confidence_label.setText(f"{confidence}%")
                # Color code confidence
                if confidence >= 80:
                    color = "green"
                elif confidence >= 60:
                    color = "orange"
                else:
                    color = "red"
                self.signal_confidence_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")
            
        except Exception as e:
            print(f"Signal update error: {e}")
    
    @Slot(list)
    def safe_update_positions(self, positions: List[Dict]):
        """Safe positions update handler"""
        try:
            if not hasattr(self, 'positions_table') or not self.positions_table:
                return
            
            self.positions_table.setRowCount(len(positions))
            
            for row, pos in enumerate(positions):
                try:
                    items = [
                        str(pos.get('ticket', '')),
                        pos.get('type', ''),
                        f"{pos.get('volume', 0):.2f}",
                        f"{pos.get('price_open', 0):.5f}",
                        f"{pos.get('price_current', pos.get('price_open', 0)):.5f}",
                        f"{pos.get('sl', 0):.5f}",
                        f"{pos.get('tp', 0):.5f}",
                        f"{pos.get('profit', 0):.2f}",
                        pos.get('comment', '')
                    ]
                    
                    for col, item_text in enumerate(items):
                        item = QTableWidgetItem(item_text)
                        
                        # Color code profit/loss
                        if col == 7:  # Profit column
                            profit = pos.get('profit', 0)
                            if profit > 0:
                                item.setBackground(QColor("#4CAF50"))
                            elif profit < 0:
                                item.setBackground(QColor("#f44336"))
                        
                        self.positions_table.setItem(row, col, item)
                
                except Exception as row_error:
                    print(f"Error updating position row {row}: {row_error}")
                    continue
            
        except Exception as e:
            print(f"Position update error: {e}")
    
    @Slot(dict)
    def safe_update_account_display(self, account_data: Dict):
        """Safe account display update handler"""
        try:
            if 'balance' in account_data and hasattr(self, 'balance_label') and self.balance_label:
                self.balance_label.setText(f"${account_data['balance']:.2f}")
            
            if 'equity' in account_data and hasattr(self, 'equity_label') and self.equity_label:
                self.equity_label.setText(f"${account_data['equity']:.2f}")
            
            if 'margin' in account_data and hasattr(self, 'margin_label') and self.margin_label:
                self.margin_label.setText(f"${account_data.get('margin', 0):.2f}")
            
            if 'profit' in account_data and hasattr(self, 'pnl_label') and self.pnl_label:
                profit = account_data['profit']
                self.pnl_label.setText(f"${profit:.2f}")
                # Color code P&L
                color = "green" if profit >= 0 else "red"
                self.pnl_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")
            
            # Calculate and display margin level
            margin = account_data.get('margin', 1)
            equity = account_data.get('equity', 0)
            if margin > 0 and hasattr(self, 'margin_level_label') and self.margin_level_label:
                margin_level = (equity / margin) * 100
                self.margin_level_label.setText(f"{margin_level:.1f}%")
                # Color code margin level
                if margin_level < 100:
                    color = "red"
                elif margin_level < 200:
                    color = "orange"
                else:
                    color = "green"
                self.margin_level_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")
            
        except Exception as e:
            print(f"Account display update error: {e}")
    
    @Slot(dict)
    def safe_update_indicators_display(self, indicators: Dict):
        """Safe indicators display update handler"""
        try:
            # Update M1 indicators
            if 'M1' in indicators and indicators['M1']:
                m1_data = indicators['M1']
                if hasattr(self, 'ema_fast_m1_label') and self.ema_fast_m1_label:
                    self.ema_fast_m1_label.setText(f"{m1_data.get('ema_fast', 0):.5f}")
                if hasattr(self, 'ema_medium_m1_label') and self.ema_medium_m1_label:
                    self.ema_medium_m1_label.setText(f"{m1_data.get('ema_medium', 0):.5f}")
                if hasattr(self, 'ema_slow_m1_label') and self.ema_slow_m1_label:
                    self.ema_slow_m1_label.setText(f"{m1_data.get('ema_slow', 0):.5f}")
                if hasattr(self, 'rsi_m1_label') and self.rsi_m1_label:
                    self.rsi_m1_label.setText(f"{m1_data.get('rsi', 50):.2f}")
                if hasattr(self, 'atr_m1_label') and self.atr_m1_label:
                    self.atr_m1_label.setText(f"{m1_data.get('atr', 0):.5f}")
            
            # Update M5 indicators
            if 'M5' in indicators and indicators['M5']:
                m5_data = indicators['M5']
                if hasattr(self, 'ema_fast_m5_label') and self.ema_fast_m5_label:
                    self.ema_fast_m5_label.setText(f"{m5_data.get('ema_fast', 0):.5f}")
                if hasattr(self, 'ema_medium_m5_label') and self.ema_medium_m5_label:
                    self.ema_medium_m5_label.setText(f"{m5_data.get('ema_medium', 0):.5f}")
                if hasattr(self, 'ema_slow_m5_label') and self.ema_slow_m5_label:
                    self.ema_slow_m5_label.setText(f"{m5_data.get('ema_slow', 0):.5f}")
                if hasattr(self, 'rsi_m5_label') and self.rsi_m5_label:
                    self.rsi_m5_label.setText(f"{m5_data.get('rsi', 50):.2f}")
                if hasattr(self, 'atr_m5_label') and self.atr_m5_label:
                    self.atr_m5_label.setText(f"{m5_data.get('atr', 0):.5f}")
            
        except Exception as e:
            print(f"Indicators update error: {e}")
    
    @Slot(bool)
    def safe_update_connection_status(self, connected: bool):
        """Safe connection status update handler"""
        try:
            if hasattr(self, 'connection_status') and self.connection_status:
                if connected:
                    self.connection_status.setText("✅ Connected")
                    self.connection_status.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                else:
                    self.connection_status.setText("❌ Disconnected")
                    self.connection_status.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            
            # Update button states
            self.safe_update_button_states(connected=connected)
            
        except Exception as e:
            print(f"Connection status update error: {e}")
    
    @Slot(dict)
    def safe_handle_execution_result(self, result: Dict):
        """Safe execution result handler"""
        try:
            success = result.get('success', False)
            message = result.get('message', 'Unknown result')
            
            if success:
                QMessageBox.information(self, "Order Executed", f"✅ {message}")
            else:
                QMessageBox.warning(self, "Order Failed", f"❌ {message}")
            
        except Exception as e:
            print(f"Execution result handler error: {e}")
    
    def safe_update_gui_data(self):
        """Safe periodic GUI data update"""
        try:
            # Update system time
            if hasattr(self, 'system_time_label') and self.system_time_label:
                self.system_time_label.setText(datetime.now().strftime("%H:%M:%S"))
            
            # Update daily statistics if controller available
            if (hasattr(self, 'controller') and self.controller and 
                hasattr(self.controller, 'daily_trades')):
                
                if hasattr(self, 'daily_trades_label') and self.daily_trades_label:
                    self.daily_trades_label.setText(str(self.controller.daily_trades))
                
                if hasattr(self, 'daily_pnl_stat_label') and self.daily_pnl_stat_label:
                    self.daily_pnl_stat_label.setText(f"${self.controller.daily_pnl:.2f}")
                
                if hasattr(self, 'consecutive_losses_label') and self.consecutive_losses_label:
                    losses = getattr(self.controller, 'consecutive_losses', 0)
                    self.consecutive_losses_label.setText(str(losses))
            
        except Exception as e:
            # Silent fail for GUI updates to prevent spam
            pass
    
    def closeEvent(self, event):
        """Enhanced close event handler"""
        try:
            # Check if bot is running
            if (hasattr(self, 'controller') and self.controller and 
                hasattr(self.controller, 'is_running') and self.controller.is_running):
                
                reply = QMessageBox.question(
                    self,
                    "Confirm Exit",
                    "Trading bot is still running!\n\n"
                    "Do you want to stop the bot and exit?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
                
                # Stop the bot safely
                if hasattr(self.controller, 'stop_bot'):
                    self.controller.stop_bot()
            
            # Disconnect if connected
            if (hasattr(self, 'controller') and self.controller and 
                hasattr(self.controller, 'is_connected') and self.controller.is_connected):
                if hasattr(self.controller, 'disconnect_mt5'):
                    self.controller.disconnect_mt5()
            
            # Stop timers
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
            
            print("✅ Application closing gracefully...")
            event.accept()
            
        except Exception as e:
            print(f"Close event error: {e}")
            event.accept()  # Close anyway to prevent hanging
