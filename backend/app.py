from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import yfinance
from technical_indicators import TechnicalIndicators
from risk_calculation import RiskCalculation
from backtesting import BacktestingSystem

app = FastAPI(title="Quantitative Trading API",
             description="API for fetching market data, calculating technical indicators, and running backtests")

# Data Models
class StockDataRequest(BaseModel):
    symbol: str
    period: str = "max"

class TechnicalIndicatorRequest(BaseModel):
    symbol: str
    length: int = 20
    period: str = "max"

class RiskMetricsRequest(BaseModel):
    symbol: str
    confidence_level: float = 0.95
    risk_free_rate: float = 0.01
    period: str = "max"

class BacktestRequest(BaseModel):
    symbol: str
    initial_capital: float = 100000
    position_size: float = 0.02
    stop_loss: float = 0.02
    take_profit: float = 0.04
    rsi_oversold: float = 35
    rsi_overbought: float = 65
    period: str = "max"

# API 1: Raw Data Endpoints
@app.get("/api/v1/market/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/market/historical")
async def get_historical_data(request: StockDataRequest):
    try:
        stock_df = pd.DataFrame(
            yfinance.Ticker(request.symbol)
            .history(period=request.period)
        ).drop(['Dividends', 'Stock Splits'], axis=1)
        
        if stock_df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {request.symbol}")
            
        return {
            "symbol": request.symbol,
            "data": stock_df.reset_index().to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API 2: Technical Indicators and Risk Metrics
@app.post("/api/v1/analysis/technical")
async def get_technical_indicators(request: TechnicalIndicatorRequest):
    try:
        # Fetch historical data
        stock_df = pd.DataFrame(
            yfinance.Ticker(request.symbol)
            .history(period=request.period)
        ).drop(['Dividends', 'Stock Splits'], axis=1)
        
        if stock_df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {request.symbol}")
        
        # Calculate technical indicators
        ti = TechnicalIndicators(df=stock_df, length=request.length)
        
        # Calculate all indicators
        bb_low, bb_mid, bb_high = ti.bollinger_bands()
        
        indicators_df = pd.DataFrame({
            'date': stock_df.index,
            'garman_klass_volatility': ti.garman_klass_volatility().values,
            'rsi': ti.rsi().values,
            'roc': ti.roc().values,
            'bb_low': bb_low.values,
            'bb_mid': bb_mid.values,
            'bb_high': bb_high.values,
            'atr': ti.atr().values,
            'macd': ti.macd().values,
            'dollar_volume': ti.dollar_volume().values
        })
        
        return {
            "symbol": request.symbol,
            "indicators": indicators_df.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analysis/risk")
async def get_risk_metrics(request: RiskMetricsRequest):
    try:
        # Fetch historical data
        stock_df = pd.DataFrame(
            yfinance.Ticker(request.symbol)
            .history(period=request.period)
        ).drop(['Dividends', 'Stock Splits'], axis=1)
        
        if stock_df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {request.symbol}")
        
        # Calculate risk metrics
        rc = RiskCalculation(
            df=stock_df,
            confidence_level=request.confidence_level,
            risk_free_rate=request.risk_free_rate
        )
        
        risk_metrics = {
            "symbol": request.symbol,
            "metrics": {
                "standard_deviation": rc.compute_stdev(),
                "value_at_risk": rc.compute_var(),
                "drawdown": rc.compute_drawdown(),
                "sharpe_ratio": rc.compute_sharpe_ratio(),
                "max_drawdown": rc.compute_max_drawdown(),
                "expected_shortfall": rc.compute_expected_shortfall()
            }
        }
        
        return risk_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API 3: Backtesting
@app.post("/api/v1/backtest")
async def run_backtest(request: BacktestRequest):
    try:
        # Fetch historical data
        stock_df = pd.DataFrame(
            yfinance.Ticker(request.symbol)
            .history(period=request.period)
        ).drop(['Dividends', 'Stock Splits'], axis=1)
        
        if stock_df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {request.symbol}")
        
        # Initialize and run backtest
        backtest = BacktestingSystem(
            df=stock_df,
            initial_capital=request.initial_capital,
            position_size=request.position_size,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            rsi_oversold=request.rsi_oversold,
            rsi_overbought=request.rsi_overbought
        )
        
        results = backtest.run_backtest()
        
        return {
            "symbol": request.symbol,
            "backtest_results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)