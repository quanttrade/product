# -*- coding: utf-8 -*-
"""
Created on Tue May 26 16:45:10 2020
linux version
@author: adair2019
"""

import math
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import json
from datetime import date,datetime
import pymysql
import warnings
import sys
import time
import os
import multiprocessing
from multiprocessing.dummy import Pool as ThreadPool

from time import strftime, localtime
from datetime import timedelta
import calendar

import pickle

#import matplotlib
#font =matplotlib.font_manager.FontProperties(fname='C:\Windows\Fonts\simkai.ttf')


warnings.filterwarnings('ignore')
num_core = multiprocessing.cpu_count()
#must be set before using
fn1 = 'para.json'
fn2 = 'para_adair.json'
if os.path.exists(fn2):
    fn = fn2
else:
    fn = fn1
with open(fn,'r',encoding='utf-8') as f:
    para = json.load(f)
    
pn = para['yuqerdata_dir']

user_name = para['mysql_para']['user_name']
pass_wd = para['mysql_para']['pass_wd']
port = para['mysql_para']['port']
if 'host' in para['mysql_para'].keys():
    host=para['mysql_para']['host']
else:
    host='localhost'

#,pool_recycle=10600, pool_size=100, max_overflow=20
def create_db(db_ak,host=host):
    eng_str='mysql+pymysql://%s:%s@%s:%d/%s?charset=utf8' % (user_name,pass_wd,host,port,db_ak)
    eg_ak = create_engine(eng_str,pool_recycle=10600, pool_size=100, max_overflow=20)
    return eg_ak


db_yq = 'yuqerdata'
engine = create_db(db_yq)

db_tdx = 'pytdx_data'
eg_tdx = create_db(db_tdx)

db_name23 = 's23'
eg_23 = create_db(db_name23)

db_name31 = 's31'
eg_31 = create_db(db_name31)

db_name40 = 's40'
eg_40 = create_db(db_name40)
#
db_40index = 's40_america'
eg_40index = create_db(db_40index)

db_name42 = 's42'
engine42 = create_db(db_name42)

db_name46 = 's46'
engine46 = create_db(db_name46)

db_name48 = 's48'
engine48 = create_db(db_name48)

db_name49 = 's49'
engine49 = create_db(db_name49)

db_name37 = 's37'
engine37 = create_db(db_name37)

db_name_us = 'us_stock'
engine_us = create_db(db_name_us)

db_name_polygon_fx_minute= 'polygon_fx_minute'
engine_db_name_polygon_fx_minute = create_db(db_name_polygon_fx_minute)

#polygon
db_name_polygon= 'polygon'
engine_db_polygon = create_db(db_name_polygon)

db_name_yq_cub = 'yuqer_cubdata_update'
engine_yq_cub = create_db(db_name_yq_cub)

db_para = 'parapool'
engine_para = create_db(db_para)

db_usindexmin = 'foreign_index_min'
eb_usindminu = create_db(db_usindexmin)

db_datapro = 'data_pro'
eg_datapro = create_db(db_datapro)

db_ak = 'aksharedata'
eg_ak = create_db(db_ak)



def get_db_data(dbname='yuqerdata',order1='show tables'):
    eg = pymysql.connect(host=host,user=user_name,password=pass_wd,database=dbname)
    tmp = pd.read_sql(order1,eg)
    eg.commit()
    eg.close()
    return tmp


sql_str_select_data1 = '''select %s from yq_dayprice where symbol="%s" and tradeDate>="%s"
    and tradeDate<="%s" order by tradeDate'''
sql_str_select_data2 = '''select %s from MktEqudAdjAfGet where ticker="%s" and tradeDate>="%s"
    and tradeDate<="%s" order by tradeDate'''

#need update
def get_inidata(tn,key_str='tradeDate',eg=engine):
    sql_str = 'select %s from %s order by %s desc limit 1'
    t = pd.read_sql(sql_str % (key_str,tn,key_str),eg)
    if len(t)>0:
        t = t[t.columns[0]].astype(str).values[0]
    else:
         t = '1989-01-01'
    return t

def get_file_name(file_dir,file_type):
    L=[]
    L_s = []   
    for root, dirs, files in os.walk(file_dir):  
        for file in files:  
            if os.path.splitext(file)[1] == file_type:  
                L.append(os.path.join(root, file))  
                L_s.append(file)
    return L,L_s
#列表转带引号str
def list_to_str_f(week_end_list):
    return  '''"'''+'","'.join(week_end_list)+'''"'''
#创建表格并分区
def create_table_update(db_name,tn_name,var_name,var_type,key_str,p_num=1,partions_str='ticker'):
    #连接本地数据库
    db = pymysql.connect(host=host,user=user_name,password=pass_wd,database=db_name)
    #创建游标
    cursor = db.cursor()
    #创建
    var_info=''
    for id,sub_var in enumerate(var_name):
        var_info=var_info + sub_var + ' ' + var_type[id] + ','
    var_info = var_info[:-1]    
    if len(key_str)>0:
        sql = 'create table  `%s`(%s,primary key(%s)) partition by key(%s) partitions %d' % (tn_name,var_info,key_str,partions_str,p_num)    
    else:
        sql = 'create table  `%s`(%s)' % (tn_name,var_info)  

    try:
        # 执行SQL语句
        cursor.execute(sql)
        print("创建数据库成功")
    except Exception as e:
        print("创建数据库失败：case%s"%e)
    finally:
        #关闭游标连接
        cursor.close()
        # 关闭数据库连接
        db.close()
        
        
def create_table(db_name,tn_name,var_name,var_type,key_str):
    #连接本地数据库
    db = pymysql.connect(host=host,user=user_name,password=pass_wd,database=db_name)
    #创建游标
    cursor = db.cursor()
    #创建
    var_info=''
    for id,sub_var in enumerate(var_name):
        var_info=var_info + sub_var + ' ' + var_type[id] + ','
    var_info = var_info[:-1]    
    if len(key_str)>0:
        sql = 'create table  `%s`(%s,primary key(%s))' % (tn_name,var_info,key_str)    
    else:
        sql = 'create table  `%s`(%s)' % (tn_name,var_info)  

    try:
        # 执行SQL语句
        cursor.execute(sql)
        print("创建数据库成功")
    except Exception as e:
        print("创建数据库失败：case%s"%e)
    finally:
        #关闭游标连接
        cursor.close()
        # 关闭数据库连接
        db.close()

def do_sql_order(order_str,db_name):
    #db = pymysql.connect(host,user_name,pass_wd,db_name)
    db = pymysql.connect(host=host,user=user_name,password=pass_wd,database=db_name)
    #创建游标
    cursor = db.cursor()
    try:
        # 执行SQL语句
        cursor.execute(order_str)
        print("执行mysql命令成功")
    except Exception as e:
        print("执行mysql命令失败：case%s"%e)
    finally:
        #关闭游标连接
        cursor.close()
        # 关闭数据库连接
        db.close()
        
        
def get_a_stock_tradeDate_S45(index,begin='2000-01-01',end='2033-01-01'):
    #每日数据
    sql_str_index = '''select symbol,tradeDate,closePrice  as closeIndex,turnoverVol
    from yq_dayprice     where symbol = "%s"  and tradeDate>="%s" and 
    tradeDate<="%s" order by tradeDate'''
    sql_str_index = sql_str_index % (index,begin,end)
    hs300_index= get_db_data(db_yq,sql_str_index)
    hs300_index = hs300_index.sort_values('tradeDate')
    
    #后复权系数 MktEqudAdjAfGet
    sql_str_fq = """select tradeDate,accumadjfactor from mktequdadjafget where 
    ticker = "%s" order by tradeDate"""
    sql_str_fq = sql_str_fq % index
    y = get_db_data(db_yq,sql_str_fq)
    y=pd.merge(hs300_index,y,on=['tradeDate'])
    y['closeIndex'] = y['closeIndex']*y['accumAdjFactor']
    y.drop(columns=['accumAdjFactor'],inplace=True)
    return y        
# 指数数据数据的起始与终止时间
def get_index_tradeDate(index,begin,end,var_name = '*'):
    if isinstance(var_name,str):
        var_sel = var_name
    else:
        var_sel = ','.join(var_name)
            
    sql_str_index = '''select %s from yq_index where symbol = "%s" and tradeDate>="%s" 
        and tradeDate<="%s" order by tradeDate'''
    sql_str_index = sql_str_index % (var_sel,index,begin,end)
    hs300_index = get_db_data(db_yq,sql_str_index)
    hs300_index = hs300_index.sort_values('tradeDate')
    return hs300_index
#指数日度数据
def MktIdxdGet(index,begin,end,var_name = '*'):
    if isinstance(var_name,str):
        var_sel = var_name
    else:
        var_sel = ','.join(var_name)
            
    sql_str_index = '''select %s from yq_index where symbol = "%s" and tradeDate>="%s" 
        and tradeDate<="%s" order by tradeDate'''
    begin = dateformat_trans(begin)
    end = dateformat_trans(end)  
    sql_str_index = sql_str_index % (var_sel,index,begin,end)
    hs300_index = get_db_data(db_yq,sql_str_index)
    hs300_index = hs300_index.sort_values('tradeDate')
    return hs300_index

