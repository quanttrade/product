# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 19:30:51 2023

@author: caifeng
"""

import backtrader as bt
import numpy as np
from datetime import datetime
import pandas as pd

class TrendFlex(bt.Indicator):
    lines = ('trendflex', 'signal')

    params = (
        ('minor_period', 8),
        ('major_period', 55),
        ('signal_period', 6)
    )

    def __init__(self):
        minor_ema = bt.indicators.EMA(self.data, period=self.p.minor_period)
        major_ema = bt.indicators.EMA(self.data, period=self.p.major_period)

        self.lines.trendflex = (minor_ema - major_ema) * 100 / self.data.close
        self.lines.signal = bt.indicators.EMA(self.lines.trendflex, period=self.p.signal_period)

class MyStrategy(bt.Strategy):
    def __init__(self):
        self.trendflex = TrendFlex()

    def next(self):
        if self.trendflex.trendflex[0] > self.trendflex.signal[0] and \
            self.trendflex.trendflex[-1] < self.trendflex.signal[-1]:
            self.buy()
        elif self.trendflex.trendflex[0] < self.trendflex.signal[0] and \
            self.trendflex.trendflex[-1] > self.trendflex.signal[-1]:
            self.sell()

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    pn0 = os.getcwd()

    daily_price = pd.read_csv(os.path.join(pn0,"daily_price.csv"), 
                              parse_dates=['datetime'],dtype = {'sec_code':str})
    daily_price = daily_price.set_index(['datetime'])  # 将datetime设置成index
    # 按股票代码，依次循环传入数据
    for stock in daily_price['sec_code'].unique():
        # 日期对齐
        data = pd.DataFrame(index=daily_price.index.unique()) # 获取回测区间内所有交易日
        df = daily_price.query(f"sec_code=='{stock}'")[['open','high','low','close','volume','openinterest']]
        data_ = pd.merge(data, df, left_index=True, right_index=True, how='left')
        # 缺失值处理：日期对齐时会使得有些交易日的数据为空，所以需要对缺失数据进行填充
        data_.loc[:,['volume','openinterest']] = data_.loc[:,['volume','openinterest']].fillna(0)
        data_.loc[:,['open','high','low','close']] = data_.loc[:,['open','high','low','close']].fillna(method='pad')
        data_.loc[:,['open','high','low','close']] = data_.loc[:,['open','high','low','close']].fillna(0)
        # 导入数据
        datafeed = bt.feeds.PandasData(dataname=data_, 
                                       fromdate=datetime(2010,1,1), 
                                       todate=datetime(2022,12,31))
        cerebro.adddata(datafeed, name=stock) # 通过 name 实现数据集与股票的一一对应
        print(f"{stock} Done !") 
    # 初始资金 100,000,000    
    cerebro.broker.setcash(100000000.0) 
    # 佣金，双边各 0.0003
    cerebro.broker.setcommission(commission=0.0003) 
    # 滑点：双边各 0.0001
    cerebro.broker.set_slippage_perc(perc=0.0001) 
    # 将编写的策略添加给大脑，别忘了 ！
    cerebro.addinicator(TrendFlex)
    # 回测时需要添加 PyFolio 分析器
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    result = cerebro.run()
    # 借助 pyfolio 进一步做回测结果分析
    
    pyfolio = result[0].analyzers.pyfolio  # 注意：后面不要调用 .get_analysis() 方法
    # 或者是 result[0].analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyfolio.get_pf_items()
    (1+returns).cumprod().plot()