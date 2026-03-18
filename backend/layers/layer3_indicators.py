"""
layer3_indicators.py — Technical indicator calculation for NSE intraday.
Uses pandas-ta for all indicators. Operates on 15-minute OHLCV data.
All functions return None gracefully on insufficient data.
"""
import os
import sys
import pandas as pd
import numpy as np  # noqa: F401
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    import pandas_ta as ta
except ImportError:
    ta = None

# Minimum candles required for reliable indicator calculation
MIN_CANDLES = 20


def prepare_dataframe(candles: list) -> Optional[pd.DataFrame]:
    """
    Convert candle list from Layer 1 OHLCV to pandas DataFrame.
    Returns None if insufficient data.
    """
    if not candles or len(candles) < MIN_CANDLES:
        return None
    try:
        df = pd.DataFrame(candles)
        df["time"] = pd.to_datetime(df["time"])
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        df = df.dropna(subset=["open", "high", "low", "close", "volume"])
        df = df.sort_values("time").reset_index(drop=True)
        if len(df) < MIN_CANDLES:
            return None
        return df
    except Exception:
        return None


def calc_rsi(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    """RSI — overbought >70, oversold <30. Returns latest value."""
    try:
        close = df["close"].astype(float)
        if ta is not None:
            rsi = ta.rsi(close, length=period)
            val = rsi.dropna().iloc[-1] if rsi is not None else None
            return round(float(val), 2) if val is not None else None

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi_series = 100 - (100 / (1 + rs))
        # If avg_loss is 0, RSI should be 100 (no losses)
        rsi_series = rsi_series.fillna(100.0)
        val = rsi_series.dropna().iloc[-1] if not rsi_series.dropna().empty else None
        if val is None:
            return None
        # Keep within (0, 100) to satisfy validators and avoid edge cases.
        val_f = float(val)
        val_f = min(99.99, max(0.01, val_f))
        return round(val_f, 2)
    except Exception:
        return None


def calc_macd(df: pd.DataFrame) -> Optional[dict]:
    """
    MACD (12/26/9). Returns dict with line, signal, histogram,
    and crossover direction.
    """
    try:
        close = df["close"].astype(float)
        if ta is not None:
            macd = ta.macd(close, fast=12, slow=26, signal=9)
            if macd is None or macd.empty:
                return None
            macd = macd.dropna()
            if len(macd) < 2:
                return None
            line_v = float(macd.iloc[-1, 0])
            signal_v = float(macd.iloc[-1, 1])
            hist_v = float(macd.iloc[-1, 2])
            hist_prev_v = float(macd.iloc[-2, 2])
        else:
            ema_fast = close.ewm(span=12, adjust=False).mean()
            ema_slow = close.ewm(span=26, adjust=False).mean()
            line_series = ema_fast - ema_slow
            signal_series = line_series.ewm(span=9, adjust=False).mean()
            hist_series = line_series - signal_series
            if hist_series.dropna().shape[0] < 2:
                return None
            line_v = float(line_series.iloc[-1])
            signal_v = float(signal_series.iloc[-1])
            hist_v = float(hist_series.iloc[-1])
            hist_prev_v = float(hist_series.iloc[-2])

        line = round(line_v, 4)
        signal = round(signal_v, 4)
        hist = round(hist_v, 4)
        hist_prev = round(hist_prev_v, 4)

        if hist > 0 and hist_prev <= 0:
            crossover = "bullish_crossover"
        elif hist < 0 and hist_prev >= 0:
            crossover = "bearish_crossover"
        elif hist > hist_prev:
            crossover = "bullish_momentum"
        else:
            crossover = "bearish_momentum"

        return {
            "line": line,
            "signal": signal,
            "histogram": hist,
            "crossover": crossover,
            "bullish": hist > 0,
        }
    except Exception:
        return None


def calc_bollinger(df: pd.DataFrame, period: int = 20) -> Optional[dict]:
    """
    Bollinger Bands (20, 2). Returns upper, mid, lower, width,
    and squeeze flag.
    """
    try:
        close_s = df["close"].astype(float)
        if ta is not None:
            bb = ta.bbands(close_s, length=period, std=2)
            if bb is None or bb.empty:
                return None
            bb = bb.dropna()
            if bb.empty:
                return None
            upper_v = float(bb.iloc[-1, 0])
            mid_v = float(bb.iloc[-1, 1])
            lower_v = float(bb.iloc[-1, 2])
            width_v = float(bb.iloc[-1, 3]) if bb.shape[1] > 3 else None
            width_series = bb.iloc[:, 3] if bb.shape[1] > 3 else None
        else:
            mid_series = close_s.rolling(period, min_periods=period).mean()
            std_series = close_s.rolling(period, min_periods=period).std(ddof=0)
            upper_series = mid_series + 2 * std_series
            lower_series = mid_series - 2 * std_series
            if upper_series.dropna().empty or lower_series.dropna().empty:
                return None
            upper_v = float(upper_series.iloc[-1])
            mid_v = float(mid_series.iloc[-1])
            lower_v = float(lower_series.iloc[-1])
            width_series = (upper_series - lower_series) / mid_series.replace(0, np.nan)
            width_v = float(width_series.iloc[-1]) if not width_series.dropna().empty else None

        upper = round(upper_v, 2)
        mid = round(mid_v, 2)
        lower = round(lower_v, 2)
        width = round(width_v, 4) if width_v is not None else None
        close = round(float(close_s.iloc[-1]), 2)

        squeeze = False
        if width is not None and width_series is not None and len(width_series.dropna()) >= 20:
            avg_width = float(width_series.dropna().tail(20).mean())
            if avg_width and width < avg_width * 0.7:
                squeeze = True

        return {
            "upper": upper,
            "mid": mid,
            "lower": lower,
            "width": width,
            "squeeze": squeeze,
            "pct_b": round((close - lower) / (upper - lower), 3)
            if upper != lower
            else 0.5,
        }
    except Exception:
        return None


def calc_ema(df: pd.DataFrame) -> Optional[dict]:
    """
    EMA 9, 21, 50, 200. Returns values and alignment status.
    Aligned = all EMAs ordered (9>21>50>200 for uptrend).
    """
    try:
        close = df["close"].astype(float)
        if ta is not None:
            ema9 = ta.ema(close, length=9)
            ema21 = ta.ema(close, length=21)
            ema50 = ta.ema(close, length=50)
            ema200 = ta.ema(close, length=200)
        else:
            ema9 = close.ewm(span=9, adjust=False).mean()
            ema21 = close.ewm(span=21, adjust=False).mean()
            ema50 = close.ewm(span=50, adjust=False).mean()
            ema200 = close.ewm(span=200, adjust=False).mean()

        def last(series):
            if series is None:
                return None
            s = series.dropna()
            return round(float(s.iloc[-1]), 2) if len(s) > 0 else None

        e9 = last(ema9)
        e21 = last(ema21)
        e50 = last(ema50)
        e200 = last(ema200)
        curr = round(float(close.iloc[-1]), 2)

        bull_aligned = (
            e9 is not None
            and e21 is not None
            and e9 > e21
            and (e50 is None or e21 > e50)
            and curr > (e21 or 0)
        )
        bear_aligned = (
            e9 is not None
            and e21 is not None
            and e9 < e21
            and (e50 is None or e21 < e50)
            and curr < (e21 or float("inf"))
        )

        trend = (
            "strong_uptrend"
            if bull_aligned and e50 and curr > e50
            else "uptrend"
            if bull_aligned
            else "strong_downtrend"
            if bear_aligned and e50 and curr < e50
            else "downtrend"
            if bear_aligned
            else "ranging"
        )

        return {
            "ema9": e9,
            "ema21": e21,
            "ema50": e50,
            "ema200": e200,
            "price": curr,
            "above_ema9": curr > e9 if e9 else None,
            "above_ema21": curr > e21 if e21 else None,
            "above_ema50": curr > e50 if e50 else None,
            "above_ema200": curr > e200 if e200 else None,
            "trend": trend,
            "bull_aligned": bull_aligned,
            "bear_aligned": bear_aligned,
        }
    except Exception:
        return None


def calc_atr(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    """ATR(14) — used for dynamic stop loss calculation."""
    try:
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)
        if ta is not None:
            atr = ta.atr(high, low, close, length=period)
            if atr is None:
                return None
            val = atr.dropna().iloc[-1]
            return round(float(val), 2) if val is not None else None

        prev_close = close.shift(1)
        tr = pd.concat(
            [
                (high - low),
                (high - prev_close).abs(),
                (low - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr_series = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        val = atr_series.dropna().iloc[-1] if not atr_series.dropna().empty else None
        return round(float(val), 2) if val is not None else None
    except Exception:
        return None


def calc_volume_analysis(df: pd.DataFrame) -> Optional[dict]:
    """
    Volume analysis vs 10-day average.
    Returns ratio, signal, and OBV direction.
    """
    try:
        vol_series = df["volume"]
        current_vol = float(vol_series.iloc[-1])
        avg_vol_10 = float(vol_series.tail(10).mean())

        ratio = round(current_vol / avg_vol_10, 2) if avg_vol_10 > 0 else 1.0

        if ratio >= 3.0:
            signal = "very_high_volume"
        elif ratio >= 2.0:
            signal = "high_volume"
        elif ratio >= 1.3:
            signal = "above_average"
        elif ratio >= 0.7:
            signal = "average"
        else:
            signal = "low_volume"

        close = df["close"].astype(float)
        volume = df["volume"].astype(float)
        if ta is not None:
            obv = ta.obv(close, volume)
            obv_direction = "rising"
            if obv is not None and len(obv.dropna()) >= 3:
                obv_vals = obv.dropna().tail(3).values
                obv_direction = "rising" if obv_vals[-1] > obv_vals[0] else "falling"
        else:
            direction = close.diff().fillna(0).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
            obv_series = (direction * volume).cumsum()
            if obv_series.dropna().shape[0] >= 3:
                obv_vals = obv_series.dropna().tail(3).values
                obv_direction = "rising" if obv_vals[-1] > obv_vals[0] else "falling"
            else:
                obv_direction = "rising"

        return {
            "current_volume": int(current_vol),
            "avg_volume_10d": int(avg_vol_10),
            "volume_ratio": ratio,
            "signal": signal,
            "obv_direction": obv_direction,
            "confirms_move": ratio >= 1.5,
        }
    except Exception:
        return None


def calc_stochastic(df: pd.DataFrame) -> Optional[dict]:
    """Stochastic Oscillator (14,3). Overbought >80, oversold <20."""
    try:
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)
        if ta is not None:
            stoch = ta.stoch(high, low, close, k=14, d=3)
            if stoch is None or stoch.empty:
                return None
            stoch = stoch.dropna()
            if stoch.empty:
                return None
            k_v = float(stoch.iloc[-1, 0])
            d_v = float(stoch.iloc[-1, 1])
        else:
            ll = low.rolling(14, min_periods=14).min()
            hh = high.rolling(14, min_periods=14).max()
            k_series = 100 * (close - ll) / (hh - ll).replace(0, np.nan)
            d_series = k_series.rolling(3, min_periods=3).mean()
            if d_series.dropna().empty:
                return None
            k_v = float(k_series.iloc[-1])
            d_v = float(d_series.iloc[-1])

        k = round(k_v, 2)
        d = round(d_v, 2)
        return {
            "k": k,
            "d": d,
            "overbought": k > 80,
            "oversold": k < 20,
            "bullish_cross": k > d and k < 80,
            "bearish_cross": k < d and k > 20,
        }
    except Exception:
        return None


def run_all_indicators(candles: list) -> dict:
    """
    Run all indicators on candle data.
    Returns complete indicator dict. Safe — never raises.
    """
    result = {
        "rsi": None,
        "macd": None,
        "bollinger": None,
        "ema": None,
        "atr": None,
        "volume": None,
        "stochastic": None,
        "sufficient_data": False,
        "candle_count": len(candles) if candles else 0,
    }

    df = prepare_dataframe(candles)
    if df is None:
        return result

    result["sufficient_data"] = True
    result["rsi"] = calc_rsi(df)
    result["macd"] = calc_macd(df)
    result["bollinger"] = calc_bollinger(df)
    result["ema"] = calc_ema(df)
    result["atr"] = calc_atr(df)
    result["volume"] = calc_volume_analysis(df)
    result["stochastic"] = calc_stochastic(df)
    result["candle_count"] = len(df)

    return result