#指数周度数据
def MktIdxwGet(index,begin,end,var_name = '*'):
    if isinstance(var_name,str):
        var_sel = var_name
    else:
        var_sel = ','.join(var_name)
            
    sql_str_index = '''select %s from yq_mktidxwget where ticker = "%s" and endDate>="%s" 
        and endDate<="%s" order by endDate'''
    begin = dateformat_trans(begin)
    end = dateformat_trans(end)  
    sql_str_index = sql_str_index % (var_sel,index,begin,end)
    hs300_index = get_db_data(db_yq,sql_str_index)
    hs300_index = hs300_index.sort_values('endDate')
    return hs300_index

#指数日度数据 多个
def MktIdxdGetCom(indexlist,begin,end,var_name = '*'):
    if isinstance(indexlist,list):
        index=list_to_str_f(indexlist)
    else:
        index = indexlist
    if isinstance(var_name,str):
        var_sel = var_name
    else:
        var_sel = ','.join(var_name)
    begin = dateformat_trans(begin)
    end = dateformat_trans(end)        
    sql_str_index = '''select %s from yq_index where symbol in (%s) and tradeDate>="%s" 
        and tradeDate<="%s" order by tradeDate'''
    sql_str_index = sql_str_index % (var_sel,index,begin,end)
    hs300_index = get_db_data(db_yq,sql_str_index)
    hs300_index = hs300_index.sort_values('tradeDate')
    return hs300_index
#指数月度数据
def MktIdxmGet(index,begin,end,var_name = '*'):
    if isinstance(var_name,str):
        var_sel = var_name
    else:
        var_sel = ','.join(var_name)
            
    sql_str_index = '''select %s from yq_index_month where symbol = "%s" and endDate>="%s" 
        and endDate<="%s" order by endDate'''
    sql_str_index = sql_str_index % (var_sel,index,begin,end)
    hs300_index = get_db_data(db_yq,sql_str_index)    
    hs300_index = hs300_index.sort_values('endDate')
    return hs300_index
    
def get_cf_future_update(index,begin='2000-01-01',end='2033-01-01',var_name = '*'):
    if isinstance(var_name,str):
        var_sel = var_name
    else:
        var_sel = ','.join(var_name)
    sql_str_index = '''select %s from yq_mktmfutdget 
    where contractObject = "%s" and mainCon = 1 and tradeDate>="%s" and 
    tradeDate<="%s" order by tradeDate'''
    sql_str_index = sql_str_index % (var_sel,index,begin,end)
    hs300_index = get_db_data(db_yq,sql_str_index)
    hs300_index = hs300_index.sort_values('tradeDate')
    return hs300_index

def get_cf_future_tradeDate(index,begin='2000-01-01',end='2033-01-01'):
    sql_str_index = '''select contractObject as symbol,tradeDate,openPrice as openIndex,highestPrice as highestIndex,
    lowestPrice as lowestIndex,closePrice  as closeIndex,turnoverVol,chgPct from yq_mktmfutdget 
    where contractObject = "%s" and mainCon = 1 and tradeDate>="%s" and 
    tradeDate<="%s" order by tradeDate'''
    sql_str_index = sql_str_index % (index,begin,end)
    hs300_index = get_db_data(db_yq,sql_str_index)
    hs300_index = hs300_index.sort_values('tradeDate')
    return hs300_index

def get_a_stock_tradeDate(index,begin='2000-01-01',end='2033-01-01'):
    #每日数据
    sql_str_index = '''select symbol,tradeDate,openPrice as openIndex,highestPrice as highestIndex,
    lowestPrice as lowestIndex,closePrice  as closeIndex from yq_dayprice
    where symbol = "%s"  and tradeDate>="%s" and 
    tradeDate<="%s" order by tradeDate'''
    sql_str_index = sql_str_index % (index,begin,end)
    hs300_index = get_db_data(db_yq,sql_str_index)
    hs300_index = hs300_index.sort_values('tradeDate')
    
    #后复权系数 MktEqudAdjAfGet
    sql_str_fq = """select tradeDate,accumAdjFactor from mktequdadjafget where 
    ticker = "%s" order by tradeDate"""
    sql_str_fq = sql_str_fq % index
    y = get_db_data(db_yq,sql_str_fq)
    y=pd.merge(hs300_index,y,on=['tradeDate'])
    y['openIndex'] = y['openIndex']*y['accumAdjFactor']
    y['highestIndex'] = y['highestIndex']*y['accumAdjFactor']
    y['lowestIndex'] = y['lowestIndex']*y['accumAdjFactor']
    y['closeIndex'] = y['closeIndex']*y['accumAdjFactor']
    return y

def get_exchange_tradeDate(index,begin='2000-01-01',end='2033-01-01'):
    #每日数据
    sql_str_index = '''select symbol,tradingdate as tradeDate,openPrice as openIndex,highestPrice as highestIndex,
    lowestPrice as lowestIndex,closePrice  as closeIndex,turnoverVol from exchange_dayly
    where symbol = "%s"  and tradingdate>="%s" and 
    tradingdate<="%s" order by tradingdate'''
    sql_str_index = sql_str_index % (index,begin,end)
    hs300_index = get_db_data(db_name42,sql_str_index)
    hs300_index = hs300_index.sort_values('tradeDate')    
    return hs300_index

def get_exchange_tradeDate_update(index,begin='2000-01-01',end='2033-01-01',var_name = '*'):
    #每日数据
    sql_str_index = '''select %s from exchange_dayly
    where symbol = "%s"  and tradingdate>="%s" and 
    tradingdate<="%s" order by tradingdate'''
    sql_str_index = sql_str_index % (var_name,index,begin,end)
    hs300_index = get_db_data(db_name42,sql_str_index)
    hs300_index = hs300_index.sort_values('tradeDate')    
    return hs300_index

#dowjones data
def get_dowjones_tradeDate(index,begin='2000-01-01',end='2033-01-01'):
    #每日数据
    sql_str_index = '''select symbol,tradeDate,openPrice as openIndex,highestPrice as highestIndex,
    lowestPrice as lowestIndex,closePrice  as closeIndex, totalVolume as turnoverVol from dowjones_dayly
    where symbol = "%s"  and tradeDate>="%s" and 
    tradeDate<="%s" order by tradeDate'''
    sql_str_index = sql_str_index % (index,begin,end)
    hs300_index = get_db_data(db_name42,sql_str_index)
    hs300_index = hs300_index.sort_values('tradeDate')    
    return hs300_index

#美股后复权数据
def get_american_stock_tradeDate(index,begin='2000-01-01',end='2033-01-01'):
    #每日数据
    sql_str_index = '''select symbol,tradingdate as tradeDate,openprice_adj as openIndex,highprice_adj as highestIndex,
    lowprice_adj as lowestIndex,closeprice_adj  as closeIndex,volume_adj as turnoverVol from us_stock_daytick
    where symbol = "%s"  and tradingdate>="%s" and 
    tradingdate<="%s" order by tradingdate'''
    sql_str_index = sql_str_index % (index,begin,end)
    hs300_index = get_db_data(db_name_us,sql_str_index)
    return hs300_index
#获取成分股
def get_IdxCons(intoDate,ticker='000300'):
    #nearst 时间
    t0='select tradingdate from idxcloseweightget where ticker="%s" order by tradingdate limit 1;'
    t0=pd.read_sql(t0 % ticker,engine)
    t0=t0[t0.columns[0]].astype(str).values[0]
    if intoDate<t0:
        intoDate=t0
    sql_str1 = '''select symbol from yuqerdata.idxcloseweightget where ticker = "%s"
            and tradingdate = (select tradingdate from yuqerdata.idxcloseweightget where 
        ticker="%s" and tradingdate<="%s"  order by tradingdate desc limit 1)''' %(ticker,
        ticker,intoDate)
    x = get_db_data(db_yq,sql_str1)
    x = x['symbol'].values   
    return x

#成分股2
def mIdxCloseWeightGet(ticker,begin,end,key_str):
    sql_tmp = 'select %s from midxcloseweightget_s76 where ticker = "%s" and effDate>="%s" and effDate<="%s"'
    order1 = sql_tmp % (key_str,ticker,begin,end)
    x = get_db_data(db_yq,order1)    
    return x

#日线数据
def chg_factor(ticker = '000005',begin = '2001-01-01' ,end = '2090-01-01' , 
               field = [u'symbol',  u'tradeDate', u'openPrice',
                        u'highestPrice', u'lowestPrice', u'closePrice', u'turnoverVol',
                        u'turnoverValue',u'dealAmount', u'chgPct',
                        'turnoverRate',u'marketValue']):
    sql_str1 = sql_str_select_data1 % (','.join(field),ticker,begin,end)
    dataday = get_db_data(db_yq,sql_str1)
    dataday = dataday.applymap(lambda x: np.nan if x == 0 else x)
    dataday.rename(columns={'symbol':'ticker'},inplace=True)
    #升级后复权系数
    #后复权系数 MktEqudAdjAfGet
    sql_str_fq = """select tradeDate,accumAdjFactor from mktequdadjafget where 
    ticker = "%s" order by tradeDate"""
    sql_str_fq = sql_str_fq % ticker
    y = get_db_data(db_yq,sql_str_fq)
    dataday=pd.merge(dataday,y,on=['tradeDate'])
    return dataday.fillna(method = 'ffill')


