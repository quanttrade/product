# -*- coding: utf-8 -*-
"""
Created on Sat Sep 17 16:13:15 2022
输出所选股票池
@author: adair2019
"""

import pandas as pd
from bac_toolS106P3 import get_s106p3_sig,export_position
from yq_toolsS45_linux import get_db_data,MktIdxdGet
from tqdm import tqdm

sub_index_id = 'A_full'

x0 = MktIdxdGet('DY0001','2014-01-01','2099-01-01','tradeDate,closeIndex as `close`')
x0.tradeDate = x0.tradeDate.astype(str)

sql_tmp = 'select ticker,tradeDate,closePrice as `close` from yq_mktequdadjafget where tradeDate>="2014-01-01"'
x = get_db_data('yuqerdata',sql_tmp)
x.tradeDate = x.tradeDate.astype(str)

p = list(x.groupby('ticker'))
r = []
for ticker,sub_x in tqdm(p):
    if len(sub_x)>200:
        sub_x.sort_values('tradeDate',inplace=True)
        sub_x.drop_duplicates(subset=['tradeDate'],inplace=True)
        sub_x.reset_index(drop=True,inplace=True)
        sub_r = get_s106p3_sig(sub_x)
        r.append(sub_r)
r=pd.concat(r)
export_position(r,sub_index_id)