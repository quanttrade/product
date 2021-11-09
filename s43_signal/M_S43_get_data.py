# -*- coding: utf-8 -*-
"""
Created on Tue Oct 19 12:07:08 2021

@author: adair-9960
"""

from pytdx.hq import TdxHq_API 
import datetime
import numpy as np
import pandas as pd
import akshare as ak
import time
from tqdm import tqdm
from yq_toolsS45_linux import get_db_data,time_use_tool,get_table_date
from yq_toolsS45_linux import eg_datapro as eg_pro
t0 = str(datetime.datetime.now().date())
disp_time = True
obj_t = time_use_tool()
import datetime

def arange_tdx_data(x_tdx):
    o = x_tdx.iloc[0].open
    c = x_tdx.iloc[-1].close
    h = x_tdx.high.max()
    l = x_tdx.low.min()
    v = x_tdx.vol.sum()/100
    a = x_tdx.amount.sum()
    v2 = np.nan
    p = pd.DataFrame({'open':o,'high':h,'low':l,'close':c,
                      'volume':v,'amount':a,'volume2':v2},index=[1])
    return p


def get_data_tdx(ticker='000001',t0=t0,N=4):
    t0_do = datetime.datetime.now()  
    p = pd.DataFrame()
    if ticker[0]=='6':
        mark_code=1
        ticker_mark = 'sh'
    else:
        mark_code=0
        ticker_mark = 'sz'
    api = TdxHq_API()
    with api.connect('119.147.212.81', 7709):
        x_tdx=api.to_df(api.get_security_bars(3,mark_code,ticker, 0,N))
        if x_tdx.shape[1]>0:
            x_tdx = x_tdx[x_tdx.hour<12]
            if len(x_tdx)>0:
                x_tdx['tradingdate'] = x_tdx.datetime.apply(lambda x:x[:10])
                x_tdx.sort_values('datetime',inplace=True)
                
                p=x_tdx.groupby('tradingdate').apply(lambda x:arange_tdx_data(x))
                p['symbol'] = '%s%s' % (ticker_mark,ticker)
                p = p.droplevel(1)
                p.reset_index(inplace=True)
                p = p[p.tradingdate>=t0]
    if disp_time:
        print(datetime.datetime.now()-t0_do)
    return p
    
def get_data_ak(ticker='000001',t0=t0):

    t0_do = datetime.datetime.now()                
    p = pd.DataFrame()
    if ticker[0]=='6':
        mark_code='sh'
    else:
        mark_code='sz'
    x_ak = ak.stock_zh_a_minute('%s%s' % (mark_code,ticker),'60')
    if len(x_ak)>0:
        x_ak=x_ak[(x_ak['day']>=('%s 00:00:00' % t0)) & (x_ak['day']<=('%s 12:00:00' % t0))]
        if len(x_ak)>0:
            x_ak.sort_values('day',inplace=True)
            o = float(x_ak.iloc[0].open)
            c = float(x_ak.iloc[-1].close)
            h = x_ak.high.astype(float).max()
            l = x_ak.low.astype(float).min()
            v = x_ak.volume.astype(float).sum()/100
            a = np.nan
            v2 = np.nan
            p = pd.DataFrame({'open':o,'high':h,'low':l,'close':c,
                                  'volume':v,'amount':a,'volume2':v2,'tradingdate':t0},index=[ticker])
    if disp_time:
        print(datetime.datetime.now()-t0_do)
    return p

#get history data
def get_tdx_history():
    sql_str = """select distinct(ticker)  from equget
                where equTypeCD = "A" and listStatusCD ="L" and 
                ListSectorCD<=3 and length(ticker)=6  order by ticker"""
    x = get_db_data('yuqerdata',sql_str) 
    ticker = x.ticker.tolist()
    X = []
    max_try = 3
    E = []
    for sub_ticker in tqdm(ticker):
        i = 0
        while i < max_try:
            try:
                x = get_data_tdx(sub_ticker,N=800,t0='1900-01-01')
                i = 100
                OK=True
            except:
                i=i+1
                OK = False
                time.sleep(3)
        if OK:
            X.append(x)
        else:
            E.append(sub_ticker)
        time.sleep(0.03)
    Y = pd.concat(X)
    Y.to_pickle('S43_sec_data.pkl')
    obj_t.use()

def update_tdx_now():
    tmp = datetime.datetime.now()
    v = tmp.hour * 100 + tmp.minute
    #这里应该加一个是否数据已经更新
    tn = 'tdx_data_s43'
    tn_t0 = get_table_date(tn,'data_pro','tradingdate')    
    #may be bug if not exist table
    if v>1132 and tmp.weekday()<=4 and t0>tn_t0:
        #get history data
        sql_str = """select distinct(ticker)  from equget
                    where equTypeCD = "A" and listStatusCD ="L" and 
                    ListSectorCD<=3 and length(ticker)=6  order by ticker"""
        x = get_db_data('yuqerdata',sql_str) 
        ticker = x.ticker.tolist()
        X = []
        max_try = 3
        E = []
        for sub_ticker in tqdm(ticker):
            i = 0
            while i < max_try:
                try:
                    x = get_data_tdx(sub_ticker,N=10,t0='1900-01-01')
                    i = 100
                    OK=True
                except:
                    i=i+1
                    OK = False
                    time.sleep(3)
            if OK:
                X.append(x)
            else:
                E.append(sub_ticker)
            time.sleep(0.03)
        Y = pd.concat(X)
        #Y.to_pickle('S43_sec_data.pkl')
        #to mysql
        Y=Y[Y.tradingdate>tn_t0]
        if len(Y)>0:
            Y.to_sql(tn,eg_pro,if_exists='append',index=False,chunksize=3000)
            OK=True
        else:
            OK=False
        obj_t.use('update tdx data complete')
    else:
        OK=False
    return OK
if __name__ == "__main__":        
    update_tdx_now()