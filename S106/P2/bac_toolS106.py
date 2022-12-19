# -*- coding: utf-8 -*-
"""
Created on Wed Sep 14 10:40:42 2022

@author: adair2019
"""
from yq_toolsS45_linux import get_delta_date
import pandas as pd
from yq_toolsS45_linux import get_db_data,MktIdxdGet
from yq_toolsS45_linux import get_week_month_tradeDate_update as get_tref
from S106_weight_tool import MVSKT2,MVSK
from tqdm import tqdm


sql_tmp = 'select * from idxcloseweightget where ticker = "000016" and tradingdate>="2016-12-01" order by tradingdate'
pool = get_db_data('yuqerdata',sql_tmp)
pool.tradingdate = pool.tradingdate.astype(str)
tref_pool = pool.tradingdate.unique().tolist()
tref_pool.sort()

sql_tmp = 'select ticker,tradeDate,closePrice/preClosePrice-1 as r from yq_mktequdadjafget where tradeDate>="2017-01-01"'
x = get_db_data('yuqerdata',sql_tmp)
x.tradeDate = x.tradeDate.astype(str)
x = x.pivot('tradeDate','ticker','r')
x.sort_index(inplace = True)

tref = x.index.tolist()
tref.sort()

r0 = MktIdxdGet('000016',min(tref),max(tref),'tradeDate,CHGPct as r0')
r0.tradeDate = r0.tradeDate.astype(str)
r0.set_index('tradeDate',inplace=True,drop=True)


_,_,t_test,_ = get_tref(tref[0],tref[-1])
if tref[-1]>t_test[-1]:
    t_test.append(tref[-1])
    
r1 = []
for t1,t2 in tqdm(zip(t_test[2:-1],t_test[3:])):
    
    t1_begin = get_delta_date(t1,90)
    sub_pool = pool[pool.tradingdate==t1]    
    sub_pool_ticker = sub_pool.symbol.unique().tolist()
    sub_w = dict(zip(sub_pool.symbol,sub_pool.weight))    
    sub_x = x.loc[t1_begin:t1,sub_pool_ticker].copy()
    sub_x = sub_x.iloc[1:]
    sub_x = sub_x.dropna(axis=1)
    #2 计算权重
    tmp = sub_x.reset_index(drop=True)
    tmp.fillna(0,inplace=True)
    sub_w = tmp.columns.map(sub_w).values
    sub_w = pd.DataFrame({'a':sub_w})
    sub_w.a = sub_w.a/sub_w.a.sum()
    
    w1 = MVSK(tmp)
    w2 = MVSKT2(tmp,sub_w.a.values)
    
    sub_r = x.loc[t1:t2,sub_x.columns].copy()
    sub_r = sub_r.iloc[1:]
    sub_r.iloc[0] = 0
    sub_r1 = w1*((1+sub_r).cumprod())
    sub_r1 = sub_r1.sum(axis=1)
    sub_r1.name = 'MVSK'    
    sub_r2 = w2*((1+sub_r).cumprod())
    sub_r2 = sub_r2.sum(axis=1)
    sub_r2.name = 'MVSKT'
    tmp = pd.concat([sub_r1,sub_r2],axis=1)
    r1.append(tmp.pct_change())    

r1 = pd.concat(r1)
r1.fillna(0,inplace=True)

r = r1.merge(r0,left_index=True,right_index=True)
#(1+r[['r0','MVSKT']]).cumprod().plot(rot=30)
(1+r).cumprod().plot(rot=30)


r2 = r1.copy()
r2.MVSK = r2.MVSK - r.r0 
r2.MVSKT = r2.MVSKT - r.r0
#(1+r2['MVSKT']).cumprod().plot(rot=30)
(1+r2).cumprod().plot(rot=30)