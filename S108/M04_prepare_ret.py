# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 09:34:36 2023
合成因子
合成20日因子

@author: adair2019
"""

import pandas as pd
from yq_toolsS45_linux import get_week_month_tradeDate_update
from yq_toolsS45_linux import get_MktEqudAdjAfGet
from quant_utilS73 import simple_group_backtest
from yq_toolsS45_linux import get_db_data
from tqdm import tqdm

f = pd.read_pickle('factor_sec_smoothing_test.pkl')
f.symbol = f.symbol.apply(lambda x:x[2:])
f.rename(columns = {'symbol':'ticker'},inplace=True)

tref = get_week_month_tradeDate_update('1990-01-01','3099-01-01')
tref = pd.DataFrame({'tradeDate':tref[0]})
tref.sort_values(by = ['tradeDate'], inplace = True)
tref1 = tref[(tref.tradeDate>='2013-01-07')].copy()
tref1 = tref1.iloc[::20]
tref_f = tref1.tradeDate.unique().tolist()
tref_f.sort()
tref_map = dict(zip(tref_f[1:],tref_f[:-1]))


'''
ret = []
for t in tqdm(tref1.tradeDate.tolist()):
    sub_x = get_MktEqudAdjAfGet(t,t,'ticker,tradeDate,closePrice')
    ret.append(sub_x)

ret= pd.concat(ret)
'''
ret = pd.read_pickle('ret20.pkl')
ret.tradeDate = ret.tradeDate.astype(str)
ret.sort_values(by=['ticker', 'tradeDate'],inplace = True)
ret = ret.groupby('ticker').apply(lambda x:x.set_index(['ticker', 'tradeDate']).closePrice.pct_change())
ret = ret.droplevel(0)
ret.name = 'r'
ret = ret.reset_index()
ret.dropna(inplace = True)

ret['t'] = ret.tradeDate.copy()
ret['tradeDate'] = ret.t.map(tref_map)
ret.dropna(inplace=True)


r1,r2 = simple_group_backtest(f,ret,'u','r',10)

r1 = r1.pivot('tradeDate','group','period_ret')
r1['long-short'] = r1[9] - r1[0]
(1+r1).cumprod().plot()