## 得交易日历
def get_calender_range(begin, end):
    sql_str = """select tradeDate from yuqerdata.yq_index where symbol = "000001" 
    and tradeDate >="%s" and tradeDate <="%s" order by tradeDate""" % (begin, end)
    x = get_db_data(db_yq,sql_str)
    x=x['tradeDate'].values
    #b=[i.strftime('%Y-%m-%d') for i in x]
    return x

#获取所有交易日历
def get_calender():
    sql_str = '''select tradeDate from yuqerdata.yq_index where symbol = "000001" order by tradeDate'''
    x = get_db_data(db_yq,sql_str)
    x=x['tradeDate'].values
    #b=[i.strftime('%Y-%m-%d') for i in x]
    return x
#获取月度日历    
def get_month_calender(begin = '2000-01-01'):
    sql_str = '''select endDate from yuqerdata.yq_index_month where symbol = "000001" and endDate>="%s" order by endDate''' % (begin)
    x = get_db_data(db_yq,sql_str)
    x=x['endDate'].values
    #b=[i.strftime('%Y-%m-%d') for i in x]
    return x

#获取某个时间点的所有股票
def get_universe_date(tradeDate):
    sql_tmp = """select * from equget where listDate<'%s' and 
        (delistDate>'%s' or delistDate is null)"""
    sql1 = sql_tmp % (tradeDate,tradeDate)
    x = get_db_data(db_yq,sql1)
    return x.ticker.tolist()
#获取A股所有的ticker 股票池
def get_symbol_A():
    sql_str = """select distinct(ticker)  from equget
                where equTypeCD = "A" and listStatusCD !="UN" and 
                ListSectorCD<=3 and length(ticker)=6  order by ticker"""
    x = get_db_data(db_yq,sql_str)    
    return x.ticker.tolist()
#A股（含创业板）
def get_symbol_A_S43():
    sql_str = """select distinct(ticker)  from equget
                where equTypeCD = "A" and listStatusCD !="UN" and 
                ListSectorCD<=4 and length(ticker)=6  order by ticker"""
    x = get_db_data(db_yq,sql_str)    
    return x.ticker.tolist()
#后复权月度数据
def get_MktEqumAdjGet(ticker,beginDate='2000-01-01', endDate='2049-01-01', field=u"ticker,endDate,chgPct"):      
    sql_str = """select %s from mktequmadjafget where endDate>="%s" and endDate<="%s" 
                order by endDate"""
    x = get_db_data(db_yq,sql_str)
    #print(sql_str)
    return x
#后复权月度收益 升级 截面同时选
def get_MktEqumAdjGet_update(beginDate='2000-01-01', endDate='2049-01-01', field=u"ticker,endDate,chgPct"):      
    sql_str = """select %s from mktequmadjafget where endDate>="%s" and endDate<="%s" 
                order by endDate"""      
    sql_str = sql_str % (field,beginDate,endDate)
    #print(sql_str)
    return get_db_data(db_yq,sql_str)
#get factor date
def get_MktStockFactorsOneDayGet(tradeDate,field=u""):
    if isinstance(field,list):
        filed_str = ','.join(field)
    else:
        filed_str = field
    sql_str = """select %s from yq_mktstockfactorsonedayget where tradeDate = "%s" order by tradeDate"""
    sql_str = sql_str % (filed_str,tradeDate)   
    #print(sql_str)
    return get_db_data(db_yq,sql_str)


def get_MktStockFactorsOneDayGet_special(factor_list,week_end_list):    
    sql_str_factor = 'select %s from yq_mktstockfactorsonedayget where tradeDate in (%s) '
    var_str = ','.join(['secID','ticker','tradeDate']+factor_list)
    date_str = '''"'''+'","'.join(week_end_list)+'''"'''
    sql_str_factor = sql_str_factor % (var_str,date_str)   
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df

#股票周行情
def get_MktEquwAdjAfGet(beginDate,endDate,field=r"*"):
    if isinstance(field,list):
        filed_str = ','.join(field)
    else:
        filed_str = field
    sql_str = """select %s from yq_mktequwadjafget where endDate >= "%s" 
                 and endDate<="%s" order by endDate """
    sql_str = sql_str % (filed_str,beginDate,endDate)   
    #print(sql_str)
    return get_db_data(db_yq,sql_str)

#股票后复权行情
def get_MktEqudAdjAfGet(beginDate,endDate,field=r""):
    if isinstance(field,list):
        filed_str = ','.join(field)
    else:
        filed_str = field
    sql_str = """select %s from yq_mktequdadjafget where tradeDate >= "%s" 
                 and tradeDate<="%s" order by tradeDate"""
    sql_str = sql_str % (filed_str,beginDate,endDate)   
    return get_db_data(db_yq,sql_str)

def get_MktEqudAdjAfGet_fill(beginDate,endDate,field=r""):
    if isinstance(field,list):
        filed_str = ','.join(field)
    else:
        filed_str = field
    sql_str = """select %s from MktEqudAdjAfGetF0S53 where tradeDate >= "%s" 
                 and tradeDate<="%s" order by tradeDate"""
    sql_str = sql_str % (filed_str,beginDate,endDate)   
    return get_db_data(db_yq,sql_str)

def get_MktEqudAdjAfGet_com(beginDate,endDate,field=r""):
    x0 = get_MktEqudAdjAfGet(beginDate,endDate,field)
    x1 = get_MktEqudAdjAfGet_fill(beginDate,endDate,field)
    x=pd.concat([x0,x1])
    x.reset_index(inplace=True,drop=True)
    return x
'''
def get_MktEqudAdjAfGet_com(beginDate,endDate,field=r""):
    if isinstance(field,list):
        filed_str = ','.join(field)
    else:
        filed_str = field
    sql_str = """select %s from MktEqudAdjAfGetF1S53 where tradeDate >= "%s" 
                 and tradeDate<="%s" order by tradeDate"""
    sql_str = sql_str % (filed_str,beginDate,endDate)   
    return pd.read_sql(sql_str,engine)
'''

#港股日行情
def MktHKEqudGet(beginDate,endDate,field=r""):
    if isinstance(field,list):
        filed_str = ','.join(field)
    else:
        filed_str = field
    sql_str = """select %s from mkthkequdgets54 where tradeDate >= "%s" 
                 and tradeDate<="%s" order by tradeDate"""
    sql_str = sql_str % (filed_str,beginDate,endDate)
    return get_db_data(db_yq,sql_str)

def MktEqudGet_single(ticker,beginDate,endDate,field=r""):
    if isinstance(field,list):
        filed_str = ','.join(field)
    else:
        filed_str = field
    sql_str = """select %s from yq_dayprice where symbol = "%s" and  tradeDate >= "%s" 
                 and tradeDate<="%s" order by tradeDate"""
    sql_str = sql_str % (filed_str,ticker,beginDate,endDate)
    return get_db_data(db_yq,sql_str)

#A股日行情    
def MktEqudGet(beginDate,endDate,field=r""):
    if isinstance(field,list):
        filed_str = ','.join(field)
    else:
        filed_str = field
    sql_str = """select %s from yq_dayprice where tradeDate >= "%s" 
                 and tradeDate<="%s" order by tradeDate"""
    sql_str = sql_str % (filed_str,beginDate,endDate)
    return get_db_data(db_yq,sql_str)
#filling=0部分
def MktEqudGet_fill(beginDate,endDate,field=r""):
    if isinstance(field,list):
        filed_str = ','.join(field)
    else:
        filed_str = field
    sql_str = """select %s from mktequdget0s53 where tradeDate >= "%s" 
                 and tradeDate<="%s" order by tradeDate"""
    sql_str = sql_str % (filed_str,beginDate,endDate)
    return get_db_data(db_yq,sql_str)

def MktEqudGet_com(beginDate,endDate,field=r""):
    x0=MktEqudGet(beginDate,endDate,field)
    x1=MktEqudGet_fill(beginDate,endDate,field)
    x =pd.concat([x0,x1])
    x.reset_index(inplace=True,drop=True)
    return x

    
def MktEqudGet_update(factor_list,week_end_list):
    if isinstance(factor_list,list):
        var_str = ','.join(factor_list)
    else:
        var_str = factor_list
    sql_str_factor = 'select %s from yq_dayprice where tradeDate in (%s) '    
    date_str = '''"'''+'","'.join(week_end_list)+'''"'''
    sql_str_factor = sql_str_factor % (var_str,date_str)
    x = get_db_data(db_yq,sql_str_factor)
    return x
def MktEqudGet_update_day(ticker_list,factor_list,begin,end):
    if isinstance(factor_list,list):
        var_str = ','.join(factor_list)
    else:
        var_str = factor_list
    sql_str_factor = 'select %s from yq_dayprice where symbol in (%s) and tradeDate>="%s" and tradeDate<="%s" '    
    ticker_list_str = '''"'''+'","'.join(ticker_list)+'''"'''
    sql_str_factor = sql_str_factor % (var_str,ticker_list_str,begin,end)
    x = get_db_data(db_yq,sql_str_factor)
    return x

