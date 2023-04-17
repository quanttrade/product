# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 09:47:25 2023
持有两天的收益

拆分
@author: adair2019
"""

import pandas as pd

x = pd.read_pickle('S112_F01.pkl')

x.sort_values(by=['ticker','tradeDate'], inplace = True)
tref = x.tradeDate.unique().tolist()
tref.sort()
x0 = pd.DataFrame({'tradeDate':tref})
#不同持有期
def get_return(sub_x):
    sub_x = x0.merge(sub_x,how = 'left', on='tradeDate')    
    sub_x.sort_values(by = 'tradeDate', inplace = True)
    sub_x['c2'] = sub_x.C.shift(-2)
    sub_x['t2'] = sub_x.tradeDate.shift(-2)
    sub_x['c5'] = sub_x.C.shift(-5)
    sub_x['t5'] = sub_x.tradeDate.shift(-5)
    
    sub_x['o2'] = sub_x.O.shift(-1)
    
    sub_x['rcc2'] = sub_x.c2 / sub_x.C - 1
    sub_x['rco2'] = sub_x.c2 / sub_x.o2 - 1
    sub_x['rcc5'] = sub_x.c5 / sub_x.C - 1
    sub_x['rco5'] = sub_x.c5 / sub_x.o2 - 1
    return sub_x

F2 = x.groupby('ticker').apply(lambda x:get_return(x))
F2.dropna(subset=['C','H','RVS','NewRVS'],inplace = True)
F2.reset_index(inplace = True,drop = True)
#F2.to_pickle('S112_F02.pkl')
tmp1 = F2[['tradeDate','ticker','c2', 't2',  'o2', 'rcc2', 'rco2']]

tmp2 = F2[['tradeDate','ticker', 'c5', 't5', 'o2','rcc5','rco5']]
