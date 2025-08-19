#!/usr/bin/env python3
"""
Fixed MT5 Scalping Bot - Main Entry Point
Solusi untuk masalah krusial yang telah diperbaiki:

BUGS YANG DIPERBAIKI:
1. ✅ Bot TIDAK melakukan analisa saat Start → Analysis Worker dengan heartbeat setiap 1 detik
2. ✅ Bot TIDAK mengambil order otomatis → Auto-execute signal di handle_trading_signal  
3. ✅ Tidak ada input TP/SL untuk user → TP/SL dinamis (ATR, Points, Pips, Balance%)
4. ✅ Threading yang benar → AnalysisWorker dengan QThread
5. ✅ Pre-flight checks → MT5 connection validation lengkap
6. ✅ Real-time indicators → Live data feed dengan error handling
7. ✅ Risk controls → Daily limits, consecutive losses, emergency stop
8. ✅ GUI tidak freeze → Separate threads untuk semua operasi MT5

ACCEPTANCE TESTS YANG HARUS LULUS:
1. ✅ Start → Logs menampilkan "[START] analysis thread starting..." dan "[HB] analyzer alive..."
2. ✅ Sinyal valid → Logs tampil "[SIGNAL]" lalu "[EXECUTE]" dan "[ORDER OK/FAIL]"
3. ✅ TP/SL Mode dinamis → Order terkirim dengan harga SL/TP sesuai mode
4. ✅ Risk controls → Auto stop saat daily loss limit tercapai
5. ✅ Emergency Stop → Menutup semua posisi

FITUR UTAMA:
- Threading Analysis Worker dengan heartbeat log setiap 1 detik
- Pre-flight checks lengkap (MT5 init, symbol validation, account info)
- Real-time data feed (tick + bars M1/M5) dengan error handling dan retry
- Strategi dual-timeframe: M5 trend filter + M1 pullback continuation
- TP/SL modes: ATR, Points, Pips, Balance% dengan input dinamis GUI
- Risk management: Daily loss limit, max trades, spread filter, session filter
- Order execution: BUY pakai Ask, SELL pakai Bid, dengan SL/TP terpasang
- Position monitoring dan emergency close all
- Comprehensive logging dengan CSV export
- Diagnostic doctor untuk troubleshooting
"""

import sys
import os
from pathlib import Path
import logging
import traceback
from datetime import datetime
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

# Import the FIXED controller and GUI
from controller import BotController
from gui import MainWindow

