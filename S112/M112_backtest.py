# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 11:22:09 2023

@author: adair2019
"""

import quant_utilS73 as qutil
import pandas as pd


o = pd.read_pickle('forbidden_pool.pkl')
#F = pd.read_pickle('S112_F02.pkl')
F = pd.read_pickle('S112_F02_neutralized.pkl')
F = F[F.tradeDate>='2006-01-01']

#F = F.merge(o[['ticker','tradeDate','special_flag']],how ='left', on = ['ticker', 'tradeDate'])
#F = F[F.special_flag.isna()]

tref = F.tradeDate.unique().tolist()
tref.sort()
x0 = pd.DataFrame({'tradeDate':tref})

x2 = x0[x0.index%2==0]
x5 = x0[x0.index%5==0]

tref_pool = [x2.tradeDate.tolist(),x5.tradeDate.tolist()]
tref_info = dict(zip([0,1],['2d','5d']))
r_info = dict(zip([0,1],['rcc2','rcc5']))
for i,sub_t in enumerate(tref_pool) :    
    sub_F = F[F.tradeDate.isin(sub_t)]
    for factor in ['HB','RVS','NewRVS']:
        for sub_fee in [0,3.0/1000]:
            a1, a2 = qutil.simple_group_backtest_adair(sub_F, factor, r_info[i], ngrp=5, commission=sub_fee)
            r = a1.pivot('tradeDate','group','period_ret')
            r1 = (1+r).cumprod()
            (1+r1).plot(title='%s-%s-%0.3f' % (tref_info[i],factor,sub_fee))
        