# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 20:41:13 2022
合成截面系数因子
预测未来1天的收益

移动平均 如何处理？
这里使用移动平均收益建模

收益建模，用价格带入计算，这个奇怪奇怪

@author: adair2019
"""
import pandas as pd
from yq_toolsS45_linux import get_db_data
from sklearn.linear_model import LinearRegression
from tqdm import tqdm
from yq_toolsS45_linux import get_week_month_tradeDate_update as get_tref
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus'] = False

#parameter
wid = [[1,3],[5,8],[10,20],[20,50],[3,20],[5,50]]
wid1 = []

N = 10

for tmp in wid:
    wid1.append(tmp[0])
    wid1.append(tmp[1])
wid1 = list(set(wid1))

sql_tmp = 'select * from idxcloseweightget where ticker = "000300" and tradingdate>="2016-12-01" order by tradingdate'
pool = get_db_data('yuqerdata',sql_tmp)
pool.tradingdate = pool.tradingdate.astype(str)
tref_pool = pool.tradingdate.unique().tolist()
tref_pool.sort()

sql_tmp = 'select ticker,tradeDate,closePrice/preClosePrice-1 as r,closePrice from yq_mktequdadjafget where tradeDate>="2017-01-01"'
x = get_db_data('yuqerdata',sql_tmp)
x.tradeDate = x.tradeDate.astype(str)

x_m = x.pivot('tradeDate','ticker','closePrice')
x_m.sort_index(inplace = True)
x_m = x_m.rolling(20).mean()
x = x.pivot('tradeDate','ticker','r')
x.sort_index(inplace = True)

#未来期望的截面收益率
R = (1+x).cumprod()
R = R.shift(-N)/R-1
R['t']=R.index
R.t = R.t.shift(-N)
R.dropna(subset=['t'],inplace=True)
t_map = dict(zip(R.index,R.t))




tref = pd.DataFrame({0:x_m.index})
for tmp in wid1:
    tref[tmp] = tref[0].shift(tmp)
tref.index = x.index

#Test
tref2 = tref.dropna().index.tolist()
tmp = R.index.tolist()
tref2 = list(set(tref2)&set(tmp))
tref2 = [i for i in tref2 if i >='2017-05-19']
tref2.sort()
B = []
for t in tqdm(tref2):
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
    y1.dropna(inplace=True)
    x1 = x1.loc[y1.index.tolist()]
    
    #多元线性回归
    model = LinearRegression()
    model.fit(x1,y1)
    
    a = model.intercept_  # 截距
    b = model.coef_  # 回归系数
    tmp = pd.DataFrame({t_map[t]:b.tolist()+[a]})
    B.append(tmp.T)
B = pd.concat(B)

#从2017-05-19选股，持有2周，然后下个周末再次选股
_,tref_w,_,_ = get_tref('2017-06-06','3033-01-01')
#
tref_w = tref_w[::2]
BF = B.rolling(9).mean()
r = []
r1 = []
for t1,t2 in zip(tref_w[:-1],tref_w[1:]):
    sub_b = BF.loc[t1]
    model = LinearRegression()
    model.intercept_ = sub_b.iloc[-1]
    model.coef_ = sub_b.iloc[:-1].values
    #get X
    v = tref.loc[t1]
    tmp = max([i for i in tref_pool if i<=t1])
    sub_symbol = pool[pool.tradingdate==tmp].symbol.tolist()
    sub_x = x_m[sub_symbol].copy()
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
    x1.dropna(inplace=True)
    p = model.predict(x1)
    p = pd.DataFrame({'y':p},index=x1.index)
    p.sort_values('y',inplace=True)
    
    symbol_sel = p.iloc[:30].index.tolist()
    #recored bac
    sub_x2 = x[symbol_sel]
    sub_x2 = sub_x2.loc[t1:t2].copy()
    #sub_x2 = sub_x2.iloc[1:]
    #sub_x2.iloc[0] = 0
    sub_x2 = (1+sub_x2).cumprod()
    sub_x2 = sub_x2.sum(axis=1).pct_change()
    sub_x2 = sub_x2.iloc[1:]
    r.append(sub_x2)
    
    symbol_sel = p.iloc[-30:].index.tolist()
    #recored bac
    sub_x2 = x[symbol_sel]
    sub_x2 = sub_x2.loc[t1:t2].copy()
    #sub_x2 = sub_x2.iloc[1:]
    #sub_x2.iloc[0] = 0
    sub_x2 = (1+sub_x2).cumprod()
    sub_x2 = sub_x2.sum(axis=1).pct_change()
    sub_x2 = sub_x2.iloc[1:]
    r1.append(sub_x2)
    
y=pd.concat(r)
y.name = 'r'
y = y.to_frame()
#y = -y
(1+y.fillna(0)).cumprod().plot()

y0=pd.concat(r1)
y0.name = 'r1'
y0 = y0.to_frame().merge(y,left_index=True,right_index=True)
y0['rf'] =y0.r1-y0.r
y0_tmp = y0.rename(columns = dict(zip(['r1', 'r', 'rf'],['多','空','多空对冲'])))
(1+y0_tmp).cumprod().plot(rot=30)

sql_tmp = 'select tradeDate,chgPct as r0 from yq_index where symbol = "000300" and tradeDate >="2017-05-17" order by tradeDate'
r0 = get_db_data('yuqerdata',sql_tmp)
r0.tradeDate = r0.tradeDate.astype(str)
r0.set_index('tradeDate',inplace=True)

y1= y0.merge(r0,left_index=True,right_index=True)
y1['v'] = y1.r1-y1.r0
y1_tmp=y1.rename(columns = dict(zip(['r1', 'r0', 'v'],['策略多','指数','策略对冲指数'])))
(1+y1_tmp[['策略多','指数','策略对冲指数']]).cumprod().plot(rot = 30)