#股票后复权行情    
def get_MktEqudAdjAfGet_update(ticker,begin,end,field=r""):
    if isinstance(field,list):
        filed_str = ','.join(field)
    else:
        filed_str = field
    sql_str = """select %s from yq_mktequdadjafget where ticker="%s" and tradeDate >= "%s" 
                 and tradeDate<="%s" order by tradeDate"""
    sql_str = sql_str % (filed_str,ticker,begin,end)   
    #print(sql_str)
    #print(sql_str)
    return get_db_data(db_yq,sql_str)

class time_use_tool():
    def __init__(self,ini_str=' '):
        self.t_now=time.time()
        self.t_now0=time.time()
        self.use('开始记录 %s ' % ini_str)
    def use(self,key_str=' ' ):
        tt = time.time()
        print('%s %s Time used %0.2f(All= %0.2f) seconds' % (key_str,time.ctime(),tt-self.t_now,tt-self.t_now0))
        self.t_now = tt

def get_week_month_tradeDate(start_date,end_date,exchangeCD='XSHG'):
    #dates = pd.date_range(start_date,end_date,freq="D").astype(str)    
    # 获取月末交易日
    sql_str_calender = """select * from yuqerdata.yuqer_cal where exchangeCD = "%s" 
                        and calendarDate>="%s" and calendarDate<="%s" order by calendarDate"""
    sql_str = sql_str_calender % (exchangeCD,start_date,end_date)
    calendar_df = get_db_data(db_yq,sql_str)
    calendar_df['calendarDate'] = calendar_df['calendarDate'].astype(str)
    calendar_df['prevTradeDate'] = calendar_df['prevTradeDate'].astype(str)
    week_end_list = calendar_df[calendar_df['isWeekEnd']==1]['calendarDate'].values
    month_end_list = calendar_df[calendar_df['isMonthEnd']==1]['calendarDate'].values
    trade_date_list = calendar_df[calendar_df['isOpen']==1]['calendarDate'].values
    return trade_date_list,week_end_list,month_end_list

#时间函数
#日历
def get_week_month_tradeDate_update(start_date,end_date):
    #dates = pd.date_range(start_date,end_date,freq="D").astype(str)    
    # 获取月末交易日
    sql_str_calender = """select * from yuqerdata.yuqer_cal where exchangeCD = "%s" 
                        and calendarDate>="%s" and calendarDate<="%s" order by calendarDate"""
    sql_str = sql_str_calender % ('XSHG',start_date,end_date)
    calendar_df = get_db_data(db_yq,sql_str)
    calendar_df['calendarDate'] = calendar_df['calendarDate'].astype(str)
    calendar_df['prevTradeDate'] = calendar_df['prevTradeDate'].astype(str)
    week_end_list = sorted(calendar_df[calendar_df['isWeekEnd']==1]['calendarDate'].tolist())
    month_end_list = sorted(calendar_df[calendar_df['isMonthEnd']==1]['calendarDate'].tolist())
    trade_date_list = sorted(calendar_df[calendar_df['isOpen']==1]['calendarDate'].tolist())
    #daily_trade_list = sorted(cal_dates_df.query("isOpen==1")['calendarDate'].tolist())
    return trade_date_list,week_end_list,month_end_list,calendar_df

#S49添加 根据endDate选择数据
def get_FdmtBSGet(beginDate,endDate,field):
    sql_str_factor = 'select %s from yq_fdmtbsget where endDate >="%s" and endDate<="%s" '
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    sql_str_factor = sql_str_factor % (var_str,beginDate,endDate)
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df

def get_FdmtISQPITGet(beginDate,endDate,field):
    sql_str_factor = 'select %s from yq_fdmtisqpitget where endDate >="%s" and endDate<="%s" '
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    sql_str_factor = sql_str_factor % (var_str,beginDate,endDate)
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df

def FdmtEeGet(beginDate,endDate,field,key_words = 'publishDate'):
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    sql_str_factor = 'select %s from yq_fdmteeget where %s >="%s" and %s<="%s" '
    sql_str_factor = sql_str_factor % (var_str,key_words,beginDate,key_words,endDate)
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df

#20220509
def FdmtIndiRtnPitGet(beginDate,endDate,field,key_words = 'publishDate'):
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    sql_str_factor = 'select %s from yq_fdmtindirtnpitget where %s >="%s" and %s<="%s" '
    sql_str_factor = sql_str_factor % (var_str,key_words,beginDate,key_words,endDate)
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df

#TTM利润表数据 20220207
def FdmtISTTMPITGet(beginDate,endDate,field,key_words = 'publishDate'):
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    sql_str_factor = 'select %s from yq_fdmtisttmpitget where %s >="%s" and %s<="%s" '
    sql_str_factor = sql_str_factor % (var_str,key_words,beginDate,key_words,endDate)
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df

def FdmtEfGet(beginDate,endDate,field,key_words = 'publishDate'):
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    sql_str_factor = 'select %s from yq_fdmtefget where %s >="%s" and %s<="%s" '
    sql_str_factor = sql_str_factor % (var_str,key_words,beginDate,key_words,endDate) 
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df
#zx04 update
#业绩预告
def FdmtEfNewGet(beginDate,endDate,field,key_words = 'publishDate'):
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    sql_str_factor = 'select %s from fdmtefnewgetzx04 where %s >="%s" and %s<="%s" '
    sql_str_factor = sql_str_factor % (var_str,key_words,beginDate,key_words,endDate)
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df
#zx04 update
def ResConSecDataGet(beginDate,endDate,field,key_words = 'repForeTime'):
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    sql_str_factor = 'select %s from resconsecdataget18 where %s >="%s" and %s<="%s" '
    sql_str_factor = sql_str_factor % (var_str,key_words,beginDate,key_words,endDate)  
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df

def ResConInduSwGet(beginDate,endDate,field,key_words = 'repForeTime'):
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    sql_str_factor = 'select %s from resconinduswget18 where %s >="%s" and %s<="%s" '
    sql_str_factor = sql_str_factor % (var_str,key_words,beginDate,key_words,endDate)  
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df

#默认的key word最好设置为endDate
#FdmtISGet
def FdmtISGet(beginDate,endDate,field,key_words = 'publishDate'):
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    beginDate = dateformat_trans(beginDate)
    endDate = dateformat_trans(endDate)
    sql_str_factor = 'select %s from nincome where %s >="%s" and %s<="%s" '
    sql_str_factor = sql_str_factor % (var_str,key_words,beginDate,key_words,endDate)
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df    
#zx04 update 20210729
def FdmtISQPIT2018Get(beginDate,endDate,field,key_words = 'endDate'):
    if isinstance(field,list):
        var_str = ','.join(field)
    else:
        var_str = field
    beginDate = dateformat_trans(beginDate)
    endDate = dateformat_trans(endDate)
    
    sql_str_factor = 'select %s from fdmtisqpit2018getzx04 where %s >="%s" and %s<="%s" '
    sql_str_factor = sql_str_factor % (var_str,key_words,beginDate,key_words,endDate)  
    factor_df = get_db_data(db_yq,sql_str_factor)
    return factor_df    

def get_a_stock_pool():
    sql_str_temp = """select ticker from equget where equTypeCD="A" and listStatusCD in
    ("L","S","DE")"""
    x=get_db_data(db_yq,sql_str_temp)['ticker'].tolist()
    x.remove('DY600018')
    return x

#获取行业分类
def get_industry_class(t):
    sql_str1 = '''select ticker,industryID1 from yuqerdata.yq_industry_sw where 
                industryVersionCD="010303" and intodate <= "%s" and 
                (outDate>"%s" or outDate is null)''' % (t,t)
    x = get_db_data(db_yq,sql_str1)
    return x
#获取行业分类
def get_industry_class_update(t,fileds_str = 'ticker,industryID1',industryVersionCD="010303"):
    sql_str1 = '''select %s from yuqerdata.yq_industry_sw where 
                industryVersionCD="%s" and intodate <= "%s" and 
                (outDate>"%s" or outDate is null)''' % (fileds_str,industryVersionCD,t,t)
    x = get_db_data(db_yq,sql_str1)
    return x
#
def get_file_name(file_dir,file_type):
    L=[]
    L_s = []   
    for root, dirs, files in os.walk(file_dir):  
        for file in files:  
            if os.path.splitext(file)[1] == file_type:  
                L.append(os.path.join(root, file))  
                L_s.append(file)
    return L,L_s

def get_ini_data(tn,var_name,db):
    sql_str = 'select %s from %s order by %s desc limit 1' % (var_name,tn,var_name)
    t0 = pd.read_sql(sql_str,db)
    return t0[var_name].astype(str).values[0]

#两个list并集
def list_com(a,b):
    return list(set(a).union(set(b)))

#两个list交集
def list_intersec(a,b):
    return list(set(a).intersection(set(b)))

#两个list差
def list_diff(a,b):
    return list(set(a).difference(set(b)))

def save_pickle(fn,x):
    with open(fn, 'wb') as f:
        pickle.dump(x, f)
def read_pickle(fn):    
    with open(fn, 'rb') as f:
        return pickle.load(f)

def MktStockFactorsOneDayProGet_multi(t,field='*'):
    if isinstance(t,str):
        return MktStockFactorsOneDayProGet_adair(t,field)
    else:
        p1 = t
        p2 = [field]*len(t)
        pool = ThreadPool(processes=num_core)
        temp = pool.map(MktStockFactorsOneDayProGet_adair, zip(p1,p2))
        pool.close()
        pool.join() 
        factor_df=pd.concat(temp)
        return factor_df
    
