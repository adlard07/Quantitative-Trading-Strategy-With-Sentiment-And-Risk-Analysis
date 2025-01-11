from scipy.stats import norm
import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass(init=True, order=False, kw_only=True)
class RiskCalculation:
    df: pd.DataFrame
    confidence_level: float = 0.95
    risk_free_rate: float = 0.01

    def compute_stdev(self):
        return self.df['Close'].pct_change().dropna().std()

    def compute_var(self):
        mean_return = self.df['Close'].pct_change().dropna().mean()
        std_dev = self.compute_stdev()
        z_score = norm.ppf(1 - self.confidence_level)
        return mean_return + z_score * std_dev

    def compute_drawdown(self):
        cumulative_returns = (1 + self.df['Close'].pct_change().dropna()).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max
        return drawdown.min()

    def compute_sharpe_ratio(self):
        mean_return = self.df['Close'].pct_change().dropna().mean()
        std_dev = self.compute_stdev()
        return (mean_return - self.risk_free_rate) / std_dev if std_dev != 0 else np.nan

    def compute_max_drawdown(self):
        cumulative_returns = (1 + self.df['Close'].pct_change().dropna()).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max
        return drawdown.min()

    def compute_expected_shortfall(self):
        sorted_returns = np.sort(self.df['Close'].pct_change().dropna())
        cutoff_index = int((1 - self.confidence_level) * len(sorted_returns))
        return sorted_returns[:cutoff_index].mean() if cutoff_index > 0 else np.nan


if __name__ == '__main__':
    from data_collection.pull_historical_data import stock_history
    df = stock_history('RS')
    confidence_level = 0.95
    risk_free_rate = 0.01

    rc = RiskCalculation(df=df, confidence_level=confidence_level, risk_free_rate=risk_free_rate)
    df['stdev'] = rc.compute_stdev()
    df['var'] = rc.compute_var()
    df['drawdown'] = rc.compute_drawdown()
    df['sharpe_ratio'] = rc.compute_sharpe_ratio()
    df['max_drawdown'] = rc.compute_max_drawdown()
    df['expected_shortfall'] = rc.compute_expected_shortfall()

    print(df)
