
# 🚀 MT5 Professional Scalping Bot - Windows Installation Guide

## ✅ REQUIREMENTS FOR 100% FUNCTIONALITY

### 1. **MetaTrader 5 Terminal Installation**
```
1. Download MT5 from: https://www.metatrader5.com/en/download
2. Install to default location: C:\Program Files\MetaTrader 5\
3. Open MT5 and login with your broker credentials
4. Enable "Tools → Options → Expert Advisors → Allow automated trading"
5. Add Python to trusted programs if prompted
```

### 2. **Python Environment Setup**
```bash
# Install Python 3.8+ from python.org
# Then install bot requirements:
pip install -r requirements_production.txt

# OR install manually:
pip install PySide6 MetaTrader5 numpy pandas pytz
```

### 3. **MT5 Python API Configuration**
```
1. Ensure MT5 terminal is RUNNING and LOGGED IN
2. Symbol XAUUSD must be visible in Market Watch
3. Auto-trading must be enabled (green button in MT5)
4. Account must have trading permissions
```

## 🎯 RUNNING THE BOT

### Start the Application:
```bash
cd TradingBot
python production_mt5_bot.py
```

### Expected Startup Sequence:
```
🚀 Starting MT5 Professional Scalping Bot
✓ MetaTrader5 module loaded - LIVE TRADING MODE
✅ Application started successfully!
```

## 🔧 TROUBLESHOOTING CONNECTION ISSUES

### If you see "MT5 not available - demo mode":
```
PROBLEM: MetaTrader5 Python module not installed
SOLUTION: pip install MetaTrader5
```

### If connection fails:
```
PROBLEM: MT5 terminal not running or not logged in
SOLUTION:
1. Open MT5 terminal
2. Login with broker credentials  
3. Check "Tools → Options → Expert Advisors → Allow automated trading"
4. Restart the bot
```

### If symbol info missing:
```
PROBLEM: XAUUSD not available in Market Watch
SOLUTION:
1. Right-click Market Watch in MT5
2. Click "Symbols"
3. Find XAUUSD and add to Market Watch
4. Restart the bot
```

### If analysis worker not running:
```
PROBLEM: Insufficient market data
SOLUTION:
1. Ensure MT5 has live market connection
2. Check symbol is selected in Market Watch
3. Wait for sufficient historical data to load
4. Run diagnostic check in bot
```

## 🎯 USAGE WORKFLOW

### 1. **Initial Setup**
```
1. Start bot: python production_mt5_bot.py
2. Click "Connect to MT5"
3. Verify connection status shows "Connected"
4. Check account information is displayed
```

### 2. **Configuration**
```
1. Go to Strategy tab
2. Configure EMA periods (default: 9, 21, 50)
3. Set RSI period (default: 14)
4. Go to Trading tab
5. Set risk percentage (recommended: 1%)
6. Configure TP/SL mode (ATR recommended)
```

### 3. **Start Trading**
```
1. Click "Start Analysis"
2. Monitor logs for heartbeat messages
3. Check indicators are calculating
4. Enable "Auto Trading" when ready
5. Disable "Demo Mode" for live trading
```

### 4. **Monitoring**
```
1. Watch live market data updates
2. Monitor indicator calculations
3. Check for trading signals in logs
4. Monitor positions in Positions tab
5. Use diagnostic check if issues arise
```

## ⚠️ SAFETY FEATURES

### Demo Mode (Default):
- Signals are generated but NO orders are placed
- Safe for testing and learning
- Disable only when ready for live trading

### Risk Management:
- Position sizing based on account percentage
- Maximum spread filtering
- ATR-based stop losses
- Emergency close all positions

### Emergency Controls:
- Stop analysis immediately
- Close all positions with one click
- Demo mode toggle
- Comprehensive logging

## 📊 EXPECTED PERFORMANCE

### Live Data Feed:
- Market data updates every 500ms
- Indicator calculations in real-time
- Signal generation based on strategy
- Automatic order execution (if enabled)

### Trading Strategy:
- M5 timeframe trend filtering using EMAs
- M1 timeframe entry signals on pullbacks
- RSI confirmation for momentum
- ATR-based position sizing and stops

## 🆘 SUPPORT CHECKLIST

If bot is not working 100%, check:

- [ ] MetaTrader 5 installed and running
- [ ] Logged into MT5 with valid account
- [ ] XAUUSD symbol in Market Watch
- [ ] Auto-trading enabled in MT5
- [ ] Python MetaTrader5 module installed
- [ ] Bot shows "Connected" status
- [ ] Analysis worker running (check logs)
- [ ] Market data updating in real-time
- [ ] Indicators calculating properly

## 🎉 SUCCESS INDICATORS

Bot is working 100% when you see:

✅ "Connected to MT5" in connection status
✅ Live bid/ask prices updating
✅ "Analysis alive" heartbeat messages
✅ EMA/RSI/ATR indicators updating
✅ Account balance and equity displayed
✅ Trading signals in logs (when conditions met)
✅ Positions table updating (if trades placed)

---
**🚨 IMPORTANT: Always start with Demo Mode enabled and small risk percentages for testing!**
