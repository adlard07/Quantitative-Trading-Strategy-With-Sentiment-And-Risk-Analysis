import yfinance
import pandas as pd
from utils import logging

def stock_history(stock):
    try:
        stock_df = pd.DataFrame(yfinance.Ticker(stock).history(period='max')).drop(['Dividends', 'Stock Splits'], axis=1)
        return stock_df 
    except Exception as e:
        logging.info(f'Error occured while fetching dataframe.\nError: {e}')
        return 



if __name__=='__main__':
    def main():
        try:
            stocks = ['RS', 'TCS.NS', 'HDFCBANK.NS', 'BHARTIARTL.NS', 
                      'IBN', 'INFY', 'SBIN.NS', 'HINDUNILVR.NS', 
                      'ITC.NS', 'HCLTECH.NS', 'LT.NS', 'BAJFINANCE.NS', 
                      'SUNPHARMA.NS', 'MHIDL.XC', 'MARUTI.BO', 'KOTAKBANK.BO']
            for stock in stocks:
                df = stock_historical(stock)

            logging.info(f'Pulled all dataframes.')
            return df
        except Exception as e:
            logging.info(f'Error occured while concatinating historical data.\nError: {e}')
            
    print(main().head())