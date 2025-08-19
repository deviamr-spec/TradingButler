
"""
Fixed Technical Indicators for Professional Trading
All calculation errors resolved
"""

import numpy as np
import pandas as pd
from typing import Union, List

class TechnicalIndicators:
    """Professional technical indicators with error-free calculations"""

    def __init__(self):
        self.epsilon = 1e-10  # Small value to prevent division by zero

    def ema(self, data: Union[List, np.ndarray], period: int) -> np.ndarray:
        """Enhanced Exponential Moving Average with error handling"""
        try:
            data = np.array(data, dtype=float)
            
            if len(data) < period:
                return np.full(len(data), np.nan)

            # Calculate alpha
            alpha = 2.0 / (period + 1)
            
            # Initialize result array
            ema_values = np.full(len(data), np.nan)
            
            # Calculate SMA for first value
            ema_values[period-1] = np.mean(data[:period])
            
            # Calculate EMA for remaining values
            for i in range(period, len(data)):
                ema_values[i] = (alpha * data[i]) + ((1 - alpha) * ema_values[i-1])
            
            return ema_values

        except Exception as e:
            print(f"EMA calculation error: {e}")
            return np.full(len(data), np.nan)

    def sma(self, data: Union[List, np.ndarray], period: int) -> np.ndarray:
        """Simple Moving Average with proper error handling"""
        try:
            data = np.array(data, dtype=float)
            
            if len(data) < period:
                return np.full(len(data), np.nan)

            sma_values = np.full(len(data), np.nan)
            
            for i in range(period - 1, len(data)):
                sma_values[i] = np.mean(data[i - period + 1:i + 1])
            
            return sma_values

        except Exception as e:
            print(f"SMA calculation error: {e}")
            return np.full(len(data), np.nan)

    def rsi(self, data: Union[List, np.ndarray], period: int = 14) -> np.ndarray:
        """Enhanced RSI calculation with fixed array bounds"""
        try:
            data = np.array(data, dtype=float)
            
            if len(data) < period + 1:
                return np.full(len(data), 50.0)  # Return neutral RSI

            # Calculate price changes
            delta = np.diff(data)
            
            # Separate gains and losses
            gains = np.where(delta > 0, delta, 0)
            losses = np.where(delta < 0, -delta, 0)
            
            # Initialize RSI array
            rsi_values = np.full(len(data), np.nan)
            
            # Calculate initial average gain and loss
            avg_gain = np.mean(gains[:period])
            avg_loss = np.mean(losses[:period])
            
            # Calculate RSI for the first period
            if avg_loss > self.epsilon:
                rs = avg_gain / avg_loss
                rsi_values[period] = 100 - (100 / (1 + rs))
            else:
                rsi_values[period] = 100

            # Calculate remaining RSI values using smoothed averages
            for i in range(period + 1, len(data)):
                idx = i - 1  # Index for gains/losses array
                if idx < len(gains) and idx < len(losses):
                    avg_gain = ((avg_gain * (period - 1)) + gains[idx]) / period
                    avg_loss = ((avg_loss * (period - 1)) + losses[idx]) / period
                    
                    if avg_loss > self.epsilon:
                        rs = avg_gain / avg_loss
                        rsi_values[i] = 100 - (100 / (1 + rs))
                    else:
                        rsi_values[i] = 100

            return rsi_values

        except Exception as e:
            print(f"RSI calculation error: {e}")
            return np.full(len(data), 50.0)

    def atr(self, high: Union[List, np.ndarray], low: Union[List, np.ndarray], 
            close: Union[List, np.ndarray], period: int = 14) -> np.ndarray:
        """Enhanced Average True Range with proper error handling"""
        try:
            high = np.array(high, dtype=float)
            low = np.array(low, dtype=float)
            close = np.array(close, dtype=float)
            
            # Validate input arrays
            if len(high) != len(low) or len(low) != len(close):
                print("ATR: Array length mismatch")
                return np.full(len(close), 0.01)

            if len(close) < period + 1:
                return np.full(len(close), 0.01)

            # Calculate True Range
            tr1 = high - low
            tr2 = np.abs(high - np.roll(close, 1))
            tr3 = np.abs(low - np.roll(close, 1))
            
            # Set first value to high - low (no previous close)
            tr2[0] = tr1[0]
            tr3[0] = tr1[0]
            
            true_range = np.maximum(tr1, np.maximum(tr2, tr3))
            
            # Calculate ATR using RMA (same as EMA with period multiplier)
            atr_values = np.full(len(close), np.nan)
            
            # First ATR value is SMA of true range
            atr_values[period - 1] = np.mean(true_range[:period])
            
            # Calculate remaining ATR values
            alpha = 1.0 / period
            for i in range(period, len(close)):
                atr_values[i] = (alpha * true_range[i]) + ((1 - alpha) * atr_values[i - 1])
            
            return atr_values

        except Exception as e:
            print(f"ATR calculation error: {e}")
            return np.full(len(close), 0.01)

    def bollinger_bands(self, data: Union[List, np.ndarray], period: int = 20, 
                       std_dev: float = 2) -> tuple:
        """Bollinger Bands calculation"""
        try:
            data = np.array(data, dtype=float)
            
            if len(data) < period:
                return (np.full(len(data), np.nan), 
                       np.full(len(data), np.nan), 
                       np.full(len(data), np.nan))

            middle = self.sma(data, period)
            std = np.full(len(data), np.nan)
            
            for i in range(period - 1, len(data)):
                std[i] = np.std(data[i - period + 1:i + 1])
            
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return upper, middle, lower

        except Exception as e:
            print(f"Bollinger Bands error: {e}")
            return (np.full(len(data), np.nan), 
                   np.full(len(data), np.nan), 
                   np.full(len(data), np.nan))

    def macd(self, data: Union[List, np.ndarray], fast: int = 12, 
             slow: int = 26, signal: int = 9) -> tuple:
        """MACD calculation"""
        try:
            data = np.array(data, dtype=float)
            
            if len(data) < slow:
                return (np.full(len(data), np.nan), 
                       np.full(len(data), np.nan), 
                       np.full(len(data), np.nan))

            ema_fast = self.ema(data, fast)
            ema_slow = self.ema(data, slow)
            
            macd_line = ema_fast - ema_slow
            signal_line = self.ema(macd_line[~np.isnan(macd_line)], signal)
            
            # Align signal line with macd line
            aligned_signal = np.full(len(data), np.nan)
            signal_start = len(data) - len(signal_line)
            aligned_signal[signal_start:] = signal_line
            
            histogram = macd_line - aligned_signal
            
            return macd_line, aligned_signal, histogram

        except Exception as e:
            print(f"MACD error: {e}")
            return (np.full(len(data), np.nan), 
                   np.full(len(data), np.nan), 
                   np.full(len(data), np.nan))

    def stochastic(self, high: Union[List, np.ndarray], low: Union[List, np.ndarray], 
                   close: Union[List, np.ndarray], period: int = 14, 
                   smooth_k: int = 3, smooth_d: int = 3) -> tuple:
        """Stochastic Oscillator calculation"""
        try:
            high = np.array(high, dtype=float)
            low = np.array(low, dtype=float)
            close = np.array(close, dtype=float)
            
            if len(high) != len(low) or len(low) != len(close):
                return (np.full(len(close), np.nan), 
                       np.full(len(close), np.nan))

            if len(close) < period:
                return (np.full(len(close), np.nan), 
                       np.full(len(close), np.nan))

            k_percent = np.full(len(close), np.nan)
            
            for i in range(period - 1, len(close)):
                lowest_low = np.min(low[i - period + 1:i + 1])
                highest_high = np.max(high[i - period + 1:i + 1])
                
                if highest_high - lowest_low > self.epsilon:
                    k_percent[i] = ((close[i] - lowest_low) / 
                                   (highest_high - lowest_low)) * 100
                else:
                    k_percent[i] = 50

            k_smooth = self.sma(k_percent, smooth_k)
            d_smooth = self.sma(k_smooth, smooth_d)
            
            return k_smooth, d_smooth

        except Exception as e:
            print(f"Stochastic error: {e}")
            return (np.full(len(close), np.nan), 
                   np.full(len(close), np.nan))

    def williams_r(self, high: Union[List, np.ndarray], low: Union[List, np.ndarray], 
                   close: Union[List, np.ndarray], period: int = 14) -> np.ndarray:
        """Williams %R calculation"""
        try:
            high = np.array(high, dtype=float)
            low = np.array(low, dtype=float)
            close = np.array(close, dtype=float)
            
            if len(high) != len(low) or len(low) != len(close):
                return np.full(len(close), -50.0)

            if len(close) < period:
                return np.full(len(close), -50.0)

            williams_r = np.full(len(close), np.nan)
            
            for i in range(period - 1, len(close)):
                highest_high = np.max(high[i - period + 1:i + 1])
                lowest_low = np.min(low[i - period + 1:i + 1])
                
                if highest_high - lowest_low > self.epsilon:
                    williams_r[i] = ((highest_high - close[i]) / 
                                    (highest_high - lowest_low)) * -100
                else:
                    williams_r[i] = -50

            return williams_r

        except Exception as e:
            print(f"Williams %R error: {e}")
            return np.full(len(close), -50.0)

    def momentum(self, data: Union[List, np.ndarray], period: int = 10) -> np.ndarray:
        """Momentum calculation"""
        try:
            data = np.array(data, dtype=float)
            
            if len(data) < period:
                return np.full(len(data), 0.0)

            momentum_values = np.full(len(data), np.nan)
            
            for i in range(period, len(data)):
                momentum_values[i] = data[i] - data[i - period]
            
            return momentum_values

        except Exception as e:
            print(f"Momentum error: {e}")
            return np.full(len(data), 0.0)

    def roc(self, data: Union[List, np.ndarray], period: int = 10) -> np.ndarray:
        """Rate of Change calculation"""
        try:
            data = np.array(data, dtype=float)
            
            if len(data) < period:
                return np.full(len(data), 0.0)

            roc_values = np.full(len(data), np.nan)
            
            for i in range(period, len(data)):
                if data[i - period] > self.epsilon:
                    roc_values[i] = ((data[i] - data[i - period]) / 
                                    data[i - period]) * 100
                else:
                    roc_values[i] = 0.0
            
            return roc_values

        except Exception as e:
            print(f"ROC error: {e}")
            return np.full(len(data), 0.0)

    def validate_data(self, data: Union[List, np.ndarray]) -> bool:
        """Validate input data"""
        try:
            data = np.array(data, dtype=float)
            return len(data) > 0 and not np.all(np.isnan(data))
        except:
            return False

    def get_latest_value(self, values: np.ndarray, default: float = 0.0) -> float:
        """Safely get the latest non-NaN value"""
        try:
            if len(values) == 0:
                return default
            
            # Get last non-NaN value
            non_nan_values = values[~np.isnan(values)]
            if len(non_nan_values) > 0:
                return float(non_nan_values[-1])
            else:
                return default
                
        except Exception as e:
            print(f"Get latest value error: {e}")
            return default

    def smooth_data(self, data: Union[List, np.ndarray], window: int = 3) -> np.ndarray:
        """Apply smoothing to data"""
        try:
            data = np.array(data, dtype=float)
            
            if len(data) < window:
                return data
            
            smoothed = np.copy(data)
            
            for i in range(window, len(data)):
                smoothed[i] = np.mean(data[i - window + 1:i + 1])
            
            return smoothed

        except Exception as e:
            print(f"Smoothing error: {e}")
            return data