# 载入uqer因子截面数据
def MktStockFactorsOneDayProGet_adair(t,field='*'):
    sql_tmp = 'select %s from yq_mktstockfactorsonedayproget where tradeDate="%s"'
    sql_str = sql_tmp % (field,t)
    x = get_db_data(db_yq,sql_str)
    print('complete loading pro factor %s' % t)
    return x
            
#载入yuqer因子
def get_factor_data_update(fac_name,target_date,method='outer'):
    def fac_info_trans(id_sec):
        factor_style10_str0 = 'select symbol,f_val as %s from %s where tradingdate ="%s"'
        factor_style10_str1 = 'select ticker as symbol,%s from %s where tradeDate ="%s"'
        if id_sec==0:
            sub_tn = db_name_factor0
            factor_style10_str = factor_style10_str1
            sub_engine = db_yq
        elif id_sec==-1:
            sub_tn = db_name_factor1
            factor_style10_str = factor_style10_str1
            sub_engine = db_yq
        else:
            sub_tn = ''
            factor_style10_str = factor_style10_str0
            sub_engine = db_name_yq_cub
        return sub_tn,factor_style10_str,sub_engine
    #def get_factor_data_update(fac_name,target_date):
    t_cut = '2020-07-01'
    db_name_factor0 = 'yq_MktStockFactorsOneDayGet'.lower()
    db_name_factor1 = 'yq_MktStockFactorsOneDayProGet'.lower()
    fac_name = [i.lower() for i in fac_name]
    
    tn = ['yq_MktStockFactorsOneDayGet'.lower(),'yq_MktStockFactorsOneDayProGet'.lower()]
    var = [pd.read_sql('desc %s ' % i,engine).Field.tolist() for i in tn]
    var[0] = [i.lower() for i in var[0]]
    var[1] = [i.lower() for i in var[1]]
        
    fac_id = [0 if i in var[0] else 1 if i in var[1] else 3 for i in fac_name]
    factor_style10=fac_name.copy()
    factor_style_tn = fac_id.copy()
    x=pd.DataFrame()
    
    obj_time = time_use_tool('载入数据立方因子 %s' % target_date)
    fac0=[]
    fac1=[]
    for i,j in enumerate(factor_style_tn):
        if j==0:
            fac0.append(factor_style10[i])
        elif j==1:
            fac1.append(factor_style10[i])
    
    if len(fac0)>0:
        sub_tn,factor_style10_str,sub_engine=fac_info_trans(0)
        sub_sql_str = factor_style10_str % (','.join(fac0),sub_tn,target_date)
        sub_x0 = get_db_data(sub_engine,sub_sql_str)
    else:
        sub_x0= pd.DataFrame()
    obj_time.use('loading factor %d-%d out of %d' % (0,len(fac0),len(factor_style_tn)))   
    sub_x=[]
    sub_y=[]
    if len(fac1)>0:
        if target_date>=t_cut:
            sub_tn,factor_style10_str,sub_engine=fac_info_trans(-1)
            sub_sql_str = factor_style10_str % (','.join(fac1),sub_tn,target_date)
            sub_y = get_db_data(sub_engine,sub_sql_str)
        else:        
            T = len(fac1)
            _,factor_style10_str,sub_engine=fac_info_trans(1)
            sub_y=pd.DataFrame()
            for i,sub_f_name in enumerate(fac1):
                sub_tn = sub_f_name.lower()
                sub_sql_str = factor_style10_str % (sub_f_name,sub_tn,target_date)
                sub_x = get_db_data(sub_engine,sub_sql_str)
                if len(sub_x)==0:
                    continue
                if len(sub_y)==0:
                    sub_y = sub_x
                else:
                    sub_y = pd.merge(sub_y,sub_x,on='symbol',how = method)
                obj_time.use('loading factor %s %d out of %d' % (sub_f_name,i,T))
        
    if len(sub_x0)>0 and len(sub_y)==0:
        x=sub_x0
    elif len(sub_x0)==0 and len(sub_y)>0:
        x=sub_y
    else:
        x=pd.merge(sub_x0,sub_y,on='symbol',how = method)
    return x

def get_factor_data_update2(fac_name,target_date,method='outer'):
    factor_df=get_factor_data_update(fac_name,target_date,method)
    c={}
    for sub_f in fac_name:
        c[sub_f.lower()]=sub_f
    factor_df.rename(columns=c,inplace=True)
    factor_df.rename(columns={'symbol':'ticker'},inplace=True)
    factor_df['secID'] = factor_df.ticker.apply(lambda x:ticker2secID(x))
    return factor_df
    
def get_factor_update(field,week_end_list):
    def get_factor_thread(inputdata):
        x,y=inputdata
        f = get_factor_data_update(x,y)
        f['tradeDate'] = y
        return f
    pool = ThreadPool(processes=num_core)
    fac_name=[field for i in week_end_list]
    temp = pool.map(get_factor_thread, zip(fac_name,week_end_list))
    pool.close()
    pool.join() 
    factor_df=pd.concat(temp)
    #名称对齐
    c={}
    for sub_f in field:
        c[sub_f.lower()]=sub_f
    factor_df.rename(columns=c,inplace=True)
    factor_df.rename(columns={'symbol':'ticker'},inplace=True)
    factor_df['secID'] = factor_df.ticker.apply(lambda x:ticker2secID(x))
    return factor_df

def add_0(x):
    if isinstance(x,int):
        x= '%0.6d' % x
    else:
        x=x.rjust(6,'0')
    return x
#ST info
def SecSTGet(t0,t1):
    sql_tmp = 'select * from yuqerdata.st_info where tradeDate>="%s" and tradeDate<="%s"'
    sql_str = sql_tmp % (t0,t1)
    ticker = get_db_data(db_yq,sql_str)
    ticker['ticker'] = ticker.ticker.apply(lambda x:add_0(x))
    return ticker

def ticker2secID(ticker):
    """
    ticker转换secID
    转换规则：secID = ticker + 后缀：如果股票属于沪市，则后缀为'.XSHG'，如果属于深市，则后缀为'.XSHE'
    """
    ticker = '0'*(6-len(ticker)) + ticker
    if ticker[0] == '6':
        secID = ticker + '.XSHG'
    else:
        secID = ticker + '.XSHE'
    return secID

def TradeCalGet(t0='1900-01-01',tt='2099-01-01',key_str='calendarDate',exchangeCD='"XSHG"'):
    sql_tmp = 'select %s from yuqer_cal where calendarDate>="%s" and calendarDate<="%s" and exchangeCD in (%s) order by calendarDate'
    t = get_db_data(db_yq,sql_tmp %(key_str,t0,tt,exchangeCD))
    return t

def get_trade_dates(start_date, end_date, frequency='d'):
    """
    输入起始日期和频率，即可获得日期列表（daily包括起始日，其余的都是位于起始日中间的）
    输入：
       start_date，开始日期，'YYYYMMDD'形式
       end_date，截止日期，'YYYYMMDD'形式
       frequency，频率，daily为所有交易日，weekly为每周最后一个交易日，monthly为每月最后一个交易日，quarterly为每季最后一个交易日
    返回：
       获得list型日期列表，以'YYYYMMDD'形式存储
    """
    #data = DataAPI.TradeCalGet(exchangeCD=u"XSHG", beginDate=start_date, endDate=end_date,
    #                           field=u"calendarDate,isOpen,isWeekEnd,isMonthEnd,isQuarterEnd", pandas="1")
    field=u"calendarDate,isOpen,isWeekEnd,isMonthEnd,isQuarterEnd"
    #yuqer_cal
    sql_tmp = """select %s from yuqer_cal where exchangeCD = "XSHG" and calendarDate>="%s" 
                and calendarDate<= "%s" order by calendarDate""" % (field,start_date,end_date)
    data = get_db_data(db_yq,sql_tmp)
    if frequency == 'd':
        data = data[data['isOpen'] == 1]
    elif frequency == 'w':
        data = data[data['isWeekEnd'] == 1]
    elif frequency == 'm':
        data = data[data['isMonthEnd'] == 1]
    elif frequency == 'q':
        data = data[data['isQuarterEnd'] == 1]
    else:
        raise ValueError('调仓频率必须为d/w/m！！')
    #date_list = map(lambda x: x[0:4] + x[5:7] + x[8:10], data['calendarDate'].values.tolist())
    date_list = data['calendarDate'].astype(str).values.tolist()
    return date_list

