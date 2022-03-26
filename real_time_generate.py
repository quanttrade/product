# -*- coding: utf-8 -*-
"""
Created on Tue Nov 23 10:06:48 2021
S87回测框架
国内指数成分股回测工具




@author: adair-9960
"""
from yq_toolsS45_linux import get_MktEqudAdjAfGet_update
from tqdm import tqdm
import os
import pickle
import pandas as pd
from yq_toolsS45_linux import get_db_data,get_iso_index_data_68
from yq_toolsS45_linux import engine37,get_fee_info
from s1_deap_result import toolbox
import numpy as np
import matplotlib.pyplot as plt
from yq_toolsS45_linux import get_iso_ticker_data_68

year_cut = '2020'

csi_index=['000905','000300']
csi_index_v = [1,1]
iso_index = ['as51', 'topix', 'twse', 'hsce', 'kosdaq', 'kospi', 'msci', 'ndx',
 'nifty', 'nky', 'RTY', 'set50', 'sx5e', 'ukx', 'xin9i']
iso_index_v = [2 for i in iso_index]
model_info = dict(zip(csi_index+iso_index,csi_index_v+iso_index_v))
fee1,fee2 = get_fee_info()

pn_model = 'S87_model'


only_long=False

draw_ = True

def get_uq_index_data(index):
    ind = model_info[index]
    if ind==1:
        sql_tmp = 'select * from yq_index where symbol = "%s" and tradeDate>="2010-01-01" order by tradeDate' % (index)
        data = get_db_data('yuqerdata',sql_tmp)
        data.tradeDate = data.tradeDate.astype(str)
        data['CHGPct'].fillna(0,inplace=True)
        data.set_index('tradeDate',inplace=True,drop=True)
        df_x = data[['closeIndex', 'openIndex', 'turnoverVol', 'lowestIndex', 'highestIndex', 'CHGPct']]
        df_y = data.copy()
        df_y['CHGPct_open_b'] = df_y.closeIndex/df_y.openIndex-1
        df_y['CHGPct_open_s'] = df_y.openIndex/df_y.preCloseIndex-1
        df_y = df_y[['CHGPct','CHGPct_open_b','CHGPct_open_s','openIndex','closeIndex']]
        return df_x,df_y

def get_iso_index_data(index_code):
    data = get_iso_index_data_68(index_code,key_str="""tradeDate,openPrice as openIndex,closePrice as closeIndex,
                                 lowPrice as lowestIndex,highPrice as highestIndex,
                                 Volume as turnoverVol""")
    data['CHGPct'] = data.closeIndex.pct_change()
    data.tradeDate = data.tradeDate.astype(str)
    data['CHGPct'].fillna(0,inplace=True)
    data.set_index('tradeDate',inplace=True,drop=True)
    df_x = data[['closeIndex', 'openIndex', 'turnoverVol', 'lowestIndex', 'highestIndex', 'CHGPct']]
    df_y = data.copy()
    df_y['CHGPct_open_b'] = df_y.closeIndex/df_y.openIndex-1
    df_y['CHGPct_open_s'] = df_y.openIndex/df_y.closeIndex.shift(1)-1
    df_y = df_y[['CHGPct','CHGPct_open_b','CHGPct_open_s','openIndex','closeIndex']]
    return df_x,df_y
    

def get_iso_ticker_data(index_code,ticker):
    data = get_iso_ticker_data_68(index_code,ticker,key_str="""tradeDate,openPrice as openIndex,closePrice as closeIndex,
                                 lowPrice as lowestIndex,highPrice as highestIndex,
                                 Volume as turnoverVol""")
    data['CHGPct'] = data.closeIndex.pct_change()
    data.tradeDate = data.tradeDate.astype(str)
    data['CHGPct'].fillna(0,inplace=True)
    data.set_index('tradeDate',inplace=True,drop=True)
    df_x = data[['closeIndex', 'openIndex', 'turnoverVol', 'lowestIndex', 'highestIndex', 'CHGPct']]
    df_y = data.copy()
    df_y['CHGPct_open_b'] = df_y.closeIndex/df_y.openIndex-1
    df_y['CHGPct_open_s'] = df_y.openIndex/df_y.closeIndex.shift(1)-1
    df_y = df_y[['CHGPct','CHGPct_open_b','CHGPct_open_s','openIndex','closeIndex']]
    return df_x,df_y

