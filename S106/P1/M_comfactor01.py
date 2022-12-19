# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 20:41:13 2022
过去N日累积收益

截面数据
成分股

和文献图1的结果非常相似
@author: adair2019
"""
import pandas as pd
from yq_toolsS45_linux import get_db_data
from sklearn.linear_model import LinearRegression


#parameter
wid = [[1,3],[5,8],[10,20],[20,50],[3,20],[5,50]]
wid1 = []
for tmp in wid:
    wid1.append(tmp[0])
    wid1.append(tmp[1])
wid1 = list(set(wid1))

sql_tmp = 'select * from idxcloseweightget where ticker = "000300" and tradingdate>="2016-12-01" order by tradingdate'
pool = get_db_data('yuqerdata',sql_tmp)
pool.tradingdate = pool.tradingdate.astype(str)
tref_pool = pool.tradingdate.unique().tolist()
tref_pool.sort()

sql_tmp = 'select ticker,tradeDate,closePrice/preClosePrice-1 as r from yq_mktequdadjafget where tradeDate>="2017-01-01"'
x = get_db_data('yuqerdata',sql_tmp)
x.tradeDate = x.tradeDate.astype(str)
x = x.pivot('tradeDate','ticker','r')
x.sort_index(inplace = True)


tref = pd.DataFrame({0:x.index})
for tmp in wid1:
    tref[tmp] = tref[0].shift(tmp)
tref.index = x.index

#Test
B = []
for t in ['2022-07-11','2022-07-12']:
    v = tref.loc[t]
    tmp = max([i for i in tref_pool if i<=t])
    sub_symbol = pool[pool.tradingdate==tmp].symbol.tolist()
    sub_x = x[sub_symbol].copy()
    #组织变量
    #sub_x.fillna(0,inplace=True)
    x1 = []
    for i,sub_wid in enumerate(wid):
        sub_wid1,sub_wid2 = sub_wid
        sub_t1,sub_t2 = v[sub_wid1],v[sub_wid2]
        tmp = sub_x.loc[sub_t2:sub_t1]
        tmp = (1+tmp).cumprod(skipna=False)
        tmp = tmp.iloc[-1]-1
        x1.append(pd.DataFrame({i:tmp},index=sub_x.columns))
    x1 = pd.concat(x1,axis=1)
    y1 = sub_x.loc[t]
    
    x1.dropna(inplace=True)
    y1 = y1.loc[x1.index.tolist()]
    #多元线性回归
    model = LinearRegression()
    model.fit(x1,y1)
    
    a = model.intercept_  # 截距
    b = model.coef_  # 回归系数
    B.append(pd.DataFrame({t:b}))
B = pd.concat(B,axis=1)