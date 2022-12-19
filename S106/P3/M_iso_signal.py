# -*- coding: utf-8 -*-
"""
Created on Sat Sep 17 16:13:15 2022

@author: adair2019
"""

import pandas as pd
from bac_toolS106P3 import get_s106p3_sig,export_position
from yq_toolsS45_linux import get_db_data
from tqdm import tqdm
from yq_toolsS45_linux import get_tdx_index_info


index_info = get_tdx_index_info()
index_id = list(index_info.keys())

index_info = get_tdx_index_info()


sql_f1 = 'select ticker,tradeDate,closePrice as `close` from main_index_s68 where index_id = "%s"'
sql_f2 = 'select ticker,tradeDate,closePrice as `close` from main_index_s68 where index_id = "%s" and ticker = "%s"'
for sub_index_id in index_id:
    print(sub_index_id)
    sub_index_ticker = index_info[sub_index_id]
    if sub_index_id in list(index_info.keys()):
        x = get_db_data('data_pro',sql_f1 % sub_index_id)
        x.tradeDate = x.tradeDate.astype(str)
        #tickers = pool[pool.tradingdate==pool.tradingdate.max()].symbol.unique().tolist()
        tickers = x.ticker.unique().tolist()
        r = []
        for ticker in tqdm(tickers):
            if ticker!=sub_index_ticker:
                sub_x = x[x.ticker==ticker].copy()
                if len(sub_x)>200:
                    sub_x.sort_values('tradeDate',inplace=True)
                    sub_x.drop_duplicates(subset=['tradeDate'],inplace=True)
                    sub_x.reset_index(drop=True,inplace=True)
                    sub_r = get_s106p3_sig(sub_x)
                    r.append(sub_r)
        r=pd.concat(r)
        if sub_index_id == 'sx5e':
            r = r[r.ticker!='SAN']
        export_position(r,sub_index_id)