def get_csi_ticker_data(ticker):
    
    sql_tmp = '''ticker,tradeDate,openPrice as openIndex,highestPrice as highestIndex,lowestPrice as lowestIndex,
    closePrice as closeIndex,turnoverVol'''
    data = get_MktEqudAdjAfGet_update(ticker,'2012-01-01','2099-01-01',sql_tmp)
    data['CHGPct'] = data.closeIndex.pct_change()
    data.tradeDate = data.tradeDate.astype(str)
    data['CHGPct'].fillna(0,inplace=True)
    data.set_index('tradeDate',inplace=True,drop=True)
    df_x = data[['closeIndex', 'openIndex', 'turnoverVol', 'lowestIndex', 'highestIndex', 'CHGPct']]
    df_y = data.copy()
    df_y['CHGPct_open_b'] = df_y.closeIndex/df_y.openIndex-1
    df_y['CHGPct_open_s'] = df_y.openIndex/df_y.closeIndex.shift(1)-1
    df_y = df_y[['CHGPct','CHGPct_open_b','CHGPct_open_s','openIndex','closeIndex']]
    return df_x,df_y


def get_TW_ticker_data(index_code,ticker):
    pn = 'csv_%s' % index_code
    fn = '%s-%s.csv' % (index_code,ticker)
    fn = os.path.join(pn,fn)
    data =pd.read_csv(fn,index_col=0,dtype={'ticker':str})
    dtype = dict(zip(['openPrice','highPrice','lowPrice','closePrice','Volume'],
                     ['openIndex','highestIndex','lowestIndex','closeIndex','turnoverVol']))
    data.rename(columns = dtype,inplace=True)
    data['CHGPct'] = data.closeIndex.pct_change()
    data.tradeDate = data.tradeDate.astype(str)
    data['CHGPct'].fillna(0,inplace=True)
    data.set_index('tradeDate',inplace=True,drop=True)
    df_x = data[['closeIndex', 'openIndex', 'turnoverVol', 'lowestIndex', 'highestIndex', 'CHGPct']]
    df_y = data.copy()
    df_y['CHGPct_open_b'] = df_y.closeIndex/df_y.openIndex-1
    df_y['CHGPct_open_s'] = df_y.openIndex/df_y.closeIndex.shift(1)-1
    df_y = df_y[['CHGPct','CHGPct_open_b','CHGPct_open_s','openIndex','closeIndex']]
    return df_x,df_y


def back_test_f1(y,t_fee1=0,t_fee2=0):
    
    #add new_col
    y.loc['2099-01-01'] = np.nan
    
    y['do_order']= 'keep'
    y['r'] = 0
    #一般情况,今天的执行信号
    y.r = y.sig.shift(1) * y.CHGPct
    #建仓情况，当天信号为1，昨天信号为0
    y.loc[(y.sig.shift(1)==1)&(y.sig.shift(2)==0),'r'] =y.loc[(y.sig.shift(1)==1)&(y.sig.shift(2)==0),'CHGPct_open_b'] -t_fee1
    y.loc[(y.sig.shift(1)==1)&(y.sig.shift(2)==0),'do_order'] = '开盘建仓'
    
    y.loc[(y.sig.shift(1)==-1)&(y.sig.shift(2)==0),'r'] =-y.loc[(y.sig.shift(1)==-1)&(y.sig.shift(2)==0),'CHGPct_open_b'] -t_fee1 
    y.loc[(y.sig.shift(1)==-1)&(y.sig.shift(2)==0),'do_order'] = '开盘建仓'
    
    #平仓情况，当天信号为0，昨天信号为1
    y.loc[(y.sig.shift(1)==0)&(y.sig.shift(2)==1),'r'] =y.loc[(y.sig.shift(1)==0)&(y.sig.shift(2)==1),'CHGPct_open_s'] -t_fee2
    y.loc[(y.sig.shift(1)==0)&(y.sig.shift(2)==1),'do_order'] = '开盘平仓'
    
    y.loc[(y.sig.shift(1)==0)&(y.sig.shift(2)==-1),'r'] = -y.loc[(y.sig.shift(1)==0)&(y.sig.shift(2)==-1),'CHGPct_open_s'] -t_fee1
    y.loc[(y.sig.shift(1)==0)&(y.sig.shift(2)==-1),'do_order'] = '开盘平仓'
    return y


