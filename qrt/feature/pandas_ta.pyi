"""Auto-generated stubs for the dynamic indicator wrappers (IDE support).

Do not edit by hand. Regenerate with:

    uv run python tools/gen_feat_stubs.py
"""

from typing import Any

import pandas as pd


def aberration(data: pd.Series | pd.DataFrame, length: Any = None, atr_length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Aberration

    A volatility indicator similar to Keltner Channels.

    Sources:
        Few internet resources on definitive definition.
        Request by Github user homily, issue #46

    Calculation:
        Default Inputs:
            length=5, atr_length=15
        ATR = Average True Range
        SMA = Simple Moving Average

        ATR = ATR(length=atr_length)
        JG = TP = HLC3(high, low, close)
        ZG = SMA(JG, length)
        SG = ZG + ATR
        XG = ZG - ATR

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): The short period. Default: 5
        atr_length (int): The short period. Default: 15
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: zg, sg, xg, atr columns.
    """
    ...

def accbands(data: pd.Series | pd.DataFrame, length: Any = None, c: Any = None, drift: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Acceleration Bands (ACCBANDS)

    Acceleration Bands created by Price Headley plots upper and lower envelope
    bands around a simple moving average.

    Sources:
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/acceleration-bands-abands/

    Calculation:
        Default Inputs:
            length=10, c=4
        EMA = Exponential Moving Average
        SMA = Simple Moving Average
        HL_RATIO = c * (high - low) / (high + low)
        LOW = low * (1 - HL_RATIO)
        HIGH = high * (1 + HL_RATIO)

        if 'ema':
            LOWER = EMA(LOW, length)
            MID = EMA(close, length)
            UPPER = EMA(HIGH, length)
        else:
            LOWER = SMA(LOW, length)
            MID = SMA(close, length)
            UPPER = SMA(HIGH, length)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        c (int): Multiplier. Default: 4
        mamode (str): See ```help(ta.ma)```. Default: 'sma'
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: lower, mid, upper columns.
    """
    ...

