# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 17:41:42 2021

@author: adair2019
"""
import os
from yq_toolsS45 import MktIdxdGet
from tqdm import tqdm
import pandas as pd
#fee
fee = 1/1000
#fee = 0

#os.system('python S84_P1.py')
def get_fee(x):
    #x = x[x.ticker=='000001'].copy()
    x['fee'] = 0
    x.loc[x.sig!=x.sig.shift(1),'fee'] = 1
    return x
x = pd.read_pickle('s84p1_csi000300_V2.pkl')
x.index = x.index.astype(str)
x = x[x.index>='2010-01-01']

y0 = MktIdxdGet('000300','2010-01-01','2099-01-01','tradeDate, CHGPct')
y0.tradeDate = y0.tradeDate.astype(str)
y0.set_index('tradeDate',inplace=True)

X = []
ticker = x.ticker.unique().tolist()
for sub_ticker in tqdm(ticker):
    sub_x = x[x.ticker==sub_ticker].copy()
    X.append(get_fee(sub_x))

x = pd.concat(X)
x.loc[x.oo.abs()>0.4,'oo']=0
x['oo'] = x.oo-x.fee*fee

x.reset_index(inplace=True)
x.set_index(['tradeDate','ticker'],inplace=True)
x0 = x.copy()
x = x[['oo']].unstack()
x = x.droplevel(0,axis=1)

r = x.sum(axis=1)/x.shape[1]
r.name = 'stragety'

y0 = pd.concat([y0,r],axis=1)
y0.iloc[0]=0


y0['long-short'] = y0['stragety']-y0['CHGPct']

(1+y0).cumprod().plot(figsize=(14,7))