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
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'scalping_bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Main application entry point dengan error handling lengkap"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("STARTING FIXED MT5 SCALPING BOT - PRODUCTION READY")
    logger.info("=" * 60)
    
    # MT5 REAL TRADING VALIDATION - MANDATORY FOR OPERATION
    try:
        import MetaTrader5 as mt5
        # Test real MT5 connection immediately
        if mt5.initialize():
            account_info = mt5.account_info()
            if account_info is not None:
                MT5_AVAILABLE = True
                logger.info(f"✅ REAL MT5 CONNECTED - Account: {account_info.login}")
                logger.info(f"✅ Live Balance: ${account_info.balance:.2f}")
                logger.info(f"✅ Server: {account_info.server if hasattr(account_info, 'server') else 'Unknown'}")
                logger.info("🚀 LIVE MONEY TRADING MODE ACTIVATED")
                mt5.shutdown()  # Close test connection
            else:
                logger.error("❌ CRITICAL: MT5 not logged in!")
                logger.error("❌ Please login to MetaTrader 5 terminal first")
                logger.error("❌ Real money trading requires valid account")
                MT5_AVAILABLE = False
                
                # Exit if no real account
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
            logger.error("❌ Check MetaTrader 5 installation")
            MT5_AVAILABLE = False
            
            print("\n" + "="*60)
            print("CRITICAL ERROR: METATRADER 5 NOT AVAILABLE")
            print("This bot requires MetaTrader 5 for live trading.")
            print("Please install MetaTrader 5 and try again.")
            print("="*60)
            return 1
            
    except ImportError:
        logger.error("❌ CRITICAL: MetaTrader5 Python module not installed!")
        logger.error("❌ Install with: pip install MetaTrader5")
        MT5_AVAILABLE = False
        
        print("\n" + "="*60)
        print("CRITICAL ERROR: METATRADER5 MODULE MISSING")
        print("Install the required module:")
        print("pip install MetaTrader5")
        print("="*60)
        return 1
    
    # Reject startup if no real MT5
    if not MT5_AVAILABLE:
        logger.error("❌ STARTUP REJECTED - REAL MT5 REQUIRED")
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