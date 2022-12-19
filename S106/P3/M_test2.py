# -*- coding: utf-8 -*-
"""
Created on Thu Sep 15 13:12:56 2022

@author: adair2019
"""

from yq_toolsS45_linux import get_db_data
from yq_toolsS45_linux import MktIdxdGet
import pandas as pd



def cal_macd(df,short=12, long=26, dea=9, close='closeIndex'):
    df['EMA_short'] = df[close].ewm(span=short,adjust=False).mean()
    df['EMA_long'] = df[close].ewm(span=long,adjust=False).mean()
    df['DIF'] = df['EMA_short'] - df['EMA_long']
    df['DEA'] = df['DIF'].ewm(span=dea, adjust=False).mean()
    df['MACD'] = (df['DIF'] - df['DEA']) * 2
    del df['EMA_short'], df['EMA_long']
    return df

'''
r0 = MktIdxdGet('000001','2007-01-01','2099-01-01','tradeDate,closeIndex')
r0.tradeDate = r0.tradeDate.astype(str)
r0.set_index('tradeDate',inplace=True,drop=True)
r0.sort_index(inplace=True)
r0.to_pickle('000001.pkl')
'''

x = pd.read_pickle('000001.pkl')

#macd
y = cal_macd(x)