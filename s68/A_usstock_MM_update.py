# -*- coding: utf-8 -*-
"""
Created on Sat Mar 27 22:34:38 2021
分钟数据对接

对接到sqlight中

获取美股历史数据
PNL名字文件无法新建 需要做一个映射
b.loc['A1']=2
['BZZST', 'LMOSV', 'PRN', 'PTEST.Z', 'ZNWAA', 'ZOZZT', 'ZZK']
没有数据
@author: adair2019
"""
from tqdm import tqdm
import os
import sqlite3
import sqlalchemy as sa
from sqlalchemy import create_engine

from yq_toolsS45 import get_file_name
from yq_toolsS45 import time_use_tool

from Polygon_updateV2 import get_aggregates_tick
from multiprocessing.dummy import Pool as ThreadPool
from yq_toolsS45 import engine_db_polygon as eg_po,save_pickle,read_pickle
import pandas as pd
import json

num_core=32
obj_t = time_use_tool()
#pn = r'F:\datasets\polygon_min_stock'

with open('para.json','r',encoding='utf-8') as f:
    para = json.load(f)
p2 = para['sql3_usstock']

dtypes = {'turnoverVol': sa.FLOAT,
 'vw': sa.FLOAT,
 'openPrice': sa.FLOAT,
 'closePrice': sa.FLOAT,
 'highPrice': sa.FLOAT,
 'lowPrice': sa.FLOAT,
 'tradeDate': sa.DATETIME,
 'ticker': sa.VARCHAR(12)}

def split_num(N1,N2):
    L= [i for i in range(0,N1,N2)]
    if N1 not in L:
        L.append(N1)
    return L

#执行sqlight 语句
def do_sqlight_order(db,order_str):
    with sqlite3.connect(db) as con:
        cur =  con.cursor()
        cur.execute(order_str)
        con.commit()


def iswrongticker(ticker):
    return  '\x00' in ticker or '�' in ticker

def get_MM_date(ticker):
    t_ini = '2000-01-01'
    fn = os.path.join(p2,'%s.db3' % ticker)
    if os.path.exists(fn):
        with sqlite3.connect(fn) as conn:
            x = pd.read_sql_query('select max(tradeDate) from `%s`;' % ticker,conn)
            if len(x)>0:
                t0=x.iloc[0,0]
                if t0 is None:
                    t0 = t_ini
            else:
                t0 = t_ini
    else:
        t0 = t_ini
    print('%s-t0:%s' % (ticker,t0))
    return t0

#先读取时间，再下载数据，再写入，三步
def MM_flow1(x):
    ticker,t0 = x
    #t0 = get_MM_date(ticker)
    t0_0 = t0[:10]
    try:
        x=get_aggregates_tick(ticker, t0_0,'2033-03-27', multiplier=1, 
                              timespan='minute',client=None,unadjusted=True,P0=50000)
        #save
        if len(x)>0:
            x = x[x.tradeDate>t0]
            if len(x)>0:
                #to mysql
                tmp_eg = create_engine('sqlite:///%s' % (os.path.join(p2,'%s.db3' % ticker)))
                x.tradeDate=pd.to_datetime(x.tradeDate)
                x.to_sql(ticker,tmp_eg,index=False,if_exists='append',dtype=dtypes)
                sub_re = pd.DataFrame({'ticker':[ticker],'t0':[x.tradeDate.astype(str).max()]})
                x=None #释放内存
                return sub_re
            else:
                return pd.DataFrame({'ticker':[ticker],'t0':[t0]})
        return pd.DataFrame({'ticker':[ticker],'t0':[t0]})
    except:
        return pd.DataFrame({'ticker':[ticker],'t0':[t0]})

