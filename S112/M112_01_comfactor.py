# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 07:48:37 2023
合成因子
@author: adair2019
"""

from yq_toolsS45_linux import get_db_data
import pandas as pd
import os


fn1 = 'day_price.pkl'

if os.path.exists(fn1):
    r = pd.read_pickle(fn1)
else:
    sql_tmp = '''select symbol as ticker,tradeDate, openPrice,closePrice,HighestPrice,lowestPrice,
            turnoverVol,chgPct from yq_dayprice order by ticker,tradeDate'''
    r =  get_db_data('yuqerdata',sql_tmp)
    r.tradeDate = r.tradeDate.astype(str)
    r.to_pickle(fn1)

d= dict(zip(['openPrice', 'closePrice', 'HighestPrice',
       'lowestPrice', 'turnoverVol', 'chgPct'],['O','C','H','L','V','r']))
r.rename(columns = d, inplace = True)
#
tref = r.tradeDate.unique().tolist()
tref.sort()
x0 = pd.DataFrame({'tradeDate':tref})
#cal factor

def cal_factor(sub_x):
    sub_x = x0.merge(sub_x,how = 'left', on='tradeDate')    
    sub_x.sort_values(by = 'tradeDate', inplace = True)
    sub_x['RVS'] = sub_x.rolling(5).r.mean()
    sub_x['Vmax'] = sub_x.rolling(5).V.max()
    sub_x['HB'] = (1-(sub_x.C-sub_x.O).abs()/(sub_x.H-sub_x.L))*(sub_x.V/sub_x.Vmax)
    sub_x['NewRVS'] = sub_x.RVS * sub_x.HB
    return sub_x

F = r.groupby('ticker').apply(lambda x:cal_factor(x))
F = F.reset_index(drop = True)
F.to_pickle('S112_F01.pkl')