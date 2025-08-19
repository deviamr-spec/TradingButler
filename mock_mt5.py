
"""
MOCK MT5 MODULE DISABLED
This file is disabled to force real MetaTrader5 connection only.
For live trading, install: pip install MetaTrader5
"""

# NO MOCK IMPLEMENTATION - REAL MT5 REQUIRED
def __getattr__(name):
    raise ImportError(
        "Mock MT5 disabled. Install real MetaTrader5: pip install MetaTrader5"
    )
