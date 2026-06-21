import pandas as pd, numpy as np
import data_sources
synth = pd.DataFrame({'close':100*np.exp(np.cumsum(np.random.RandomState(3).randn(500)*0.012))},
                     index=pd.date_range('2021-01-01',periods=500,freq='B'))
data_sources.get_prices = lambda ticker, **k: synth.copy()
import compare, backtest, metrics
from strategies import REGISTRY
print('backtest.load_prices rows:', len(backtest.load_prices('AAPL','2y')))
compare.BASKET=['AAPL','SHOP.TO']; compare.WINDOWS={'5Y':{'period':'5y'}}
compare.main(dry=True)
print('INTEGRATION OK')
