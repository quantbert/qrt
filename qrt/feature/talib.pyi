"""Auto-generated stubs for the dynamic indicator wrappers (IDE support).

Do not edit by hand. Regenerate with:

    uv run python tools/gen_feature_stubs.py
"""

from typing import Any

import pandas as pd


def ACCBANDS(data: pd.Series | pd.DataFrame, timeperiod: Any = 20) -> pd.Series | pd.DataFrame:
    """
    ACCBANDS(ndarray high, ndarray low, ndarray close, int timeperiod=-0x80000000)

    ACCBANDS(high, low, close[, timeperiod=?])

    Acceleration Bands (Overlap Studies)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod: 20
    Outputs:
        upperband
        middleband
        lowerband
    """
    ...

def ACOS(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    ACOS(ndarray real)

    ACOS(real)

    Vector Trigonometric ACos (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def AD(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    AD(ndarray high, ndarray low, ndarray close, ndarray volume)

    AD(high, low, close, volume)

    Chaikin A/D Line (Volume Indicators)

    Inputs:
        prices: ['high', 'low', 'close', 'volume']
    Outputs:
        real
    """
    ...

def ADD(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    ADD(ndarray real0, ndarray real1)

    ADD(real0, real1)

    Vector Arithmetic Add (Math Operators)

    Inputs:
        real0: (any ndarray)
        real1: (any ndarray)
    Outputs:
        real
    """
    ...

def ADOSC(data: pd.Series | pd.DataFrame, fastperiod: Any = 3, slowperiod: Any = 10) -> pd.Series | pd.DataFrame:
    """
    ADOSC(ndarray high, ndarray low, ndarray close, ndarray volume, int fastperiod=-0x80000000, int slowperiod=-0x80000000)

    ADOSC(high, low, close, volume[, fastperiod=?, slowperiod=?])

    Chaikin A/D Oscillator (Volume Indicators)

    Inputs:
        prices: ['high', 'low', 'close', 'volume']
    Parameters:
        fastperiod: 3
        slowperiod: 10
    Outputs:
        real
    """
    ...

def ADX(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    ADX(ndarray high, ndarray low, ndarray close, int timeperiod=-0x80000000)

    ADX(high, low, close[, timeperiod=?])

    Average Directional Movement Index (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def ADXR(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    ADXR(ndarray high, ndarray low, ndarray close, int timeperiod=-0x80000000)

    ADXR(high, low, close[, timeperiod=?])

    Average Directional Movement Index Rating (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def APO(data: pd.Series | pd.DataFrame, fastperiod: Any = 12, slowperiod: Any = 26, matype: Any = 0) -> pd.Series | pd.DataFrame:
    """
    APO(ndarray real, int fastperiod=-0x80000000, int slowperiod=-0x80000000, int matype=0)

    APO(real[, fastperiod=?, slowperiod=?, matype=?])

    Absolute Price Oscillator (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        fastperiod: 12
        slowperiod: 26
        matype: 0 (Simple Moving Average)
    Outputs:
        real
    """
    ...

def AROON(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    AROON(ndarray high, ndarray low, int timeperiod=-0x80000000)

    AROON(high, low[, timeperiod=?])

    Aroon (Momentum Indicators)

    Inputs:
        prices: ['high', 'low']
    Parameters:
        timeperiod: 14
    Outputs:
        aroondown
        aroonup
    """
    ...

def AROONOSC(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    AROONOSC(ndarray high, ndarray low, int timeperiod=-0x80000000)

    AROONOSC(high, low[, timeperiod=?])

    Aroon Oscillator (Momentum Indicators)

    Inputs:
        prices: ['high', 'low']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def ASIN(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    ASIN(ndarray real)

    ASIN(real)

    Vector Trigonometric ASin (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def ATAN(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    ATAN(ndarray real)

    ATAN(real)

    Vector Trigonometric ATan (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def ATR(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    ATR(ndarray high, ndarray low, ndarray close, int timeperiod=-0x80000000)

    ATR(high, low, close[, timeperiod=?])

    Average True Range (Volatility Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def AVGDEV(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    AVGDEV(ndarray real, int timeperiod=-0x80000000)

    AVGDEV(real[, timeperiod=?])

    Average Deviation (Price Transform)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def AVGPRICE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    AVGPRICE(ndarray open, ndarray high, ndarray low, ndarray close)

    AVGPRICE(open, high, low, close)

    Average Price (Price Transform)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        real
    """
    ...

def BBANDS(data: pd.Series | pd.DataFrame, timeperiod: Any = 5, nbdevup: Any = 2.0, nbdevdn: Any = 2.0, matype: Any = 0) -> pd.Series | pd.DataFrame:
    """
    BBANDS(ndarray real, int timeperiod=-0x80000000, double nbdevup=-4e37, double nbdevdn=-4e37, int matype=0)

    BBANDS(real[, timeperiod=?, nbdevup=?, nbdevdn=?, matype=?])

    Bollinger Bands (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 5
        nbdevup: 2.0
        nbdevdn: 2.0
        matype: 0 (Simple Moving Average)
    Outputs:
        upperband
        middleband
        lowerband
    """
    ...

def BETA(data: pd.Series | pd.DataFrame, timeperiod: Any = 5) -> pd.Series | pd.DataFrame:
    """
    BETA(ndarray real0, ndarray real1, int timeperiod=-0x80000000)

    BETA(real0, real1[, timeperiod=?])

    Beta (Statistic Functions)

    Inputs:
        real0: (any ndarray)
        real1: (any ndarray)
    Parameters:
        timeperiod: 5
    Outputs:
        real
    """
    ...

def BOP(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    BOP(ndarray open, ndarray high, ndarray low, ndarray close)

    BOP(open, high, low, close)

    Balance Of Power (Momentum Indicators)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        real
    """
    ...

def CCI(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    CCI(ndarray high, ndarray low, ndarray close, int timeperiod=-0x80000000)

    CCI(high, low, close[, timeperiod=?])

    Commodity Channel Index (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def CDL2CROWS(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDL2CROWS(ndarray open, ndarray high, ndarray low, ndarray close)

    CDL2CROWS(open, high, low, close)

    Two Crows (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDL3BLACKCROWS(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDL3BLACKCROWS(ndarray open, ndarray high, ndarray low, ndarray close)

    CDL3BLACKCROWS(open, high, low, close)

    Three Black Crows (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDL3INSIDE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDL3INSIDE(ndarray open, ndarray high, ndarray low, ndarray close)

    CDL3INSIDE(open, high, low, close)

    Three Inside Up/Down (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDL3LINESTRIKE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDL3LINESTRIKE(ndarray open, ndarray high, ndarray low, ndarray close)

    CDL3LINESTRIKE(open, high, low, close)

    Three-Line Strike  (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDL3OUTSIDE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDL3OUTSIDE(ndarray open, ndarray high, ndarray low, ndarray close)

    CDL3OUTSIDE(open, high, low, close)

    Three Outside Up/Down (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDL3STARSINSOUTH(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDL3STARSINSOUTH(ndarray open, ndarray high, ndarray low, ndarray close)

    CDL3STARSINSOUTH(open, high, low, close)

    Three Stars In The South (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDL3WHITESOLDIERS(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDL3WHITESOLDIERS(ndarray open, ndarray high, ndarray low, ndarray close)

    CDL3WHITESOLDIERS(open, high, low, close)

    Three Advancing White Soldiers (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLABANDONEDBABY(data: pd.Series | pd.DataFrame, penetration: Any = 0.3) -> pd.Series | pd.DataFrame:
    """
    CDLABANDONEDBABY(ndarray open, ndarray high, ndarray low, ndarray close, double penetration=0.3)

    CDLABANDONEDBABY(open, high, low, close[, penetration=?])

    Abandoned Baby (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Parameters:
        penetration: 0.3
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLADVANCEBLOCK(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLADVANCEBLOCK(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLADVANCEBLOCK(open, high, low, close)

    Advance Block (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLBELTHOLD(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLBELTHOLD(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLBELTHOLD(open, high, low, close)

    Belt-hold (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLBREAKAWAY(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLBREAKAWAY(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLBREAKAWAY(open, high, low, close)

    Breakaway (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLCLOSINGMARUBOZU(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLCLOSINGMARUBOZU(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLCLOSINGMARUBOZU(open, high, low, close)

    Closing Marubozu (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLCONCEALBABYSWALL(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLCONCEALBABYSWALL(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLCONCEALBABYSWALL(open, high, low, close)

    Concealing Baby Swallow (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLCOUNTERATTACK(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLCOUNTERATTACK(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLCOUNTERATTACK(open, high, low, close)

    Counterattack (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLDARKCLOUDCOVER(data: pd.Series | pd.DataFrame, penetration: Any = 0.5) -> pd.Series | pd.DataFrame:
    """
    CDLDARKCLOUDCOVER(ndarray open, ndarray high, ndarray low, ndarray close, double penetration=0.5)

    CDLDARKCLOUDCOVER(open, high, low, close[, penetration=?])

    Dark Cloud Cover (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Parameters:
        penetration: 0.5
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLDOJI(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLDOJI(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLDOJI(open, high, low, close)

    Doji (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLDOJISTAR(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLDOJISTAR(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLDOJISTAR(open, high, low, close)

    Doji Star (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLDRAGONFLYDOJI(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLDRAGONFLYDOJI(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLDRAGONFLYDOJI(open, high, low, close)

    Dragonfly Doji (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLENGULFING(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLENGULFING(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLENGULFING(open, high, low, close)

    Engulfing Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLEVENINGDOJISTAR(data: pd.Series | pd.DataFrame, penetration: Any = 0.3) -> pd.Series | pd.DataFrame:
    """
    CDLEVENINGDOJISTAR(ndarray open, ndarray high, ndarray low, ndarray close, double penetration=0.3)

    CDLEVENINGDOJISTAR(open, high, low, close[, penetration=?])

    Evening Doji Star (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Parameters:
        penetration: 0.3
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLEVENINGSTAR(data: pd.Series | pd.DataFrame, penetration: Any = 0.3) -> pd.Series | pd.DataFrame:
    """
    CDLEVENINGSTAR(ndarray open, ndarray high, ndarray low, ndarray close, double penetration=0.3)

    CDLEVENINGSTAR(open, high, low, close[, penetration=?])

    Evening Star (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Parameters:
        penetration: 0.3
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLGAPSIDESIDEWHITE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLGAPSIDESIDEWHITE(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLGAPSIDESIDEWHITE(open, high, low, close)

    Up/Down-gap side-by-side white lines (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLGRAVESTONEDOJI(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLGRAVESTONEDOJI(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLGRAVESTONEDOJI(open, high, low, close)

    Gravestone Doji (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLHAMMER(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLHAMMER(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLHAMMER(open, high, low, close)

    Hammer (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLHANGINGMAN(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLHANGINGMAN(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLHANGINGMAN(open, high, low, close)

    Hanging Man (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLHARAMI(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLHARAMI(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLHARAMI(open, high, low, close)

    Harami Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLHARAMICROSS(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLHARAMICROSS(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLHARAMICROSS(open, high, low, close)

    Harami Cross Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLHIGHWAVE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLHIGHWAVE(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLHIGHWAVE(open, high, low, close)

    High-Wave Candle (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLHIKKAKE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLHIKKAKE(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLHIKKAKE(open, high, low, close)

    Hikkake Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLHIKKAKEMOD(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLHIKKAKEMOD(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLHIKKAKEMOD(open, high, low, close)

    Modified Hikkake Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLHOMINGPIGEON(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLHOMINGPIGEON(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLHOMINGPIGEON(open, high, low, close)

    Homing Pigeon (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLIDENTICAL3CROWS(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLIDENTICAL3CROWS(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLIDENTICAL3CROWS(open, high, low, close)

    Identical Three Crows (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLINNECK(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLINNECK(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLINNECK(open, high, low, close)

    In-Neck Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLINVERTEDHAMMER(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLINVERTEDHAMMER(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLINVERTEDHAMMER(open, high, low, close)

    Inverted Hammer (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLKICKING(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLKICKING(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLKICKING(open, high, low, close)

    Kicking (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLKICKINGBYLENGTH(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLKICKINGBYLENGTH(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLKICKINGBYLENGTH(open, high, low, close)

    Kicking - bull/bear determined by the longer marubozu (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLLADDERBOTTOM(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLLADDERBOTTOM(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLLADDERBOTTOM(open, high, low, close)

    Ladder Bottom (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLLONGLEGGEDDOJI(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLLONGLEGGEDDOJI(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLLONGLEGGEDDOJI(open, high, low, close)

    Long Legged Doji (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLLONGLINE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLLONGLINE(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLLONGLINE(open, high, low, close)

    Long Line Candle (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLMARUBOZU(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLMARUBOZU(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLMARUBOZU(open, high, low, close)

    Marubozu (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLMATCHINGLOW(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLMATCHINGLOW(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLMATCHINGLOW(open, high, low, close)

    Matching Low (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLMATHOLD(data: pd.Series | pd.DataFrame, penetration: Any = 0.5) -> pd.Series | pd.DataFrame:
    """
    CDLMATHOLD(ndarray open, ndarray high, ndarray low, ndarray close, double penetration=0.5)

    CDLMATHOLD(open, high, low, close[, penetration=?])

    Mat Hold (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Parameters:
        penetration: 0.5
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLMORNINGDOJISTAR(data: pd.Series | pd.DataFrame, penetration: Any = 0.3) -> pd.Series | pd.DataFrame:
    """
    CDLMORNINGDOJISTAR(ndarray open, ndarray high, ndarray low, ndarray close, double penetration=0.3)

    CDLMORNINGDOJISTAR(open, high, low, close[, penetration=?])

    Morning Doji Star (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Parameters:
        penetration: 0.3
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLMORNINGSTAR(data: pd.Series | pd.DataFrame, penetration: Any = 0.3) -> pd.Series | pd.DataFrame:
    """
    CDLMORNINGSTAR(ndarray open, ndarray high, ndarray low, ndarray close, double penetration=0.3)

    CDLMORNINGSTAR(open, high, low, close[, penetration=?])

    Morning Star (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Parameters:
        penetration: 0.3
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLONNECK(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLONNECK(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLONNECK(open, high, low, close)

    On-Neck Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLPIERCING(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLPIERCING(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLPIERCING(open, high, low, close)

    Piercing Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLRICKSHAWMAN(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLRICKSHAWMAN(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLRICKSHAWMAN(open, high, low, close)

    Rickshaw Man (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLRISEFALL3METHODS(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLRISEFALL3METHODS(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLRISEFALL3METHODS(open, high, low, close)

    Rising/Falling Three Methods (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLSEPARATINGLINES(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLSEPARATINGLINES(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLSEPARATINGLINES(open, high, low, close)

    Separating Lines (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLSHOOTINGSTAR(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLSHOOTINGSTAR(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLSHOOTINGSTAR(open, high, low, close)

    Shooting Star (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLSHORTLINE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLSHORTLINE(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLSHORTLINE(open, high, low, close)

    Short Line Candle (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLSPINNINGTOP(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLSPINNINGTOP(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLSPINNINGTOP(open, high, low, close)

    Spinning Top (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLSTALLEDPATTERN(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLSTALLEDPATTERN(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLSTALLEDPATTERN(open, high, low, close)

    Stalled Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLSTICKSANDWICH(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLSTICKSANDWICH(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLSTICKSANDWICH(open, high, low, close)

    Stick Sandwich (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLTAKURI(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLTAKURI(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLTAKURI(open, high, low, close)

    Takuri (Dragonfly Doji with very long lower shadow) (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLTASUKIGAP(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLTASUKIGAP(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLTASUKIGAP(open, high, low, close)

    Tasuki Gap (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLTHRUSTING(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLTHRUSTING(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLTHRUSTING(open, high, low, close)

    Thrusting Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLTRISTAR(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLTRISTAR(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLTRISTAR(open, high, low, close)

    Tristar Pattern (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLUNIQUE3RIVER(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLUNIQUE3RIVER(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLUNIQUE3RIVER(open, high, low, close)

    Unique 3 River (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLUPSIDEGAP2CROWS(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLUPSIDEGAP2CROWS(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLUPSIDEGAP2CROWS(open, high, low, close)

    Upside Gap Two Crows (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CDLXSIDEGAP3METHODS(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CDLXSIDEGAP3METHODS(ndarray open, ndarray high, ndarray low, ndarray close)

    CDLXSIDEGAP3METHODS(open, high, low, close)

    Upside/Downside Gap Three Methods (Pattern Recognition)

    Inputs:
        prices: ['open', 'high', 'low', 'close']
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def CEIL(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    CEIL(ndarray real)

    CEIL(real)

    Vector Ceil (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def CMO(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    CMO(ndarray real, int timeperiod=-0x80000000)

    CMO(real[, timeperiod=?])

    Chande Momentum Oscillator (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def CORREL(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    CORREL(ndarray real0, ndarray real1, int timeperiod=-0x80000000)

    CORREL(real0, real1[, timeperiod=?])

    Pearson's Correlation Coefficient (r) (Statistic Functions)

    Inputs:
        real0: (any ndarray)
        real1: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def COS(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    COS(ndarray real)

    COS(real)

    Vector Trigonometric Cos (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def COSH(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    COSH(ndarray real)

    COSH(real)

    Vector Trigonometric Cosh (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def DEMA(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    DEMA(ndarray real, int timeperiod=-0x80000000)

    DEMA(real[, timeperiod=?])

    Double Exponential Moving Average (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def DIV(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    DIV(ndarray real0, ndarray real1)

    DIV(real0, real1)

    Vector Arithmetic Div (Math Operators)

    Inputs:
        real0: (any ndarray)
        real1: (any ndarray)
    Outputs:
        real
    """
    ...

def DX(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    DX(ndarray high, ndarray low, ndarray close, int timeperiod=-0x80000000)

    DX(high, low, close[, timeperiod=?])

    Directional Movement Index (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def EMA(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    EMA(ndarray real, int timeperiod=-0x80000000)

    EMA(real[, timeperiod=?])

    Exponential Moving Average (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def EXP(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    EXP(ndarray real)

    EXP(real)

    Vector Arithmetic Exp (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def FLOOR(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    FLOOR(ndarray real)

    FLOOR(real)

    Vector Floor (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def HT_DCPERIOD(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    HT_DCPERIOD(ndarray real)

    HT_DCPERIOD(real)

    Hilbert Transform - Dominant Cycle Period (Cycle Indicators)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def HT_DCPHASE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    HT_DCPHASE(ndarray real)

    HT_DCPHASE(real)

    Hilbert Transform - Dominant Cycle Phase (Cycle Indicators)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def HT_PHASOR(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    HT_PHASOR(ndarray real)

    HT_PHASOR(real)

    Hilbert Transform - Phasor Components (Cycle Indicators)

    Inputs:
        real: (any ndarray)
    Outputs:
        inphase
        quadrature
    """
    ...

def HT_SINE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    HT_SINE(ndarray real)

    HT_SINE(real)

    Hilbert Transform - SineWave (Cycle Indicators)

    Inputs:
        real: (any ndarray)
    Outputs:
        sine
        leadsine
    """
    ...

def HT_TRENDLINE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    HT_TRENDLINE(ndarray real)

    HT_TRENDLINE(real)

    Hilbert Transform - Instantaneous Trendline (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def HT_TRENDMODE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    HT_TRENDMODE(ndarray real)

    HT_TRENDMODE(real)

    Hilbert Transform - Trend vs Cycle Mode (Cycle Indicators)

    Inputs:
        real: (any ndarray)
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def IMI(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    IMI(ndarray open, ndarray close, int timeperiod=-0x80000000)

    IMI(open, close[, timeperiod=?])

    Intraday Momentum Index (Momentum Indicators)

    Inputs:
        prices: ['open', 'close']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def KAMA(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    KAMA(ndarray real, int timeperiod=-0x80000000)

    KAMA(real[, timeperiod=?])

    Kaufman Adaptive Moving Average (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def LINEARREG(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    LINEARREG(ndarray real, int timeperiod=-0x80000000)

    LINEARREG(real[, timeperiod=?])

    Linear Regression (Statistic Functions)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def LINEARREG_ANGLE(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    LINEARREG_ANGLE(ndarray real, int timeperiod=-0x80000000)

    LINEARREG_ANGLE(real[, timeperiod=?])

    Linear Regression Angle (Statistic Functions)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def LINEARREG_INTERCEPT(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    LINEARREG_INTERCEPT(ndarray real, int timeperiod=-0x80000000)

    LINEARREG_INTERCEPT(real[, timeperiod=?])

    Linear Regression Intercept (Statistic Functions)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def LINEARREG_SLOPE(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    LINEARREG_SLOPE(ndarray real, int timeperiod=-0x80000000)

    LINEARREG_SLOPE(real[, timeperiod=?])

    Linear Regression Slope (Statistic Functions)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def LN(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    LN(ndarray real)

    LN(real)

    Vector Log Natural (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def LOG10(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    LOG10(ndarray real)

    LOG10(real)

    Vector Log10 (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def MA(data: pd.Series | pd.DataFrame, timeperiod: Any = 30, matype: Any = 0) -> pd.Series | pd.DataFrame:
    """
    MA(ndarray real, int timeperiod=-0x80000000, int matype=0)

    MA(real[, timeperiod=?, matype=?])

    Moving average (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
        matype: 0 (Simple Moving Average)
    Outputs:
        real
    """
    ...

def MACD(data: pd.Series | pd.DataFrame, fastperiod: Any = 12, slowperiod: Any = 26, signalperiod: Any = 9) -> pd.Series | pd.DataFrame:
    """
    MACD(ndarray real, int fastperiod=-0x80000000, int slowperiod=-0x80000000, int signalperiod=-0x80000000)

    MACD(real[, fastperiod=?, slowperiod=?, signalperiod=?])

    Moving Average Convergence/Divergence (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        fastperiod: 12
        slowperiod: 26
        signalperiod: 9
    Outputs:
        macd
        macdsignal
        macdhist
    """
    ...

def MACDEXT(data: pd.Series | pd.DataFrame, fastperiod: Any = 12, fastmatype: Any = 0, slowperiod: Any = 26, slowmatype: Any = 0, signalperiod: Any = 9, signalmatype: Any = 0) -> pd.Series | pd.DataFrame:
    """
    MACDEXT(ndarray real, int fastperiod=-0x80000000, int fastmatype=0, int slowperiod=-0x80000000, int slowmatype=0, int signalperiod=-0x80000000, int signalmatype=0)

    MACDEXT(real[, fastperiod=?, fastmatype=?, slowperiod=?, slowmatype=?, signalperiod=?, signalmatype=?])

    MACD with controllable MA type (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        fastperiod: 12
        fastmatype: 0
        slowperiod: 26
        slowmatype: 0
        signalperiod: 9
        signalmatype: 0
    Outputs:
        macd
        macdsignal
        macdhist
    """
    ...

def MACDFIX(data: pd.Series | pd.DataFrame, signalperiod: Any = 9) -> pd.Series | pd.DataFrame:
    """
    MACDFIX(ndarray real, int signalperiod=-0x80000000)

    MACDFIX(real[, signalperiod=?])

    Moving Average Convergence/Divergence Fix 12/26 (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        signalperiod: 9
    Outputs:
        macd
        macdsignal
        macdhist
    """
    ...

def MAMA(data: pd.Series | pd.DataFrame, fastlimit: Any = 0.5, slowlimit: Any = 0.05) -> pd.Series | pd.DataFrame:
    """
    MAMA(ndarray real, double fastlimit=-4e37, double slowlimit=-4e37)

    MAMA(real[, fastlimit=?, slowlimit=?])

    MESA Adaptive Moving Average (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        fastlimit: 0.5
        slowlimit: 0.05
    Outputs:
        mama
        fama
    """
    ...

def MAVP(data: pd.Series | pd.DataFrame, minperiod: Any = 2, maxperiod: Any = 30, matype: Any = 0) -> pd.Series | pd.DataFrame:
    """
    MAVP(ndarray real, ndarray periods, int minperiod=-0x80000000, int maxperiod=-0x80000000, int matype=0)

    MAVP(real, periods[, minperiod=?, maxperiod=?, matype=?])

    Moving average with variable period (Overlap Studies)

    Inputs:
        real: (any ndarray)
        periods: (any ndarray)
    Parameters:
        minperiod: 2
        maxperiod: 30
        matype: 0 (Simple Moving Average)
    Outputs:
        real
    """
    ...

def MAX(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    MAX(ndarray real, int timeperiod=-0x80000000)

    MAX(real[, timeperiod=?])

    Highest value over a specified period (Math Operators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def MAXINDEX(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    MAXINDEX(ndarray real, int timeperiod=-0x80000000)

    MAXINDEX(real[, timeperiod=?])

    Index of highest value over a specified period (Math Operators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def MEDPRICE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    MEDPRICE(ndarray high, ndarray low)

    MEDPRICE(high, low)

    Median Price (Price Transform)

    Inputs:
        prices: ['high', 'low']
    Outputs:
        real
    """
    ...

def MFI(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    MFI(ndarray high, ndarray low, ndarray close, ndarray volume, int timeperiod=-0x80000000)

    MFI(high, low, close, volume[, timeperiod=?])

    Money Flow Index (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close', 'volume']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def MIDPOINT(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    MIDPOINT(ndarray real, int timeperiod=-0x80000000)

    MIDPOINT(real[, timeperiod=?])

    MidPoint over period (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def MIDPRICE(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    MIDPRICE(ndarray high, ndarray low, int timeperiod=-0x80000000)

    MIDPRICE(high, low[, timeperiod=?])

    Midpoint Price over period (Overlap Studies)

    Inputs:
        prices: ['high', 'low']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def MIN(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    MIN(ndarray real, int timeperiod=-0x80000000)

    MIN(real[, timeperiod=?])

    Lowest value over a specified period (Math Operators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def MININDEX(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    MININDEX(ndarray real, int timeperiod=-0x80000000)

    MININDEX(real[, timeperiod=?])

    Index of lowest value over a specified period (Math Operators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        integer (values are -100, 0 or 100)
    """
    ...

def MINMAX(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    MINMAX(ndarray real, int timeperiod=-0x80000000)

    MINMAX(real[, timeperiod=?])

    Lowest and highest values over a specified period (Math Operators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        min
        max
    """
    ...

def MINMAXINDEX(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    MINMAXINDEX(ndarray real, int timeperiod=-0x80000000)

    MINMAXINDEX(real[, timeperiod=?])

    Indexes of lowest and highest values over a specified period (Math Operators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        minidx
        maxidx
    """
    ...

def MINUS_DI(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    MINUS_DI(ndarray high, ndarray low, ndarray close, int timeperiod=-0x80000000)

    MINUS_DI(high, low, close[, timeperiod=?])

    Minus Directional Indicator (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def MINUS_DM(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    MINUS_DM(ndarray high, ndarray low, int timeperiod=-0x80000000)

    MINUS_DM(high, low[, timeperiod=?])

    Minus Directional Movement (Momentum Indicators)

    Inputs:
        prices: ['high', 'low']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def MOM(data: pd.Series | pd.DataFrame, timeperiod: Any = 10) -> pd.Series | pd.DataFrame:
    """
    MOM(ndarray real, int timeperiod=-0x80000000)

    MOM(real[, timeperiod=?])

    Momentum (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 10
    Outputs:
        real
    """
    ...

def MULT(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    MULT(ndarray real0, ndarray real1)

    MULT(real0, real1)

    Vector Arithmetic Mult (Math Operators)

    Inputs:
        real0: (any ndarray)
        real1: (any ndarray)
    Outputs:
        real
    """
    ...

def NATR(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    NATR(ndarray high, ndarray low, ndarray close, int timeperiod=-0x80000000)

    NATR(high, low, close[, timeperiod=?])

    Normalized Average True Range (Volatility Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def OBV(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    OBV(ndarray real, ndarray volume)

    OBV(real, volume)

    On Balance Volume (Volume Indicators)

    Inputs:
        real: (any ndarray)
        prices: ['volume']
    Outputs:
        real
    """
    ...

def PLUS_DI(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    PLUS_DI(ndarray high, ndarray low, ndarray close, int timeperiod=-0x80000000)

    PLUS_DI(high, low, close[, timeperiod=?])

    Plus Directional Indicator (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def PLUS_DM(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    PLUS_DM(ndarray high, ndarray low, int timeperiod=-0x80000000)

    PLUS_DM(high, low[, timeperiod=?])

    Plus Directional Movement (Momentum Indicators)

    Inputs:
        prices: ['high', 'low']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def PPO(data: pd.Series | pd.DataFrame, fastperiod: Any = 12, slowperiod: Any = 26, matype: Any = 0) -> pd.Series | pd.DataFrame:
    """
    PPO(ndarray real, int fastperiod=-0x80000000, int slowperiod=-0x80000000, int matype=0)

    PPO(real[, fastperiod=?, slowperiod=?, matype=?])

    Percentage Price Oscillator (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        fastperiod: 12
        slowperiod: 26
        matype: 0 (Simple Moving Average)
    Outputs:
        real
    """
    ...

def ROC(data: pd.Series | pd.DataFrame, timeperiod: Any = 10) -> pd.Series | pd.DataFrame:
    """
    ROC(ndarray real, int timeperiod=-0x80000000)

    ROC(real[, timeperiod=?])

    Rate of change : ((real/prevPrice)-1)*100 (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 10
    Outputs:
        real
    """
    ...

def ROCP(data: pd.Series | pd.DataFrame, timeperiod: Any = 10) -> pd.Series | pd.DataFrame:
    """
    ROCP(ndarray real, int timeperiod=-0x80000000)

    ROCP(real[, timeperiod=?])

    Rate of change Percentage: (real-prevPrice)/prevPrice (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 10
    Outputs:
        real
    """
    ...

def ROCR(data: pd.Series | pd.DataFrame, timeperiod: Any = 10) -> pd.Series | pd.DataFrame:
    """
    ROCR(ndarray real, int timeperiod=-0x80000000)

    ROCR(real[, timeperiod=?])

    Rate of change ratio: (real/prevPrice) (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 10
    Outputs:
        real
    """
    ...

def ROCR100(data: pd.Series | pd.DataFrame, timeperiod: Any = 10) -> pd.Series | pd.DataFrame:
    """
    ROCR100(ndarray real, int timeperiod=-0x80000000)

    ROCR100(real[, timeperiod=?])

    Rate of change ratio 100 scale: (real/prevPrice)*100 (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 10
    Outputs:
        real
    """
    ...

def RSI(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    RSI(ndarray real, int timeperiod=-0x80000000)

    RSI(real[, timeperiod=?])

    Relative Strength Index (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def SAR(data: pd.Series | pd.DataFrame, acceleration: Any = 0.02, maximum: Any = 0.2) -> pd.Series | pd.DataFrame:
    """
    SAR(ndarray high, ndarray low, double acceleration=0.02, double maximum=0.2)

    SAR(high, low[, acceleration=?, maximum=?])

    Parabolic SAR (Overlap Studies)

    Inputs:
        prices: ['high', 'low']
    Parameters:
        acceleration: 0.02
        maximum: 0.2
    Outputs:
        real
    """
    ...

def SAREXT(data: pd.Series | pd.DataFrame, startvalue: Any = 0.0, offsetonreverse: Any = 0.0, accelerationinitlong: Any = 0.02, accelerationlong: Any = 0.02, accelerationmaxlong: Any = 0.2, accelerationinitshort: Any = 0.02, accelerationshort: Any = 0.02, accelerationmaxshort: Any = 0.2) -> pd.Series | pd.DataFrame:
    """
    SAREXT(ndarray high, ndarray low, double startvalue=-4e37, double offsetonreverse=-4e37, double accelerationinitlong=-4e37, double accelerationlong=-4e37, double accelerationmaxlong=-4e37, double accelerationinitshort=-4e37, double accelerationshort=-4e37, double accelerationmaxshort=-4e37)

    SAREXT(high, low[, startvalue=?, offsetonreverse=?, accelerationinitlong=?, accelerationlong=?, accelerationmaxlong=?, accelerationinitshort=?, accelerationshort=?, accelerationmaxshort=?])

    Parabolic SAR - Extended (Overlap Studies)

    Inputs:
        prices: ['high', 'low']
    Parameters:
        startvalue: 0.0
        offsetonreverse: 0.0
        accelerationinitlong: 0.02
        accelerationlong: 0.02
        accelerationmaxlong: 0.2
        accelerationinitshort: 0.02
        accelerationshort: 0.02
        accelerationmaxshort: 0.2
    Outputs:
        real
    """
    ...

def SIN(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    SIN(ndarray real)

    SIN(real)

    Vector Trigonometric Sin (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def SINH(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    SINH(ndarray real)

    SINH(real)

    Vector Trigonometric Sinh (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def SMA(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    SMA(ndarray real, int timeperiod=-0x80000000)

    SMA(real[, timeperiod=?])

    Simple Moving Average (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def SQRT(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    SQRT(ndarray real)

    SQRT(real)

    Vector Square Root (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def STDDEV(data: pd.Series | pd.DataFrame, timeperiod: Any = 5, nbdev: Any = 1.0) -> pd.Series | pd.DataFrame:
    """
    STDDEV(ndarray real, int timeperiod=-0x80000000, double nbdev=-4e37)

    STDDEV(real[, timeperiod=?, nbdev=?])

    Standard Deviation (Statistic Functions)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 5
        nbdev: 1.0
    Outputs:
        real
    """
    ...

def STOCH(data: pd.Series | pd.DataFrame, fastk_period: Any = 5, slowk_period: Any = 3, slowk_matype: Any = 0, slowd_period: Any = 3, slowd_matype: Any = 0) -> pd.Series | pd.DataFrame:
    """
    STOCH(ndarray high, ndarray low, ndarray close, int fastk_period=-0x80000000, int slowk_period=-0x80000000, int slowk_matype=0, int slowd_period=-0x80000000, int slowd_matype=0)

    STOCH(high, low, close[, fastk_period=?, slowk_period=?, slowk_matype=?, slowd_period=?, slowd_matype=?])

    Stochastic (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        fastk_period: 5
        slowk_period: 3
        slowk_matype: 0
        slowd_period: 3
        slowd_matype: 0
    Outputs:
        slowk
        slowd
    """
    ...

def STOCHF(data: pd.Series | pd.DataFrame, fastk_period: Any = 5, fastd_period: Any = 3, fastd_matype: Any = 0) -> pd.Series | pd.DataFrame:
    """
    STOCHF(ndarray high, ndarray low, ndarray close, int fastk_period=-0x80000000, int fastd_period=-0x80000000, int fastd_matype=0)

    STOCHF(high, low, close[, fastk_period=?, fastd_period=?, fastd_matype=?])

    Stochastic Fast (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        fastk_period: 5
        fastd_period: 3
        fastd_matype: 0
    Outputs:
        fastk
        fastd
    """
    ...

def STOCHRSI(data: pd.Series | pd.DataFrame, timeperiod: Any = 14, fastk_period: Any = 5, fastd_period: Any = 3, fastd_matype: Any = 0) -> pd.Series | pd.DataFrame:
    """
    STOCHRSI(ndarray real, int timeperiod=-0x80000000, int fastk_period=-0x80000000, int fastd_period=-0x80000000, int fastd_matype=0)

    STOCHRSI(real[, timeperiod=?, fastk_period=?, fastd_period=?, fastd_matype=?])

    Stochastic Relative Strength Index (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 14
        fastk_period: 5
        fastd_period: 3
        fastd_matype: 0
    Outputs:
        fastk
        fastd
    """
    ...

def SUB(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    SUB(ndarray real0, ndarray real1)

    SUB(real0, real1)

    Vector Arithmetic Subtraction (Math Operators)

    Inputs:
        real0: (any ndarray)
        real1: (any ndarray)
    Outputs:
        real
    """
    ...

def SUM(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    SUM(ndarray real, int timeperiod=-0x80000000)

    SUM(real[, timeperiod=?])

    Summation (Math Operators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def T3(data: pd.Series | pd.DataFrame, timeperiod: Any = 5, vfactor: Any = 0.7) -> pd.Series | pd.DataFrame:
    """
    T3(ndarray real, int timeperiod=-0x80000000, double vfactor=-4e37)

    T3(real[, timeperiod=?, vfactor=?])

    Triple Exponential Moving Average (T3) (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 5
        vfactor: 0.7
    Outputs:
        real
    """
    ...

def TAN(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    TAN(ndarray real)

    TAN(real)

    Vector Trigonometric Tan (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def TANH(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    TANH(ndarray real)

    TANH(real)

    Vector Trigonometric Tanh (Math Transform)

    Inputs:
        real: (any ndarray)
    Outputs:
        real
    """
    ...

def TEMA(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    TEMA(ndarray real, int timeperiod=-0x80000000)

    TEMA(real[, timeperiod=?])

    Triple Exponential Moving Average (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def TRANGE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    TRANGE(ndarray high, ndarray low, ndarray close)

    TRANGE(high, low, close)

    True Range (Volatility Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Outputs:
        real
    """
    ...

def TRIMA(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    TRIMA(ndarray real, int timeperiod=-0x80000000)

    TRIMA(real[, timeperiod=?])

    Triangular Moving Average (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def TRIX(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    TRIX(ndarray real, int timeperiod=-0x80000000)

    TRIX(real[, timeperiod=?])

    1-day Rate-Of-Change (ROC) of a Triple Smooth EMA (Momentum Indicators)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...

def TSF(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    TSF(ndarray real, int timeperiod=-0x80000000)

    TSF(real[, timeperiod=?])

    Time Series Forecast (Statistic Functions)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def TYPPRICE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    TYPPRICE(ndarray high, ndarray low, ndarray close)

    TYPPRICE(high, low, close)

    Typical Price (Price Transform)

    Inputs:
        prices: ['high', 'low', 'close']
    Outputs:
        real
    """
    ...

def ULTOSC(data: pd.Series | pd.DataFrame, timeperiod1: Any = 7, timeperiod2: Any = 14, timeperiod3: Any = 28) -> pd.Series | pd.DataFrame:
    """
    ULTOSC(ndarray high, ndarray low, ndarray close, int timeperiod1=-0x80000000, int timeperiod2=-0x80000000, int timeperiod3=-0x80000000)

    ULTOSC(high, low, close[, timeperiod1=?, timeperiod2=?, timeperiod3=?])

    Ultimate Oscillator (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod1: 7
        timeperiod2: 14
        timeperiod3: 28
    Outputs:
        real
    """
    ...

def VAR(data: pd.Series | pd.DataFrame, timeperiod: Any = 5, nbdev: Any = 1.0) -> pd.Series | pd.DataFrame:
    """
    VAR(ndarray real, int timeperiod=-0x80000000, double nbdev=-4e37)

    VAR(real[, timeperiod=?, nbdev=?])

    Variance (Statistic Functions)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 5
        nbdev: 1.0
    Outputs:
        real
    """
    ...

def WCLPRICE(data: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """
    WCLPRICE(ndarray high, ndarray low, ndarray close)

    WCLPRICE(high, low, close)

    Weighted Close Price (Price Transform)

    Inputs:
        prices: ['high', 'low', 'close']
    Outputs:
        real
    """
    ...

def WILLR(data: pd.Series | pd.DataFrame, timeperiod: Any = 14) -> pd.Series | pd.DataFrame:
    """
    WILLR(ndarray high, ndarray low, ndarray close, int timeperiod=-0x80000000)

    WILLR(high, low, close[, timeperiod=?])

    Williams' %R (Momentum Indicators)

    Inputs:
        prices: ['high', 'low', 'close']
    Parameters:
        timeperiod: 14
    Outputs:
        real
    """
    ...

def WMA(data: pd.Series | pd.DataFrame, timeperiod: Any = 30) -> pd.Series | pd.DataFrame:
    """
    WMA(ndarray real, int timeperiod=-0x80000000)

    WMA(real[, timeperiod=?])

    Weighted Moving Average (Overlap Studies)

    Inputs:
        real: (any ndarray)
    Parameters:
        timeperiod: 30
    Outputs:
        real
    """
    ...
