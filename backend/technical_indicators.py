import pandas_ta
import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass(init=True, order=False, kw_only=True)
class TechnicalIndicators:
    df: pd.DataFrame
    length: int

    def garman_klass_volatility(self):
        return ((np.log(self.df['High']) - np.log(self.df['Low'])) / 2)**2 - (2 * np.log(2) - 1) * (np.log(self.df['Close']) - np.log(self.df['Open']))**2

    def rsi(self):
      return pandas_ta.rsi(close=self.df['Close'], length=self.length)

    def roc(self):
      return pandas_ta.momentum.roc(close=self.df['Close'], length=self.length)

    def bollinger_bands(self):
      bb = pandas_ta.bbands(close=self.df['Close'], length=self.length)
      return bb.iloc[:,0], bb.iloc[:,1], bb.iloc[:,2]

    def atr(self):
      atr = pandas_ta.atr(high=self.df['High'], low=self.df['Low'], close=self.df['Close'], length=self.length)
      return atr.sub(atr.mean()).div(atr.std())

    def macd(self):
      macd = pandas_ta.macd(close=self.df['Close'], level=20).iloc[:, 0]
      return macd.sub(macd.mean()).div(macd.std())

    def dollar_volume(self):
      return self.df['Close'] * self.df['Volume']


if __name__=='__main__':
    from data_collection.pull_historical_data import stock_history

    df = stock_history('RS')
    length = 30
    technical_indicators = TechnicalIndicators(df=df, length=length)
    df['garman_klass_volatility'] = technical_indicators.garman_klass_volatility().values
    df['rsi'] = technical_indicators.rsi().values
    df['roc'] = technical_indicators.roc().values

    bb_low, bb_mid, bb_high = technical_indicators.bollinger_bands()
    df['bb_low'] = bb_low
    df['bb_mid'] = bb_mid
    df['bb_high'] = bb_high

    df['atr'] = technical_indicators.atr().values
    df['macd'] = technical_indicators.macd().values
    df['dollar_volume'] = technical_indicators.dollar_volume().values

    print(df)