def month_tool(x,N,method='today'):
    if isinstance(x,str):
        x = datetime.strptime(x,'%Y-%m-%d')
    year = x.year
    mon  = x.month
    day  = x.day
    hour = x.hour
    minu  = x.minute
    sec  = x.second
    def today():
        '''
        get today,date format="YYYY-MM-DD"
        '''
        return date.today()
    def todaystr():
        '''
        get date string
        date format="YYYYMMDD"
        '''
        return year+mon+day
    #def datetime():
    #    '''
    #    get datetime,format="YYYY-MM-DD HH:MM:SS"
    #    '''
    #    return strftime("%Y-%m-%d %H:%M:%S",localtime())
    def datetimestr():
        '''
        get datetime string
        date format="YYYYMMDDHHMMSS"
        '''
        return year+mon+day+hour+minu+sec
    def getdayofday(n=0):
        '''
        if n>=0,date is larger than today
        if n<0,date is less than today
        date format = "YYYY-MM-DD"
        '''
        if(n<0):
            n = abs(n)
            return date.today()-timedelta(days=n)
        else:
            return date.today()+timedelta(days=n)
    def getdaysofmonth(year,mon):
        '''
        get days of month
        '''
        return calendar.monthrange(year, mon)[1]
    def getfirstdayofmonth(year,mon):
        '''
        get the first day of month
        date format = "YYYY-MM-DD"
        '''
        days="01"
        if(int(mon)<10):
            mon = "0"+str(int(mon))
        arr = (year,mon,days)
        return "-".join("%s" %i for i in arr)
    def getlastdayofmonth(year,mon):
        '''
        get the last day of month
        date format = "YYYY-MM-DD"
        '''
        days=calendar.monthrange(year, mon)[1]
        mon = addzero(mon)
        arr = (year,mon,days)
        return "-".join("%s" %i for i in arr)
    def get_firstday_month(n=0):
        '''
        get the first day of month from today
        n is how many months
        '''
        (y,m,d) = getyearandmonth(n)
        d = "01"
        arr = (y,m,d)
        return "-".join("%s" %i for i in arr)
    def get_lastday_month(n=0):
        '''
        get the last day of month from today
        n is how many months
        '''
        return "-".join("%s" %i for i in getyearandmonth(n))
        
    def get_today_month(n=0):
        '''
        get last or next month's today
        n is how many months
        date format = "YYYY-MM-DD"
        '''
        (y,m,d) = getyearandmonth(n)
        arr=(y,m,d)
        if(int(day)<int(d)):
            arr = (y,m,day)
        return "-".join("%s" %i for i in arr)
    def getyearandmonth(n=0):
        '''
        get the year,month,days from today
        befor or after n months
        '''
        thisyear = int(year)
        thismon = int(mon)
        totalmon = thismon+n
        if(n>=0):
            if(totalmon<=12):
                days = str(getdaysofmonth(thisyear,totalmon))
                totalmon = addzero(totalmon)
                return (year,totalmon,days)
            else:
                i = math.floor(totalmon/12)
                j = totalmon-i*12
                thisyear += i
                days = str(getdaysofmonth(thisyear,j))
                j = addzero(j)
                return (str(thisyear),str(j),days)
        else:
            if((totalmon>0) and (totalmon<12)):
                days = str(getdaysofmonth(thisyear,totalmon))
                totalmon = addzero(totalmon)
                return (year,totalmon,days)
            else:
                i = -math.ceil(abs(totalmon)/12)
                j = totalmon -i*12
                if(j==0):
                    i-=1
                    j=12
                thisyear +=i
                days = str(getdaysofmonth(thisyear,j))
                j = addzero(j)
                return (str(thisyear),str(j),days)
    def addzero(n):
        '''
        add 0 before 0-9
        return 01-09
        '''
        nabs = abs(int(n))
        if(nabs<10):
            return "0"+str(nabs)
        else:
            return nabs
    if method == 'today' or method =='t':
        return get_today_month(N)
    elif method == 'lastday' or method=='l':
        return get_lastday_month(N)
    else:
        return get_firstday_month(N)
#回退数据日期
def get_back_date(date,N,trade_list):
    
    if not date in trade_list:
        date = max([i for i in trade_list if i <= date])
        if N>0:
            N = N-1
    
    date_id = trade_list.index(date)-N
    if date_id<0:
        date_id = 0
    elif date_id>=len(trade_list)-1:
        date_id = len(trade_list)-1
    return trade_list[date_id]
#成分股
def get_IdxConsGet(ticker,intoDate):
    intoDate = dateformat_trans(intoDate)
    if len(ticker)>=6:
        sql_str1 = 'select tradeDate from idxconsgets57 where tradeDate<="%s" and ticker="%s" order by tradeDate desc limit 1'
        t0 = pd.read_sql(sql_str1 % (intoDate,ticker),engine)
        t0 = t0.tradeDate.astype(str).tolist()[0]
        sql_strl = 'select * from idxconsgets57 where ticker="%s" and tradeDate="%s"'
        x = get_db_data(db_yq,sql_strl % (ticker,t0))
    else:
        sql_str1 = 'select tradeDate from idxconsgets57 where tradeDate<="%s"  order by tradeDate desc limit 1'
        t0 = pd.read_sql(sql_str1 % (intoDate),engine)
        t0 = t0.tradeDate.astype(str).tolist()[0]
        sql_strl = 'select * from idxconsgets57 where tradeDate="%s"'
        x = get_db_data(db_yq,sql_strl % (t0))
    return x.consTickerSymbol.unique(),x.consID.unique()


#开始时间或终止时间 表格时间
def get_table_date(tn,eg,key='tradeDate',order=1):
    sql_tmp = 'select `%s` from `%s` order by `%s` %s limit 1'
    if order==1:
        sql_tmp =sql_tmp % (key,tn,key,'desc')
    else:
        sql_tmp = sql_tmp % (key,tn,key,' ')
    if isinstance(eg,str):
        x = get_db_data(eg,sql_tmp)
    else:
        x = pd.read_sql(sql_tmp,eg)
    if len(x)>0:        
        return x[key].astype(str).tolist()[0]
    else:
        return []
    
def dateformat_trans(t):
    if isinstance(t,int):
        t = str(t)
    if len(t)==8:
        t = '%s-%s-%s' % (t[:4],t[4:6],t[6:])
    return t

def DataAPI_EcoDataProGet(ticker,t0,tt,field='*',asc=False):
    if isinstance(ticker,str):
        ticker_sel = ticker
    else:
        ticker_sel = list_to_str_f(ticker)
        
    if not isinstance(field,str):
        field = ','.join(field)
    
            
    sql_str_index = '''select %s from ecodataproget_s70 where periodDate>="%s" 
        and periodDate<="%s" and indicID in (%s)'''
    sql_str_index = sql_str_index % (field,t0,tt,ticker_sel)
    x = get_db_data(db_yq,sql_str_index)
    x = x.sort_values('periodDate',ascending=asc)
    return x

def MktIdxFactorDateRangeGet(ticker,t0='20210220',tt='20210225',field='*',asc=False):
    if isinstance(ticker,str):
        ticker_sel = ticker
    else:
        ticker_sel = list_to_str_f(ticker)
        
    if not isinstance(field,str):
        field = ','.join(field)
    t0 = dateformat_trans(t0)
    tt = dateformat_trans(tt)        
    sql_str_index = '''select %s from mktidxfactoronedayget_s70 where tradeDate>="%s" 
        and tradeDate<="%s" and ticker in (%s)'''
    sql_str_index = sql_str_index % (field,t0,tt,ticker_sel)
    x = get_db_data(db_yq,sql_str_index)
    x = x.sort_values('tradeDate',ascending=asc)
    x.tradeDate = x.tradeDate.astype(str)
    return x

def RMExposureDayGet(beginDate, endDate,field='*',ticker=""):
    sql_tmp1 = 'select %s from rmexposuredaygets73 where tradeDate>="%s" and tradeDate<="%s"'
    sql_tmp2 = 'select %s from rmexposuredaygets73 where tradeDate>="%s" and tradeDate<="%s" and ticker in (%s)'
    if isinstance(field,list):
        field = ','.join(field)
    if len(ticker)>0:
        if isinstance(ticker,list):
            ticker = list_to_str_f(ticker)
        sql_tmp = sql_tmp2 % (field,beginDate,endDate,ticker)
    else:
        sql_tmp = sql_tmp1 % (field,beginDate,endDate)
    return get_db_data(db_yq,sql_tmp)
        
def get_us_daytick(ticker,t0,tt):
    sql_str = '''select * from usastock_day where ticker = "%s" 
        and tradeDate>="%s" and tradeDate<="%s" order by tradeDate'''
    x = get_db_data(db_name_polygon,sql_str % (ticker,t0,tt))
    return x


def get_spx_daytick(ticker,t0,tt):
    sql_str = '''select * from spx_tick where ticker = "%s" 
        and tradeDate>="%s" and tradeDate<="%s" order by tradeDate'''
    x = get_db_data(db_name_polygon,sql_str % (ticker,t0,tt))
    return x

def get_us_mintick(ticker,t0='1990-01-01',tt='2099-01-01'):
    import sqlite3
    with open('para.json','r',encoding='utf-8') as f:
        para = json.load(f)
    p2 = para['sql3_usstock']
    sql_tmp = 'select * from %s where tradeDate>="%s" and tradeDate<="%s" order by tradeDate'
    with sqlite3.connect(os.path.join(p2,'%s.db3' % ticker)) as conn:
        x = pd.read_sql_query(sql_tmp % (ticker,t0,tt),conn)
    return x

def do_sql3_order(sql_tmp,ticker,sel='fx'):
    import sqlite3
    with open('para.json','r',encoding='utf-8') as f:
        para = json.load(f)
    if sel=='forex' or sel=='fx':
        p1 = para['sql3_forex']
    elif sel == 'cry':
        p1 = para['cry']
    with sqlite3.connect(os.path.join(p1,'%s.db3' % ticker)) as conn:
        cur = conn.cursor()
        cur.execute(sql_tmp)
    