def ad(data: pd.Series | pd.DataFrame, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Accumulation/Distribution (AD)

    Accumulation/Distribution indicator utilizes the relative position
    of the close to it's High-Low range with volume.  Then it is cumulated.

    Sources:
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/accumulationdistribution-ad/

    Calculation:
        CUM = Cumulative Sum
        if 'open':
            AD = close - open
        else:
            AD = 2 * close - high - low

        hl_range = high - low
        AD = AD * volume / hl_range
        AD = CUM(AD)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        open (pd.Series): Series of 'open's
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def adosc(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Accumulation/Distribution Oscillator or Chaikin Oscillator

    Accumulation/Distribution Oscillator indicator utilizes
    Accumulation/Distribution and treats it similarily to MACD
    or APO.

    Sources:
        https://www.investopedia.com/articles/active-trading/031914/understanding-chaikin-oscillator.asp

    Calculation:
        Default Inputs:
            fast=12, slow=26
        AD = Accum/Dist
        ad = AD(high, low, close, open)
        fast_ad = EMA(ad, fast)
        slow_ad = EMA(ad, slow)
        ADOSC = fast_ad - slow_ad

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        open (pd.Series): Series of 'open's
        volume (pd.Series): Series of 'volume's
        fast (int): The short period. Default: 12
        slow (int): The long period. Default: 26
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def adx(data: pd.Series | pd.DataFrame, length: Any = None, lensig: Any = None, scalar: Any = None, mamode: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Average Directional Movement (ADX)

    Average Directional Movement is meant to quantify trend strength by measuring
    the amount of movement in a single direction.

    Sources:
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/average-directional-movement-adx/
        TA Lib Correlation: >99%

    Calculation:
        DMI ADX TREND 2.0 by @TraderR0BERT, NETWORTHIE.COM
            //Created by @TraderR0BERT, NETWORTHIE.COM, last updated 01/26/2016
            //DMI Indicator
            //Resolution input option for higher/lower time frames
            study(title="DMI ADX TREND 2.0", shorttitle="ADX TREND 2.0")

            adxlen = input(14, title="ADX Smoothing")
            dilen = input(14, title="DI Length")
            thold = input(20, title="Threshold")

            threshold = thold

            //Script for Indicator
            dirmov(len) =>
                up = change(high)
                down = -change(low)
                truerange = rma(tr, len)
                plus = fixnan(100 * rma(up > down and up > 0 ? up : 0, len) / truerange)
                minus = fixnan(100 * rma(down > up and down > 0 ? down : 0, len) / truerange)
                [plus, minus]

            adx(dilen, adxlen) =>
                [plus, minus] = dirmov(dilen)
                sum = plus + minus
                adx = 100 * rma(abs(plus - minus) / (sum == 0 ? 1 : sum), adxlen)
                [adx, plus, minus]

            [sig, up, down] = adx(dilen, adxlen)
            osob=input(40,title="Exhaustion Level for ADX, default = 40")
            col = sig >= sig[1] ? green : sig <= sig[1] ? red : gray

            //Plot Definitions Current Timeframe
            p1 = plot(sig, color=col, linewidth = 3, title="ADX")
            p2 = plot(sig, color=col, style=circles, linewidth=3, title="ADX")
            p3 = plot(up, color=blue, linewidth = 3, title="+DI")
            p4 = plot(up, color=blue, style=circles, linewidth=3, title="+DI")
            p5 = plot(down, color=fuchsia, linewidth = 3, title="-DI")
            p6 = plot(down, color=fuchsia, style=circles, linewidth=3, title="-DI")
            h1 = plot(threshold, color=black, linewidth =3, title="Threshold")

            trender = (sig >= up or sig >= down) ? 1 : 0
            bgcolor(trender>0?black:gray, transp=85)

            //Alert Function for ADX crossing Threshold
            Up_Cross = crossover(up, threshold)
            alertcondition(Up_Cross, title="DMI+ cross", message="DMI+ Crossing Threshold")
            Down_Cross = crossover(down, threshold)
            alertcondition(Down_Cross, title="DMI- cross", message="DMI- Crossing Threshold")

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        lensig (int): Signal Length. Like TradingView's default ADX. Default: length
        scalar (float): How much to magnify. Default: 100
        mamode (str): See ```help(ta.ma)```. Default: 'rma'
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: adx, dmp, dmn columns.
    """
    ...

def adxr(data: pd.Series | pd.DataFrame, length: Any = None, lensig: Any = None, scalar: Any = None, mamode: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Average Directional Movement Index Rating (ADXR)

    ADXR is the average of the current ADX and the ADX from one period
    (length - 1) ago. It smooths the ADX and is used to confirm trend strength.

    Sources:
        https://www.investopedia.com/terms/a/adxr.asp
        TA Lib

    Calculation:
        Default Inputs:
            length=14
        ADX = Average Directional Index
        ADXR = (ADX + ADX.shift(length - 1)) / 2

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): The period. Default: 14
        lensig (int): Signal length. Default: length
        scalar (float): How much to magnify. Default: 100
        mamode (str): See ``help(ta.ma)``. Default: 'rma'
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: adxr, dmp, dmn columns.
    """
    ...

def alma(data: pd.Series | pd.DataFrame, length: Any = None, sigma: Any = None, distribution_offset: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Arnaud Legoux Moving Average (ALMA)

    The ALMA moving average uses the curve of the Normal (Gauss) distribution, which
    can be shifted from 0 to 1. This allows regulating the smoothness and high
    sensitivity of the indicator. Sigma is another parameter that is responsible for
    the shape of the curve coefficients. This moving average reduces lag of the data
    in conjunction with smoothing to reduce noise.

    Implemented for Pandas TA by rengel8 based on the source provided below.

    Sources:
        https://www.prorealcode.com/prorealtime-indicators/alma-arnaud-legoux-moving-average/

    Calculation:
        refer to provided source

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period, window size. Default: 10
        sigma (float): Smoothing value. Default 6.0
        distribution_offset (float): Value to offset the distribution min 0
            (smoother), max 1 (more responsive). Default 0.85
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def amat(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, lookback: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Archer Moving Averages Trends (AMAT)

    The Archer Moving Averages Trends indicator identifies trend direction by comparing
    fast and slow moving averages. It generates long and short run signals based on the
    relationship between the two moving averages over a lookback period.

    Sources:
        https://www.tradingview.com/script/nhQe8QJ0-Archer-Moving-Averages-Trends/

    Calculation:
        Default Inputs:
            fast=8, slow=21, lookback=2, mamode="ema"

        FAST_MA = MA(close, fast, mamode)
        SLOW_MA = MA(close, slow, mamode)

        AMAT_LR = LONG_RUN(FAST_MA, SLOW_MA, lookback)
        AMAT_SR = SHORT_RUN(FAST_MA, SLOW_MA, lookback)

    Args:
        close (pd.Series): Series of 'close's
        fast (int): Fast MA period. Default: 8
        slow (int): Slow MA period. Default: 21
        lookback (int): Lookback period for trend detection. Default: 2
        mamode (str): See ```help(ta.ma)```. Default: 'ema'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: AMAT_LR and AMAT_SR columns.
    """
    ...

def ao(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Awesome Oscillator (AO)

    The Awesome Oscillator is an indicator used to measure a security's momentum.
    AO is generally used to affirm trends or to anticipate possible reversals.

    Sources:
        https://www.tradingview.com/wiki/Awesome_Oscillator_(AO)
        https://www.ifcm.co.uk/ntx-indicators/awesome-oscillator

    Calculation:
        Default Inputs:
            fast=5, slow=34
        SMA = Simple Moving Average
        median = (high + low) / 2
        AO = SMA(median, fast) - SMA(median, slow)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        fast (int): The short period. Default: 5
        slow (int): The long period. Default: 34
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def aobv(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, max_lookback: Any = None, min_lookback: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Archer On Balance Volume (AOBV)

    Archer On Balance Volume enhances the traditional OBV indicator by applying moving
    averages and detecting long/short run trends. It provides multiple signals including
    OBV with min/max bounds, fast/slow moving averages of OBV, and trend direction signals.

    Sources:
        Derived from OBV (On Balance Volume)
        https://www.investopedia.com/terms/o/onbalancevolume.asp

    Calculation:
        Default Inputs:
            fast=4, slow=12, max_lookback=2, min_lookback=2, mamode="ema", run_length=2

        OBV = On Balance Volume(close, volume)
        OBV_MIN = ROLLING_MIN(OBV, min_lookback)
        OBV_MAX = ROLLING_MAX(OBV, max_lookback)
        FAST_MA = MA(OBV, fast, mamode)
        SLOW_MA = MA(OBV, slow, mamode)
        AOBV_LR = LONG_RUN(FAST_MA, SLOW_MA, run_length)
        AOBV_SR = SHORT_RUN(FAST_MA, SLOW_MA, run_length)

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        fast (int): Fast MA period. Default: 4
        slow (int): Slow MA period. Default: 12
        max_lookback (int): Max lookback period. Default: 2
        min_lookback (int): Min lookback period. Default: 2
        mamode (str): See ```help(ta.ma)```. Default: 'ema'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        run_length (int, optional): Lookback for long/short run. Default: 2
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: OBV, OBV_min, OBV_max, fast MA, slow MA, AOBV_LR, AOBV_SR columns.
    """
    ...

def apo(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, mamode: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Absolute Price Oscillator (APO)

    The Absolute Price Oscillator is an indicator used to measure a security's
    momentum.  It is simply the difference of two Exponential Moving Averages
    (EMA) of two different periods. Note: APO and MACD lines are equivalent.

    Sources:
        https://www.tradingtechnologies.com/xtrader-help/x-study/technical-indicator-definitions/absolute-price-oscillator-apo/

    Calculation:
        Default Inputs:
            fast=12, slow=26
        SMA = Simple Moving Average
        APO = SMA(close, fast) - SMA(close, slow)

    Args:
        close (pd.Series): Series of 'close's
        fast (int): The short period. Default: 12
        slow (int): The long period. Default: 26
        mamode (str): See ```help(ta.ma)```. Default: 'sma'
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def aroon(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Aroon & Aroon Oscillator (AROON)

    Aroon attempts to identify if a security is trending and how strong.

    Sources:
        https://www.tradingview.com/wiki/Aroon
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/aroon-ar/

    Calculation:
        Default Inputs:
            length=1, scalar=100

        recent_maximum_index(x): return int(np.argmax(x[::-1]))
        recent_minimum_index(x): return int(np.argmin(x[::-1]))

        periods_from_hh = high.rolling(length + 1).apply(recent_maximum_index, raw=True)
        AROON_UP = scalar * (1 - (periods_from_hh / length))

        periods_from_ll = low.rolling(length + 1).apply(recent_minimum_index, raw=True)
        AROON_DN = scalar * (1 - (periods_from_ll / length))

        AROON_OSC = AROON_UP - AROON_DN

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        scalar (float): How much to magnify. Default: 100
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: aroon_up, aroon_down, aroon_osc columns.
    """
    ...

def atr(data: pd.Series | pd.DataFrame, length: Any = None, mamode: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Average True Range (ATR)

    Averge True Range is used to measure volatility, especially volatility caused by
    gaps or limit moves.

    Sources:
        https://www.tradingview.com/wiki/Average_True_Range_(ATR)

    Calculation:
        Default Inputs:
            length=14, drift=1, percent=False
        EMA = Exponential Moving Average
        SMA = Simple Moving Average
        WMA = Weighted Moving Average
        RMA = WildeR's Moving Average
        TR = True Range

        tr = TR(high, low, close, drift)
        if 'ema':
            ATR = EMA(tr, length)
        elif 'sma':
            ATR = SMA(tr, length)
        elif 'wma':
            ATR = WMA(tr, length)
        else:
            ATR = RMA(tr, length)

        if percent:
            ATR *= 100 / close

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        mamode (str): See ```help(ta.ma)```. Default: 'rma'
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        percent (bool, optional): Return as percentage. Default: False
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def avgprice(data: pd.Series | pd.DataFrame, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Average Price (AVGPRICE)

    AVGPRICE = (Open + High + Low + Close) / 4

    Equivalent to ta.ohlc4.  TA-Lib name: AVGPRICE.

    Args:
        open_ (pd.Series): Series of 'open' prices
        high (pd.Series): Series of 'high' prices
        low (pd.Series): Series of 'low' prices
        close (pd.Series): Series of 'close' prices
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): Periods to offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series
    """
    ...

def avolume(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Annualised Historical Volatility (VOLATILITY)

    Population standard deviation of log-returns annualised by sqrt(252).

    Formula:
        log_ret = log(close / prev_close)
        VOLATILITY = std(log_ret[-length:], ddof=0) * sqrt(252)

    Equivalent to tulipy.volatility(close, period=length).
    See ta.hvol for the percentage version using sample std (ddof=1).

    tulipy name: VOLATILITY.

    Args:
        close (pd.Series): Series of 'close' prices
        length (int): Lookback period. Default: 20
        offset (int): Periods to offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series
    """
    ...

def bbands(data: pd.Series | pd.DataFrame, length: Any = None, std: Any = None, ddof: Any = 0, mamode: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Bollinger Bands (BBANDS)

    A popular volatility indicator by John Bollinger.

    Sources:
        https://www.tradingview.com/wiki/Bollinger_Bands_(BB)

    Calculation:
        Default Inputs:
            length=5, std=2, mamode="sma", ddof=0
        EMA = Exponential Moving Average
        SMA = Simple Moving Average
        STDEV = Standard Deviation
        stdev = STDEV(close, length, ddof)
        if "ema":
            MID = EMA(close, length)
        else:
            MID = SMA(close, length)

        LOWER = MID - std * stdev
        UPPER = MID + std * stdev

        BANDWIDTH = 100 * (UPPER - LOWER) / MID
        PERCENT = (close - LOWER) / (UPPER - LOWER)

    Args:
        close (pd.Series): Series of 'close's
        length (int): The short period. Default: 5
        std (int): The long period. Default: 2
        ddof (int): Degrees of Freedom to use. Default: 0
        mamode (str): See ```help(ta.ma)```. Default: 'sma'
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: lower, mid, upper, bandwidth, and percent columns.
    """
    ...

def beta(data: pd.Series | pd.DataFrame, benchmark: Any = None, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Beta (BETA)

    Beta measures the sensitivity of a security's returns to the returns of a
    benchmark.  A beta of 1 means the security moves with the benchmark;
    above 1 means more volatile, below 1 means less volatile.

    Sources:
        https://www.investopedia.com/terms/b/beta.asp

    Calculation:
        Default Inputs:
            length=30
        BETA = COV(close_ret, bench_ret, length) / VAR(bench_ret, length)

    Args:
        close (pd.Series): Series of 'close's
        benchmark (pd.Series): Series of benchmark 'close's
        length (int): The period. Default: 30
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        min_periods (int): Minimum observations required. Default: length
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
        None: If benchmark is not provided; enables df.ta.strategy("all") compatibility.
    """
    ...

def bias(data: pd.Series | pd.DataFrame, length: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Bias (BIAS)

    Rate of change between the source and a moving average.

    Sources:
        Few internet resources on definitive definition.
        Request by Github user homily, issue #46

    Calculation:
        Default Inputs:
            length=26, MA='sma'

        BIAS = (close - MA(close, length)) / MA(close, length)
             = (close / MA(close, length)) - 1

    Args:
        close (pd.Series): Series of 'close's
        length (int): The period. Default: 26
        mamode (str): See ```help(ta.ma)```. Default: 'sma'
        drift (int): The short period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def bop(data: pd.Series | pd.DataFrame, scalar: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Balance of Power (BOP)

    Balance of Power measure the market strength of buyers against sellers.

    Sources:
        http://www.worden.com/TeleChartHelp/Content/Indicators/Balance_of_Power.htm

    Calculation:
        BOP = scalar * (close - open) / (high - low)

    Args:
        open (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        scalar (float): How much to magnify. Default: 1
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def brar(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    BRAR (BRAR)

    BR and AR

    Sources:
        No internet resources on definitive definition.
        Request by Github user homily, issue #46

    Calculation:
        Default Inputs:
            length=26, scalar=100
        SUM = Sum

        HO_Diff = high - open
        OL_Diff = open - low
        HCY = high - close[-1]
        CYL = close[-1] - low
        HCY[HCY < 0] = 0
        CYL[CYL < 0] = 0
        AR = scalar * SUM(HO, length) / SUM(OL, length)
        BR = scalar * SUM(HCY, length) / SUM(CYL, length)

    Args:
        open_ (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): The period. Default: 26
        scalar (float): How much to magnify. Default: 100
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: ar, br columns.
    """
    ...

def cci(data: pd.Series | pd.DataFrame, length: Any = None, c: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Commodity Channel Index (CCI)

    Commodity Channel Index is a momentum oscillator used to primarily identify
    overbought and oversold levels relative to a mean.

    Sources:
        https://www.tradingview.com/wiki/Commodity_Channel_Index_(CCI)

    Calculation:
        Default Inputs:
            length=14, c=0.015
        SMA = Simple Moving Average
        MAD = Mean Absolute Deviation
        tp = typical_price = hlc3 = (high + low + close) / 3
        mean_tp = SMA(tp, length)
        mad_tp = MAD(tp, length)
        CCI = (tp - mean_tp) / (c * mad_tp)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        c (float): Scaling Constant. Default: 0.015
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def cdl_doji(data: pd.Series | pd.DataFrame, length: Any = None, factor: Any = None, scalar: Any = None, asint: Any = True, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Candle Type: Doji

    A candle body is Doji, when it's shorter than 10% of the
    average of the 10 previous candles' high-low range.

    Sources:
        TA-Lib: 96.56% Correlation

    Calculation:
        Default values:
            length=10, percent=10 (0.1), scalar=100
        ABS = Absolute Value
        SMA = Simple Moving Average

        BODY = ABS(close - open)
        HL_RANGE = ABS(high - low)

        DOJI = scalar IF BODY < 0.01 * percent * SMA(HL_RANGE, length) ELSE 0

    Args:
        open_ (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): The period. Default: 10
        factor (float): Doji value. Default: 100
        scalar (float): How much to magnify. Default: 100
        asint (bool): Keep results numerical instead of boolean. Default: True

    Kwargs:
        naive (bool, optional): If True, prefills potential Doji less than
            the length if less than a percentage of it's high-low range.
            Default: False
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: CDL_DOJI column.
    """
    ...

def cdl_inside(data: pd.Series | pd.DataFrame, asbool: Any = False, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Candle Type: Inside Bar

    An Inside Bar is a bar that is engulfed by the prior highs and lows of it's
    previous bar. In other words, the current bar is smaller than it's previous bar.
    Set asbool=True if you want to know if it is an Inside Bar. Note by default
    asbool=False so this returns a 0 if it is not an Inside Bar, 1 if it is an
    Inside Bar and close > open, and -1 if it is an Inside Bar but close < open.

    Sources:
        https://www.tradingview.com/script/IyIGN1WO-Inside-Bar/

    Calculation:
        Default Inputs:
            asbool=False
        inside = (high.diff() < 0) & (low.diff() > 0)

        if not asbool:
            inside *= candle_color(open_, close)

    Args:
        open_ (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        asbool (bool): Returns the boolean result. Default: False
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature
    """
    ...

def cdl_pattern(data: pd.Series | pd.DataFrame, name: Any = 'all', scalar: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Candle Pattern

    A wrapper around all candle patterns.

    Examples:

    Get all candle patterns (This is the default behaviour)
    >>> df = df.ta.cdl_pattern(name="all")
    Or
    >>> df.ta.cdl("all", append=True) # = df.ta.cdl_pattern("all", append=True)

    Get only one pattern
    >>> df = df.ta.cdl_pattern(name="doji")
    Or
    >>> df.ta.cdl("doji", append=True)

    Get some patterns
    >>> df = df.ta.cdl_pattern(name=["doji", "inside"])
    Or
    >>> df.ta.cdl(["doji", "inside"], append=True)

    Args:
        open_ (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        name: (Union[str, Sequence[str]]): name of the patterns
        scalar (float): How much to magnify. Default: 100
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: one column for each pattern.
    """
    ...

def cdl_z(data: pd.Series | pd.DataFrame, length: Any = None, full: Any = None, ddof: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Candle Type: Z

    Normalizes OHLC Candles with a rolling Z Score.

    Source: Kevin Johnson

    Calculation:
        Default values:
            length=30, full=False, ddof=1
        Z = ZSCORE

        open  = Z( open, length, ddof)
        high  = Z( high, length, ddof)
        low   = Z(  low, length, ddof)
        close = Z(close, length, ddof)

    Args:
        open_ (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): The period. Default: 10

    Kwargs:
        naive (bool, optional): If True, prefills potential Doji less than
            the length if less than a percentage of it's high-low range.
            Default: False
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: CDL_DOJI column.
    """
    ...

def ce(data: pd.Series | pd.DataFrame, length: Any = None, multiplier: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Chandelier Exit (CE)

    The Chandelier Exit is a volatility-based trailing stop indicator that uses the
    Average True Range (ATR) to determine exit levels. It helps traders stay in a
    trend while providing dynamic stop-loss levels based on market volatility.

    Sources:
        https://www.tradingview.com/support/solutions/43000773013-chandelier-exit/
        https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit

    Calculation:
        Default Inputs:
            length=22, multiplier=3.0
        ATR = Average True Range(length)
        Highest High = rolling max(high, length)
        Lowest Low = rolling min(low, length)

        CE Long = Highest High - (Multiplier * ATR)
        CE Short = Lowest Low + (Multiplier * ATR)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): Lookback period for High/Low and ATR. Default: 22
        multiplier (float): ATR multiplier. Default: 3.0
        mamode (str): See ``help(ta.ma)``. Default: 'rma'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method ('ffill' or 'bfill')

    Returns:
        pd.DataFrame: CE_L (Long) and CE_S (Short) columns.

    Examples:
        >>> import pandas as pd
        >>> import pandas_ta_classic as ta
        >>> df = pd.DataFrame({
        ...     "high":  [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        ...     "low":   [5,  6,  7,  8,  9,  10, 11, 12, 13, 14],
        ...     "close": [7,  8,  9,  10, 11, 12, 13, 14, 15, 16],
        ... })
        >>> result = ta.ce(high=df["high"], low=df["low"], close=df["close"], length=5)
        >>> result.tail()
    """
    ...

def cfo(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Chande Forcast Oscillator (CFO)

    The Forecast Oscillator calculates the percentage difference between the actual
    price and the Time Series Forecast (the endpoint of a linear regression line).

    Sources:
        https://www.fmlabs.com/reference/default.htm?url=ForecastOscillator.htm

    Calculation:
        Default Inputs:
            length=9, drift=1, scalar=100
        LINREG = Linear Regression

        CFO = scalar * (close - LINERREG(length, tdf=True)) / close

    Args:
        close (pd.Series): Series of 'close's
        length (int): The period. Default: 9
        scalar (float): How much to magnify. Default: 100
        drift (int): The short period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def cg(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Center of Gravity (CG)

    The Center of Gravity Indicator by John Ehlers attempts to identify turning
    points while exhibiting zero lag and smoothing.

    Sources:
        http://www.mesasoftware.com/papers/TheCGOscillator.pdf

    Calculation:
        Default Inputs:
            length=10

    Args:
        close (pd.Series): Series of 'close's
        length (int): The length of the period. Default: 10
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def chop(data: pd.Series | pd.DataFrame, length: Any = None, atr_length: Any = None, ln: Any = None, scalar: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Choppiness Index (CHOP)

    The Choppiness Index was created by Australian commodity trader
    E.W. Dreiss and is designed to determine if the market is choppy
    (trading sideways) or not choppy (trading within a trend in either
    direction). Values closer to 100 implies the underlying is choppier
    whereas values closer to 0 implies the underlying is trending.

    Sources:
        https://www.tradingview.com/scripts/choppinessindex/
        https://www.motivewave.com/studies/choppiness_index.htm

    Calculation:
        Default Inputs:
            length=14, scalar=100, drift=1
        HH = high.rolling(length).max()
        LL = low.rolling(length).min()

        ATR_SUM = SUM(ATR(drift), length)
        CHOP = scalar * (LOG10(ATR_SUM) - LOG10(HH - LL))
        CHOP /= LOG10(length)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        atr_length (int): Length for ATR. Default: 1
        ln (bool): If True, uses ln otherwise log10. Default: False
        scalar (float): How much to magnify. Default: 100
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def cksp(data: pd.Series | pd.DataFrame, p: Any = None, x: Any = None, q: Any = None, tvmode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Chande Kroll Stop (CKSP)

    The Tushar Chande and Stanley Kroll in their book
    “The New Technical Trader”. It is a trend-following indicator,
    identifying your stop by calculating the average true range of
    the recent market volatility. The indicator defaults to the implementation
    found on tradingview but it provides the original book implementation as well,
    which differs by the default periods and moving average mode. While the trading
    view implementation uses the Welles Wilder moving average, the book uses a
    simple moving average.

    Sources:
        https://www.multicharts.com/discussion/viewtopic.php?t=48914
        "The New Technical Trader", Wikey 1st ed. ISBN 9780471597803, page 95

    Calculation:
        Default Inputs:
            p=10, x=1, q=9, tvmode=True
        ATR = Average True Range

        LS0 = high.rolling(p).max() - x * ATR(length=p)
        LS = LS0.rolling(q).max()

        SS0 = high.rolling(p).min() + x * ATR(length=p)
        SS = SS0.rolling(q).min()

    Args:
        close (pd.Series): Series of 'close's
        p (int): ATR and first stop period. Default: 10 in both modes
        x (float): ATR scalar. Default: 1 in TV mode, 3 otherwise
        q (int): Second stop period. Default: 9 in TV mode, 20 otherwise
        tvmode (bool): Trading View or book implementation mode. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: long and short columns.
    """
    ...

def cmf(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Chaikin Money Flow (CMF)

    Chailin Money Flow measures the amount of money flow volume over a specific
    period in conjunction with Accumulation/Distribution.

    Sources:
        https://www.tradingview.com/wiki/Chaikin_Money_Flow_(CMF)
        https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:chaikin_money_flow_cmf

    Calculation:
        Default Inputs:
            length=20
        if 'open':
            ad = close - open
        else:
            ad = 2 * close - high - low

        hl_range = high - low
        ad = ad * volume / hl_range
        CMF = SUM(ad, length) / SUM(volume, length)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        open_ (pd.Series): Series of 'open's. Default: None
        length (int): The short period. Default: 20
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def cmo(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Chande Momentum Oscillator (CMO)

    Attempts to capture the momentum of an asset with overbought at 50 and
    oversold at -50.

    Sources:
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/chande-momentum-oscillator-cmo/
        https://www.tradingview.com/script/hdrf0fXV-Variable-Index-Dynamic-Average-VIDYA/

    Calculation:
        Default Inputs:
            drift=1, scalar=100

        # Same Calculation as RSI except for this step
        CMO = scalar * (PSUM - NSUM) / (PSUM + NSUM)

    Args:
        close (pd.Series): Series of 'close's
        scalar (float): How much to magnify. Default: 100
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. If TA Lib is not installed but talib is True, it runs the Python
            version TA Lib. Default: True
        drift (int): The short period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        talib (bool): If True, uses TA-Libs implementation. Otherwise uses EMA version. Default: False
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def coppock(data: pd.Series | pd.DataFrame, length: Any = None, fast: Any = None, slow: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Coppock Curve (COPC)

    Coppock Curve (originally called the "Trendex Model") is a momentum indicator
    is designed for use on a monthly time scale.  Although designed for monthly
    use, a daily calculation over the same period can be made, converting the
    periods to 294-day and 231-day rate of changes, and a 210-day weighted
    moving average.

    Sources:
        https://en.wikipedia.org/wiki/Coppock_curve

    Calculation:
        Default Inputs:
            length=10, fast=11, slow=14
        SMA = Simple Moving Average
        MAD = Mean Absolute Deviation
        tp = typical_price = hlc3 = (high + low + close) / 3
        mean_tp = SMA(tp, length)
        mad_tp = MAD(tp, length)
        CCI = (tp - mean_tp) / (c * mad_tp)

    Args:
        close (pd.Series): Series of 'close's
        length (int): WMA period. Default: 10
        fast (int): Fast ROC period. Default: 11
        slow (int): Slow ROC period. Default: 14
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def correl(data: pd.Series | pd.DataFrame, benchmark: Any = None, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Pearson Correlation Coefficient (CORREL)

    The Pearson Correlation Coefficient measures the linear relationship between
    two series over a rolling window.  Values range from -1 (perfect negative
    correlation) to +1 (perfect positive correlation).

    Sources:
        https://www.investopedia.com/terms/c/correlationcoefficient.asp

    Calculation:
        Default Inputs:
            length=30
        CORREL = close.rolling(length).corr(benchmark)

    Args:
        close (pd.Series): Series of 'close's
        benchmark (pd.Series): Series of benchmark 'close's
        length (int): The period. Default: 30
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        min_periods (int): Minimum observations required. Default: length
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
        None: If benchmark is not provided; enables df.ta.strategy("all") compatibility.
    """
    ...

def cpr(data: pd.Series | pd.DataFrame, method: Any = 'classic', timeframe: Any = 'daily', interval: Any = None, levels: Any = 'standard', width_analysis: Any = True, price_position: Any = True, virgin_cpr: Any = False, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    CPR (Central Pivot Range)

    Central Pivot Range is a trending indicator that helps identify potential
    support and resistance levels for the trading session based on previous
    period's price action.

    Sources:
        https://tradingqna.com/what-is-central-pivot-range-cpr-how-to-trade-using-it/
        https://www.incrediblecharts.com/indicators/pivot_point_calculator.php

    Examples:
        import pandas_ta_classic as ta
        df.ta.cpr(method='classic', timeframe='daily', levels='standard', append=True)
        df.ta.cpr(method='camarilla', levels='all', virgin_cpr=True, append=True)

        # Intraday CPR
        df.ta.cpr(method='classic', timeframe='intraday', interval='5min', append=True)

        # Direct function call
        result = ta.cpr(df['open'], df['high'], df['low'], df['close'],
                        method='fibonacci', levels='extended')

    Calculation:
        Default Inputs:
            method="classic", timeframe="daily", levels="standard"

        Classic Floor Pivots:
            Pivot = (H + L + C) / 3
            BC = (H + L) / 2
            TC = (Pivot - BC) + Pivot
            R1 = (2 * Pivot) - L
            S1 = (2 * Pivot) - H
            R2 = Pivot + (H - L)
            S2 = Pivot - (H - L)
            R3 = H + 2 * (Pivot - L)
            S3 = L - 2 * (H - Pivot)
            R4 = H + 3 * (Pivot - L)
            S4 = L - 3 * (H - Pivot)

        Camarilla Pivots:
            Pivot = (H + L + C) / 3
            BC = (H + L) / 2
            TC = (Pivot - BC) + Pivot
            Range = H - L
            R1 = C + (Range * 1.1/12)
            R2 = C + (Range * 1.1/6)
            R3 = C + (Range * 1.1/4)
            R4 = C + (Range * 1.1/2)
            S1 = C - (Range * 1.1/12)
            S2 = C - (Range * 1.1/6)
            S3 = C - (Range * 1.1/4)
            S4 = C - (Range * 1.1/2)

        Fibonacci Pivots:
            Pivot = (H + L + C) / 3
            BC = (H + L) / 2
            TC = (Pivot - BC) + Pivot
            Range = H - L
            R1 = Pivot + (Range * 0.382)
            R2 = Pivot + (Range * 0.618)
            R3 = Pivot + (Range * 1.000)
            S1 = Pivot - (Range * 0.382)
            S2 = Pivot - (Range * 0.618)
            S3 = Pivot - (Range * 1.000)

        Woodie's Pivots:
            Pivot = (H + L + 2*C) / 4
            BC = (H + L) / 2
            TC = (Pivot - BC) + Pivot
            R1 = (2 * Pivot) - L
            S1 = (2 * Pivot) - H
            R2 = Pivot + (H - L)
            S2 = Pivot - (H - L)

    Args:
        open (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        volume (pd.Series, optional): Series of 'volume's
        method (str): Pivot calculation method.
            Options: 'classic', 'camarilla', 'fibonacci', 'woodie'. Default: 'classic'
        timeframe (str): Time context for CPR calculation.
            Options: 'intraday', 'daily', 'weekly', 'monthly'. Default: 'daily'
        interval (str, optional): For intraday only - data interval.
            Examples: '1min', '5min', '15min', '30min', '1H'. Default: None
        levels (str): Which pivot levels to calculate.
            Options: 'basic' (TC/P/BC), 'standard' (+R1/R2/S1/S2),
                     'extended' (+R3/R4/S3/S4), 'all'. Default: 'standard'
        width_analysis (bool): Calculate CPR width metrics. Default: True
        price_position (bool): Calculate price position relative to CPR. Default: True
        virgin_cpr (bool): Detect virgin (untested) CPR levels. Default: False
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        width_narrow (float): Threshold for narrow CPR classification (%). Default: 0.5
        width_wide (float): Threshold for wide CPR classification (%). Default: 1.5
        virgin_lookforward (int): Periods to look ahead for virgin CPR detection. Default: 5
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: CPR levels and analysis columns.
            Core columns: CPR_TC, CPR_PIVOT, CPR_BC
            S/R columns (depends on 'levels'): CPR_R1, CPR_R2, CPR_S1, CPR_S2, etc.
            Analysis columns: CPR_WIDTH (float), CPR_WIDTH_PCT (float),
                CPR_WIDTH_CLASS (int8: -1=narrow, 0=medium, 1=wide),
                CPR_POSITION (int8: -1=below BC, 0=inside CPR, 1=above TC),
                CPR_VIRGIN (bool)
    """
    ...

def cti(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Correlation Trend Indicator (CTI)

    The Correlation Trend Indicator is an oscillator created by John Ehler in 2020.
    It assigns a value depending on how close prices in that range are to following
    a positively- or negatively-sloping straight line. Values range from -1 to 1.
    This is a wrapper for ta.linreg(close, r=True).

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 12
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: Series of the CTI values for the given period.
    """
    ...

def cvi(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Chaikins Volatility (CVI)

    Chaikins Volatility measures the range between the high and low prices by
    calculating the rate of change of the exponential moving average of the
    High-Low spread. Rising CVI indicates expanding volatility; falling CVI
    indicates contracting volatility.

    HL = High - Low
    EMA_HL = EMA(HL, length)
    CVI = 100 * (EMA_HL - EMA_HL[length]) / EMA_HL[length]

    Sources:
        Marc Chaikin
        https://school.stockcharts.com/doku.php?id=technical_indicators:chaikins_volatility

    Args:
        high (pd.Series): High price series.
        low (pd.Series): Low price series.
        length (int): EMA period and lookback. Default: 10
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: CVI values.
    """
    ...

def decay(data: pd.Series | pd.DataFrame, kind: Any = None, length: Any = None, mode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Decay

    Creates a decay moving forward from prior signals like crosses. The default is
    "linear". Exponential is optional as "exponential" or "exp".

    Sources:
        https://tulipindicators.org/decay

    Calculation:
        Default Inputs:
            length=5, mode=None

        if mode == "exponential" or mode == "exp":
            max(close, close[-1] - exp(-length), 0)
        else:
            max(close, close[-1] - (1 / length), 0)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 1
        mode (str): If 'exp' then "exponential" decay. Default: 'linear'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def decreasing(data: pd.Series | pd.DataFrame, length: Any = None, strict: Any = None, asint: Any = None, percent: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Decreasing

    Returns True if the series is decreasing over a period, False otherwise.
    If the kwarg 'strict' is True, it returns True if it is continuously decreasing
    over the period. When using the kwarg 'asint', then it returns 1 for True
    or 0 for False.

    Calculation:
        if strict:
            decreasing = all(i > j for i, j in zip(close[-length:], close[1:]))
        else:
            decreasing = close.diff(length) < 0

        if asint:
            decreasing = decreasing.astype(int)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 1
        strict (bool): If True, checks if the series is continuously decreasing over the period. Default: False
        percent (float): Percent as an integer. Default: None
        asint (bool): Returns as binary. Default: True
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def dema(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Double Exponential Moving Average (DEMA)

    The Double Exponential Moving Average attempts to a smoother average with less
    lag than the normal Exponential Moving Average (EMA).

    Sources:
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/double-exponential-moving-average-dema/

    Calculation:
        Default Inputs:
            length=10
        EMA = Exponential Moving Average
        ema1 = EMA(close, length)
        ema2 = EMA(ema1, length)

        DEMA = 2 * ema1 - ema2

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def dm(data: pd.Series | pd.DataFrame, length: Any = None, mamode: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Directional Movement (DM)

    The Directional Movement was developed by J. Welles Wilder in 1978 attempts to
    determine which direction the price of an asset is moving. It compares prior
    highs and lows to yield to two series +DM and -DM.

    Sources:
        https://www.tradingview.com/pine-script-reference/#fun_dmi
        https://www.sierrachart.com/index.php?page=doc/StudiesReference.php&ID=24&Name=Directional_Movement_Index

    Calculation:
        Default Inputs:
            length=14, mamode="rma", drift=1
                up = high - high.shift(drift)
            dn = low.shift(drift) - low

            pos_ = ((up > dn) & (up > 0)) * up
            neg_ = ((dn > up) & (dn > 0)) * dn

            pos_ = pos_.apply(zero)
            neg_ = neg_.apply(zero)

            # For RMA (default), Wilder cumsum smoothing is used to match TA-Lib.
            # Other MA modes are applied via the standard MA pipeline.
            if mamode == "rma":
                pos = wilder_smooth(pos_, length)
                neg = wilder_smooth(neg_, length)
            else:
                pos = ma(mamode, pos_, length=length)
                neg = ma(mamode, neg_, length=length)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        mamode (str): See ```help(ta.ma)```.  Default: 'rma'
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: False
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: DMP (+DM) and DMN (-DM) columns.
    """
    ...

def donchian(data: pd.Series | pd.DataFrame, lower_length: Any = None, upper_length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Donchian Channels (DC)

    Donchian Channels are used to measure volatility, similar to
    Bollinger Bands and Keltner Channels.

    Sources:
        https://www.tradingview.com/wiki/Donchian_Channels_(DC)

    Calculation:
        Default Inputs:
            lower_length=upper_length=20
        LOWER = low.rolling(lower_length).min()
        UPPER = high.rolling(upper_length).max()
        MID = 0.5 * (LOWER + UPPER)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        lower_length (int): The short period. Default: 20
        upper_length (int): The short period. Default: 20
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: lower, mid, upper columns.
    """
    ...

def dpo(data: pd.Series | pd.DataFrame, length: Any = None, centered: Any = True, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Detrend Price Oscillator (DPO)

    Is an indicator designed to remove trend from price and make it easier to
    identify cycles.

    Sources:
        https://www.tradingview.com/scripts/detrendedpriceoscillator/
        https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/dpo
        http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:detrended_price_osci

    Calculation:
        Default Inputs:
            length=20, centered=True
        SMA = Simple Moving Average
        t = int(0.5 * length) + 1

        DPO = close.shift(t) - SMA(close, length)
        if centered:
            DPO = DPO.shift(-t)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 1
        centered (bool): Shift the dpo back by int(0.5 * length) + 1. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def drawdown(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Drawdown (DD)

    Drawdown is a peak-to-trough decline during a specific period for an investment,
    trading account, or fund. It is usually quoted as the percentage between the
    peak and the subsequent trough.

    Sources:
        https://www.investopedia.com/terms/d/drawdown.asp

    Calculation:
        PEAKDD = close.cummax()
        DD = PEAKDD - close
        DD% = 1 - (close / PEAKDD)
        DDlog = log(PEAKDD / close)

    Args:
        close (pd.Series): Series of 'close's.
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: drawdown, drawdown percent, drawdown log columns
    """
    ...

def dsp(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Detrended Synthetic Price (DSP)

    Detrended Synthetic Price removes the trend component from price data to reveal
    the cyclical component. It's useful for cycle analysis and identifying periodic
    patterns in price movement.

    Sources:
        https://www.mesasoftware.com/papers/TheInverseFisherTransform.pdf
        Cycle Analytics for Traders by John F. Ehlers

    Calculation:
        Default Inputs:
            length=14

        EMA = EMA(close, length)
        DSP = close - EMA

    Args:
        close (pd.Series): Series of 'close's
        length (int): The EMA period. Default: 14
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def dx(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, mamode: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Directional Index (DX)

    The Directional Index (DX) is an intermediate step in calculating the Average
    Directional Index (ADX). It measures the strength of trend direction by
    comparing positive and negative directional movements.

    Sources:
        https://www.investopedia.com/terms/d/dmi.asp

    Args:
        high (pd.Series): High price series.
        low (pd.Series): Low price series.
        close (pd.Series): Close price series.
        length (int): The period. Default: 14
        scalar (float): Scalar multiplier. Default: 100
        mamode (str): Smoothing mode. Default: 'rma'
        talib (bool): Use TA-Lib if installed. Default: False
        drift (int): Drift period. Default: 1
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: DX values.
    """
    ...

def ebsw(data: pd.Series | pd.DataFrame, length: Any = None, bars: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Even Better SineWave (EBSW) *beta*

    This indicator measures market cycles and uses a low pass filter to remove noise.
    Its output is bound signal between -1 and 1 and the maximum length of a detected
    trend is limited by its length input.

    Written by rengel8 for Pandas TA based on a publication at 'prorealcode.com' and
    a book by J.F.Ehlers.

    * This implementation seems to be logically limited. It would make sense to
    implement exactly the version from prorealcode and compare the behaviour.


    Sources:
        https://www.prorealcode.com/prorealtime-indicators/even-better-sinewave/
        J.F.Ehlers 'Cycle Analytics for Traders', 2014

    Calculation:
        refer to 'sources' or implementation

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's max cycle/trend period. Values between 40-48 work like
            expected with minimum value: 39. Default: 40.
        bars (int): Period of low pass filtering. Default: 10
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def edecay(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Exponential Decay (EDECAY)

    Exponential variant of linear decay.  At each bar the value decays by
    exp(-length) from the previous bar, floored at the current close price.

    Equivalent to ta.decay(close, length, mode='exponential').
    tulipy name: EDECAY.

    Args:
        close (pd.Series): Series of 'close' prices
        length (int): Decay period. Default: 5
        offset (int): Periods to offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series
    """
    ...

def efi(data: pd.Series | pd.DataFrame, length: Any = None, mamode: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Elder's Force Index (EFI)

    Elder's Force Index measures the power behind a price movement using price
    and volume as well as potential reversals and price corrections.

    Sources:
        https://www.tradingview.com/wiki/Elder%27s_Force_Index_(EFI)
        https://www.motivewave.com/studies/elders_force_index.htm

    Calculation:
        Default Inputs:
            length=20, drift=1, mamode=None
        EMA = Exponential Moving Average
        SMA = Simple Moving Average

        pv_diff = close.diff(drift) * volume
        if mamode == 'sma':
            EFI = SMA(pv_diff, length)
        else:
            EFI = EMA(pv_diff, length)

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        length (int): The short period. Default: 13
        drift (int): The diff period. Default: 1
        mamode (str): See ```help(ta.ma)```. Default: 'ema'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def ema(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Exponential Moving Average (EMA)

    The Exponential Moving Average is more responsive moving average compared to the
    Simple Moving Average (SMA).  The weights are determined by alpha which is
    proportional to it's length.  There are several different methods of calculating
    EMA.  One method uses just the standard definition of EMA and another uses the
    SMA to generate the initial value for the rest of the calculation.

    Sources:
        https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_averages
        https://www.investopedia.com/ask/answers/122314/what-exponential-moving-average-ema-formula-and-how-ema-calculated.asp

    Calculation:
        Default Inputs:
            length=10, adjust=False, sma=True
        if sma:
            sma_nth = close[0:length].sum() / length
            close[:length - 1] = np.NaN
            close.iloc[length - 1] = sma_nth
        EMA = close.ewm(span=length, adjust=adjust).mean()

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        adjust (bool, optional): Default: False
        sma (bool, optional): If True, uses SMA for initial value. Default: True
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def emv(data: pd.Series | pd.DataFrame, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Ease of Movement (EMV)

    Raw (unsmoothed) Ease of Movement.  Higher values indicate price is moving
    up with ease on low volume; lower values indicate the opposite.

    Formula:
        midpoint  = (High + Low) / 2
        distance  = midpoint - prev(midpoint)
        box_ratio = Volume / (High - Low)
        EMV       = distance / box_ratio

    See ta.eom for the SMA-smoothed version.
    tulipy name: EMV.

    Args:
        high (pd.Series): Series of 'high' prices
        low (pd.Series): Series of 'low' prices
        volume (pd.Series): Series of volume
        drift (int): Difference period. Default: 1
        offset (int): Periods to offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series
    """
    ...

def entropy(data: pd.Series | pd.DataFrame, length: Any = None, base: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Entropy (ENTP)

    Introduced by Claude Shannon in 1948, entropy measures the unpredictability
    of the data, or equivalently, of its average information. A die has higher
    entropy (p=1/6) versus a coin (p=1/2).

    Sources:
        https://en.wikipedia.org/wiki/Entropy_(information_theory)

    Calculation:
        Default Inputs:
            length=10, base=2

        P = close / SUM(close, length)
        E = SUM(-P * npLog(P) / npLog(base), length)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        base (float): Logarithmic Base. Default: 2
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def eom(data: pd.Series | pd.DataFrame, length: Any = None, divisor: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Ease of Movement (EOM)

    Ease of Movement is a volume based oscillator that is designed to measure the
    relationship between price and volume flucuating across a zero line.

    Sources:
        https://www.tradingview.com/wiki/Ease_of_Movement_(EOM)
        https://www.motivewave.com/studies/ease_of_movement.htm
        https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:ease_of_movement_emv

    Calculation:
        Default Inputs:
            length=14, divisor=100000000, drift=1
        SMA = Simple Moving Average
        hl_range = high - low
        distance = 0.5 * (high - high.shift(drift) + low - low.shift(drift))
        box_ratio = (volume / divisor) / hl_range
        eom = distance / box_ratio
        EOM = SMA(eom, length)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        length (int): The short period. Default: 14
        drift (int): The diff period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def er(data: pd.Series | pd.DataFrame, length: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Efficiency Ratio (ER)

    The Efficiency Ratio was invented by Perry J. Kaufman and presented in his book "New Trading Systems and Methods". It is designed to account for market noise or volatility.

    It is calculated by dividing the net change in price movement over N periods by the sum of the absolute net changes over the same N periods.

    Sources:
        https://help.tc2000.com/m/69404/l/749623-kaufman-efficiency-ratio

    Calculation:
        Default Inputs:
            length=10
        ABS = Absolute Value
        EMA = Exponential Moving Average

        abs_diff = ABS(close.diff(length))
        volatility = ABS(close.diff(1))
        ER = abs_diff / SUM(volatility, length)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def eri(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Elder Ray Index (ERI)

    Elder's Bulls Ray Index contains his Bull and Bear Powers. Which are useful ways
    to look at the price and see the strength behind the market. Bull Power
    measures the capability of buyers in the market, to lift prices above an average
    consensus of value.

    Bears Power measures the capability of sellers, to drag prices below an average
    consensus of value. Using them in tandem with a measure of trend allows you to
    identify favourable entry points. We hope you've found this to be a useful
    discussion of the Bulls and Bears Power indicators.

    Sources:
        https://admiralmarkets.com/education/articles/forex-indicators/bears-and-bulls-power-indicator

    Calculation:
        Default Inputs:
            length=13
        EMA = Exponential Moving Average

        BULLPOWER = high - EMA(close, length)
        BEARPOWER = low - EMA(close, length)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: bull power and bear power columns.
    """
    ...

def fisher(data: pd.Series | pd.DataFrame, length: Any = None, signal: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Fisher Transform (FISHT)

    Attempts to identify significant price reversals by normalizing prices over a
    user-specified number of periods. A reversal signal is suggested when the the
    two lines cross.

    Sources:
        TradingView (Correlation >99%)

    Calculation:
        Default Inputs:
            length=9, signal=1
        HL2 = hl2(high, low)
        HHL2 = HL2.rolling(length).max()
        LHL2 = HL2.rolling(length).min()

        HLR = HHL2 - LHL2
        HLR[HLR < 0.001] = 0.001

        position = ((HL2 - LHL2) / HLR) - 0.5

        v = 0
        m = high.size
        FISHER = [npNaN for _ in range(0, length - 1)] + [0]
        for i in range(length, m):
            v = 0.66 * position[i] + 0.67 * v
            if v < -0.99: v = -0.999
            if v >  0.99: v =  0.999
            FISHER.append(0.5 * (nplog((1 + v) / (1 - v)) + FISHER[i - 1]))

        SIGNAL = FISHER.shift(signal)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        length (int): Fisher period. Default: 9
        signal (int): Fisher Signal period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def fosc(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Forecast Oscillator (FOSC)

    The Forecast Oscillator computes the percentage difference between the actual
    close price and the Time Series Forecast (linear regression projected one step
    ahead). Positive values suggest price above forecast (bullish), negative
    values suggest price below forecast (bearish).

    FOSC = 100 * (Close - TSF[n]) / Close

    Where TSF = Time Series Forecast (Linear Regression + 1 step ahead projection)

    Sources:
        Tushar Chande, "The New Technical Trader", 1994
        https://library.tradingtechnologies.com/trade/chrt-ti-forecast-osc.html

    Args:
        close (pd.Series): Close price series.
        length (int): Lookback period. Default: 14
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: FOSC values.
    """
    ...

def fwma(data: pd.Series | pd.DataFrame, length: Any = None, asc: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Fibonacci's Weighted Moving Average (FWMA)

    Fibonacci's Weighted Moving Average is similar to a Weighted Moving Average
    (WMA) where the weights are based on the Fibonacci Sequence.

    Source: Kevin Johnson

    Calculation:
        Default Inputs:
            length=10,

        def weights(w):
            def _compute(x):
                return np.dot(w * x)
            return _compute

        fibs = utils.fibonacci(length - 1)
        FWMA = close.rolling(length)_.apply(weights(fibs), raw=True)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        asc (bool): Recent values weigh more. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def ha(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Heikin Ashi Candles (HA)

    The Heikin-Ashi technique averages price data to create a Japanese
    candlestick chart that filters out market noise. Heikin-Ashi charts,
    developed by Munehisa Homma in the 1700s, share some characteristics
    with standard candlestick charts but differ based on the values used
    to create each candle. Instead of using the open, high, low, and close
    like standard candlestick charts, the Heikin-Ashi technique uses a
    modified formula based on two-period averages. This gives the chart a
    smoother appearance, making it easier to spots trends and reversals,
    but also obscures gaps and some price data.

    Sources:
        https://www.investopedia.com/terms/h/heikinashi.asp

    Calculation:
        HA_OPEN[0] = (open[0] + close[0]) / 2
        HA_CLOSE = (open[0] + high[0] + low[0] + close[0]) / 4

        for i > 1 in df.index:
            HA_OPEN = (HA_OPEN[i−1] + HA_CLOSE[i−1]) / 2

        HA_HIGH = MAX(HA_OPEN, HA_HIGH, HA_CLOSE)
        HA_LOW = MIN(HA_OPEN, HA_LOW, HA_CLOSE)

        How to Calculate Heikin-Ashi

        Use one period to create the first Heikin-Ashi (HA) candle, using
        the formulas. For example use the high, low, open, and close to
        create the first HA close price. Use the open and close to create
        the first HA open. The high of the period will be the first HA high,
        and the low will be the first HA low. With the first HA calculated,
        it is now possible to continue computing the HA candles per the formulas.
    ​​
    Args:
        open_ (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: ha_open, ha_high,ha_low, ha_close columns.
    """
    ...

def hilo(data: pd.Series | pd.DataFrame, high_length: Any = None, low_length: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Gann HiLo Activator(HiLo)

    The Gann High Low Activator Indicator was created by Robert Krausz in a 1998
    issue of Stocks & Commodities Magazine. It is a moving average based trend
    indicator consisting of two different simple moving averages.

    The indicator tracks both curves (of the highs and the lows). The close of the
    bar defines which of the two gets plotted.

    Increasing high_length and decreasing low_length better for short trades,
    vice versa for long positions.

    Sources:
        https://www.sierrachart.com/index.php?page=doc/StudiesReference.php&ID=447&Name=Gann_HiLo_Activator
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/simple-moving-average-sma/
        https://www.tradingview.com/script/XNQSLIYb-Gann-High-Low/

    Calculation:
        Default Inputs:
            high_length=13, low_length=21, mamode="sma"
        EMA = Exponential Moving Average
        HMA = Hull Moving Average
        SMA = Simple Moving Average # Default

        if "ema":
            high_ma = EMA(high, high_length)
            low_ma = EMA(low, low_length)
        elif "hma":
            high_ma = HMA(high, high_length)
            low_ma = HMA(low, low_length)
        else: # "sma"
            high_ma = SMA(high, high_length)
            low_ma = SMA(low, low_length)

        # Similar to Supertrend MA selection
        hilo = Series(npNaN, index=close.index)
        for i in range(1, m):
            if close.iloc[i] > high_ma.iloc[i - 1]:
                hilo.iloc[i] = low_ma.iloc[i]
            elif close.iloc[i] < low_ma.iloc[i - 1]:
                hilo.iloc[i] = high_ma.iloc[i]
            else:
                hilo.iloc[i] = hilo.iloc[i - 1]

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        high_length (int): It's period. Default: 13
        low_length (int): It's period. Default: 21
        mamode (str): See ```help(ta.ma)```. Default: 'sma'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        adjust (bool): Default: True
        presma (bool, optional): If True, uses SMA for initial value.
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: HILO (line), HILOl (long), HILOs (short) columns.
    """
    ...

def hl2(data: pd.Series | pd.DataFrame, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    HL2 (Median Price)

    HL2 calculates the median price, which is the average of the High and Low
    prices for each period. This indicator is commonly used to represent the
    mid-point of a period's price range and is often used in technical analysis
    as a reference point for price action.

    Sources:
        https://www.tradingview.com/support/solutions/43000502274-hl2/
        https://www.investopedia.com/terms/m/median.asp
        https://school.stockcharts.com/doku.php?id=chart_analysis:typical_price

    Calculation:
        Default Inputs:
            None (uses raw high and low prices)

        HL2 = (High + Low) / 2

    Args:
        high (pd.Series): Series of 'high' prices
        low (pd.Series): Series of 'low' prices
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def hlc3(data: pd.Series | pd.DataFrame, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    HLC3 (Typical Price)

    HLC3 calculates the typical price, which is the average of the High, Low,
    and Close prices for each period. This indicator provides a simple measure
    of the average price level during a period and is widely used in technical
    analysis. It's also known as the TA-Lib TYPPRICE function.

    Sources:
        https://www.tradingview.com/support/solutions/43000502273-hlc3/
        https://school.stockcharts.com/doku.php?id=chart_analysis:typical_price
        https://www.investopedia.com/terms/t/typicalprice.asp

    Calculation:
        Default Inputs:
            None (uses raw HLC prices)

        HLC3 = (High + Low + Close) / 3

    Args:
        high (pd.Series): Series of 'high' prices
        low (pd.Series): Series of 'low' prices
        close (pd.Series): Series of 'close' prices
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def hma(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Hull Moving Average (HMA)

    The Hull Exponential Moving Average attempts to reduce or remove lag in moving
    averages.

    Sources:
        https://alanhull.com/hull-moving-average

    Calculation:
        Default Inputs:
            length=10
        WMA = Weighted Moving Average
        half_length = int(0.5 * length)
        sqrt_length = int(sqrt(length))

        wmaf = WMA(close, half_length)
        wmas = WMA(close, length)
        HMA = WMA(2 * wmaf - wmas, sqrt_length)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def ht_dcperiod(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Hilbert Transform - Dominant Cycle Period (HT_DCPERIOD)

    The Dominant Cycle Period uses the Hilbert Transform to estimate the
    dominant cycle period of the price data.

    Sources:
        John F. Ehlers, "Rocket Science for Traders"

    Args:
        close (pd.Series): Series of 'close's
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def ht_dcphase(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Hilbert Transform - Dominant Cycle Phase (HT_DCPHASE)

    The Dominant Cycle Phase uses the Hilbert Transform to estimate the
    phase of the dominant cycle.

    Sources:
        John F. Ehlers, "Rocket Science for Traders"

    Args:
        close (pd.Series): Series of 'close's
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def ht_phasor(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Hilbert Transform - Phasor Components (HT_PHASOR)

    Returns the InPhase and Quadrature components of the Hilbert Transform,
    which together form a phasor representation of the dominant cycle.

    Sources:
        John F. Ehlers, "Rocket Science for Traders"

    Args:
        close (pd.Series): Series of 'close's
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: inphase and quadrature columns.
    """
    ...

def ht_sine(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Hilbert Transform - SineWave (HT_SINE)

    Returns the Sine and LeadSine of the dominant cycle phase.  Crossovers
    of the Sine and LeadSine can be used as cycle-mode trading signals.

    Sources:
        John F. Ehlers, "Rocket Science for Traders"

    Args:
        close (pd.Series): Series of 'close's
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: sine and leadsine columns.
    """
    ...

def ht_trendline(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Hilbert Transform - Instantaneous Trendline (HT_TRENDLINE)

    The Instantaneous Trendline uses the Hilbert Transform dominant cycle
    period to compute a smoothed trendline that adapts to the current
    market cycle.

    Sources:
        John F. Ehlers, "Rocket Science for Traders"

    Args:
        close (pd.Series): Series of 'close's
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def ht_trendmode(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Hilbert Transform - Trend vs Cycle Mode (HT_TRENDMODE)

    Returns 1 when the market is in a trend and 0 when it is in a cycle,
    based on the Hilbert Transform dominant cycle analysis.

    Sources:
        John F. Ehlers, "Rocket Science for Traders"

    Args:
        close (pd.Series): Series of 'close's
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated (0 or 1).
    """
    ...

def hvol(data: pd.Series | pd.DataFrame, length: Any = None, annualization: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Historical Volatility (HVOL)

    Historical Volatility is the annualized standard deviation of logarithmic
    daily returns over a given period. It measures how much the price has varied
    historically, expressed as an annualized percentage.

    log_return = log(close / close[1])
    HVOL = 100 * StdDev(log_return, length) * sqrt(annualization)

    Sources:
        https://www.investopedia.com/terms/h/historicalvolatility.asp

    Args:
        close (pd.Series): Close price series.
        length (int): Lookback period for std dev. Default: 20
        annualization (float): Annualization factor. Default: 252 (trading days/year)
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: HVOL values (annualized %).
    """
    ...

def hwc(data: pd.Series | pd.DataFrame, na: Any = None, nb: Any = None, nc: Any = None, nd: Any = None, scalar: Any = None, channel_eval: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    HWC (Holt-Winter Channel)

    Channel indicator HWC (Holt-Winters Channel) based on HWMA - a three-parameter
    moving average calculated by the method of Holt-Winters.

    This version has been implemented for Pandas TA by rengel8 based on a
    publication for MetaTrader 5 extended by width and percentage price position
    against width of channel.

    Sources:
        https://www.mql5.com/en/code/20857

    Calculation:
        HWMA[i] = F[i] + V[i] + 0.5 * A[i]
        where..
        F[i] = (1-na) * (F[i-1] + V[i-1] + 0.5 * A[i-1]) + na * Price[i]
        V[i] = (1-nb) * (V[i-1] + A[i-1]) + nb * (F[i] - F[i-1])
        A[i] = (1-nc) * A[i-1] + nc * (V[i] - V[i-1])

        Top = HWMA + Multiplier * StDt
        Bottom = HWMA - Multiplier * StDt
        where..
        StDt[i] = Sqrt(Var[i-1])
        Var[i] = (1-d) * Var[i-1] + nD * (Price[i-1] - HWMA[i-1]) * (Price[i-1] - HWMA[i-1])

    Args:
        na - parameter of the equation that describes a smoothed series (from 0 to 1)
        nb - parameter of the equation to assess the trend (from 0 to 1)
        nc - parameter of the equation to assess seasonality (from 0 to 1)
        nd - parameter of the channel equation (from 0 to 1)
        scaler - multiplier for the width of the channel calculated
        channel_eval - boolean to return width and percentage price position against price
        close (pd.Series): Series of 'close's

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method
    Returns:
        pd.DataFrame: HWM (Mid), HWU (Upper), HWL (Lower) columns.
    """
    ...

def hwma(data: pd.Series | pd.DataFrame, na: Any = None, nb: Any = None, nc: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    HWMA (Holt-Winter Moving Average)

    Indicator HWMA (Holt-Winter Moving Average) is a three-parameter moving average
    by the Holt-Winter method; the three parameters should be selected to obtain a
    forecast.

    This version has been implemented for Pandas TA by rengel8 based
    on a publication for MetaTrader 5.

    Sources:
        https://www.mql5.com/en/code/20856

    Calculation:
        HWMA[i] = F[i] + V[i] + 0.5 * A[i]
        where..
        F[i] = (1-na) * (F[i-1] + V[i-1] + 0.5 * A[i-1]) + na * Price[i]
        V[i] = (1-nb) * (V[i-1] + A[i-1]) + nb * (F[i] - F[i-1])
        A[i] = (1-nc) * A[i-1] + nc * (V[i] - V[i-1])

    Args:
        close (pd.Series): Series of 'close's
        na (float): Smoothed series parameter (from 0 to 1). Default: 0.2
        nb (float): Trend parameter (from 0 to 1). Default: 0.1
        nc (float): Seasonality parameter (from 0 to 1). Default: 0.1
        close (pd.Series): Series of 'close's

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: hwma
    """
    ...

def ichimoku(data: pd.Series | pd.DataFrame, tenkan: Any = None, kijun: Any = None, senkou: Any = None, include_chikou: Any = True, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Ichimoku Kinkō Hyō (ichimoku)

    Developed Pre WWII as a forecasting model for financial markets.

    Sources:
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/ichimoku-ich/

    Calculation:
        Default Inputs:
            tenkan=9, kijun=26, senkou=52
        MIDPRICE = Midprice
        TENKAN_SEN = MIDPRICE(high, low, close, length=tenkan)
        KIJUN_SEN = MIDPRICE(high, low, close, length=kijun)
        CHIKOU_SPAN = close.shift(-kijun)

        SPAN_A = 0.5 * (TENKAN_SEN + KIJUN_SEN)
        SPAN_A = SPAN_A.shift(kijun)

        SPAN_B = MIDPRICE(high, low, close, length=senkou)
        SPAN_B = SPAN_B.shift(kijun)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        tenkan (int): Tenkan period. Default: 9
        kijun (int): Kijun period. Default: 26
        senkou (int): Senkou period. Default: 52
        include_chikou (bool): Whether to include chikou component. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: Two DataFrames.
            For the visible period: spanA, spanB, tenkan_sen, kijun_sen,
                and chikou_span columns
            For the forward looking period: spanA and spanB columns
    """
    ...

def increasing(data: pd.Series | pd.DataFrame, length: Any = None, strict: Any = None, asint: Any = None, percent: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Increasing

    Returns True if the series is increasing over a period, False otherwise.
    If the kwarg 'strict' is True, it returns True if it is continuously increasing
    over the period. When using the kwarg 'asint', then it returns 1 for True
    or 0 for False.

    Calculation:
        if strict:
            increasing = all(i < j for i, j in zip(close[-length:], close[1:]))
        else:
            increasing = close.diff(length) > 0

        if asint:
            increasing = increasing.astype(int)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 1
        strict (bool): If True, checks if the series is continuously increasing over the period. Default: False
        percent (float): Percent as an integer. Default: None
        asint (bool): Returns as binary. Default: True
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def inertia(data: pd.Series | pd.DataFrame, length: Any = None, rvi_length: Any = None, scalar: Any = None, refined: Any = None, thirds: Any = None, mamode: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Inertia (INERTIA)

    Inertia was developed by Donald Dorsey and was introduced his article
    in September, 1995. It is the Relative Vigor Index smoothed by the Least
    Squares Moving Average. Postive Inertia when values are greater than 50,
    Negative Inertia otherwise.

    Sources:
        https://www.investopedia.com/terms/r/relative_vigor_index.asp

    Calculation:
        Default Inputs:
            length=14, ma_length=20
        LSQRMA = Least Squares Moving Average

        INERTIA = LSQRMA(RVI(length), ma_length)

    Args:
        open_ (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 20
        rvi_length (int): RVI period. Default: 14
        refined (bool): Use 'refined' calculation. Default: False
        thirds (bool): Use 'thirds' calculation. Default: False
        mamode (str): See ```help(ta.ma)```. Default: 'ema'
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def jma(data: pd.Series | pd.DataFrame, length: Any = None, phase: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Jurik Moving Average Average (JMA)

    Mark Jurik's Moving Average (JMA) attempts to eliminate noise to see the "true"
    underlying activity. It has extremely low lag, is very smooth and is responsive
    to market gaps.

    Sources:
        https://c.mql5.com/forextsd/forum/164/jurik_1.pdf
        https://www.prorealcode.com/prorealtime-indicators/jurik-volatility-bands/

    Calculation:
        Default Inputs:
            length=7, phase=0

    Args:
        close (pd.Series): Series of 'close's
        length (int): Period of calculation. Default: 7
        phase (float): How heavy/light the average is [-100, 100]. Default: 0
        offset (int): How many lengths to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def kama(data: pd.Series | pd.DataFrame, length: Any = None, fast: Any = None, slow: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Kaufman's Adaptive Moving Average (KAMA)

    Developed by Perry Kaufman, Kaufman's Adaptive Moving Average (KAMA) is a moving average
    designed to account for market noise or volatility. KAMA will closely follow prices when
    the price swings are relatively small and the noise is low. KAMA will adjust when the
    price swings widen and follow prices from a greater distance. This trend-following indicator
    can be used to identify the overall trend, time turning points and filter price movements.

    Sources:
        https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:kaufman_s_adaptive_moving_average
        https://www.tradingview.com/script/wZGOIz9r-REPOST-Indicators-3-Different-Adaptive-Moving-Averages/

    Calculation:
        Default Inputs:
            length=10

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        fast (int): Fast MA period. Default: 2
        slow (int): Slow MA period. Default: 30
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def kc(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Keltner Channels (KC)

    A popular volatility indicator similar to Bollinger Bands and
    Donchian Channels.

    Sources:
        https://www.tradingview.com/wiki/Keltner_Channels_(KC)

    Calculation:
        Default Inputs:
            length=20, scalar=2, mamode=None, tr=True
        TR = True Range
        SMA = Simple Moving Average
        EMA = Exponential Moving Average

        if tr:
            RANGE = TR(high, low, close)
        else:
            RANGE = high - low

        if mamode == "ema":
            BASIS = sma(close, length)
            BAND = sma(RANGE, length)
        elif mamode == "sma":
            BASIS = sma(close, length)
            BAND = sma(RANGE, length)

        LOWER = BASIS - scalar * BAND
        UPPER = BASIS + scalar * BAND

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): The short period.  Default: 20
        scalar (float): A positive float to scale the bands. Default: 2
        mamode (str): See ```help(ta.ma)```. Default: 'ema'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        tr (bool): When True, it uses True Range for calculation. When False, use a
            high - low as it's range calculation. Default: True
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: lower, basis, upper columns.
    """
    ...

def kdj(data: pd.Series | pd.DataFrame, length: Any = None, signal: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    KDJ (KDJ)

    The KDJ indicator is actually a derived form of the Slow
    Stochastic with the only difference being an extra line
    called the J line. The J line represents the divergence
    of the %D value from the %K. The value of J can go
    beyond [0, 100] for %K and %D lines on the chart.

    Sources:
        https://www.prorealcode.com/prorealtime-indicators/kdj/
        https://docs.anychart.com/Stock_Charts/Technical_Indicators/Mathematical_Description#kdj

    Calculation:
        Default Inputs:
            length=9, signal=3
        LL = low for last 9 periods
        HH = high for last 9 periods

        FAST_K = 100 * (close - LL) / (HH - LL)

        K = RMA(FAST_K, signal)
        D = RMA(K, signal)
        J = 3K - 2D

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): Default: 9
        signal (int): Default: 3
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def kst(data: pd.Series | pd.DataFrame, roc1: Any = None, roc2: Any = None, roc3: Any = None, roc4: Any = None, sma1: Any = None, sma2: Any = None, sma3: Any = None, sma4: Any = None, signal: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    'Know Sure Thing' (KST)

    The 'Know Sure Thing' is a momentum based oscillator and based on ROC.

    Sources:
        https://www.tradingview.com/wiki/Know_Sure_Thing_(KST)
        https://www.incrediblecharts.com/indicators/kst.php

    Calculation:
        Default Inputs:
            roc1=10, roc2=15, roc3=20, roc4=30,
            sma1=10, sma2=10, sma3=10, sma4=15, signal=9, drift=1
        ROC = Rate of Change
        SMA = Simple Moving Average
        rocsma1 = SMA(ROC(close, roc1), sma1)
        rocsma2 = SMA(ROC(close, roc2), sma2)
        rocsma3 = SMA(ROC(close, roc3), sma3)
        rocsma4 = SMA(ROC(close, roc4), sma4)

        KST = 100 * (rocsma1 + 2 * rocsma2 + 3 * rocsma3 + 4 * rocsma4)
        KST_Signal = SMA(KST, signal)

    Args:
        close (pd.Series): Series of 'close's
        roc1 (int): ROC 1 period. Default: 10
        roc2 (int): ROC 2 period. Default: 15
        roc3 (int): ROC 3 period. Default: 20
        roc4 (int): ROC 4 period. Default: 30
        sma1 (int): SMA 1 period. Default: 10
        sma2 (int): SMA 2 period. Default: 10
        sma3 (int): SMA 3 period. Default: 10
        sma4 (int): SMA 4 period. Default: 15
        signal (int): It's period. Default: 9
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: kst and kst_signal columns
    """
    ...

def kurtosis(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rolling Kurtosis

    Sources:

    Calculation:
        Default Inputs:
            length=30
        KURTOSIS = close.rolling(length).kurt()

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 30
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def kvo(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, signal: Any = None, mamode: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Klinger Volume Oscillator (KVO)

    This indicator was developed by Stephen J. Klinger. It is designed to predict
    price reversals in a market by comparing volume to price.

    Sources:
        https://www.investopedia.com/terms/k/klingeroscillator.asp
        https://www.daytrading.com/klinger-volume-oscillator

    Calculation:
        Default Inputs:
            fast=34, slow=55, signal=13, drift=1
        EMA = Exponential Moving Average

        SV = volume * signed_series(HLC3, 1)
        KVO = EMA(SV, fast) - EMA(SV, slow)
        Signal = EMA(KVO, signal)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        fast (int): The fast period. Default: 34
        long (int): The long period. Default: 55
        length_sig (int): The signal period. Default: 13
        mamode (str): See ```help(ta.ma)```. Default: 'ema'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: KVO and Signal columns.
    """
    ...

def linreg(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Linear Regression Moving Average (linreg)

    Linear Regression Moving Average (LINREG). This is a simplified version of a
    Standard Linear Regression. LINREG is a rolling regression of one variable. A
    Standard Linear Regression is between two or more variables.

    Source: TA Lib

    Calculation:
        Default Inputs:
            length=14
        x = [0, 1, ..., n-1]  (matches TA-Lib convention)
        x_sum = 0.5 * length * (length - 1)
        x2_sum = length * (length - 1) * (2 * length - 1) / 6
        divisor = length * x2_sum - x_sum * x_sum

        lr(series):
            y_sum = series.sum()
            y2_sum = (series* series).sum()
            xy_sum = (x * series).sum()

            m = (length * xy_sum - x_sum * y_sum) / divisor
            b = (y_sum * x2_sum - x_sum * xy_sum) / divisor
            return m * (length - 1) + b

        linreg = close.rolling(length).apply(lr)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period.  Default: 10
        offset (int): How many periods to offset the result.  Default: 0

    Kwargs:
        angle (bool, optional): If True, returns the angle of the slope.
            Default: False.
        degrees (bool, optional): If True, returns the angle in degrees;
            if False, in radians. Default: True (matches TA-Lib convention).
        intercept (bool, optional): If True, returns the angle of the slope in
            radians. Default: False.
        r (bool, optional): If True, returns it's correlation 'r'. Default: False.
        slope (bool, optional): If True, returns the slope. Default: False.
        tsf (bool, optional): If True, returns the Time Series Forecast value.
            Default: False.
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def linregangle(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Linear Regression Angle (LINEARREG_ANGLE)

    Returns the angle (in degrees) of the linear regression line over the
    last *length* bars.  Equivalent to ta.linreg(..., angle=True).

    Args:
        close (pd.Series): Series of 'close' prices
        length (int): Lookback period. Default: 14
        offset (int): Periods to offset. Default: 0

    Returns:
        pd.Series
    """
    ...

def linregintercept(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Linear Regression Intercept (LINEARREG_INTERCEPT)

    Returns the y-intercept of the linear regression line over the last
    *length* bars.  Equivalent to ta.linreg(..., intercept=True).

    Args:
        close (pd.Series): Series of 'close' prices
        length (int): Lookback period. Default: 14
        offset (int): Periods to offset. Default: 0

    Returns:
        pd.Series
    """
    ...

def linregslope(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Linear Regression Slope (LINEARREG_SLOPE)

    Returns the slope of the linear regression line over the last *length*
    bars.  Equivalent to ta.linreg(..., slope=True).

    Args:
        close (pd.Series): Series of 'close' prices
        length (int): Lookback period. Default: 14
        offset (int): Periods to offset. Default: 0

    Returns:
        pd.Series
    """
    ...

def log_return(data: pd.Series | pd.DataFrame, length: Any = None, cumulative: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Log Return

    Calculates the logarithmic return of a Series.
    See also: help(df.ta.log_return) for additional **kwargs a valid 'df'.

    Sources:
        https://stackoverflow.com/questions/31287552/logarithmic-returns-in-pandas-dataframe

    Calculation:
        Default Inputs:
            length=1, cumulative=False
        LOGRET = log( close.diff(periods=length) )
        CUMLOGRET = LOGRET.cumsum() if cumulative

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 20
        cumulative (bool): If True, returns the cumulative returns. Default: False
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def long_run(data: pd.Series | pd.DataFrame, fast: Any = ..., slow: Any = ..., length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Long Run

    Identifies potential long (bullish) trend conditions by detecting when the fast
    moving average is increasing while the slow moving average is either decreasing
    (potential bottom) or also increasing (confirmed uptrend).

    Sources:
        Used in AMAT (Archer Moving Averages Trends) indicator

    Calculation:
        Default Inputs:
            length=2

        PB = INCREASING(fast, length) AND DECREASING(slow, length)  # Potential bottom
        BI = INCREASING(fast, length) AND INCREASING(slow, length)  # Both increasing
        LONG_RUN = PB OR BI

    Args:
        fast (pd.Series): Fast moving average Series (e.g. EMA(5)). Pre-computed,
            not a period length.
        slow (pd.Series): Slow moving average Series (e.g. EMA(20)). Pre-computed,
            not a period length.
        length (int): Lookback period. Default: 2
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Example:
        fast_ma = df.ta.ema(length=5)
        slow_ma = df.ta.ema(length=20)
        lr = ta.long_run(fast_ma, slow_ma)

    Returns:
        pd.Series: New feature generated (boolean).
    """
    ...

def lrsi(data: pd.Series | pd.DataFrame, length: Any = None, gamma: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Laguerre RSI (LRSI)

    The Laguerre RSI is a modified RSI indicator that uses Laguerre polynomials to
    reduce lag and provide earlier signals. It adapts to price changes more quickly
    than the standard RSI while maintaining smooth oscillations.

    Sources:
        https://www.tradingview.com/script/3p0QrN5C-Laguerre-RSI/
        https://www.mesasoftware.com/papers/LaguerreFilters.pdf

    Calculation:
        Default Inputs:
            length=14, gamma=0.5

        Apply Laguerre filter with gamma coefficient:
        L0 = (1 - gamma) * Close + gamma * L0[1]
        L1 = -gamma * L0 + L0[1] + gamma * L1[1]
        L2 = -gamma * L1 + L1[1] + gamma * L2[1]
        L3 = -gamma * L2 + L2[1] + gamma * L3[1]

        Calculate ups and downs:
        CU = sum of (L0-L1, L1-L2, L2-L3) when positive
        CD = sum of (L0-L1, L1-L2, L2-L3) when negative (absolute)

        LRSI = 100 * CU / (CU + CD)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        gamma (float): Laguerre filter coefficient (0 to 1). Default: 0.5
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def ma(data: pd.Series | pd.DataFrame, name: Any = None, source: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Simple MA Utility for easier MA selection

    Available MAs:
        dema, ema, fwma, hma, linreg, midpoint, pwma, rma,
        sinwma, sma, swma, t3, tema, trima, vidya, wma, zlma

    Examples:
        ema8 = ta.ma("ema", df.close, length=8)
        sma50 = ta.ma("sma", df.close, length=50)
        pwma10 = ta.ma("pwma", df.close, length=10, asc=False)

    Args:
        name (str): One of the Available MAs. Default: "ema"
        source (pd.Series): The 'source' Series.

    Kwargs:
        Any additional kwargs the MA may require.

    Returns:
        pd.Series: New feature generated.
    """
    ...

def macd(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, signal: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Moving Average Convergence Divergence (MACD)

    The MACD is a popular indicator to that is used to identify a security's trend.
    While APO and MACD are the same calculation, MACD also returns two more series
    called Signal and Histogram. The Signal is an EMA of MACD and the Histogram is
    the difference of MACD and Signal.

    Sources:
        https://www.tradingview.com/wiki/MACD_(Moving_Average_Convergence/Divergence)
        AS Mode: https://tr.tradingview.com/script/YFlKXHnP/

    Calculation:
        Default Inputs:
            fast=12, slow=26, signal=9
        EMA = Exponential Moving Average
        MACD = EMA(close, fast) - EMA(close, slow)
        Signal = EMA(MACD, signal)
        Histogram = MACD - Signal

        if asmode:
            MACD = MACD - Signal
            Signal = EMA(MACD, signal)
            Histogram = MACD - Signal

    Args:
        close (pd.Series): Series of 'close's
        fast (int): The short period. Default: 12
        slow (int): The long period. Default: 26
        signal (int): The signal period. Default: 9
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        asmode (value, optional): When True, enables AS version of MACD.
            Default: False
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: macd, histogram, signal columns.
    """
    ...

def macdext(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, signal: Any = None, fastmatype: Any = None, slowmatype: Any = None, signalmatype: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    MACD Extended (MACDEXT)

    Like MACD but each of the three moving averages (fast, slow, signal) can use
    a different MA type, following the TA-Lib convention.

    MA type integers:
        0=SMA, 1=EMA (default), 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=KAMA*, 7=MAMA*, 8=T3
        (* native fallback uses EMA; UserWarning emitted)

    Sources:
        TA-Lib: https://ta-lib.org/functions/

    Args:
        close (pd.Series): Close price series.
        fast (int): Fast period. Default: 12.
        slow (int): Slow period. Default: 26.
        signal (int): Signal period. Default: 9.
        fastmatype (int): MA type for fast line. Default: 1 (EMA).
        slowmatype (int): MA type for slow line. Default: 1 (EMA).
        signalmatype (int): MA type for signal line. Default: 1 (EMA).
            Native fallback supports: 0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA,
            5=TRIMA, 8=T3. Types 6=KAMA and 7=MAMA use EMA as a fallback and
            emit a UserWarning. Use talib=True for correct KAMA/MAMA behaviour.
        talib (bool): Use TA-Lib if available. Default: False.
        offset (int): Number of periods to offset. Default: 0.

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: Columns MACDEXT_{f}_{s}_{sig}, MACDEXTs_{f}_{s}_{sig},
                      MACDEXTh_{f}_{s}_{sig}.

    Example:
        df[['MACDEXT_12_26_9', 'MACDEXTs_12_26_9', 'MACDEXTh_12_26_9']] = df.ta.macdext()
        # SMA-based MACD:
        df.ta.macdext(fastmatype=0, slowmatype=0, signalmatype=0)
    """
    ...

def macdfix(data: pd.Series | pd.DataFrame, signal: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    MACD with Fixed Periods (MACDFIX)

    MACD using fixed fast=12 and slow=26 with a variable signal period.
    Equivalent to ta.macd(close, fast=12, slow=26, signal=signalperiod).

    TA-Lib name: MACDFIX.

    Args:
        close (pd.Series): Series of 'close' prices
        signal (int): Signal period. Default: 9
        talib (bool): Use TA-Lib C library if installed. Default: False
        offset (int): Periods to offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: macdfix, histogram, signal columns.
    """
    ...

def mad(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rolling Mean Absolute Deviation

    Sources:

    Calculation:
        Default Inputs:
            length=30
        mad = close.rolling(length).mad()

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 30
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def mama(data: pd.Series | pd.DataFrame, fastlimit: Any = None, slowlimit: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    MESA Adaptive Moving Average (MAMA)

    MAMA adapts to price movement based on the rate of change of the Hilbert
    Transform phase.  It uses a fast limit and slow limit to bound the
    smoothing factor.  FAMA (Following Adaptive Moving Average) is a further
    smoothed version of MAMA.

    Sources:
        John F. Ehlers, "MESA and Trading Market Cycles"

    Calculation:
        Default Inputs:
            fastlimit=0.5, slowlimit=0.05
        alpha = fastlimit / delta_phase  (clamped to [slowlimit, fastlimit])
        MAMA = alpha * close + (1 - alpha) * MAMA[1]
        FAMA = 0.5 * alpha * MAMA + (1 - 0.5 * alpha) * FAMA[1]

    Args:
        close (pd.Series): Series of 'close's
        fastlimit (float): Upper bound for the adaptive alpha. Default: 0.5
        slowlimit (float): Lower bound for the adaptive alpha. Default: 0.05
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: MAMA and FAMA columns.
    """
    ...

def marketfi(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Market Facilitation Index (MARKETFI)

    The Market Facilitation Index (MFI) was developed by Dr. Bill Williams.
    It measures the efficiency of price movement per unit of volume. A higher
    value means each tick of volume is driving more price movement.

    MARKETFI = (High - Low) / Volume

    Sources:
        Bill Williams, "Trading Chaos", 1995
        https://www.investopedia.com/terms/m/marketfacilitationindex.asp

    Args:
        high (pd.Series): High price series.
        low (pd.Series): Low price series.
        volume (pd.Series): Volume series.
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: MARKETFI values.
    """
    ...

def massi(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Mass Index (MASSI)

    The Mass Index is a non-directional volatility indicator that utilitizes the
    High-Low Range to identify trend reversals based on range expansions.

    Sources:
        https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:mass_index
        mi = sum(ema(high - low, 9) / ema(ema(high - low, 9), 9), length)

    Calculation:
        Default Inputs:
            fast: 9, slow: 25
        EMA = Exponential Moving Average
        hl = high - low
        hl_ema1 = EMA(hl, fast)
        hl_ema2 = EMA(hl_ema1, fast)
        hl_ratio = hl_ema1 / hl_ema2
        MASSI = SUM(hl_ratio, slow)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        fast (int): The short period. Default: 9
        slow (int): The long period. Default: 25
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def mavp(data: pd.Series | pd.DataFrame, periods: Any = None, minperiod: Any = None, maxperiod: Any = None, mamode: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Moving Average with Variable Period (MAVP)

    Moving Average with Variable Period computes a moving average where the
    lookback period is different for each bar. The periods Series determines
    the window size at each data point. When periods is None, a linearly
    interpolated range from minperiod to maxperiod is used.

    Sources:
        https://mrjbq7.github.io/ta-lib/func_groups/overlap_studies.html

    Args:
        close (pd.Series): Close price series.
        periods (pd.Series): Variable period series (optional). Default: linearly spaced [minperiod, maxperiod]
        minperiod (int): Minimum allowed period. Default: 2
        maxperiod (int): Maximum allowed period. Default: 30
        mamode (int): MA type (TA-Lib convention). Default: 0 (SMA).
            Only mamode=0 (SMA) is supported natively. All other values
            require TA-Lib and emit a UserWarning if talib=False.
        talib (bool): Use TA-Lib if installed. Default: False
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: MAVP values.
    """
    ...

def mcgd(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, c: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    McGinley Dynamic Indicator

    The McGinley Dynamic looks like a moving average line, yet it is actually a
    smoothing mechanism for prices that minimizes price separation, price whipsaws,
    and hugs prices much more closely. Because of the calculation, the Dynamic Line
    speeds up in down markets as it follows prices yet moves more slowly in up
    markets. The indicator was designed by John R. McGinley, a Certified Market
    Technician and former editor of the Market Technicians Association's Journal
    of Technical Analysis.

    Sources:
        https://www.investopedia.com/articles/forex/09/mcginley-dynamic-indicator.asp

    Calculation:
        Default Inputs:
            length=10
            offset=0
            c=1

        def mcg_(series):
            denom = (constant * length * (series.iloc[1] / series.iloc[0]) ** 4)
            series.iloc[1] = (series.iloc[0] + ((series.iloc[1] - series.iloc[0]) / denom))
            return series.iloc[1]
        mcg_cell = close[0:].rolling(2, min_periods=2).apply(mcg_, raw=False)
        mcg_ds = pd.concat([close[:1], mcg_cell[1:]])

    Args:
        close (pd.Series): Series of 'close's
        length (int): Indicator's period. Default: 10
        offset (int): Number of periods to offset the result. Default: 0
        c (float): Multiplier for the denominator, sometimes set to 0.6. Default: 1

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def md(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Mean Deviation (MD)

    Rolling mean of absolute deviations from the rolling mean.
    Equivalent to ta.mad.  tulipy name: MD.

    Args:
        close (pd.Series): Series of 'close' prices
        length (int): Lookback period. Default: 30
        offset (int): Periods to offset. Default: 0

    Returns:
        pd.Series
    """
    ...

def median(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rolling Median

    Rolling Median of over 'n' periods. Sibling of a Simple Moving Average.

    Sources:
        https://www.incrediblecharts.com/indicators/median_price.php

    Calculation:
        Default Inputs:
            length=30
        MEDIAN = close.rolling(length).median()

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 30
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def medprice(data: pd.Series | pd.DataFrame, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Median Price (MEDPRICE)

    MEDPRICE = (High + Low) / 2

    Equivalent to ta.hl2.  TA-Lib name: MEDPRICE.

    Args:
        high (pd.Series): Series of 'high' prices
        low (pd.Series): Series of 'low' prices
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): Periods to offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series
    """
    ...

def mfi(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Money Flow Index (MFI)

    Money Flow Index is an oscillator indicator that is used to measure buying and
    selling pressure by utilizing both price and volume.

    Sources:
        https://www.tradingview.com/wiki/Money_Flow_(MFI)

    Calculation:
        Default Inputs:
            length=14, drift=1
        tp = typical_price = hlc3 = (high + low + close) / 3
        rmf = raw_money_flow = tp * volume

        pmf = pos_money_flow = SUM(rmf, length) if tp.diff(drift) > 0 else 0
        nmf = neg_money_flow = SUM(rmf, length) if tp.diff(drift) < 0 else 0

        MFR = money_flow_ratio = pmf / nmf
        MFI = money_flow_index = 100 * pmf / (pmf + nmf)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        length (int): The sum period. Default: 14
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def midpoint(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Midpoint Over Period (MIDPOINT)

    MIDPOINT calculates the midpoint between the highest and lowest values of
    the close price over a specified period. This indicator helps identify the
    center of the price range and can be used to detect potential support and
    resistance levels.

    Sources:
        https://www.tradingview.com/support/solutions/43000594683-midpoint/
        https://ta-lib.org/function.html?name=MIDPOINT

    Calculation:
        Default Inputs:
            length=2

        LOWEST = MIN(close, length)
        HIGHEST = MAX(close, length)
        MIDPOINT = (LOWEST + HIGHEST) / 2

    Args:
        close (pd.Series): Series of 'close's
        length (int): Its period. Default: 2
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        min_periods (int, optional): Minimum number of observations required. Default: length
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def midprice(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Midpoint Price Over Period (MIDPRICE)

    MIDPRICE calculates the midpoint between the highest high and lowest low
    over a specified period. Similar to MIDPOINT but uses high and low prices
    instead of close prices. This provides a measure of the center of the
    price range and is useful for identifying equilibrium levels.

    Sources:
        https://www.tradingview.com/support/solutions/43000594684-midprice/
        https://ta-lib.org/function.html?name=MIDPRICE

    Calculation:
        Default Inputs:
            length=2

        LOWEST_LOW = MIN(low, length)
        HIGHEST_HIGH = MAX(high, length)
        MIDPRICE = (LOWEST_LOW + HIGHEST_HIGH) / 2

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        length (int): Its period. Default: 2
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        min_periods (int, optional): Minimum number of observations required. Default: length
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def minus_dm(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Minus Directional Movement (-DM, MINUS_DM)

    Raw Wilder-smoothed negative directional movement before conversion to DI-.

    TA-Lib name: MINUS_DM.

    Args:
        high (pd.Series): Series of 'high' prices
        low (pd.Series): Series of 'low' prices
        length (int): Lookback period. Default: 14
        talib (bool): Use TA-Lib C library if installed. Default: False
        drift (int): Difference period. Default: 1
        offset (int): Periods to offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series
    """
    ...

def mmar(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Madrid Moving Average Ribbon (MMAR)

    The Madrid Moving Average Ribbon is a visual trend indicator that consists of
    multiple EMAs with incrementally increasing periods. It helps identify trend
    strength and direction through the spacing and alignment of the moving averages.

    Sources:
        https://www.tradingview.com/script/a87v7d4L-Madrid-Moving-Average-Ribbon/
        https://www.forexstrategiesresources.com/trend-following-forex-strategies/

    Calculation:
        Default Inputs:
            length=10, step=5, num_ribbons=6

        For i in range(num_ribbons):
            period = length + (i * step)
            MMAR[i] = EMA(close, period)

        Returns DataFrame with columns:
        MMAR_10, MMAR_15, MMAR_20, MMAR_25, MMAR_30, MMAR_35

    Args:
        close (pd.Series): Series of 'close's
        length (int): Initial EMA period. Default: 10
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        step (int): Period increment between ribbons. Default: 5
        num_ribbons (int): Number of EMA ribbons. Default: 6
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: New features generated.
    """
    ...

def mom(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Momentum (MOM)

    Momentum is an indicator used to measure a security's speed (or strength) of
    movement.  Or simply the change in price.

    Sources:
        http://www.onlinetradingconcepts.com/TechnicalAnalysis/Momentum.html

    Calculation:
        Default Inputs:
            length=1
        MOM = close.diff(length)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 1
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def msw(data: pd.Series | pd.DataFrame, period: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Mesa Sine Wave (MSW)

    Introduced by John F. Ehlers in "Rocket Science For Traders" (2001).
    Uses a DFT of the recent ``period`` bars to estimate phase and outputs
    two oscillators that help identify cycle turning points.

    Sources:
        Tulip Indicators: https://tulipindicators.org/msw
        Ehlers, John F. (2001) Rocket Science For Traders

    Args:
        close (pd.Series): Close price series.
        period (int): Lookback period. Default: 5.
        offset (int): Number of periods to offset. Default: 0.

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: Columns MSW_SINE_{period}, MSW_LEAD_{period}.

    Example:
        df[['MSW_SINE_5', 'MSW_LEAD_5']] = df.ta.msw()
    """
    ...

def natr(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, mamode: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Normalized Average True Range (NATR)

    Normalized Average True Range attempt to normalize the average true range.

    Sources:
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/normalized-average-true-range-natr/

    Calculation:
        Default Inputs:
            length=20
        ATR = Average True Range
        NATR = (100 / close) * ATR(high, low, close)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): The short period. Default: 20
        scalar (float): How much to magnify. Default: 100
        mamode (str): See ```help(ta.ma)```. Default: 'ema'
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature
    """
    ...

def nvi(data: pd.Series | pd.DataFrame, length: Any = None, initial: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Negative Volume Index (NVI)

    The Negative Volume Index is a cumulative indicator that uses volume change in
    an attempt to identify where smart money is active.

    Sources:
        https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:negative_volume_inde
        https://www.motivewave.com/studies/negative_volume_index.htm

    Calculation:
        Default Inputs:
            length=1, initial=1000
        ROC = Rate of Change

        roc = ROC(close, length)
        signed_volume = signed_series(volume, initial=1)
        nvi = signed_volume[signed_volume < 0].abs() * roc_
        nvi.fillna(0, inplace=True)
        nvi.iloc[0]= initial
        nvi = nvi.cumsum()

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        length (int): The short period. Default: 13
        initial (int): The short period. Default: 1000
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def obv(data: pd.Series | pd.DataFrame, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    On Balance Volume (OBV)

    On Balance Volume is a cumulative indicator to measure buying and selling
    pressure.

    Sources:
        https://www.tradingview.com/wiki/On_Balance_Volume_(OBV)
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/on-balance-volume-obv/
        https://www.motivewave.com/studies/on_balance_volume.htm

    Calculation:
        signed_volume = signed_series(close, initial=1) * volume
        obv = signed_volume.cumsum()

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def ohlc4(data: pd.Series | pd.DataFrame, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    OHLC4 (Average of Open, High, Low, Close)

    OHLC4 calculates the average of the Open, High, Low, and Close prices for
    each period. This simple average provides a balanced representation of price
    action across the entire period, giving equal weight to all four OHLC values.
    It's commonly used as a smoother alternative to close prices alone.

    Sources:
        https://www.tradingview.com/support/solutions/43000502001-ohlc4/
        https://www.investopedia.com/terms/o/ohlc-chart.asp

    Calculation:
        Default Inputs:
            None (uses raw OHLC prices)

        OHLC4 = (Open + High + Low + Close) / 4

    Args:
        open_ (pd.Series): Series of 'open' prices
        high (pd.Series): Series of 'high' prices
        low (pd.Series): Series of 'low' prices
        close (pd.Series): Series of 'close' prices
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def pdist(data: pd.Series | pd.DataFrame, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Price Distance (PDIST)

    Measures the "distance" covered by price movements.

    Sources:
        https://www.prorealcode.com/prorealtime-indicators/pricedistance/

    Calculation:
        Default Inputs:
            drift=1

        PDIST = 2(high - low) - ABS(close - open) + ABS(open - close[drift])

    Args:
        open_ (pd.Series): Series of 'opens's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def percent_return(data: pd.Series | pd.DataFrame, length: Any = None, cumulative: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Percent Return

    Calculates the percent return of a Series.
    See also: help(df.ta.percent_return) for additional **kwargs a valid 'df'.

    Sources:
        https://stackoverflow.com/questions/31287552/logarithmic-returns-in-pandas-dataframe

    Calculation:
        Default Inputs:
            length=1, cumulative=False
        PCTRET = close / close.shift(length) - 1
        CUMPCTRET = PCTRET.cumsum() if cumulative

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 20
        cumulative (bool): If True, returns the cumulative returns. Default: False
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def pgo(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Pretty Good Oscillator (PGO)

    The Pretty Good Oscillator indicator was created by Mark Johnson to measure the distance of the current close from its N-day Simple Moving Average, expressed in terms of an average true range over a similar period. Johnson's approach was to
    use it as a breakout system for longer term trades. Long if greater than 3.0 and
    short if less than -3.0.

    Sources:
        https://library.tradingtechnologies.com/trade/chrt-ti-pretty-good-oscillator.html

    Calculation:
        Default Inputs:
            length=14
        ATR = Average True Range
        SMA = Simple Moving Average
        EMA = Exponential Moving Average

        PGO = (close - SMA(close, length)) / EMA(ATR(high, low, close, length), length)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def plus_dm(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Plus Directional Movement (+DM, PLUS_DM)

    Raw Wilder-smoothed positive directional movement before conversion to DI+.

    TA-Lib name: PLUS_DM.

    Args:
        high (pd.Series): Series of 'high' prices
        low (pd.Series): Series of 'low' prices
        length (int): Lookback period. Default: 14
        talib (bool): Use TA-Lib C library if installed. Default: False
        drift (int): Difference period. Default: 1
        offset (int): Periods to offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series
    """
    ...

def pmax(data: pd.Series | pd.DataFrame, length: Any = None, multiplier: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    PMAX (Price Max)

    PMAX is a trend-following indicator that combines moving averages with ATR
    (Average True Range) to create adaptive support and resistance levels. It helps
    identify trend direction and potential reversal points.

    Sources:
        https://www.tradingview.com/script/sU9molfV/
        https://www.prorealcode.com/prorealtime-indicators/pmax/

    Calculation:
        Default Inputs:
            length=10, multiplier=3.0, mamode='ema'

        ATR = ATR(high, low, close, length)
        MA = MA(close, length, mamode)

        PMAX_UP = MA - (multiplier * ATR)
        PMAX_DOWN = MA + (multiplier * ATR)

        If close > PMAX_DOWN[1]: trend = 1 (uptrend)
        If close < PMAX_UP[1]: trend = -1 (downtrend)

        PMAX = PMAX_UP if trend == 1 else PMAX_DOWN

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): ATR period. Default: 10
        multiplier (float): ATR multiplier. Default: 3.0
        mamode (str): Moving average mode. Default: 'ema'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def po(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Projection Oscillator (PO)

    The Projection Oscillator measures the percentage deviation of price from its
    linear regression trend line. It helps identify overbought and oversold conditions
    relative to the trend.

    Sources:
        https://www.tradingview.com/script/CDdh2vTz-Projection-Oscillator/
        Technical Analysis of Stock Trends by Edwards & Magee

    Calculation:
        Default Inputs:
            length=14

        LR = Linear Regression(close, length)
        PO = 100 * (close - LR) / LR

    Args:
        close (pd.Series): Series of 'close's
        length (int): The period. Default: 14
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def ppo(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, signal: Any = None, scalar: Any = None, mamode: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Percentage Price Oscillator (PPO)

    The Percentage Price Oscillator is similar to MACD in measuring momentum.

    Sources:
        https://www.tradingview.com/wiki/MACD_(Moving_Average_Convergence/Divergence)

    Calculation:
        Default Inputs:
            fast=12, slow=26
        SMA = Simple Moving Average
        EMA = Exponential Moving Average
        fast_sma = SMA(close, fast)
        slow_sma = SMA(close, slow)
        PPO = 100 * (fast_sma - slow_sma) / slow_sma
        Signal = EMA(PPO, signal)
        Histogram = PPO - Signal

    Args:
        close(pandas.Series): Series of 'close's
        fast(int): The short period. Default: 12
        slow(int): The long period. Default: 26
        signal(int): The signal period. Default: 9
        scalar (float): How much to magnify. Default: 100
        mamode (str): See ```help(ta.ma)```. Default: 'sma'
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset(int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: ppo, histogram, signal columns
    """
    ...

def psar(data: pd.Series | pd.DataFrame, af0: Any = None, af: Any = None, max_af: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Parabolic Stop and Reverse (psar)

    Parabolic Stop and Reverse (PSAR) was developed by J. Wells Wilder, that is used
    to determine trend direction and it's potential reversals in price. PSAR uses a
    trailing stop and reverse method called "SAR," or stop and reverse, to identify
    possible entries and exits. It is also known as SAR.

    PSAR indicator typically appears on a chart as a series of dots, either above or
    below an asset's price, depending on the direction the price is moving. A dot is
    placed below the price when it is trending upward, and above the price when it
    is trending downward.

    Sources:
        https://www.tradingview.com/pine-script-reference/#fun_sar
        https://www.sierrachart.com/index.php?page=doc/StudiesReference.php&ID=66&Name=Parabolic

    Calculation:
        Default Inputs:
            af0=0.02, af=0.02, max_af=0.2

        See Source links

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series, optional): Series of 'close's. Optional
        af0 (float): Initial Acceleration Factor. Default: 0.02
        af (float): Acceleration Factor. Default: 0.02
        max_af (float): Maximum Acceleration Factor. Default: 0.2
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version (SAR only, long/short/af/reversal columns not available). Default: False
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: long, short, af, and reversal columns.
    """
    ...

def psl(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Psychological Line (PSL)

    The Psychological Line is an oscillator-type indicator that compares the
    number of the rising periods to the total number of periods. In other
    words, it is the percentage of bars that close above the previous
    bar over a given period.

    Sources:
        https://www.quantshare.com/item-851-psychological-line

    Calculation:
        Default Inputs:
            length=12, scalar=100, drift=1

        IF NOT open:
            DIFF = SIGN(close - close[drift])
        ELSE:
            DIFF = SIGN(close - open)

        DIFF.fillna(0)
        DIFF[DIFF <= 0] = 0

        PSL = scalar * SUM(DIFF, length) / length

    Args:
        close (pd.Series): Series of 'close's
        open_ (pd.Series, optional): Series of 'open's
        length (int): It's period. Default: 12
        scalar (float): How much to magnify. Default: 100
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def pvi(data: pd.Series | pd.DataFrame, length: Any = None, initial: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Positive Volume Index (PVI)

    The Positive Volume Index is a cumulative indicator that uses volume change in
    an attempt to identify where smart money is active.
    Used in conjunction with NVI.

    Sources:
        https://www.investopedia.com/terms/p/pvi.asp

    Calculation:
        Default Inputs:
            length=1, initial=1000
        ROC = Rate of Change

        roc = ROC(close, length)
        signed_volume = signed_series(volume, initial=1)
        pvi = signed_volume[signed_volume > 0].abs() * roc_
        pvi.fillna(0, inplace=True)
        pvi.iloc[0]= initial
        pvi = pvi.cumsum()

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        length (int): The short period. Default: 13
        initial (int): The short period. Default: 1000
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def pvo(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, signal: Any = None, scalar: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Percentage Volume Oscillator (PVO)

    Percentage Volume Oscillator is a Momentum Oscillator for Volume.

    Sources:
        https://www.fmlabs.com/reference/default.htm?url=PVO.htm

    Calculation:
        Default Inputs:
            fast=12, slow=26, signal=9
        EMA = Exponential Moving Average

        PVO = (EMA(volume, fast) - EMA(volume, slow)) / EMA(volume, slow)
        Signal = EMA(PVO, signal)
        Histogram = PVO - Signal

    Args:
        volume (pd.Series): Series of 'volume's
        fast (int): The short period. Default: 12
        slow (int): The long period. Default: 26
        signal (int): The signal period. Default: 9
        scalar (float): How much to magnify. Default: 100
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: pvo, histogram, signal columns.
    """
    ...

def pvol(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Price-Volume (PVOL)

    Returns a series of the product of price and volume.

    Calculation:
        if signed:
            pvol = signed_series(close, 1) * close * volume
        else:
            pvol = close * volume

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        signed (bool): Keeps the sign of the difference in 'close's. Default: False
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def pvr(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Price Volume Rank

    The Price Volume Rank was developed by Anthony J. Macek and is described in his
    article in the June, 1994 issue of Technical Analysis of Stocks & Commodities
    Magazine. It was developed as a simple indicator that could be calculated even
    without a computer. The basic interpretation is to buy when the PV Rank is below
    2.5 and sell when it is above 2.5.

    Sources:
        https://www.fmlabs.com/reference/default.htm?url=PVrank.htm

    Calculation:
        return 1 if 'close change' >= 0 and 'volume change' >= 0
        return 2 if 'close change' >= 0 and 'volume change' < 0
        return 3 if 'close change' < 0 and 'volume change' >= 0
        return 4 if 'close change' < 0 and 'volume change' < 0

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method ('ffill' or 'bfill')

    Returns:
        pd.Series: New feature generated.
    """
    ...

def pvt(data: pd.Series | pd.DataFrame, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Price-Volume Trend (PVT)

    The Price-Volume Trend utilizes the Rate of Change with volume to
    and it's cumulative values to determine money flow.

    Sources:
        https://www.tradingview.com/wiki/Price_Volume_Trend_(PVT)

    Calculation:
        Default Inputs:
            drift=1
        ROC = Rate of Change
        pv = ROC(close, drift) * volume
        PVT = pv.cumsum()

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        drift (int): The diff period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def pwma(data: pd.Series | pd.DataFrame, length: Any = None, asc: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Pascal's Weighted Moving Average (PWMA)

    Pascal's Weighted Moving Average is similar to a symmetric triangular window
    except PWMA's weights are based on Pascal's Triangle.

    Source: Kevin Johnson

    Calculation:
        Default Inputs:
            length=10

        def weights(w):
            def _compute(x):
                return np.dot(w * x)
            return _compute

        triangle = utils.pascals_triangle(length + 1)
        PWMA = close.rolling(length)_.apply(weights(triangle), raw=True)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period.  Default: 10
        asc (bool): Recent values weigh more. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def qqe(data: pd.Series | pd.DataFrame, length: Any = None, smooth: Any = None, factor: Any = None, mamode: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Quantitative Qualitative Estimation (QQE)

    The Quantitative Qualitative Estimation (QQE) is similar to SuperTrend but uses a Smoothed RSI with an upper and lower bands. The band width is a combination of a one period True Range of the Smoothed RSI which is double smoothed using Wilder's smoothing length (2 * rsiLength - 1) and multiplied by the default factor of 4.236. A Long trend is determined when the Smoothed RSI crosses the previous upperband and a Short trend when the Smoothed RSI crosses the previous lowerband.

    Based on QQE.mq5 by EarnForex Copyright © 2010, based on version by Tim Hyder (2008), based on version by Roman Ignatov (2006)

    Sources:
        https://www.tradingview.com/script/IYfA9R2k-QQE-MT4/
        https://www.tradingpedia.com/forex-trading-indicators/quantitative-qualitative-estimation
        https://www.prorealcode.com/prorealtime-indicators/qqe-quantitative-qualitative-estimation/

    Calculation:
        Default Inputs:
            length=14, smooth=5, factor=4.236, mamode="ema", drift=1

    Args:
        close (pd.Series): Series of 'close's
        length (int): RSI period. Default: 14
        smooth (int): RSI smoothing period. Default: 5
        factor (float): QQE Factor. Default: 4.236
        mamode (str): See ```help(ta.ma)```. Default: 'sma'
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: QQE, RSI_MA (basis), QQEl (sparse long signal),
            QQEs (sparse short signal), QQEb_l (continuous long band),
            QQEb_s (continuous short band), and QQEd (trend direction) columns.
    """
    ...

def qstick(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Q Stick

    The Q Stick indicator, developed by Tushar Chande, attempts to quantify and
    identify trends in candlestick charts.

    Sources:
        https://library.tradingtechnologies.com/trade/chrt-ti-qstick.html

    Calculation:
        Default Inputs:
            length=10
        xMA is one of: sma (default), dema, ema, hma, rma
        qstick = xMA(close - open, length)

    Args:
        open (pd.Series): Series of 'open's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 1
        ma (str): The type of moving average to use. Default: None, which is 'sma'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def quantile(data: pd.Series | pd.DataFrame, length: Any = None, q: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rolling Quantile

    Sources:

    Calculation:
        Default Inputs:
            length=30, q=0.5
        QUANTILE = close.rolling(length).quantile(q)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 30
        q (float): The quantile. Default: 0.5
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def rainbow(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rainbow Charts

    Rainbow Charts use multiple moving averages calculated sequentially, where each
    MA is calculated on the previous MA rather than the price. This creates a
    "rainbow" effect that helps visualize trend strength and potential reversals.

    Sources:
        https://www.investopedia.com/articles/trading/06/rainbow.asp
        https://www.prorealcode.com/prorealtime-indicators/rainbow-oscillator/

    Calculation:
        Default Inputs:
            length=2, num_ribbons=10

        MA1 = SMA(close, length)
        MA2 = SMA(MA1, length)
        MA3 = SMA(MA2, length)
        ...
        MA[n] = SMA(MA[n-1], length)

    Args:
        close (pd.Series): Series of 'close's
        length (int): SMA period. Default: 2
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        num_ribbons (int): Number of rainbow bands. Default: 10
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: New features generated.
    """
    ...

def rma(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Wilder's Moving Average (RMA)

    Wilder's Moving Average is simply an Exponential Moving Average (EMA) with
    a modified alpha = 1 / length.

    Sources:
        https://tlc.thinkorswim.com/center/reference/Tech-Indicators/studies-library/V-Z/WildersSmoothing
        https://www.incrediblecharts.com/indicators/wilder_moving_average.php

    Calculation:
        Default Inputs:
            length=10
        alpha = 1 / length
        SMA_nth = SMA(close, length)
        close[:length - 1] = NaN
        close[length - 1] = SMA_nth
        RMA = EWM(close, alpha=alpha, adjust=False)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def roc(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rate of Change (ROC)

    Rate of Change is an indicator is also referred to as Momentum (yeah, confusingly).
    It is a pure momentum oscillator that measures the percent change in price with the
    previous price 'n' (or length) periods ago.

    Sources:
        https://www.tradingview.com/wiki/Rate_of_Change_(ROC)

    Calculation:
        Default Inputs:
            length=1
        MOM = Momentum
        ROC = 100 * MOM(close, length) / close.shift(length)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 1
        scalar (float): How much to magnify. Default: 100
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def rocp(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rate of Change Percentage (ROCP)

    Rate of Change Percentage measures the percentage change in price over a
    given period, expressed as a ratio (not multiplied by 100).

    ROCP = (close - close[n]) / close[n]

    Sources:
        https://www.investopedia.com/terms/r/rateofchange.asp

    Args:
        close (pd.Series): Close price series.
        length (int): The period. Default: 10
        talib (bool): Use TA-Lib if installed. Default: False
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: ROCP values.
    """
    ...

def rocr(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rate of Change Ratio (ROCR)

    Rate of Change Ratio measures the ratio of the current price to the price
    n periods ago.

    ROCR = close / close[n]

    Sources:
        https://www.investopedia.com/terms/r/rateofchange.asp

    Args:
        close (pd.Series): Close price series.
        length (int): The period. Default: 10
        talib (bool): Use TA-Lib if installed. Default: False
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: ROCR values.
    """
    ...

def rocr100(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rate of Change Ratio * 100 (ROCR100)

    Rate of Change Ratio * 100 measures the ratio of the current price to the
    price n periods ago, scaled by 100. A value of 100 means no change.

    ROCR100 = 100 * (close / close[n])

    Sources:
        https://www.investopedia.com/terms/r/rateofchange.asp

    Args:
        close (pd.Series): Close price series.
        length (int): The period. Default: 10
        talib (bool): Use TA-Lib if installed. Default: False
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: ROCR100 values.
    """
    ...

def rsi(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Relative Strength Index (RSI)

    The Relative Strength Index is popular momentum oscillator used to measure the
    velocity as well as the magnitude of directional price movements.

    Sources:
        https://www.tradingview.com/wiki/Relative_Strength_Index_(RSI)

    Calculation:
        Default Inputs:
            length=14, scalar=100, drift=1
        ABS = Absolute Value
        RMA = Rolling Moving Average

        diff = close.diff(drift)
        positive = diff if diff > 0 else 0
        negative = diff if diff < 0 else 0

        pos_avg = RMA(positive, length)
        neg_avg = ABS(RMA(negative, length))

        RSI = scalar * pos_avg / (pos_avg + neg_avg)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        scalar (float): How much to magnify. Default: 100
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def rsx(data: pd.Series | pd.DataFrame, length: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Relative Strength Xtra (rsx)

    The Relative Strength Xtra is based on the popular RSI indicator and inspired
    by the work Jurik Research. The code implemented is based on published code
    found at 'prorealcode.com'. This enhanced version of the rsi reduces noise and
    provides a clearer, only slightly delayed insight on momentum and velocity of
    price movements.

    Sources:
        http://www.jurikres.com/catalog1/ms_rsx.htm
        https://www.prorealcode.com/prorealtime-indicators/jurik-rsx/

    Calculation:
        Refer to the sources above for information as well as code example.

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def rvgi(data: pd.Series | pd.DataFrame, length: Any = None, swma_length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Relative Vigor Index (RVGI)

    The Relative Vigor Index attempts to measure the strength of a trend relative to
    its closing price to its trading range.  It is based on the belief that it tends
    to close higher than they open in uptrends or close lower than they open in
    downtrends.

    Sources:
        https://www.investopedia.com/terms/r/relative_vigor_index.asp

    Calculation:
        Default Inputs:
            length=14, swma_length=4
        SWMA = Symmetrically Weighted Moving Average
        numerator = SUM(SWMA(close - open, swma_length), length)
        denominator = SUM(SWMA(high - low, swma_length), length)
        RVGI = numerator / denominator

    Args:
        open_ (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        swma_length (int): It's period. Default: 4
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def rvi(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, refined: Any = None, thirds: Any = None, mamode: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Relative Volatility Index (RVI)

    The Relative Volatility Index (RVI) was created in 1993 and revised in 1995.
    Instead of adding up price changes like RSI based on price direction, the RVI
    adds up standard deviations based on price direction.

    Sources:
        https://www.tradingview.com/wiki/Keltner_Channels_(KC)

    Calculation:
        Default Inputs:
            length=14, scalar=100, refined=None, thirds=None
        EMA = Exponential Moving Average
        STDEV = Standard Deviation

        UP = STDEV(src, length) IF src.diff() > 0 ELSE 0
        DOWN = STDEV(src, length) IF src.diff() <= 0 ELSE 0

        UPSUM = EMA(UP, length)
        DOWNSUM = EMA(DOWN, length)

        RVI = scalar * (UPSUM / (UPSUM + DOWNSUM))

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): The short period. Default: 14
        scalar (float): A positive float to scale the bands. Default: 100
        refined (bool): Use 'refined' calculation which is the average of
            RVI(high) and RVI(low) instead of RVI(close). Default: False
        thirds (bool): Average of high, low and close. Default: False
        mamode (str): See ```help(ta.ma)```. Default: 'ema'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: lower, basis, upper columns.
    """
    ...

def sarext(data: pd.Series | pd.DataFrame, startvalue: Any = None, offsetonreverse: Any = None, accelerationinitlong: Any = None, accelerationlong: Any = None, accelerationmaxlong: Any = None, accelerationinitshort: Any = None, accelerationshort: Any = None, accelerationmaxshort: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Parabolic SAR Extended (SAREXT)

    The Parabolic SAR Extended is an enhanced version of the Parabolic SAR that
    allows separate acceleration factor settings for long and short positions,
    plus an optional offset applied when a reversal occurs.

    Sources:
        https://mrjbq7.github.io/ta-lib/func_groups/overlap_studies.html

    Args:
        high (pd.Series): High price series.
        low (pd.Series): Low price series.
        startvalue (float): Starting SAR value (0 = use first high/low). Default: 0
        offsetonreverse (float): Fractional offset added to SAR on reversal. Default: 0
        accelerationinitlong (float): Initial AF for long positions. Default: 0.02
        accelerationlong (float): AF increment for long positions. Default: 0.02
        accelerationmaxlong (float): Maximum AF for long positions. Default: 0.2
        accelerationinitshort (float): Initial AF for short positions. Default: 0.02
        accelerationshort (float): AF increment for short positions. Default: 0.02
        accelerationmaxshort (float): Maximum AF for short positions. Default: 0.2
        talib (bool): Use TA-Lib if installed. Default: False
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: SAREXT values (positive = long SAR, negative = short SAR).
    """
    ...

def short_run(data: pd.Series | pd.DataFrame, fast: Any = ..., slow: Any = ..., length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Short Run

    Identifies potential short (bearish) trend conditions by detecting when the fast
    moving average is decreasing while the slow moving average is either increasing
    (potential top) or also decreasing (confirmed downtrend).

    Sources:
        Used in AMAT (Archer Moving Averages Trends) indicator

    Calculation:
        Default Inputs:
            length=2

        PT = DECREASING(fast, length) AND INCREASING(slow, length)  # Potential top
        BD = DECREASING(fast, length) AND DECREASING(slow, length)  # Both decreasing
        SHORT_RUN = PT OR BD

    Args:
        fast (pd.Series): Fast moving average Series (e.g. EMA(5)). Pre-computed,
            not a period length.
        slow (pd.Series): Slow moving average Series (e.g. EMA(20)). Pre-computed,
            not a period length.
        length (int): Lookback period. Default: 2
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Example:
        fast_ma = df.ta.ema(length=5)
        slow_ma = df.ta.ema(length=20)
        sr = ta.short_run(fast_ma, slow_ma)

    Returns:
        pd.Series: New feature generated (boolean).
    """
    ...

def sinwma(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Sine Weighted Moving Average (SWMA)

    A weighted average using sine cycles. The middle term(s) of the average have the
    highest weight(s).

    Source:
        https://www.tradingview.com/script/6MWFvnPO-Sine-Weighted-Moving-Average/
        Author: Everget (https://www.tradingview.com/u/everget/)

    Calculation:
        Default Inputs:
            length=10

        def weights(w):
            def _compute(x):
                return np.dot(w * x)
            return _compute

        sines = Series([sin((i + 1) * pi / (length + 1)) for i in range(0, length)])
        w = sines / sines.sum()
        SINWMA = close.rolling(length, min_periods=length).apply(weights(w), raw=True)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def skew(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rolling Skew

    Sources:

    Calculation:
        Default Inputs:
            length=30
        SKEW = close.rolling(length).skew()

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 30
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def slope(data: pd.Series | pd.DataFrame, length: Any = None, as_angle: Any = None, to_degrees: Any = None, vertical: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Slope

    Returns the slope of a series of length n. Can convert the slope to angle.
    Default: slope.

    Sources: Algebra I

    Calculation:
        Default Inputs:
            length=1
        slope = close.diff(length) / length

        if as_angle:
            slope = slope.apply(atan)
            if to_degrees:
                slope *= 180 / PI

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period.  Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        as_angle (value, optional): Converts slope to an angle. Default: False
        to_degrees (value, optional): Converts slope angle to degrees. Default: False
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def sma(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Simple Moving Average (SMA)

    The Simple Moving Average is the classic moving average that is the equally
    weighted average over n periods.

    Sources:
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/simple-moving-average-sma/

    Calculation:
        Default Inputs:
            length=10
        SMA = SUM(close, length) / length

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        adjust (bool): Default: True
        presma (bool, optional): If True, uses SMA for initial value.
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def smc_sweep(data: pd.Series | pd.DataFrame, length: Any = None, wick_mult: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Smart Money Concept Liquidity Sweep (SMC_SWEEP)

    Identifies when price sweeps below a swing low (or above a swing high),
    violently rejects it, leaving a long wick and closing in the opposite direction.

    Sources:
        Smart Money Concept / ICT trading methodology

    Calculation:
        Default Inputs:
            length=15, wick_mult=1.5
        swing_low  = rolling min of low over length bars (shifted 1)
        swing_high = rolling max of high over length bars (shifted 1)
        body       = abs(close - open)
        lower_wick = min(open, close) - low
        upper_wick = high - max(open, close)
        Bull: low < swing_low AND close > swing_low AND close > open AND lower_wick > body * wick_mult → +1
        Bear: high > swing_high AND close < swing_high AND close < open AND upper_wick > body * wick_mult → -1

    Args:
        open_ (pd.Series): Series of 'open's
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): Swing high/low lookback period. Default: 15
        wick_mult (float): Wick-to-body ratio multiplier. Default: 1.5
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: 1 (Bullish Sweep), -1 (Bearish Sweep), 0 (None).
    """
    ...

def smi(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, signal: Any = None, scalar: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    SMI Ergodic Indicator (SMI)

    The SMI Ergodic Indicator is the same as the True Strength Index (TSI) developed
    by William Blau, except the SMI includes a signal line. The SMI uses double
    moving averages of price minus previous price over 2 time frames. The signal
    line, which is an EMA of the SMI, is plotted to help trigger trading signals.
    The trend is bullish when crossing above zero and bearish when crossing below
    zero. This implementation includes both the SMI Ergodic Indicator and SMI
    Ergodic Oscillator.

    Sources:
        https://www.motivewave.com/studies/smi_ergodic_indicator.htm
        https://www.tradingview.com/script/Xh5Q0une-SMI-Ergodic-Oscillator/
        https://www.tradingview.com/script/cwrgy4fw-SMIIO/

    Calculation:
        Default Inputs:
            fast=5, slow=20, signal=5
        TSI = True Strength Index
        EMA = Exponential Moving Average

        ERG = TSI(close, fast, slow)
        Signal = EMA(ERG, signal)
        OSC = ERG - Signal

    Args:
        close (pd.Series): Series of 'close's
        fast (int): The short period. Default: 5
        slow (int): The long period. Default: 20
        signal (int): The signal period. Default: 5
        scalar (float): How much to magnify. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: smi, signal, oscillator columns.
    """
    ...

def squeeze(data: pd.Series | pd.DataFrame, bb_length: Any = None, bb_std: Any = None, kc_length: Any = None, kc_scalar: Any = None, mom_length: Any = None, mom_smooth: Any = None, use_tr: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Squeeze (SQZ)

    The default is based on John Carter's "TTM Squeeze" indicator, as discussed
    in his book "Mastering the Trade" (chapter 11). The Squeeze indicator attempts
    to capture the relationship between two studies: Bollinger Bands® and Keltner's
    Channels. When the volatility increases, so does the distance between the bands,
    conversely, when the volatility declines, the distance also decreases. It finds
    sections of the Bollinger Bands® study which fall inside the Keltner's Channels.

    Sources:
        https://tradestation.tradingappstore.com/products/TTMSqueeze
        https://www.tradingview.com/scripts/lazybear/
        https://tlc.thinkorswim.com/center/reference/Tech-Indicators/studies-library/T-U/TTM-Squeeze

    Calculation:
        Default Inputs:
            bb_length=20, bb_std=2, kc_length=20, kc_scalar=1.5, mom_length=12,
            mom_smooth=12, tr=True, lazybear=False,
        BB = Bollinger Bands
        KC = Keltner Channels
        MOM = Momentum
        SMA = Simple Moving Average
        EMA = Exponential Moving Average
        TR = True Range

        RANGE = TR(high, low, close) if using_tr else high - low
        BB_LOW, BB_MID, BB_HIGH = BB(close, bb_length, std=bb_std)
        KC_LOW, KC_MID, KC_HIGH = KC(high, low, close, kc_length, kc_scalar, TR)

        if lazybear:
            HH = high.rolling(kc_length).max()
            LL = low.rolling(kc_length).min()
            AVG  = 0.25 * (HH + LL) + 0.5 * KC_MID
            SQZ = linreg(close - AVG, kc_length)
        else:
            MOMO = MOM(close, mom_length)
            if mamode == "ema":
                SQZ = EMA(MOMO, mom_smooth)
            else:
                SQZ = EMA(momo, mom_smooth)

        SQZ_ON  = (BB_LOW > KC_LOW) and (BB_HIGH < KC_HIGH)
        SQZ_OFF = (BB_LOW < KC_LOW) and (BB_HIGH > KC_HIGH)
        NO_SQZ = !SQZ_ON and !SQZ_OFF

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        bb_length (int): Bollinger Bands period. Default: 20
        bb_std (float): Bollinger Bands Std. Dev. Default: 2
        kc_length (int): Keltner Channel period. Default: 20
        kc_scalar (float): Keltner Channel scalar. Default: 1.5
        mom_length (int): Momentum Period. Default: 12
        mom_smooth (int): Smoothing Period of Momentum. Default: 6
        mamode (str): Only "ema" or "sma". Default: "sma"
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        tr (value, optional): Use True Range for Keltner Channels. Default: True
        asint (value, optional): Use integers instead of bool. Default: True
        mamode (value, optional): Which MA to use. Default: "sma"
        lazybear (value, optional): Use LazyBear's TradingView implementation.
            Default: False
        detailed (value, optional): Return additional variations of SQZ for
            visualization. Default: False
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: SQZ, SQZ_ON, SQZ_OFF, NO_SQZ columns by default. More
            detailed columns if 'detailed' kwarg is True.
    """
    ...

def squeeze_pro(data: pd.Series | pd.DataFrame, bb_length: Any = None, bb_std: Any = None, kc_length: Any = None, kc_scalar_wide: Any = None, kc_scalar_normal: Any = None, kc_scalar_narrow: Any = None, mom_length: Any = None, mom_smooth: Any = None, use_tr: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Squeeze PRO(SQZPRO)

    This indicator is an extended version of "TTM Squeeze" from John Carter.
    The default is based on John Carter's "TTM Squeeze" indicator, as discussed
    in his book "Mastering the Trade" (chapter 11). The Squeeze indicator attempts
    to capture the relationship between two studies: Bollinger Bands® and Keltner's
    Channels. When the volatility increases, so does the distance between the bands,
    conversely, when the volatility declines, the distance also decreases. It finds
    sections of the Bollinger Bands® study which fall inside the Keltner's Channels.

    Sources:
        https://usethinkscript.com/threads/john-carters-squeeze-pro-indicator-for-thinkorswim-free.4021/
        https://www.tradingview.com/script/TAAt6eRX-Squeeze-PRO-Indicator-Makit0/

    Calculation:
        Default Inputs:
            bb_length=20, bb_std=2, kc_length=20, kc_scalar_wide=2,
            kc_scalar_normal=1.5, kc_scalar_narrow=1, mom_length=12,
            mom_smooth=6, tr=True,
        BB = Bollinger Bands
        KC = Keltner Channels
        MOM = Momentum
        SMA = Simple Moving Average
        EMA = Exponential Moving Average
        TR = True Range

        RANGE = TR(high, low, close) if using_tr else high - low
        BB_LOW, BB_MID, BB_HIGH = BB(close, bb_length, std=bb_std)
        KC_LOW_WIDE, KC_MID_WIDE, KC_HIGH_WIDE = KC(high, low, close, kc_length, kc_scalar_wide, TR)
        KC_LOW_NORMAL, KC_MID_NORMAL, KC_HIGH_NORMAL = KC(high, low, close, kc_length, kc_scalar_normal, TR)
        KC_LOW_NARROW, KC_MID_NARROW, KC_HIGH_NARROW = KC(high, low, close, kc_length, kc_scalar_narrow, TR)

        MOMO = MOM(close, mom_length)
        if mamode == "ema":
            SQZPRO = EMA(MOMO, mom_smooth)
        else:
            SQZPRO = EMA(momo, mom_smooth)

        SQZPRO_ON_WIDE  = (BB_LOW > KC_LOW_WIDE) and (BB_HIGH < KC_HIGH_WIDE)
        SQZPRO_ON_NORMAL  = (BB_LOW > KC_LOW_NORMAL) and (BB_HIGH < KC_HIGH_NORMAL)
        SQZPRO_ON_NARROW  = (BB_LOW > KC_LOW_NARROW) and (BB_HIGH < KC_HIGH_NARROW)
        SQZPRO_OFF_WIDE = (BB_LOW < KC_LOW_WIDE) and (BB_HIGH > KC_HIGH_WIDE)
        SQZPRO_NO = !SQZ_ON_WIDE and !SQZ_OFF_WIDE

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        bb_length (int): Bollinger Bands period. Default: 20
        bb_std (float): Bollinger Bands Std. Dev. Default: 2
        kc_length (int): Keltner Channel period. Default: 20
        kc_scalar_wide (float): Keltner Channel scalar for wider channel. Default: 2
        kc_scalar_normal (float): Keltner Channel scalar for normal channel. Default: 1.5
        kc_scalar_narrow (float): Keltner Channel scalar for narrow channel. Default: 1
        mom_length (int): Momentum Period. Default: 12
        mom_smooth (int): Smoothing Period of Momentum. Default: 6
        mamode (str): Only "ema" or "sma". Default: "sma"
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        tr (value, optional): Use True Range for Keltner Channels. Default: True
        asint (value, optional): Use integers instead of bool. Default: True
        mamode (value, optional): Which MA to use. Default: "sma"
        detailed (value, optional): Return additional variations of SQZ for
            visualization. Default: False
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: SQZPRO, SQZPRO_ON_WIDE, SQZPRO_ON_NORMAL, SQZPRO_ON_NARROW, SQZPRO_OFF_WIDE, SQZPRO_NO columns by default. More
            detailed columns if 'detailed' kwarg is True.
    """
    ...

def ssf(data: pd.Series | pd.DataFrame, length: Any = None, poles: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Ehler's Super Smoother Filter (SSF) © 2013

    John F. Ehlers's solution to reduce lag and remove aliasing noise with his
    research in aerospace analog filter design. This indicator comes with two
    versions determined by the keyword poles. By default, it uses two poles but
    there is an option for three poles. Since SSF is a (Resursive) Digital Filter,
    the number of poles determine how many prior recursive SSF bars to include in
    the design of the filter. So two poles uses two prior SSF bars and three poles
    uses three prior SSF bars for their filter calculations.

    Sources:
        http://www.stockspotter.com/files/PredictiveIndicators.pdf
        https://www.tradingview.com/script/VdJy0yBJ-Ehlers-Super-Smoother-Filter/
        https://www.mql5.com/en/code/588
        https://www.mql5.com/en/code/589

    Calculation:
        Default Inputs:
            length=10, poles=[2, 3]

        See the source code or Sources listed above.

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        poles (int): The number of poles to use, either 2 or 3. Default: 2
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def stc(data: pd.Series | pd.DataFrame, tclength: Any = None, fast: Any = None, slow: Any = None, factor: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Schaff Trend Cycle (STC)

    The Schaff Trend Cycle is an evolution of the popular MACD incorportating two
    cascaded stochastic calculations with additional smoothing.

    The STC returns also the beginning MACD result as well as the result after the
    first stochastic including its smoothing. This implementation has been extended
    for Pandas TA to also allow for separatly feeding any other two moving Averages
    (as ma1 and ma2) or to skip this to feed an oscillator (osc), based on which the
    Schaff Trend Cycle should be calculated.

    Feed external moving averages:
    Internally calculation..
        stc = ta.stc(close=df["close"], tclen=stc_tclen, fast=ma1_interval, slow=ma2_interval, factor=stc_factor)
    becomes..
        extMa1 = df.ta.zlma(close=df["close"], length=ma1_interval, append=True)
        extMa2 = df.ta.ema(close=df["close"], length=ma2_interval, append=True)
        stc = ta.stc(close=df["close"], tclen=stc_tclen, ma1=extMa1, ma2=extMa2, factor=stc_factor)

    The same goes for osc=, which allows the input of an externally calculated oscillator, overriding ma1 & ma2.


    Sources:
        Implemented by rengel8 based on work found here:
        https://www.prorealcode.com/prorealtime-indicators/schaff-trend-cycle2/

    Calculation:
        STCmacd = Moving Average Convergance/Divergance or Oscillator
        STCstoch = Intermediate Stochastic of MACD/Osc.
        2nd Stochastic including filtering with results in the
        STC = Schaff Trend Cycle

    Args:
        close (pd.Series): Series of 'close's, used for indexing Series, mandatory
        tclen (int): SchaffTC Signal-Line length.  Default: 10 (adjust to the half of cycle)
        fast (int): The short period.   Default: 12
        slow (int): The long period.   Default: 26
        factor (float): smoothing factor for last stoch. calculation.   Default: 0.5
        offset (int): How many periods to offset the result.  Default: 0

    Kwargs:
        ma1: 1st moving average provided externally (mandatory in conjuction with ma2)
        ma2: 2nd moving average provided externally (mandatory in conjuction with ma1)
        osc: an externally feeded osillator
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: stc, macd, stoch
    """
    ...

def stderr(data: pd.Series | pd.DataFrame, length: Any = None, ddof: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Standard Error (STDERR)

    Standard Error is the standard deviation of the sample divided by the square
    root of the sample size. It estimates the precision of the sample mean as an
    estimate of the population mean.

    STDERR = StdDev(close, length) / sqrt(length)

    Sources:
        https://en.wikipedia.org/wiki/Standard_error

    Args:
        close (pd.Series): Price series.
        length (int): Rolling window period. Default: 14
        ddof (int): Degrees of freedom for std. Default: 1
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: STDERR values.
    """
    ...

def stdev(data: pd.Series | pd.DataFrame, length: Any = None, ddof: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rolling Standard Deviation

    Sources:

    Calculation:
        Default Inputs:
            length=30
        VAR = Variance
        STDEV = variance(close, length).apply(np.sqrt)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 30
        ddof (int): Delta Degrees of Freedom.
                    The divisor used in calculations is N - ddof,
                    where N represents the number of elements. Default: 0
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def stoch(data: pd.Series | pd.DataFrame, k: Any = None, d: Any = None, smooth_k: Any = None, mamode: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Stochastic (STOCH)

    The Stochastic Oscillator (STOCH) was developed by George Lane in the 1950's.
    He believed this indicator was a good way to measure momentum because changes in
    momentum precede changes in price.

    It is a range-bound oscillator with two lines moving between 0 and 100.
    The first line (%K) displays the current close in relation to the period's
    high/low range. The second line (%D) is a Simple Moving Average of the %K line.
    The most common choices are a 14 period %K and a 3 period SMA for %D.

    Sources:
        https://www.tradingview.com/wiki/Stochastic_(STOCH)
        https://www.sierrachart.com/index.php?page=doc/StudiesReference.php&ID=332&Name=KD_-_Slow

    Calculation:
        Default Inputs:
            k=14, d=3, smooth_k=3
        SMA = Simple Moving Average
        LL  = low for last k periods
        HH  = high for last k periods

        STOCH = 100 * (close - LL) / (HH - LL)
        STOCHk = SMA(STOCH, smooth_k)
        STOCHd = SMA(FASTK, d)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        k (int): The Fast %K period. Default: 14
        d (int): The Slow %K period. Default: 3
        smooth_k (int): The Slow %D period. Default: 3
        mamode (str): See ```help(ta.ma)```. Default: 'sma'
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version (SMA smoothing only). Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: %K, %D columns.
    """
    ...

def stochf(data: pd.Series | pd.DataFrame, fastk: Any = None, fastd: Any = None, mamode: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Stochastic Fast (STOCHF)

    The Stochastic Fast oscillator is a faster variant of the classic Stochastic
    oscillator. It uses a shorter smoothing period for %D, making it more
    responsive to price changes.

    %FastK = 100 * (Close - Lowest Low[n]) / (Highest High[n] - Lowest Low[n])
    %FastD = MA(%FastK, fastd_period)

    Sources:
        https://www.investopedia.com/terms/s/stochasticoscillator.asp

    Args:
        high (pd.Series): High price series.
        low (pd.Series): Low price series.
        close (pd.Series): Close price series.
        fastk (int): Fast %K period. Default: 5
        fastd (int): Fast %D smoothing period. Default: 3
        mamode (str): MA type for %D. Default: 'sma'
        talib (bool): Use TA-Lib if installed. Default: False
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: FastK and FastD columns.
    """
    ...

def stochrsi(data: pd.Series | pd.DataFrame, length: Any = None, rsi_length: Any = None, k: Any = None, d: Any = None, mamode: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Stochastic (STOCHRSI)

    "Stochastic RSI and Dynamic Momentum Index" was created by Tushar Chande and Stanley Kroll and published in Stock & Commodities V.11:5 (189-199)

    It is a range-bound oscillator with two lines moving between 0 and 100.
    The first line (%K) displays the current RSI in relation to the period's
    high/low range. The second line (%D) is a Simple Moving Average of the %K line.
    The most common choices are a 14 period %K and a 3 period SMA for %D.

    Sources:
        https://www.tradingview.com/wiki/Stochastic_(STOCH)

    Calculation:
        Default Inputs:
            length=14, rsi_length=14, k=3, d=3
        RSI = Relative Strength Index
        SMA = Simple Moving Average

        RSI = RSI(high, low, close, rsi_length)
        LL  = lowest RSI for last rsi_length periods
        HH  = highest RSI for last rsi_length periods

        STOCHRSI  = 100 * (RSI - LL) / (HH - LL)
        STOCHRSIk = SMA(STOCHRSI, k)
        STOCHRSId = SMA(STOCHRSIk, d)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): The STOCHRSI period. Default: 14
        rsi_length (int): RSI period. Default: 14
        k (int): The Fast %K period. Default: 3
        d (int): The Slow %K period. Default: 3
        mamode (str): See ```help(ta.ma)```. Default: 'sma'
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version (rsi_length ignored). Default: False
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: RSI %K, RSI %D columns.
    """
    ...

def supertrend(data: pd.Series | pd.DataFrame, length: Any = None, multiplier: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Supertrend (supertrend)

    Supertrend is an overlap indicator. It is used to help identify trend
    direction, setting stop loss, identify support and resistance, and/or
    generate buy & sell signals.

    Sources:
        http://www.freebsensetips.com/blog/detail/7/What-is-supertrend-indicator-its-calculation

    Calculation:
        Default Inputs:
            length=7, multiplier=3.0
        Default Direction:
    	Set to +1 or bullish trend at start

        MID = multiplier * ATR
        LOWERBAND = HL2 - MID
        UPPERBAND = HL2 + MID

        if UPPERBAND[i] < FINAL_UPPERBAND[i-1] and close[i-1] > FINAL_UPPERBAND[i-1]:
            FINAL_UPPERBAND[i] = UPPERBAND[i]
        else:
            FINAL_UPPERBAND[i] = FINAL_UPPERBAND[i-1])

        if LOWERBAND[i] > FINAL_LOWERBAND[i-1] and close[i-1] < FINAL_LOWERBAND[i-1]:
            FINAL_LOWERBAND[i] = LOWERBAND[i]
        else:
            FINAL_LOWERBAND[i] = FINAL_LOWERBAND[i-1])

        if close[i] <= FINAL_UPPERBAND[i]:
            SUPERTREND[i] = FINAL_UPPERBAND[i]
        else:
            SUPERTREND[i] = FINAL_LOWERBAND[i]

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int) : length for ATR calculation. Default: 7
        multiplier (float): Coefficient for upper and lower band distance to
            midrange. Default: 3.0
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: SUPERT (trend), SUPERTd (direction), SUPERTl (long), SUPERTs (short) columns.
    """
    ...

def swma(data: pd.Series | pd.DataFrame, length: Any = None, asc: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Symmetric Weighted Moving Average (SWMA)

    Symmetric Weighted Moving Average where weights are based on a symmetric
    triangle.  For example: n=3 -> [1, 2, 1], n=4 -> [1, 2, 2, 1], etc...
    This moving average has variable length in contrast to TradingView's fixed
    length of 4.

    Source:
        https://www.tradingview.com/study-script-reference/#fun_swma

    Calculation:
        Default Inputs:
            length=10

        def weights(w):
            def _compute(x):
                return np.dot(w * x)
            return _compute

        triangle = utils.symmetric_triangle(length - 1)
        SWMA = close.rolling(length)_.apply(weights(triangle), raw=True)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        asc (bool): Recent values weigh more. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def t3(data: pd.Series | pd.DataFrame, length: Any = None, a: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Tim Tillson's T3 Moving Average (T3)

    Tim Tillson's T3 Moving Average is considered a smoother and more responsive
    moving average relative to other moving averages.

    Sources:
        http://www.binarytribune.com/forex-trading-indicators/t3-moving-average-indicator/

    Calculation:
        Default Inputs:
            length=10, a=0.7
        c1 = -a^3
        c2 = 3a^2 + 3a^3 = 3a^2 * (1 + a)
        c3 = -6a^2 - 3a - 3a^3
        c4 = a^3 + 3a^2 + 3a + 1

        ema1 = EMA(close, length)
        ema2 = EMA(ema1, length)
        ema3 = EMA(ema2, length)
        ema4 = EMA(ema3, length)
        ema5 = EMA(ema4, length)
        ema6 = EMA(ema5, length)
        T3 = c1 * ema6 + c2 * ema5 + c3 * ema4 + c4 * ema3

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        a (float): 0 < a < 1. Default: 0.7
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        adjust (bool): Default: True
        presma (bool, optional): If True, uses SMA for initial value.
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def td_seq(data: pd.Series | pd.DataFrame, asint: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    TD Sequential (TD_SEQ)

    Tom DeMark's Sequential indicator attempts to identify a price point where an
    uptrend or a downtrend exhausts itself and reverses.

    Sources:
        https://tradetrekker.wordpress.com/tdsequential/

    Calculation:
        Compare current close price with 4 days ago price, up to 13 days. For the
        consecutive ascending or descending price sequence, display 6th to 9th day
        value.

    Args:
        close (pd.Series): Series of 'close's
        asint (bool): If True, fillnas with 0 and change type to int. Default: False
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        show_all (bool): Show 1 - 13. If set to False, show 6 - 9. Default: True
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: New feature generated.
    """
    ...

def tema(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Triple Exponential Moving Average (TEMA)

    A less laggy Exponential Moving Average.

    Sources:
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/triple-exponential-moving-average-tema/

    Calculation:
        Default Inputs:
            length=10
        EMA = Exponential Moving Average
        ema1 = EMA(close, length)
        ema2 = EMA(ema1, length)
        ema3 = EMA(ema2, length)
        TEMA = 3 * (ema1 - ema2) + ema3

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        adjust (bool): Default: True
        presma (bool, optional): If True, uses SMA for initial value.
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def thermo(data: pd.Series | pd.DataFrame, length: Any = None, long: Any = None, short: Any = None, mamode: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Elders Thermometer (THERMO)

    Elder's Thermometer measures price volatility.

    Sources:
        https://www.motivewave.com/studies/elders_thermometer.htm
        https://www.tradingview.com/script/HqvTuEMW-Elder-s-Market-Thermometer-LazyBear/

    Calculation:
        Default Inputs:
        length=20, drift=1, mamode=EMA, long=2, short=0.5
        EMA = Exponential Moving Average

        thermoL = (low.shift(drift) - low).abs()
        thermoH = (high - high.shift(drift)).abs()

        thermo = np.where(thermoH > thermoL, thermoH, thermoL)
        thermo_ma = ema(thermo, length)

        thermo_long = thermo < (thermo_ma * long)
        thermo_short = thermo > (thermo_ma * short)
        thermo_long = thermo_long.astype(int)
        thermo_short = thermo_short.astype(int)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        long(int): The buy factor
        short(float): The sell factor
        length (int): The  period. Default: 20
        mamode (str): See ```help(ta.ma)```. Default: 'ema'
        drift (int): The diff period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: thermo, thermo_ma, thermo_long, thermo_short columns.
    """
    ...

def tos_stdevall(data: pd.Series | pd.DataFrame, length: Any = None, stds: Any = None, ddof: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    TD Ameritrade's Think or Swim Standard Deviation All (TOS_STDEV)

    A port of TD Ameritrade's Think or Swim Standard Deviation All indicator which
    returns the standard deviation of data for the entire plot or for the interval
    of the last bars defined by the length parameter.

    Sources:
        https://tlc.thinkorswim.com/center/reference/thinkScript/Functions/Statistical/StDevAll

    Calculation:
        Default Inputs:
            length=None (All), stds=[1, 2, 3], ddof=1
        LR = Linear Regression
        STDEV = Standard Deviation

        LR = LR(close, length)
        STDEV = STDEV(close, length, ddof)
        for level in stds:
            LOWER = LR - level * STDEV
            UPPER = LR + level * STDEV

    Args:
        close (pd.Series): Series of 'close's
        length (int): Bars from current bar. Default: None
        stds (list): List of Standard Deviations in increasing order from the
                     central Linear Regression line. Default: [1,2,3]
        ddof (int): Delta Degrees of Freedom.
                    The divisor used in calculations is N - ddof,
                    where N represents the number of elements. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: Central LR, Pairs of Lower and Upper LR Lines based on
            mulitples of the standard deviation. Default: returns 7 columns.
    """
    ...

def trima(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Triangular Moving Average (TRIMA)

    A weighted moving average where the shape of the weights are triangular and the
    greatest weight is in the middle of the period.

    Sources:
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/triangular-moving-average-trima/
        tma = sma(sma(src, ceil(length / 2)), floor(length / 2) + 1)  # Tradingview
        trima = sma(sma(x, n), n)  # Tradingview

    Calculation:
        Default Inputs:
            length=10
        SMA = Simple Moving Average
        first_window = ceil(length / 2)
        second_window = floor(length / 2) + 1
        SMA1 = SMA(close, first_window)
        TRIMA = SMA(SMA1, second_window)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        adjust (bool): Default: True
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def trix(data: pd.Series | pd.DataFrame, length: Any = None, signal: Any = None, scalar: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Trix (TRIX)

    TRIX is a momentum oscillator to identify divergences.

    Sources:
        https://www.tradingview.com/wiki/TRIX

    Calculation:
        Default Inputs:
            length=18, drift=1
        EMA = Exponential Moving Average
        ROC = Rate of Change
        ema1 = EMA(close, length)
        ema2 = EMA(ema1, length)
        ema3 = EMA(ema2, length)
        TRIX = 100 * ROC(ema3, drift)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 18
        signal (int): It's period. Default: 9
        scalar (float): How much to magnify. Default: 100
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def trixh(data: pd.Series | pd.DataFrame, length: Any = None, signal: Any = None, scalar: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    TRIX Histogram (TRIXH)

    TRIX Histogram extends the TRIX indicator by adding a signal line and histogram.
    The histogram represents the difference between TRIX and its signal line,
    similar to MACD histogram, helping identify momentum changes and divergences.

    Sources:
        https://www.investopedia.com/terms/t/trix.asp
        https://school.stockcharts.com/doku.php?id=technical_indicators:trix

    Calculation:
        Default Inputs:
            length=18, signal=9, scalar=100

        TRIX = TRIX(close, length, scalar)
        Signal = EMA(TRIX, signal)
        Histogram = TRIX - Signal

    Args:
        close (pd.Series): Series of 'close's
        length (int): TRIX period. Default: 18
        signal (int): Signal line period. Default: 9
        scalar (float): Multiplier. Default: 100
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: TRIX, Signal, and Histogram columns.
    """
    ...

def true_range(data: pd.Series | pd.DataFrame, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    True Range

    An method to expand a classical range (high minus low) to include
    possible gap scenarios.

    Sources:
        https://www.macroption.com/true-range/

    Calculation:
        Default Inputs:
            drift=1
        ABS = Absolute Value
        prev_close = close.shift(drift)
        TRUE_RANGE = ABS([high - low, high - prev_close, low - prev_close])

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        drift (int): The shift period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature
    """
    ...

def tsf(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Time Series Forecast (TSF)

    The Time Series Forecast projects prices using linear regression.  It equals
    the linear regression value at the last bar of each window, i.e. the predicted
    next value.  Equivalent to ``linreg(close, length, tsf=True)``.

    Sources:
        TA Lib

    Calculation:
        Default Inputs:
            length=14
        TSF = slope * length + intercept  (linear regression forecast)

    Args:
        close (pd.Series): Series of 'close's
        length (int): The period. Default: 14
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def tsi(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, signal: Any = None, scalar: Any = None, mamode: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    True Strength Index (TSI)

    The True Strength Index is a momentum indicator used to identify short-term
    swings while in the direction of the trend as well as determining overbought
    and oversold conditions.

    Sources:
        https://www.investopedia.com/terms/t/tsi.asp

    Calculation:
        Default Inputs:
            fast=13, slow=25, signal=13, scalar=100, drift=1
        EMA = Exponential Moving Average
        diff = close.diff(drift)

        slow_ema = EMA(diff, slow)
        fast_slow_ema = EMA(slow_ema, fast)

        abs_diff_slow_ema = absolute_diff_ema = EMA(ABS(diff), slow)
        abema = abs_diff_fast_slow_ema = EMA(abs_diff_slow_ema, fast)

        TSI = scalar * fast_slow_ema / abema
        Signal = EMA(TSI, signal)

    Args:
        close (pd.Series): Series of 'close's
        fast (int): The short period. Default: 13
        slow (int): The long period. Default: 25
        signal (int): The signal period. Default: 13
        scalar (float): How much to magnify. Default: 100
        mamode (str): Moving Average of TSI Signal Line.
            See ```help(ta.ma)```. Default: 'ema'
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: tsi, signal.
    """
    ...

def tsignals(data: pd.Series | pd.DataFrame, trend: Any = ..., asbool: Any = None, trend_reset: Any = 0, trade_offset: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Trend Signals

    Given a Trend, Trend Signals returns the Trend, Trades, Entries and Exits as
    boolean integers. When 'asbool=True', it returns Trends, Entries and Exits as
    boolean values which is helpful when combined with the vectorbt backtesting
    package.

    A Trend can be a simple as: 'close' > 'moving average' or something more complex
    whose values are boolean or integers (0 or 1).

    Examples:
    ta.tsignals(close > ta.sma(close, 50), asbool=False)
    ta.tsignals(ta.ema(close, 8) > ta.ema(close, 21), asbool=True)

    Source: Kevin Johnson

    Calculation:
        Default Inputs:
            asbool=False, trend_reset=0, trade_offset=0, drift=1

        trades = trends.diff().shift(trade_offset).fillna(0).astype(int)
        entries = (trades > 0).astype(int)
        exits = (trades < 0).abs().astype(int)

    Args:
        trend (pd.Series): Series of 'trend's. The trend can be either a boolean or
            integer series of '0's and '1's
        asbool (bool): If True, it converts the Trends, Entries and Exits columns to
            booleans. When boolean, it is also useful for backtesting with
            vectorbt's Portfolio.from_signal(close, entries, exits) Default: False
        trend_reset (value): Value used to identify if a trend has ended. Default: 0
        trade_offset (value): Value used shift the trade entries/exits Use 1 for
            backtesting and 0 for live. Default: 0
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame with columns:
        Trends (trend: 1, no trend: 0), Trades (Enter: 1, Exit: -1, Otherwise: 0),
        Entries (entry: 1, nothing: 0), Exits (exit: 1, nothing: 0)
    """
    ...

def ttm_trend(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    TTM Trend (TTM_TRND)

    This indicator is from John Carters book “Mastering the Trade” and plots the
    bars green or red. It checks if the price is above or under the average price of
    the previous 5 bars. The indicator should hep you stay in a trade until the
    colors chance. Two bars of the opposite color is the signal to get in or out.

    Sources:
        https://www.prorealcode.com/prorealtime-indicators/ttm-trend-price/

    Calculation:
        Default Inputs:
            length=6
        averageprice = (((high[5]+low[5])/2)+((high[4]+low[4])/2)+((high[3]+low[3])/2)+((high[2]+low[2])/2)+((high[1]+low[1])/2)+((high[6]+low[6])/2)) / 6

        if close > averageprice:
            drawcandle(open,high,low,close) coloured(0,255,0)

        if close < averageprice:
            drawcandle(open,high,low,close) coloured(255,0,0)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 6
        offset (int): How many periods to offset the result. Default: 0
    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method
    Returns:
        pd.DataFrame: ttm_trend.
    """
    ...

def typprice(data: pd.Series | pd.DataFrame, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Typical Price (TYPPRICE)

    TYPPRICE = (High + Low + Close) / 3

    Equivalent to ta.hlc3.  TA-Lib name: TYPPRICE.

    Args:
        high (pd.Series): Series of 'high' prices
        low (pd.Series): Series of 'low' prices
        close (pd.Series): Series of 'close' prices
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): Periods to offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series
    """
    ...

def ui(data: pd.Series | pd.DataFrame, length: Any = None, scalar: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Ulcer Index (UI)

    The Ulcer Index by Peter Martin measures the downside volatility with the use of
    the Quadratic Mean, which has the effect of emphasising large drawdowns.

    Sources:
        https://library.tradingtechnologies.com/trade/chrt-ti-ulcer-index.html
        https://en.wikipedia.org/wiki/Ulcer_index
        http://www.tangotools.com/ui/ui.htm

    Calculation:
        Default Inputs:
            length=14, scalar=100
        HC = Highest Close
        SMA = Simple Moving Average

        HCN = HC(close, length)
        DOWNSIDE = scalar * (close - HCN) / HCN
        if kwargs["everget"]:
            UI = SQRT(SMA(DOWNSIDE^2, length) / length)
        else:
            UI = SQRT(SUM(DOWNSIDE^2, length) / length)

    Args:
        high (pd.Series): Series of 'high's
        close (pd.Series): Series of 'close's
        length (int): The short period.  Default: 14
        scalar (float): A positive float to scale the bands. Default: 100
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method
        everget (value, optional): TradingView's Evergets SMA instead of SUM
            calculation. Default: False

    Returns:
        pd.Series: New feature
    """
    ...

def uo(data: pd.Series | pd.DataFrame, fast: Any = None, medium: Any = None, slow: Any = None, fast_w: Any = None, medium_w: Any = None, slow_w: Any = None, talib: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Ultimate Oscillator (UO)

    The Ultimate Oscillator is a momentum indicator over three different
    periods.  It attempts to correct false divergence trading signals.

    Sources:
        https://www.tradingview.com/wiki/Ultimate_Oscillator_(UO)

    Calculation:
        Default Inputs:
            fast=7, medium=14, slow=28,
            fast_w=4.0, medium_w=2.0, slow_w=1.0, drift=1
        min_low_or_pc  = close.shift(drift).combine(low, min)
        max_high_or_pc = close.shift(drift).combine(high, max)

        bp = buying pressure = close - min_low_or_pc
        tr = true range = max_high_or_pc - min_low_or_pc

        fast_avg = SUM(bp, fast) / SUM(tr, fast)
        medium_avg = SUM(bp, medium) / SUM(tr, medium)
        slow_avg = SUM(bp, slow) / SUM(tr, slow)

        total_weight = fast_w + medium_w + slow_w
        weights = (fast_w * fast_avg) + (medium_w * medium_avg) + (slow_w * slow_avg)
        UO = 100 * weights / total_weight

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        fast (int): The Fast %K period. Default: 7
        medium (int): The Slow %K period. Default: 14
        slow (int): The Slow %D period. Default: 28
        fast_w (float): The Fast %K period. Default: 4.0
        medium_w (float): The Slow %K period. Default: 2.0
        slow_w (float): The Slow %D period. Default: 1.0
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def variance(data: pd.Series | pd.DataFrame, length: Any = None, ddof: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rolling Variance

    Sources:

    Calculation:
        Default Inputs:
            length=30
        VARIANCE = close.rolling(length).var()

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 30
        ddof (int): Delta Degrees of Freedom.
                    The divisor used in calculations is N - ddof,
                    where N represents the number of elements. Default: 0
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def vfi(data: pd.Series | pd.DataFrame, length: Any = None, coef: Any = None, vcoef: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Volume Flow Indicator (VFI)

    The Volume Flow Indicator (VFI) is a volume-based indicator that helps identify
    the strength of bulls vs bears in the market. It combines price movement with
    volume to show the flow of money into or out of a security.

    Sources:
        https://www.tradingview.com/script/MhlDpfdS-Volume-Flow-Indicator-LazyBear/
        https://www.investopedia.com/terms/v/volume-analysis.asp

    Calculation:
        Default Inputs:
            length=130, coef=0.2, vcoef=2.5, mamode='ema'

        typical = close
        inter = typical - typical.shift(1)  # Price change
        cutoff = coef * close  # Volatility threshold
        mf = inter if abs(inter) > cutoff else 0  # Filter minimal price changes

        vave = SMA(volume, length).shift(1)
        vmax = vave * vcoef
        vc = min(volume, vmax)  # Clipped volume

        vcp = vc * mf  # Volume-weighted money flow

        VFI = SUM(vcp, length) / SMA(vave, length)  # Protected against division by zero
        VFI = EMA(VFI, 3)  # Smooth the result

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        length (int): The period. Default: 130
        coef (float): Volatility threshold coefficient (0.2 for day trading, 0.1 for intra-day). Default: 0.2
        vcoef (float): Volume coefficient. Default: 2.5
        mamode (str): Moving average mode for smoothing. Default: 'ema'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def vhf(data: pd.Series | pd.DataFrame, length: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Vertical Horizontal Filter (VHF)

    VHF was created by Adam White to identify trending and ranging markets.

    Sources:
        https://www.incrediblecharts.com/indicators/vertical_horizontal_filter.php

    Calculation:
        Default Inputs:
            length = 28
        HCP = Highest Close Price in Period
        LCP = Lowest Close Price in Period
        Change = abs(Ct - Ct-1)
        VHF = (HCP - LCP) / RollingSum[length] of Change

    Args:
        source (pd.Series): Series of prices (usually close).
        length (int): The period length. Default: 28
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def vidya(data: pd.Series | pd.DataFrame, length: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Variable Index Dynamic Average (VIDYA)

    Variable Index Dynamic Average (VIDYA) was developed by Tushar Chande. It is
    similar to an Exponential Moving Average but it has a dynamically adjusted
    lookback period dependent on relative price volatility as measured by Chande
    Momentum Oscillator (CMO). When volatility is high, VIDYA reacts faster to
    price changes. It is often used as moving average or trend identifier.

    Sources:
        https://www.tradingview.com/script/hdrf0fXV-Variable-Index-Dynamic-Average-VIDYA/
        https://www.perfecttrendsystem.com/blog_mt4_2/en/vidya-indicator-for-mt4

    Calculation:
        Default Inputs:
            length=10, adjust=False, sma=True
        if sma:
            sma_nth = close[0:length].sum() / length
            close[:length - 1] = np.NaN
            close.iloc[length - 1] = sma_nth
        EMA = close.ewm(span=length, adjust=adjust).mean()

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        adjust (bool, optional): Use adjust option for EMA calculation. Default: False
        sma (bool, optional): If True, uses SMA for initial value for EMA calculation. Default: True
        talib (bool): If True, uses TA-Libs implementation for CMO. Otherwise uses EMA version. Default: False
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def vortex(data: pd.Series | pd.DataFrame, length: Any = None, drift: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Vortex

    Two oscillators that capture positive and negative trend movement.

    Sources:
        https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:vortex_indicator

    Calculation:
        Default Inputs:
            length=14, drift=1
        TR = True Range
        SMA = Simple Moving Average
        tr = TR(high, low, close)
        tr_sum = tr.rolling(length).sum()

        vmp = (high - low.shift(drift)).abs()
        vmn = (low - high.shift(drift)).abs()

        VIP = vmp.rolling(length).sum() / tr_sum
        VIM = vmn.rolling(length).sum() / tr_sum

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): ROC 1 period. Default: 14
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: vip and vim columns
    """
    ...

def vosc(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Volume Oscillator (VOSC)

    The Volume Oscillator measures the difference between two volume moving
    averages (fast and slow SMAs) as a percentage of the slow SMA.
    Rising VOSC indicates increasing volume momentum.

    VOSC = 100 * (SMA(volume, fast) - SMA(volume, slow)) / SMA(volume, slow)

    Sources:
        https://school.stockcharts.com/doku.php?id=technical_indicators:volume_oscillator_vo

    Args:
        volume (pd.Series): Volume series.
        fast (int): Fast SMA period. Default: 14
        slow (int): Slow SMA period. Default: 28
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: VOSC values.
    """
    ...

def vp(data: pd.Series | pd.DataFrame, width: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Volume Profile (VP)

    Calculates the Volume Profile by slicing price into ranges.
    Note: Value Area is not calculated.

    Sources:
        https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:volume_by_price
        https://www.tradingview.com/wiki/Volume_Profile
        http://www.ranchodinero.com/volume-tpo-essentials/
        https://www.tradingtechnologies.com/blog/2013/05/15/volume-at-price/

    Calculation:
        Default Inputs:
            width=10

        vp = pd.concat([close, pos_volume, neg_volume], axis=1)
        if sort_close:
            vp_ranges = cut(vp[close_col], width)
            result = ({range_left, mean_close, range_right, pos_volume, neg_volume} foreach range in vp_ranges
        else:
            vp_ranges = np.array_split(vp, width)
            result = ({low_close, mean_close, high_close, pos_volume, neg_volume} foreach range in vp_ranges
        vpdf = pd.DataFrame(result)
        vpdf['total_volume'] = vpdf['pos_volume'] + vpdf['neg_volume']

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        width (int): How many ranges to distrubute price into. Default: 10

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method
        sort_close (value, optional): Whether to sort by close before splitting
            into ranges. Default: False

    Returns:
        pd.DataFrame: New feature generated.
    """
    ...

def vwap(data: pd.Series | pd.DataFrame, anchor: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Volume Weighted Average Price (VWAP)

    The Volume Weighted Average Price that measures the average typical price
    by volume.  It is typically used with intraday charts to identify general
    direction.

    Sources:
        https://www.tradingview.com/wiki/Volume_Weighted_Average_Price_(VWAP)
        https://www.tradingtechnologies.com/help/x-study/technical-indicator-definitions/volume-weighted-average-price-vwap/
        https://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:vwap_intraday

    Calculation:
        tp = typical_price = hlc3(high, low, close)
        tpv = tp * volume
        VWAP = tpv.cumsum() / volume.cumsum()

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        anchor (str): How to anchor VWAP. Depending on the index values, it will
            implement various Timeseries Offset Aliases as listed here:
            https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#timeseries-offset-aliases
            Default: "D".
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def vwma(data: pd.Series | pd.DataFrame, length: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Volume Weighted Moving Average (VWMA)

    Volume Weighted Moving Average.

    Sources:
        https://www.motivewave.com/studies/volume_weighted_moving_average.htm

    Calculation:
        Default Inputs:
            length=10
        SMA = Simple Moving Average
        pv = close * volume
        VWMA = SMA(pv, length) / SMA(volume, length)

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        length (int): It's period. Default: 10
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def vwmacd(data: pd.Series | pd.DataFrame, fast: Any = None, slow: Any = None, signal: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Volume Weighted MACD (VWMACD)

    Volume Weighted MACD is a variation of the traditional MACD that incorporates
    volume into the calculation. It uses Volume Weighted Moving Averages (VWMA)
    instead of EMAs to give more weight to periods with higher volume.

    Sources:
        https://www.tradingview.com/script/NUs1Y5V7-Volume-Weighted-MACD/
        Technical Analysis Using Multiple Timeframes by Brian Shannon

    Calculation:
        Default Inputs:
            fast=12, slow=26, signal=9

        FastVWMA = VWMA(close, volume, fast)
        SlowVWMA = VWMA(close, volume, slow)

        VWMACD = FastVWMA - SlowVWMA
        Signal = VWMA(VWMACD, volume, signal)
        Histogram = VWMACD - Signal

    Args:
        close (pd.Series): Series of 'close's
        volume (pd.Series): Series of 'volume's
        fast (int): The fast period. Default: 12
        slow (int): The slow period. Default: 26
        signal (int): The signal period. Default: 9
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame: VWMACD, Signal, and Histogram columns.
    """
    ...

def wad(data: pd.Series | pd.DataFrame, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Williams Accumulation/Distribution (WAD)

    Williams' Accumulation/Distribution line measures the cumulative flow of
    money into and out of a security. Unlike the standard A/D line, it uses
    True Range High and True Range Low to determine the daily accumulation or
    distribution value.

    TRH = max(prev_close, high)
    TRL = min(prev_close, low)

    AD_day = close - TRL  if close > prev_close
    AD_day = close - TRH  if close < prev_close
    AD_day = 0            if close == prev_close

    WAD = cumsum(AD_day)

    Sources:
        Larry Williams, "How I Made One Million Dollars Last Year Trading Commodities"
        https://www.investopedia.com/terms/w/williamspctR.asp

    Args:
        high (pd.Series): High price series.
        low (pd.Series): Low price series.
        close (pd.Series): Close price series.
        offset (int): Result offset. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: WAD values.
    """
    ...

def wcp(data: pd.Series | pd.DataFrame, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Weighted Closing Price (WCP)

    Weighted Closing Price is the weighted price given: high, low
    and double the close.

    Sources:
        https://www.fmlabs.com/reference/default.htm?url=WeightedCloses.htm

    Calculation:
        WCP = (2 * close + high + low) / 4

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def willr(data: pd.Series | pd.DataFrame, length: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    William's Percent R (WILLR)

    William's Percent R is a momentum oscillator similar to the RSI that
    attempts to identify overbought and oversold conditions.

    Sources:
        https://www.tradingview.com/wiki/Williams_%25R_(%25R)

    Calculation:
        Default Inputs:
            length=20
        LL = low.rolling(length).min()
        HH = high.rolling(length).max()

        WILLR = 100 * ((close - LL) / (HH - LL) - 1)

    Args:
        high (pd.Series): Series of 'high's
        low (pd.Series): Series of 'low's
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 14
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def wma(data: pd.Series | pd.DataFrame, length: Any = None, asc: Any = None, talib: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Weighted Moving Average (WMA)

    The Weighted Moving Average where the weights are linearly increasing and
    the most recent data has the heaviest weight.

    Sources:
        https://en.wikipedia.org/wiki/Moving_average#Weighted_moving_average

    Calculation:
        Default Inputs:
            length=10, asc=True
        total_weight = 0.5 * length * (length + 1)
        weights_ = [1, 2, ..., length + 1]  # Ascending
        weights = weights if asc else weights[::-1]

        def linear_weights(w):
            def _compute(x):
                return (w * x).sum() / total_weight
            return _compute

        WMA = close.rolling(length)_.apply(linear_weights(weights), raw=True)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        asc (bool): Recent values weigh more. Default: True
        talib (bool): If TA Lib is installed and talib is True, Returns the TA Lib
            version. Default: True
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def xsignals(data: pd.Series | pd.DataFrame, signal: Any = ..., xa: Any = ..., xb: Any = ..., above: Any = True, long: Any = True, asbool: Any = None, trend_reset: Any = 0, trade_offset: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Cross Signals (XSIGNALS)

    Cross Signals returns Trend Signal (TSIGNALS) results for Signal Crossings. This
    is useful for indicators like RSI, ZSCORE, et al where one wants trade Entries
    and Exits (and Trends).

    Cross Signals has two kinds of modes: above and long.

    The first mode 'above', default True, xsignals determines if the signal first
    crosses above 'xa' and then below 'xb'. If 'above' is False, xsignals determines
    if the signal first crosses below 'xa' and then above 'xb'.

    The second mode 'long', default True, passes the long trend result into
    tsignals so it can determine the appropriate Entries and Exits. When 'long' is
    False, it does the same but for the short side.

    Example:
    # These are two different outcomes and depends on the indicator and it's
    # characteristics. Please check BOTH outcomes BEFORE making an Issue.
    rsi = df.ta.rsi()
    # Returns tsignal DataFrame when RSI crosses above 20 and then below 80
    ta.xsignals(rsi, 20, 80, above=True)
    # Returns tsignal DataFrame when RSI crosses below 20 and then above 80
    ta.xsignals(rsi, 20, 80, above=False)

    Source: Kevin Johnson

    Calculation:
        Default Inputs:
            asbool=False, trend_reset=0, trade_offset=0, drift=1
            (xa, xb: no defaults — required)

        trades = trends.diff().shift(trade_offset).fillna(0).astype(int)
        entries = (trades > 0).astype(int)
        exits = (trades < 0).abs().astype(int)

    Args:
        signal (pd.Series): Oscillator or signal Series to evaluate.
        xa (float): Entry threshold. Choose based on indicator range.
            RSI/Stoch/KDJ (0–100): typical 20–30 (oversold) or 70–80 (overbought).
            Unbounded indicators (MACD, CCI): must match their actual value range.
            WARNING: xa=80 with MACD (range ~-5 to +5) will never trigger.
        xb (float): Exit threshold, opposite side of xa (e.g. if xa=20 use xb=80).
        above (bool): When the signal crosses above 'xa' first and then 'xb'. When
            False, then when the signal crosses below 'xa' first and then 'xb'.
            Default: True
        long (bool): Passes the long trend into tsignals' trend argument. When
            False, it passes the short trend into tsignals trend argument.
            Default: True
        drift (int): The difference period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

        # TSIGNAL Passthrough arguments
        asbool (bool): If True, it converts the Trends, Entries and Exits columns to
            booleans. When boolean, it is also useful for backtesting with
            vectorbt's Portfolio.from_signal(close, entries, exits) Default: False
        trend_reset (value): Value used to identify if a trend has ended. Default: 0
        trade_offset (value): Value used shift the trade entries/exits Use 1 for
            backtesting and 0 for live. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.DataFrame with columns:
        Trends (trend: 1, no trend: 0), Trades (Enter: 1, Exit: -1, Otherwise: 0),
        Entries (entry: 1, nothing: 0), Exits (exit: 1, nothing: 0)
    """
    ...

def zlma(data: pd.Series | pd.DataFrame, length: Any = None, mamode: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Zero Lag Moving Average (ZLMA)

    The Zero Lag Moving Average attempts to eliminate the lag associated
    with moving averages.  This is an adaption created by John Ehler and Ric Way.

    Sources:
        https://en.wikipedia.org/wiki/Zero_lag_exponential_moving_average

    Calculation:
        Default Inputs:
            length=10, mamode=EMA
        EMA = Exponential Moving Average
        lag = int(0.5 * (length - 1))

        SOURCE = 2 * close - close.shift(lag)
        ZLMA = MA(kind=mamode, SOURCE, length)

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 10
        mamode (str): Options: 'ema', 'hma', 'sma', 'wma'. Default: 'ema'
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...

def zscore(data: pd.Series | pd.DataFrame, length: Any = None, std: Any = None, offset: Any = None, **kwargs: Any) -> pd.Series | pd.DataFrame:
    """
    Rolling Z Score

    Sources:

    Calculation:
        Default Inputs:
            length=30, std=1
        SMA = Simple Moving Average
        STDEV = Standard Deviation
        std = std * STDEV(close, length)
        mean = SMA(close, length)
        ZSCORE = (close - mean) / std

    Args:
        close (pd.Series): Series of 'close's
        length (int): It's period. Default: 30
        std (float): It's period. Default: 1
        offset (int): How many periods to offset the result. Default: 0

    Kwargs:
        fillna (value, optional): pd.DataFrame.fillna(value)
        fill_method (value, optional): Type of fill method

    Returns:
        pd.Series: New feature generated.
    """
    ...
