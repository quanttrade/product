# -*- coding: utf-8 -*-
"""
Created on Wed Sep 14 10:40:42 2022
计算实在太慢，保留计算结果
@author: adair2019
"""
from yq_toolsS45_linux import get_back_date
import pandas as pd
from yq_toolsS45_linux import get_db_data,MktIdxdGet
from yq_toolsS45_linux import get_week_month_tradeDate_update as get_tref
from S106_weight_tool import MVSKT2,MVSK
from tqdm import tqdm
from yq_toolsS45_linux import get_tdx_index_info
import numpy as np
import matplotlib.pyplot as plt


#
index_id = [ 'as51', 'hsce', 'hsi', 'kosdaq150' 'kospi', 'msci', 'ndx', 'nifty', 'nky', 'set50','simsci', 'sx5e', 'ukx', 'xin9i']

index_info = get_tdx_index_info()


sql_f1 = 'select ticker,tradeDate,closePrice from main_index_s68 where index_id = "%s"'
for sub_index_id in index_id:
    print(sub_index_id)
    if sub_index_id in list(index_info.keys()):
        x = get_db_data('data_pro',sql_f1 % sub_index_id)
        x.drop_duplicates(subset=['ticker','tradeDate'],inplace=True)
        x.tradeDate = x.tradeDate.astype(str)
        x = x.pivot('tradeDate','ticker','closePrice')
        x.sort_index(inplace = True)
        x = x.pct_change()
        x = x.iloc[1:]
        x[x.abs()>0.5] = 0#这里很重要
        tref = x.index.tolist()
        tref.sort()
        
        sub_index_ticker = index_info[sub_index_id]
        r0 = x[sub_index_ticker]
        del x[sub_index_ticker]
        r0.name = 'r0'
        r0 = r0.to_frame()
        
        
        t_test = pd.DataFrame({'t':r0.index})
        t_test['m'] = t_test.t.apply(lambda x:x[:7])
        t_test = t_test[t_test.m!=t_test.m.shift(-1)]
        #这里末尾的处理需要慎重
        t_test = t_test.t.tolist()
        t_test.sort()
        
        t_test = [i for i in t_test if i>="2018-01-01"]
        
        r1 = []
        _,N = x.shape
        N= int(N/20)
        for t1,t2 in tqdm(zip(t_test[N:-1],t_test[N+1:])):
            t1_begin = get_back_date(t1,int(N*20*1.2),tref)  
            sub_x = x.loc[t1_begin:t1].copy()
            sub_x = sub_x.iloc[1:]
            sub_x = sub_x.dropna(axis=1)
            #2 计算权重
            tmp = sub_x.reset_index(drop=True)
            tmp.fillna(0,inplace=True)
            _,n = tmp.shape
            sub_w = pd.DataFrame({'a':np.ones(n)/n})
            sub_w.a = sub_w.a/sub_w.a.sum()
            #try:
            #    w1 = MVSK(tmp)
            #except:
            w1 = sub_w.a.values
            try:
                w2 = MVSKT2(tmp,sub_w.a.values)
            except:
                w2 = sub_w.a.values
            
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
        (1+r).cumprod().plot(rot=30,title=sub_index_id)
        plt.show()
        
        r2 = r1.copy()
        r2.MVSK = r2.MVSK - r.r0 
        r2.MVSKT = r2.MVSKT - r.r0
        #(1+r2['MVSKT']).cumprod().plot(rot=30)
        (1+r2).cumprod().plot(rot=30,title=sub_index_id)
        plt.show()