def get_forex_mintick(ticker,t0='1990-01-01',tt='2099-01-01',sel='forex'):
    import sqlite3
    with open('para.json','r',encoding='utf-8') as f:
        para = json.load(f)
    if sel=='forex' or sel=='fx':
        p1 = para['sql3_forex']
    elif sel == 'cry':
        p1 = para['cry']
    sql_tmp = 'select * from %s where tradeDate>="%s" and tradeDate<="%s" order by tradeDate'
    with sqlite3.connect(os.path.join(p1,'%s.db3' % ticker)) as conn:
        x = pd.read_sql_query(sql_tmp % (ticker,t0,tt),conn)
    return x


def get_us_adj(ticker):
    sql_str = 'select exDate as tradeDate,ratio from p_split where ticker = "%s" order by tradeDate desc'
    x=get_db_data(db_name_polygon,sql_str % ticker)
    return x

def get_spx_daytick_adj(ticker,t0="2000-01-01",tt="2099-01-01"):
    x1 = get_spx_daytick(ticker,t0,tt)
    x2 = get_us_adj(ticker)
    x2['ratio'] = x2.ratio.cumprod()
    
    x3 = x1.merge(x2,how = 'outer',on=['tradeDate'])
    x3.sort_values(by='tradeDate',inplace=True)
    x3.ratio.fillna(method='bfill',inplace=True)
    x3.ratio.fillna(1,inplace=True)
    x3.dropna(subset=['t'],inplace=True)
    var = ['openPrice', 'closePrice', 'highPrice','lowPrice']
    for sub_var in var:
        x3['%s_adj' % sub_var] = x3[sub_var] * x3['ratio']
    return x3    


def get_us_daytick_adj(ticker,t0="2000-01-01",tt="2099-01-01"):
    x1 = get_us_daytick(ticker,t0,tt)
    x2 = get_us_adj(ticker)
    x2['ratio'] = x2.ratio.cumprod()
    
    x3 = x1.merge(x2,how = 'outer',on=['tradeDate'])
    x3.sort_values(by='tradeDate',inplace=True)
    x3.ratio.fillna(method='bfill',inplace=True)
    x3.ratio.fillna(1,inplace=True)
    x3.dropna(subset=['t'],inplace=True)
    var = ['openPrice', 'closePrice', 'highPrice','lowPrice']
    for sub_var in var:
        x3['%s_adj' % sub_var] = x3[sub_var] * x3['ratio']
    return x3    
#获取sp500成分股    
def get_spx_com(t0,dis=True):
    sql_str = 'select tradeDate,tickers from sp500_com where tradeDate<="%s" order by tradeDate desc limit 1' % t0
    x = get_db_data(db_datapro,sql_str)
    tt = x.tradeDate.astype(str).values[0]
    ticker = x.tickers.values[0].split(',')
    if dis:
        print('SPX-com %s %s ' % (t0,tt))
    return ticker
#一段时间的SP500成分股
def get_spx_com_all(t0,tt,dis=True):
    sql_str = 'select tradeDate,tickers from sp500_com where tradeDate>="%s" and tradeDate<="%s" ' % (t0,tt)
    x = get_db_data(db_datapro,sql_str)
    ticker = [x.iloc[i].tickers.split(',') for i in range(len(x))]
    tmp = []
    for i in ticker:
        tmp = tmp+i
    tmp = pd.DataFrame({'ticker':tmp}).ticker.unique().tolist()
    ticker = list(set(tmp))
    if dis:
        print('SPX-com %s %s ' % (t0,tt))
    return ticker

def table_in_database(dn,tn):
    x = get_db_data(db_yq,'show tables from %s' % dn)
    if len(x)>0:
        x = x[x.columns[0]].tolist()
        return tn in x
    else:
        return False

def get_delta_date(t='2021-01-01',days=365):
    if isinstance(t,str):
        t = datetime.strptime(t,'%Y-%m-%d')
    t = t-timedelta(days=days)
    t = t.strftime('%Y-%m-%d')
    return t

def export_zx02_symbolpool(taskID = 57):
    tn = 'symbol_pool_s%d' % taskID
    pn0 = r'para_pool_S%d' % taskID
    if not os.path.exists(pn0):
        os.mkdir(pn0)
    def un_fold_data(v):
        tradeDate=v.tradeDate
        pool_l = v.pool_l.split(',')
        if ',' in v.pool_l:
            pool_s = v.pool_s.split(',')
        else:
            pool_s = v.pool_s.split(' ')
        
        tmp= pd.DataFrame({'ticker':pool_l+pool_s})
        tmp['tradeDate'] = tradeDate
        tmp['sig'] = 1
        tmp['sig'][tmp.ticker.isin(pool_s)] = -1
        return tmp
    x = get_db_data('zx02','select * from %s order by tradeDate' % tn)
    mID = x.mID.unique().tolist()
    poolID = x.poolID.unique().tolist()    
    for sub_id in mID:
        for sub_pool_id in poolID:
            sub_x = x[(x.mID==sub_id) & (x.poolID==sub_pool_id)][['tradeDate','pool_l','pool_s']]
            sub_x1 = sub_x.apply(lambda x:un_fold_data(x),axis=1)
            sub_x1 = pd.concat(sub_x1.tolist())
            sub_x2 = sub_x1.set_index(['tradeDate','ticker']).unstack()
            #recored
            fn = 'position-S%d-%s-%s.csv' % (taskID,sub_pool_id,sub_id)
            fn = os.path.join(pn0,fn)
            sub_x2.to_csv(fn)
            
def last_day_of_month(any_day):
    #获取每个月的最后一天
    next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
    return next_month - timedelta(days=next_month.day) 

def EquAnnoInfoGet(ticker, beginDate,endDate, field):
    if isinstance(field,list):
        field = ','.join(field)
    sql_tmp1 = 'select %s from equannoinfoget_s80 where ticker = "%s" and publishDate>="%s" and publishDate<="%s" order by publishDate'
    sql_tmp2 = 'select %s from equannoinfoget_s80 where publishDate>="%s" and publishDate<="%s" order by publishDate'
    if len(ticker)>0:
        sql_tmp = sql_tmp1 % (field,ticker,beginDate,endDate)
    else:
        sql_tmp = sql_tmp2 % (field,beginDate,endDate)
    x = get_db_data(db_yq,sql_tmp)
    return x
    
def ResRrMainGet(secCode,beginDate,endDate,field,key = 'endDate'):
    if isinstance(field,list):
        field = ','.join(field)    
    beginDate = dateformat_trans(beginDate)
    endDate = dateformat_trans(endDate)    
    if key=='endDate':
        sql_tmp1 = 'select %s from resrrmaingets80 where secCode = "%s" and writeDate>="%s" and writeDate<="%s" order by writeDate'
        sql_tmp2 = 'select %s from resrrmaingets80 where writeDate>="%s" and writeDate<="%s" order by writeDate'
    else:
        sql_tmp1 = 'select %s from resrrmaingets80 where secCode = "%s" and publishDate>="%s" and publishDate<="%s" order by publishDate'
        sql_tmp2 = 'select %s from resrrmaingets80 where publishDate>="%s" and publishDate<="%s" order by publishDate'
    if len(secCode)>0:
        sql_tmp = sql_tmp1 % (field,secCode,beginDate,endDate)
    else:
        sql_tmp = sql_tmp2 % (field,beginDate,endDate)
    x = get_db_data(db_yq,sql_tmp)
    return x

def FdmtISAllLatestGet(ticker, beginDate,endDate, field):
    if isinstance(field,list):
        field = ','.join(field)
    sql_tmp1 = 'select %s from fdmtisalllatestgets80 where ticker = "%s" and publishDate>="%s" and publishDate<="%s" order by publishDate'
    sql_tmp2 = 'select %s from fdmtisalllatestgets80 where publishDate>="%s" and publishDate<="%s" order by publishDate'
    beginDate = dateformat_trans(beginDate)
    endDate = dateformat_trans(endDate)
    if len(ticker)>0:
        sql_tmp = sql_tmp1 % (field,ticker,beginDate,endDate)
    else:
        sql_tmp = sql_tmp2 % (field,beginDate,endDate)
    x = get_db_data(db_yq,sql_tmp)
    return x
#获取月度交易的起止时间
def get_month_cal():
    sql_tmp = 'select * from yuqer_cal where exchangeCD = "XSHG" and isOpen=1 order by calendarDate'
    t = get_db_data(db_yq,sql_tmp)
    t.calendarDate = t.calendarDate.astype(str)
    t['isMonthBegin'] = t.isMonthEnd.shift(1)
    t = t[(t['isMonthBegin']==1) | (t.isMonthEnd==1)]
    t1 = t[t['isMonthBegin']==1].calendarDate.tolist()
    t2 = t[t.isMonthEnd==1].calendarDate.tolist()
    t = t[['calendarDate']]
    t['m'] = t.calendarDate.apply(lambda x:x[:7])
    t1_a = dict(zip([i[:7] for i in t1],t1))
    t2_a = dict(zip([i[:7] for i in t2],t2))
    t['t1'] = t.m.map(t1_a)
    t['t2'] = t.m.map(t2_a)
    return t1,t2,t

