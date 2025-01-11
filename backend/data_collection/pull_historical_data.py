import yfinance
import pandas as pd
from utils import logging

def pull_historical(stock):
    try:
        return pd.DataFrame(yfinance.Ticker(stock).history(period='max')).drop(['Dividends', 'Stock Splits'], axis=1)
    except Exception as e:
        logging.info(f'Error occured while fetching dataframe.\nError: {e}')
        return 

def main():
    try:
        stocks = ['RS', 'TCS.NS', 'HDFCBANK.NS', 'BHARTIARTL.NS', 
                  'IBN', 'INFY', 'SBIN.NS', 'HINDUNILVR.NS', 
                  'ITC.NS', 'HCLTECH.NS', 'LT.NS', 'BAJFINANCE.NS', 
                  'SUNPHARMA.NS', 'MHIDL.XC', 'MARUTI.BO', 'KOTAKBANK.BO']
        dfs = []
        for stock in stocks:
            df = pull_historical(stock)
            dfs.append(df)
            df['Stock'] = stock

        df = pd.concat(dfs, axis=0)
        logging.info(f'All dataframes pulled')
        return df

    except Exception as e:
        logging.info(f'Error occured while concatinating historical data.\nError: {e}')


if __name__=='__main__':
    print(main().head())