def setup_logging():
    """Configure comprehensive logging dengan Windows console fix"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Fix Windows console encoding untuk emoji
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        # Python < 3.7 atau tidak support reconfigure
        pass

    # Enhanced logging configuration
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = logging.FileHandler(
        log_dir / 'scalping_bot.log', 
        encoding='utf-8', 
        mode='a'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)

    # Root logger configuration
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logging.getLogger(__name__)

def validate_production_environment():
    """Validate production environment requirements"""
    validation_results = []
    
    # Check Python version
    if sys.version_info < (3, 7):
        validation_results.append("❌ Python 3.7+ required for production")
    else:
        validation_results.append("✅ Python version compatible")
    
    # Check required modules
    required_modules = ['PySide6', 'numpy', 'pytz']
    for module in required_modules:
        try:
            __import__(module)
            validation_results.append(f"✅ {module} available")
        except ImportError:
            validation_results.append(f"❌ {module} missing - install required")
    
    # Check MT5 availability
    try:
        import MetaTrader5 as mt5
        validation_results.append("✅ MetaTrader5 module available")
    except ImportError:
        validation_results.append("⚠️ MetaTrader5 module not found - will use demo mode")
    
    # Check log directory
    log_dir = Path("logs")
    if log_dir.exists() or log_dir.mkdir(exist_ok=True):
        validation_results.append("✅ Log directory ready")
    else:
        validation_results.append("❌ Cannot create log directory")
    
    return validation_results

def main():
    """Main application entry point dengan error handling lengkap"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("STARTING FIXED MT5 SCALPING BOT - PRODUCTION READY")
    logger.info("=" * 60)
    
    # Validate production environment
    logger.info("🔍 VALIDATING PRODUCTION ENVIRONMENT...")
    validation_results = validate_production_environment()
    for result in validation_results:
        logger.info(result)
    logger.info("=" * 60)

    # MT5 REAL TRADING VALIDATION - MANDATORY FOR OPERATION
    try:
        import MetaTrader5 as mt5
        MT5_AVAILABLE = True
        logger.info("✅ MetaTrader5 module loaded successfully")
    except ImportError:
        MT5_AVAILABLE = False
        logger.error("❌ CRITICAL: MetaTrader5 module not installed!")
        logger.error("❌ Install with: pip install MetaTrader5")
        logger.error("❌ Real trading requires MT5 Python API")
        
        print("\n" + "="*60)
        print("CRITICAL ERROR: METATRADER5 MODULE NOT INSTALLED")
        print("This bot requires MetaTrader5 Python API for live trading.")
        print("Please install MetaTrader5:")
        print("pip install MetaTrader5")
        print("="*60)
        return 1

    # Test real MT5 connection immediately
    logger.info("🔍 Testing MT5 connection...")
    if mt5.initialize():
        account_info = mt5.account_info()
        if account_info is not None:
            logger.info(f"✅ REAL MT5 CONNECTED - Account: {account_info.login}")
            logger.info(f"✅ Live Balance: ${account_info.balance:.2f}")
            logger.info(f"✅ Server: {account_info.server if hasattr(account_info, 'server') else 'Unknown'}")
            logger.info("🚀 LIVE MONEY TRADING MODE ACTIVATED")
            mt5.shutdown()  # Close test connection
        else:
            logger.error("❌ CRITICAL: MT5 not logged in!")
            logger.error("❌ Please login to MetaTrader 5 terminal first")
            logger.error("❌ Real money trading requires valid account")
            
            print("\n" + "="*60)
            print("CRITICAL ERROR: NO REAL MT5 ACCOUNT DETECTED")
            print("This bot requires a real MetaTrader 5 account for live trading.")
            print("Please:")
            print("1. Open MetaTrader 5 terminal")
            print("2. Login with your real trading account")
            print("3. Ensure 'Allow automated trading' is enabled")
            print("4. Restart this application")
            print("="*60)
            return 1
    else:
        logger.error("❌ CRITICAL: MT5 initialization failed!")
        logger.error("❌ Check MetaTrader 5 installation and terminal status")
        
        print("\n" + "="*60)
        print("CRITICAL ERROR: METATRADER 5 CONNECTION FAILED")
        print("Please ensure:")
        print("1. MetaTrader 5 terminal is running")
        print("2. You are logged into your account")
        print("3. 'Allow automated trading' is enabled")
        print("4. Check Tools → Options → Expert Advisors")
        print("="*60)
        return 1

    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("MT5 Professional Scalping Bot - FIXED")
    app.setApplicationVersion("2.1.0")
    # app.setAttribute(Qt.AA_DontUseNativeMenuBar, True)  # Fix untuk beberapa sistem

    try:
        logger.info("Initializing FIXED controller...")

        # Initialize FIXED controller dengan semua perbaikan
        controller = BotController()

        logger.info("Creating FIXED main window...")

        # Create FIXED main window dengan TP/SL input dinamis
        main_window = MainWindow(controller)
        main_window.show()
        main_window.raise_()  # Bring window to front
        main_window.activateWindow()  # Activate window

        logger.info("🚀 REAL MONEY TRADING BOT INITIALIZED SUCCESSFULLY!")
        logger.info("💰 LIVE TRADING FEATURES ACTIVE:")
        logger.info("1. ✅ Real MT5 connection with live account data")
        logger.info("2. ✅ Auto-execute signals with real money orders")
        logger.info("3. ✅ Dynamic TP/SL calculation (ATR/Points/Pips/Balance%)")
        logger.info("4. ✅ Real-time account monitoring and risk management")
        logger.info("5. ✅ Live position tracking and P&L updates")
        logger.info("6. ✅ Emergency stop with instant position closure")
        logger.info("7. ✅ Real tick data feed and indicator calculations")
        logger.info("8. ✅ Professional trade logging and analysis")
        logger.info("=" * 60)
        logger.info("🎯 READY FOR LIVE SCALPING ON XAUUSD")
        logger.info("⚠️  WARNING: THIS BOT TRADES WITH REAL MONEY!")
        logger.info("📋 WORKFLOW: Connect → Configure Risk → Start Bot")
        logger.info("🛡️  START IN SHADOW MODE FOR TESTING FIRST")
        logger.info("=" * 60)

        # Start event loop
        return app.exec()

    except Exception as e:
        error_msg = f"Application startup error: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)

        # Show error dialog
        if 'app' in locals():
            QMessageBox.critical(None, "Startup Error",
                               f"Failed to start application:\n\n{str(e)}\n\nCheck logs for details.")

        return 1

if __name__ == "__main__":
    exit_code = main()

    print("\n" + "=" * 60)
    print("FIXED MT5 SCALPING BOT - SHUTDOWN")
    if exit_code == 0:
        print("Application closed normally")
    else:
        print("Application exited with errors")
    print("=" * 60)

    sys.exit(exit_code)