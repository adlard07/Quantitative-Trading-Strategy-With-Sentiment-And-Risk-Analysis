import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from technical_indicators import TechnicalIndicators
from risk_calculation import RiskCalculation

@dataclass
class Trade:
    entry_date: pd.Timestamp
    entry_price: float
    shares: float
    stop_loss: float
    take_profit: float
    status: str = 'open'
    exit_date: pd.Timestamp = None
    exit_price: float = None
    profit: float = None

@dataclass
class BacktestingSystem:
    df: pd.DataFrame
    initial_capital: float
    position_size: float = 0.02
    stop_loss: float = 0.02
    take_profit: float = 0.04
    rsi_oversold: float = 35
    rsi_overbought: float = 65
    positions: List[Trade] = field(default_factory=list)
    trade_history: List[Trade] = field(default_factory=list)
    
    def __post_init__(self):
        self.capital = self.initial_capital
        self._calculate_indicators()
        
    def _calculate_indicators(self) -> None:
        """Pre-calculate all technical indicators for optimization"""
        ti = TechnicalIndicators(df=self.df, length=20)
        
        # Calculate all indicators at once and store as numpy arrays for faster access
        self.indicators = {
            'rsi': ti.rsi().to_numpy(),
            'macd': ti.macd().to_numpy(),
            'roc': ti.roc().to_numpy(),
        }
        
        bb_low, bb_mid, bb_high = ti.bollinger_bands()
        self.indicators.update({
            'bb_low': bb_low.to_numpy(),
            'bb_high': bb_high.to_numpy()
        })
        
        # Pre-calculate price arrays
        self.prices = {
            'close': self.df['Close'].to_numpy(),
            'high': self.df['High'].to_numpy(),
            'low': self.df['Low'].to_numpy()
        }
        
    def generate_signals(self) -> np.ndarray:
        """Vectorized signal generation"""
        signals = np.zeros(len(self.df))
        
        # Buy conditions (vectorized)
        buy_conditions = (
            (self.indicators['rsi'] < self.rsi_oversold) & 
            (
                (self.prices['close'] < self.indicators['bb_low']) |
                (np.diff(self.indicators['macd'], prepend=np.nan) > 0) |
                (self.indicators['roc'] > 0)
            )
        )
        
        # Sell conditions (vectorized)
        sell_conditions = (
            (self.indicators['rsi'] > self.rsi_overbought) &
            (
                (self.prices['close'] > self.indicators['bb_high']) |
                (np.diff(self.indicators['macd'], prepend=np.nan) < 0) |
                (self.indicators['roc'] < 0)
            )
        )
        
        signals[buy_conditions] = 1
        signals[sell_conditions] = -1
        
        return signals
    
    def calculate_position_size(self, entry_price: float) -> Tuple[float, float]:
        """Optimized position size calculation"""
        risk_amount = self.capital * self.position_size
        stop_loss_amount = entry_price * self.stop_loss
        shares = risk_amount / stop_loss_amount if stop_loss_amount > 0 else 0
        capital_required = shares * entry_price
        return shares, min(capital_required, self.capital)
    
    def execute_trade(self, signal: int, price: float, date: pd.Timestamp) -> None:
        """Optimized trade execution"""
        if signal == 0 or price <= 0:
            return
            
        if signal == 1 and not self.positions:  # Buy signal and no open positions
            shares, capital_required = self.calculate_position_size(price)
            if capital_required <= self.capital and shares > 0:
                self.capital -= capital_required
                trade = Trade(
                    entry_date=date,
                    entry_price=price,
                    shares=shares,
                    stop_loss=price * (1 - self.stop_loss),
                    take_profit=price * (1 + self.take_profit)
                )
                self.positions.append(trade)
                
        elif signal == -1 and self.positions:  # Sell signal
            position = self.positions[0]  # We only maintain one position at a time
            position.status = 'closed'
            position.exit_date = date
            position.exit_price = price
            position.profit = (price - position.entry_price) * position.shares
            self.capital += (position.shares * price)
            self.trade_history.append(position)
            self.positions.clear()
    
    def run_backtest(self) -> Dict:
        """Optimized backtest execution"""
        signals = self.generate_signals()
        equity_curve = np.zeros(len(self.df))
        equity_curve[0] = self.initial_capital
        
        for i in range(1, len(self.df)):
            current_price = self.prices['close'][i]
            current_date = self.df.index[i]
            
            # Check stop loss and take profit
            if self.positions:
                position = self.positions[0]
                if current_price <= position.stop_loss:
                    self.execute_trade(-1, position.stop_loss, current_date)
                elif current_price >= position.take_profit:
                    self.execute_trade(-1, position.take_profit, current_date)
            
            # Execute new trades
            self.execute_trade(signals[i], current_price, current_date)
            
            # Update equity curve
            equity_curve[i] = self.capital + sum(
                p.shares * current_price for p in self.positions
            )
        
        # Calculate metrics using numpy operations
        total_trades = len(self.trade_history)
        winning_trades = sum(1 for t in self.trade_history if t.profit > 0)
        
        risk_calc = RiskCalculation(df=self.df)
        
        metrics = {
            'total_return': (equity_curve[-1] - self.initial_capital) / self.initial_capital,
            'sharpe_ratio': risk_calc.compute_sharpe_ratio(),
            'max_drawdown': risk_calc.compute_max_drawdown(),
            'var': risk_calc.compute_var(),
            'expected_shortfall': risk_calc.compute_expected_shortfall(),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
            'equity_curve': equity_curve.tolist()
        }
        
        # Add additional performance metrics
        if total_trades > 0:
            profits = np.array([t.profit for t in self.trade_history])
            metrics.update({
                'avg_profit': np.mean(profits),
                'profit_std': np.std(profits),
                'max_profit': np.max(profits),
                'max_loss': np.min(profits),
                'profit_factor': np.sum(profits[profits > 0]) / abs(np.sum(profits[profits < 0])) if np.sum(profits[profits < 0]) != 0 else np.inf
            })
        
        return metrics

if __name__ == '__main__':
    from pull_historical_data import stock_history
    import time
    
    df = stock_history('RS')
    
    start_time = time.time()
    backtest = BacktestingSystem(
        df=df,
        initial_capital=100000,
        position_size=0.02,
        stop_loss=0.02,
        take_profit=0.04,
        rsi_oversold=35,
        rsi_overbought=65
    )
    
    results = backtest.run_backtest()
    end_time = time.time()
    
    print("\nBacktest Results:")
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.2%}")
    if results['total_trades'] > 0:
        print(f"Profit Factor: {results['profit_factor']:.2f}")
        print(f"Average Profit: ${results['avg_profit']:.2f}")
        print(f"Profit Std Dev: ${results['profit_std']:.2f}")
    print(f"\nBacktest Duration: {end_time - start_time:.2f} seconds")