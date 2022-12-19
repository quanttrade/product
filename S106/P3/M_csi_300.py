# -*- coding: utf-8 -*-
"""
Created on Sat Sep 17 16:13:15 2022

@author: adair2019
"""

import pandas as pd
from bac_toolS106P3 import get_s106p3_sig2
from yq_toolsS45_linux import get_db_data,MktIdxdGet
from tqdm import tqdm


df = pd.read_pickle('data1.pkl')
df.rename(columns={'closeIndex': 'close', 'openIndex': 'open' }, inplace=True)
df = df[['tradeDate','close']]


sql_tmp = 'select * from idxcloseweightget where ticker = "000300" and tradingdate>="2015-01-01" order by tradingdate'
pool = get_db_data('yuqerdata',sql_tmp)
pool.tradingdate = pool.tradingdate.astype(str)
tref_pool = pool.tradingdate.unique().tolist()
tref_pool.sort()

sql_tmp = 'select ticker,tradeDate,closePrice as `close` from yq_mktequdadjafget where tradeDate>="2014-01-01"'
x = get_db_data('yuqerdata',sql_tmp)
x.tradeDate = x.tradeDate.astype(str)

tickers = pool[pool.tradingdate==pool.tradingdate.min()].symbol.unique().tolist()
r = []
for ticker in tqdm(tickers):
    sub_x = x[x.ticker==ticker].copy()
    if len(sub_x)>200:
        sub_x.sort_values('tradeDate',inplace=True)
        sub_x.reset_index(drop=True,inplace=True)
        sub_r = get_s106p3_sig2(sub_x)
        r.append(sub_r)
    
r=pd.concat(r)
r['f'] = r.sig2*r.r
#r['tradeDate'] = r.index
#del r['tradeDate']
r1 = r.groupby('tradeDate').r.mean()
r1.sort_index(inplace=True)

(1+r1).cumprod().plot(rot=30)

r0 = MktIdxdGet('000016',min(r.index),max(r.index),'tradeDate,CHGPct as r0')
r0.tradeDate = r0.tradeDate.astype(str)
r0.set_index('tradeDate',inplace=True,drop=True)

r1.name='s106'

r1 = r1.to_frame().merge(r0,left_index=True,right_index=True)
(1+r1).cumprod().plot(rot=30)