#获取单个股票的序列数据
def yq_MktStockFactorsOneDayProGet_seri(ticker='000001',t0='1990-01-01',tt='3099-01-01',var="*"):
    sql_str = 'select %s from yq_mktstockfactorsonedayproget where ticker = "%s" and tradeDate>="%s" and tradeDate <="%s"'
    x = get_db_data(db_yq,sql_str % (var,ticker,t0,tt))
    return x

def get_fee_info():
    index_id_zx02 = ['kosdaq', 'kospi', 'msci', 'ndx', 'nifty', 'nky', 'RTY', 'set50', 'sx5e',
                       'ukx', 'xin9i']
    fee1_tmp = [3/10000,3/10000,2/10000,1/10000,1/1000,1/10000,1/10000,11/10000,1/10000,1/10000,2/10000]
    fee2_tmp = [3/1000,3/1000,32/10000,1/10000,1/1000,1/10000,1/10000,22/10000,1/10000,1/10000,12/10000]
    fee1 = dict(zip(['US','HK','forex_day','as51','topix','twse','csi','hsce','hk_ggt'],[1,11,0.25,1,1,2,2,11,11]))
    fee2 = dict(zip(['US','HK','forex_day','as51','topix','twse','csi','hsce','hk_ggt'],[1,11,0.25,1,1,32,12,11,11]))
    fee1_1 = dict(zip(index_id_zx02,[i*10000 for i in fee1_tmp]))
    fee2_1 = dict(zip(index_id_zx02,[i*10000 for i in fee2_tmp]))
    fee1.update(fee1_1)
    fee2.update(fee2_1)
    return fee1,fee2

def get_IdxCons_multi(intoDate,ticker='000300'):
    intoDate = [str(i) for i in intoDate]
    sql_tmp = """select tradingdate from yuqerdata.idxcloseweightget where 
        ticker='%s' and tradingdate<='%s'  order by tradingdate desc limit 1""" %(ticker,min(intoDate))
    t = pd.read_sql(sql_tmp,engine)
    if len(t)>0:
        t = t[t.columns[0]].values[0]
    else:
        t = '1990-01-01'
    sql_str1 = """select ticker,tradingdate,symbol from yuqerdata.idxcloseweightget where ticker = '%s'
        and tradingdate >= '%s' and tradingdate<='%s' """ %(ticker,t,max(intoDate))
        
    x = pd.read_sql(sql_str1,engine)
    x.tradingdate = x.tradingdate.astype(str)
    tref1 = x.tradingdate.unique().tolist()

    X = []
    for sub_t in intoDate:
        t =[i for i in tref1 if i<=sub_t]
        if len(t)>0:
            t = max(t)
            tmp = x[x.tradingdate==t].copy()
            tmp['tradingdate'] = sub_t
            X.append(tmp)
    X = pd.concat(X)
    X.rename(columns={'tradingdate':'tradeDate'},inplace=True)
    return X

#
def get_IdxCons_multi2(intoDate,ticker='000300'):
    intoDate = [str(i) for i in intoDate]
    sql_tmp = """select effDate from yuqerdata.midxcloseweightget_s76 where 
        ticker='%s' and effDate<='%s'  order by effDate desc limit 1""" %(ticker,min(intoDate))
    t = pd.read_sql(sql_tmp,engine)
    if len(t)>0:
        t = t[t.columns[0]].values[0]
    else:
        t = '1990-01-01'
    sql_str1 = """select ticker,effDate,consTickerSymbol as symbol from yuqerdata.midxcloseweightget_s76 where ticker = '%s'
        and effDate >= '%s' and effDate<='%s' """ %(ticker,t,max(intoDate))
        
    x = pd.read_sql(sql_str1,engine)
    x.effDate = x.effDate.astype(str)
    tref1 = x.effDate.unique().tolist()

    X = []
    for sub_t in intoDate:
        t =[i for i in tref1 if i<=sub_t]
        if len(t)>0:
            t = max(t)
            tmp = x[x.effDate==t].copy()
            tmp['effDate'] = sub_t
            X.append(tmp)
    X = pd.concat(X)
    X.rename(columns={'effDate':'tradeDate'},inplace=True)
    return X

def get_tdx_index_info():
    index_id_zx02 = ['kosdaq', 'kospi', 'msci', 'ndx', 'nifty', 'nky', 'RTY', 'set50', 'sx5e',
                       'ukx', 'xin9i','hsi']
    index_id_zx02_info = ['KOSDAQ','KOSPI2','TAMSCI','NDX','NIFTY','NKY','RTY','SET50','SX5E',
                      'UKX','XIN9I','HSI']
    index_tdx = {'as51':'AS51','topix':'TPX','twse':'TWSE','hsce':'HSCEI'}
    index_tdx.update(dict(zip(index_id_zx02,index_id_zx02_info)))
    return index_tdx

def check_month_end(x):
    v = []
    i=0
    while i<40:
        i=i+1
        tmp1 = x+timedelta(days=i)
        if tmp1.month==x.month:
            v.append(tmp1)
        else:
            i=1e10
    if len(v)==0:
        OK = True
    else:
        OK = True
        for sub_t in v:
            if sub_t.weekday()<=4:
                OK=False
                break
    return OK

def insert_data_sql(x,tn,dn,app='append',index=False):
    #eg = pymysql.connect(host=host,user=user_name,password=pass_wd,database=dn)
    
    #print(eg)
    eg = create_db(dn)
    x.to_sql(tn,eg,if_exists=app,index=index,chunksize=8000)
    #eg.commit()
    #eg.close() 

def get_iso_index_data_68(index_id='as51',t0='1990-01-01',tt='2099-01-01',key_str = "*"):
    index_tdx = get_tdx_index_info()
    ticker = index_tdx[index_id]
    sql_tmp = 'select %s from main_index_s68 where index_id = "%s" and ticker = "%s" and tradeDate>="%s" and tradeDate<="%s" order by tradeDate'
    return get_db_data('data_pro',sql_tmp % (key_str,index_id,ticker,t0,tt))

#过滤停复牌股
def filter_paused_stock(t0,tt):
    sql_tmp = 'select distinct(ticker) from yq_sechaltget where haltBeginTime<="%s 16:00:00" and (haltEndTime>="%s 09:00:00" or haltEndTime is null) and assetClass="E"'
    x = get_db_data('yuqerdata',sql_tmp %(t0,tt))
    return x

#获取上市时间，并过滤次新
def filter_new_stock(t0,N):
    sql_tmp = 'select ticker,listDate,delistDate from equget where equTypeCD = "A" and length(ticker)=6 and listDate is not null order by ticker,listDate'
    x = get_db_data('yuqerdata',sql_tmp)
    x = x[x.ticker.apply(lambda x:x[0] in '360')]
    x.delistDate.fillna('2099-01-01',inplace=True)
    x.listDate = x.listDate.astype(str)
    x.delistDate = x.delistDate.astype(str)
    t0_N = get_delta_date(t0,N)
    y = x[(x.listDate<=t0_N) & (x.delistDate>t0)]
    return y.ticker.unique().tolist()

#A股交易日，含未之星交易日
def get_tradingdate_A():
    sql_tmp = 'select * from yq_tradingdate_future'
    x = get_db_data('yuqerdata',sql_tmp)
    if len(x)>0:
        x.tradingdate = x.tradingdate.astype(str)
        x = x.tradingdate.astype(str).tolist()
        x.sort()
        return x
    else:
        print('表格yq_tradingdate_future未更新成功，请核查')
        
def get_iso_ticker_data_68(ticker,index_id='as51',t0='1990-01-01',tt='2099-01-01',key_str = "*"):
    sql_tmp = 'select %s from main_index_s68 where index_id = "%s" and ticker = "%s" and tradeDate>="%s" and tradeDate<="%s" order by tradeDate'
    return get_db_data('data_pro',sql_tmp % (key_str,index_id,ticker,t0,tt))

#选择”退“的股票
def get_delist_ticker(t0):
    sql_tmp = 'select * from instnamechgget where  chgDate<"%s" order by chgDate' % t0
    x = get_db_data('yuqerdata',sql_tmp)
    x.drop_duplicates('secID',keep='last',inplace=True)
    x = x[x.secShortName.apply(lambda x:(x[-1]=='退') or (x.startswith('ST'))or (x.startswith('PT')) or (x.startswith('*ST')))]
    if len(x)>0:
        return x.ticker.tolist(),x.secID.tolist()
    else:
        return [],[]
#获取特殊状态股票    
def get_special_code(t0):
    sql_tmp = 'select * from equinstsstateget where effDate <"%s" order by effDate' % t0
    x = get_db_data('yuqerdata',sql_tmp)
    x.drop_duplicates('secID',keep='last',inplace=True)
    x = x[x.partyState!=3]
    return x.ticker.tolist()

#公司股本变动(新)
def EquSharesChgGet(t0,tt,key_str):
    tmp = 'EquSharesChgGetS109'.lower()
    sql_tmp = 'select %s from %s where publishDate>="%s" and publishDate<="%s"' % (key_str,tmp,t0,tt)
    return get_db_data('yuqerdata',sql_tmp)
    
    