def MM_flow2(ticker):
    if not isinstance(ticker,str):
        ticker,_ = ticker
    t0 = get_MM_date(ticker)
    t0_0 = t0[:10]
    try:
        x=get_aggregates_tick(ticker, t0_0,'2033-03-27', multiplier=1, 
                              timespan='minute',client=None,unadjusted=True,P0=50000)
        #save
        if len(x)>0:
            x = x[x.tradeDate>t0]
            if len(x)>0:
                #to mysql
                tmp_eg = create_engine('sqlite:///%s' % (os.path.join(p2,'%s.db3' % ticker)))
                x.tradeDate=pd.to_datetime(x.tradeDate)
                x.to_sql(ticker,tmp_eg,index=False,if_exists='append',dtype=dtypes)
                sub_re = pd.DataFrame({'ticker':[ticker],'t0':[x.tradeDate.astype(str).max()]})
                x=None #释放内存
                return sub_re
            else:
                return pd.DataFrame({'ticker':[ticker],'t0':[t0]})
        return pd.DataFrame({'ticker':[ticker],'t0':[t0]})
    except:
        return pd.DataFrame({'ticker':[ticker],'t0':[t0]})
    
def download_data(x):
    ticker,t0 = x
    t0_0 = t0[:10]
    try:
        x=get_aggregates_tick(ticker, t0_0,'2033-03-27', multiplier=1, 
                              timespan='minute',client=None,unadjusted=True,P0=50000)
        x=x[x.tradeDate>t0]
        print('download %s-%s complete' % (ticker,x.tradeDate.max()))
        return x
    except:
        print('download %s-%s complete' % (ticker,t0))
        return pd.DataFrame()

#get newest date
#时间特别长，开并行会有嘎吱嘎吱声音
def get_com_date():
    _,ticker_com = get_file_name(p2,'.db3')
    ticker_com = [i.replace('.db3','') for i in ticker_com]
    #获取日期
    pool = ThreadPool(processes=10)
    t0 = pool.map(get_MM_date, ticker_com)
    pool.close()
    pool.join()
    #t0 = []
    #for ticker in tqdm(ticker_com):
    #    t0.append(get_MM_date(ticker))
    result = pd.DataFrame({'ticker':ticker_com,'t0':t0})
    return result
if __name__ == "__main__":
    #并行更新测试
    run_mod = 1;
    #1 多线程模式
    #2 单线程模式
    t0_start = '2000-01-01'
    t0_start1 = '2021-03-01'
    sql_tmp = 'select distinct(ticker) from usastock_day where tradeDate>="%s"' % t0_start1
    ticker = pd.read_sql(sql_tmp,eg_po)
    ticker = ticker[ticker.columns[0]].tolist()
    ticker = [i for i in ticker if not iswrongticker(i)]
    
    t0_com = read_pickle(os.path.join(r's47_para','stock_MM_t0.pkl'))
    if 'ticker' in t0_com.columns.tolist():
        t0_com.set_index('ticker',inplace=True)
    ticker_tmp =t0_com.index.tolist()
    
    t_p = []
    for sub_ticker in ticker:
        if sub_ticker in ticker_tmp:
            t_p.append(t0_com.loc[sub_ticker].t0)
        else:
            t_p.append(t0_start)
    
    if run_mod==1:
        
        N = len(ticker)
        L = split_num(N,100)        
        x = []
        for sub_L1,sub_L2 in zip(L[:-1],L[1:]):
            pool = ThreadPool(processes=num_core)
            tmp = pool.map(MM_flow1, zip(ticker[sub_L1:sub_L2],t_p[sub_L1:sub_L2]))
            pool.close()
            pool.join()
            x = x+tmp
        print('complete %d-%d ' % (sub_L1,sub_L2))
        
    else:
        x = []
        for sub_ticker in tqdm(ticker):
            x.append(MM_flow2(sub_ticker))
    save_pickle('update_t0.pkl',x) #需要用于更新时间        
    x=pd.concat(x)
    x1,x2 = x.ticker.tolist(),x.t0.tolist()
    for sub_x1,sub_x2 in zip(x1,x2):
        t0_com.loc[sub_x1] = sub_x2    
    save_pickle(os.path.join(r's47_para','stock_MM_t0.pkl'),t0_com)    
    obj_t.use('一共耗时：')