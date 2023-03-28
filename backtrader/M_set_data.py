# -*- coding: utf-8 -*-
"""
Created on Sat Feb 25 11:06:31 2023

@author: adair2019
"""
import pandas as pd
from yq_toolsS45_linux import get_db_data
import os
#get position
tn = 'symbol_pool_s109f'

sql_tmp = 'select * from %s where fac_name = "abs_overnight_20" and pool = "A" and pre = 1'
pool = get_db_data('s37',sql_tmp % tn)
v = pool.groupby('tradeDate').l.apply(lambda x:pd.DataFrame({'sec_code':x.values[0].split(',')})).droplevel(1).reset_index()
w = 1/v.groupby('tradeDate').tradeDate.count()
w = dict(zip(w.index.tolist(),w.values.tolist()))
v['weight'] = v.tradeDate.map(w)
v.rename(columns = {'tradeDate': 'trade_date'}, inplace = True)


#获取数据
fn = 'ret_data.pkl'
if os.path.exists(fn):
    x = pd.read_pickle(fn)
else:
    sql_tmp = 'select * from yq_mktequdadjafget order by tradeDate'
    x = get_db_data('yuqerdata',sql_tmp)
    x.tradeDate = x.tradeDate.astype(str)
    x.to_pickle(fn)
x = x[x.ticker.isin(v.sec_code.unique().tolist())]
#datetime	sec_code	open	high	low	close	volume	openinterest
d1 = 'datetime,sec_code,open,high,low,close,volume'.split(',')
d2 = 'tradeDate,ticker,openPrice,highestPrice,lowestPrice,closePrice,turnoverValue'.split(',')
d = dict(zip(d2,d1))
x.rename(columns = d,inplace = True)
x = x[d1]
x['openinterest'] = 0

x.to_csv('daily_price.csv',index = False)
v.to_csv('trade_info.csv', index = False)