if __name__ == "__main__":
    '''
    import random
    from ib_insync import *
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=random.randint(1,1000))
    print('start interactive broker')
    
    contract = Future('ES','20220617','GLOBEX')
    '''
    from datetime import datetime, date, time
    from pandas.tseries.offsets import BDay
    today = datetime.today()
    prev = (today - BDay(10))
    import pybbg
    bbg = pybbg.Pybbg()
    ticker = 'ESM2 Index'
    fld_list = ['close']
    data_pd = bbg.bdib(ticker, fld_list, prev, today, eventType='TRADE', interval = 30)

    index_code = 'TW'
    
    sub_fee1 = 0.00001
    sub_fee2 = 0.00001
    
    pn_model = 'model_%s' % index_code    
    key_model =os.path.join(pn_model,'%s.pkl' % index_code) 
    model = pickle.load(open(key_model, 'rb'))
    tickers = list(model.keys())
    #tickers.sort()
    tickers = ['HSI']
    
    Y = []
    for sub_ticker in tickers:
        #import model
        bests = model[sub_ticker]
        if len(bests)>0:
            x,y0 = get_TW_ticker_data(index_code,sub_ticker)   
            func_p = toolbox.compile(bests)
            pred_ser = func_p(*[x[col] for col in x.columns])
            signal_up = (pred_ser > pred_ser.rolling(60).quantile(0.8)).astype(int)
            signal_down = (pred_ser < pred_ser.rolling(60).quantile(0.2)).astype(int)
            signal = signal_down - signal_up
            signal.name='sig'
            if only_long:
                signal[signal<0] = 0
            
            y = pd.concat([signal,y0],axis=1)
            y.sort_index(inplace=True)    
            y = back_test_f1(y.copy(),sub_fee1,sub_fee2)
            if draw_:
                (1+y[year_cut:].r).cumprod().plot(figsize=(14,7),title=sub_ticker)
                plt.show()
            #record result
            tmp = y.copy()
            tmp['index_code'] = index_code
            tmp['ticker'] = sub_ticker
            tmp.index.name='tradeDate'
            Y.append(tmp.reset_index())
    Y = pd.concat(Y)
    #Y.to_sql('s87_result',engine37,if_exists='replace',index=False,chunksize=10000)
    Y.to_excel('%s_signal.xlsx' % index_code)
    
    tmp = Y.set_index(['tradeDate','ticker'])[['sig']].unstack().droplevel(0,axis=1)
    tmp.to_excel('S87_%s_信号.xlsx' % index_code)
    y = Y.set_index(['tradeDate','ticker'])[['r']].unstack().droplevel(0,axis=1)
    
    y = y.loc[year_cut:]
    (1+y.mean(axis=1)).cumprod().plot(figsize=(14,7),title=index_code)
    (1+y.mean(axis=1)).cumprod().to_excel('%s_com_cureve.xlsx' % index_code)
    #(1+y.sum(axis=1)/y.shape[1]).cumprod().plot(figsize=(14,7),title=index_code)
    '''
    #对冲指数结果
    tmp2,_ = get_uq_index_data(index_code)
    tmp1 = y.mean(axis=1)
    tmp1.name = 'r0'
    tmp2 = tmp2[['CHGPct']]
    tmp2.columns=['r1']
    
    tmp3 = pd.concat([tmp1,tmp2],axis=1)
    tmp3 = tmp3[tmp3.index.isin(tmp1.index.tolist())]
    tmp3 = tmp3.iloc[:-1]
    tmp3['r'] = tmp3.r0-tmp3.r1
    tmp3.iloc[0] = 0
    (1+tmp3).cumprod().plot(figsize=(14,7),title=index_code)
    '''