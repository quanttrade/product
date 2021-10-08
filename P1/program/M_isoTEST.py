# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 17:41:42 2021

@author: adair2019
"""
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import pandas as pd
from S84_P1 import get_iso_index_info,get_iso_index_data
from yq_toolsS45 import save_pickle
#fee
fee = 1/1000
#fee = 0

#os.system('python S84_P1.py')
def get_fee(x):
    #x = x[x.ticker=='000001'].copy()
    x['fee1'] = 0
    x['fee2'] = 0
    #oo执行，信号延迟2天执行
    #当日信号！=前一天信号，执行买或这卖
    x.loc[(x.sig.shift(2)!=x.sig.shift(3)) & (x.sig.shift(2)==1),'fee1'] = 1 #buy
    x.loc[(x.sig.shift(2)!=x.sig.shift(3)) & (x.sig.shift(2)==0),'fee2'] = 1 #sell
    return x

index_tdx,fee1,fee2 = get_iso_index_info()
index_iso = list(index_tdx.keys())

result = {}
for index_code in index_iso:
    fn = 's84p1_csi%s.pkl' % index_code
    if os.path.exists(fn):
        x = pd.read_pickle(fn)
        y0 = get_iso_index_data(index_code)
        y0 = y0[['chgPct']]
        if index_code =='hsi':
            sub_fee1 = fee1['HK']/10000
            sub_fee2 = fee2['HK']/10000
        else:
            sub_fee1 = fee1[index_code]/10000
            sub_fee2 = fee2[index_code]/10000
        
        X = []
        ticker = x.ticker.unique().tolist()
        for sub_ticker in tqdm(ticker):
            sub_x = x[x.ticker==sub_ticker].copy()
            X.append(get_fee(sub_x))

        x = pd.concat(X)
        x.loc[x.oo.abs()>0.4,'oo']=0
        x['oo'] = x.oo-x.fee1*sub_fee1 - x.fee2 * sub_fee2
        
        x.reset_index(inplace=True)
        x.set_index(['tradeDate','ticker'],inplace=True)
        x0 = x.copy()
        x = x[['oo']].unstack()
        x = x.droplevel(0,axis=1)
        #做法2 平均分配
        #r = x.sum(axis=1)/x.shape[1]
        #做法1 单独有仓位的统计
        tmp = x.fillna(0)
        r1 = tmp.sum(axis=1)
        r2 = tmp!=0
        r2 = r2.sum(axis=1)
        r2[r2==0]=1
        r = r1/r2        
        r.name = 'strategy'
        
        y0 = pd.concat([y0,r],axis=1)
        y0.sort_index(inplace=True)
        y0.drop_duplicates(inplace=True)
        y0['strategy-index'] = y0.strategy-y0.chgPct
        y0= y0[y0.index>'2010-01-01']
        y0.iloc[0]=0
        
        (1+y0).cumprod().plot(figsize=(14,7),title=index_code)
        plt.show()
        
        result[index_code] = y0
save_pickle('tmp1.pkl',result)

