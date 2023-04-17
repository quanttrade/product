# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 09:34:36 2023
合成因子

基于M02合成基础因子值Gu Gd，做20日平滑，合成涨幅、跌幅因子
240 过滤日内趋势数据的
v2 每日第一个收益采用隔日收益
oc 收益计算close/open-1
@author: adair2019
"""

import pandas as pd
from yq_toolsS45_linux import get_week_month_tradeDate_update
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
    


key = '240'

F0 = pd.read_pickle('factor_sec_%s.pkl' % key)
F0['tao'] = F0.Gd - F0.Gu
F0['u'] = F0['tao'].abs()

F0.sort_values(by = ['symbol', 'tradeDate'], inplace=True)
#平滑
F = F0.groupby('symbol').apply(lambda x: smoothing_factor(x)).droplevel(0)
F.dropna(inplace=True)
F.reset_index(inplace = True)


F.to_pickle('factor_sec_smoothing_%s.pkl' % key)


tref1 = tref[(tref.tradeDate>='2013-01-07')].copy()
tref1 = tref1.iloc[::20]


F[F.tradeDate.isin(tref1.tradeDate.tolist())].to_pickle('factor_sec_smoothing_test_%s.pkl' % key)
F[F.tradeDate.isin(tref_month)].to_pickle('factor_sec_smoothing_month_%s.pkl' % key)