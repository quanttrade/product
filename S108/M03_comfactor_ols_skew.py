# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 09:34:36 2023
合成平滑因子


以跌幅时间重心作为被解释变量，对涨幅时间重心回归取残差，取其 其 20 日均值作
为选股因子 ，记为跌幅时间重心偏离因子

1 tgd

2 加入峰度因子计算

@author: adair2019
"""

import pandas as pd
from yq_toolsS45_linux import get_week_month_tradeDate_update
import statsmodels.api as sm


smoothing_N = 20
smoothing_N_min = 18


tref = get_week_month_tradeDate_update('1990-01-01','3099-01-01')
tref_month = tref[2]
tref = pd.DataFrame({'tradeDate':tref[0]})
tref.sort_values(by = ['tradeDate'], inplace = True)
def smoothing_factor(sub_x):
    sub_tref = tref[(tref.tradeDate>=sub_x.iloc[0].tradeDate) & (tref.tradeDate<=sub_x.iloc[-1].tradeDate)]
    sub_tref0 = sub_x.tradeDate.tolist()
    sub_x = sub_tref.merge(sub_x, how = 'left', on ='tradeDate')
    sub_x['symbol'] = sub_x.iloc[0].symbol
    sub_x = sub_x.set_index(['symbol','tradeDate']).rolling(smoothing_N, min_periods = smoothing_N_min).mean().reset_index()
    sub_x = sub_x[sub_x.tradeDate.isin(sub_tref0)]
    return sub_x.set_index(['symbol','tradeDate'])
    
def com_ols_factor_tgd(sub_x):
    sub_x = sub_x.copy()
    y = sub_x[['Gu']]
    x = sub_x[['r_u_bar','R1','R2','R_night']]
    x=sm.add_constant(x) #添加常数项
    est=sm.OLS(y,x)
    model=est.fit()#建立最小二乘回归模型
    sub_x['error_u'] = model.resid
    
    y = sub_x[['Gd']]
    x = sub_x[['r_d_bar','R1','R2','R_night']]
    x=sm.add_constant(x) #添加常数项
    est=sm.OLS(y,x)
    model=est.fit()#建立最小二乘回归模型
    sub_x['error_d'] = model.resid
    
    
    x = sub_x[['error_u']]
    y = sub_x[['error_d']]
    x=sm.add_constant(x) #添加常数项
    est=sm.OLS(y,x)
    model=est.fit()#建立最小二乘回归模型
    sub_x['tgd'] = model.resid
    
    x = sub_x[['Gu']]
    y = sub_x[['Gd']]
    x=sm.add_constant(x) #添加常数项
    est=sm.OLS(y,x)
    model=est.fit()#建立最小二乘回归模型
    sub_x['f'] = model.resid
    
    return sub_x

key = 'v3'

F0 = pd.read_pickle('factor_sec_%s.pkl' % key)
F0 = F0.groupby('tradeDate').apply(lambda x:com_ols_factor_tgd(x))


F0['tao'] = F0.Gd - F0.Gu
F0['u'] = F0['tao'].abs()

F0.sort_values(by = ['symbol', 'tradeDate'], inplace=True)
#平滑
F = F0.groupby('symbol').apply(lambda x: smoothing_factor(x)).droplevel(0)
F.dropna(inplace=True)
F.reset_index(inplace = True)

'''
from yq_toolsS45_linux import engine37
from sqlalchemy.types import NVARCHAR, Float,DATE,Integer
from sqlalchemy.dialects.mysql import DOUBLE
d = F.columns.tolist()
d = dict(zip(d,[DOUBLE]*len(d)))
d.update({'tradeDate':DATE})
d.update({'ticker':NVARCHAR(8)})

F.sk = -F.sk
F.symbol = F.symbol.apply(lambda x:x[2:])
F.rename(columns = {'symbol':'ticker'},inplace=True)
F.reset_index(inplace=True,drop =True)
F['sk_rank'] = F.groupby('tradeDate').sk.rank()
F['tgd_rank'] = F.groupby('tradeDate').tgd.rank()
F['tgd_skew'] = F.sk_rank+F.tgd_rank

F.to_sql('s108_factor_rolling',engine37,index=False,chunksize=5000,if_exists = 'replace',dtype=d)
'''

F.to_pickle('factor_sec_smoothing_ols_tgd.pkl')


tref1 = tref[(tref.tradeDate>='2013-01-07')].copy()
tref1 = tref1.iloc[::20]


F[F.tradeDate.isin(tref1.tradeDate.tolist())].to_pickle('factor_sec_smoothing_test_ols_tgd.pkl')
F[F.tradeDate.isin(tref_month)].to_pickle('factor_sec_smoothing_month_ols_tgd.pkl')