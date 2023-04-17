# -*- coding: utf-8 -*-
"""
Created on Thu Mar 16 19:56:18 2023
历史数据写入
@author: adair2019
"""

import pandas as pd
import quant_utilS73 as qutil
import numpy as np
from sqlalchemy.types import NVARCHAR, Float,DATE,Integer
from yq_toolsS45_linux import create_db


eg = create_db('s37')

F = pd.read_pickle('S112_F02.pkl')
o = pd.read_pickle('forbidden_pool.pkl')


tmp1 = qutil.stock_special_tag('2005-01-01', '2010-01-03', 
                                         pre_new_length=60, dateformat = 1)  # 次新股、st股、停牌个股

tmp2= qutil.stock_special_tag('2022-10-01', '2023-03-10', 
                                         pre_new_length=60, dateformat = 1)  # 次新股、st股、停牌个股

o = pd.concat([tmp1,o,tmp2])
o = o.drop_duplicates(subset=['ticker','tradeDate'])

F = F.merge(o, on = ['ticker', 'tradeDate'], how = 'left')
F = F[F.special_flag.isna()]
#拆分
d1 = ['tradeDate', 'ticker','O', 'C', 'H', 'L', 'V', 'r', 'RVS', 'Vmax',
       'HB', 'NewRVS']
F1 = F[d1]
F1.dropna(subset=['O'],inplace = True)
F1 = F1.replace([np.inf, -np.inf], np.nan)

d1 = dict(zip(d1,[Float] * len(d1)))
d1.update({'tradeDate':DATE})
d1.update({'ticker':NVARCHAR(6)})

tn1 = 'symbol_pool_s112'
F1.to_sql(tn1,eg,if_exists='replace',index=False,chunksize=10000,dtype=d1)


d2 = ['tradeDate', 'ticker','c2',  'o2', 'rcc2', 'rco2']
d2 = dict(zip(d2,[Float] * len(d2)))
d2.update({'tradeDate':DATE})
d2.update({'ticker':NVARCHAR(6)})
F2 = F[d2]
F2.dropna(subset=['c2'], inplace = True)
tn2 = 's112_return_d2'
F2.to_sql(tn2,eg,if_exists='replace',index=False,chunksize=10000,dtype=d2)


d3 = ['tradeDate', 'ticker', 'c5', 'rcc5', 'rco5']
d3 = dict(zip(d3,[Float] * len(d3)))
d3.update({'tradeDate':DATE})
d3.update({'ticker':NVARCHAR(6)})
F3 = F[d3]
F3.dropna(subset=['c5'], inplace = True)
tn3 = 's112_return_d5'
F3.to_sql(tn3,eg,if_exists='replace',index=False,chunksize=10000,dtype=d3)