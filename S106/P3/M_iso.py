# -*- coding: utf-8 -*-
"""
Created on Sat Sep 17 16:13:15 2022

@author: adair2019
"""

import pandas as pd
from bac_toolS106P3 import get_s106p3_sig
from yq_toolsS45_linux import get_db_data,MktIdxdGet
from tqdm import tqdm
from yq_toolsS45_linux import get_tdx_index_info
import os


index_info = get_tdx_index_info()
index_id = list(index_info.keys())

index_info = get_tdx_index_info()


sql_f1 = 'select ticker,tradeDate,closePrice as `close` from main_index_s68 where index_id = "%s"'
sql_f2 = 'select ticker,tradeDate,closePrice as `close` from main_index_s68 where index_id = "%s" and ticker = "%s"'
for sub_index_id in index_id:
    print(sub_index_id)
    sub_index_ticker = index_info[sub_index_id]
    if sub_index_id in list(index_info.keys()):
        fn_re = 're_%s.pkl' % sub_index_id
        if os.path.exists(fn_re):
            r = pd.read_pickle(fn_re)
            x = get_db_data('data_pro',sql_f2 % (sub_index_id,sub_index_ticker))
            x.tradeDate = x.tradeDate.astype(str)
            
        else:
            
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
            r['f_long'] = r.sig_long*r.r
            r['f_short'] = r.sig_short*r.r
            r.to_pickle(fn_re)        
        #r['tradeDate'] = r.index
        #del r['tradeDate']
        if sub_index_id == 'sx5e':
            r = r[r.ticker!='SAN']
        r['f_short'] = -r['f_short']
        #r1 = r.groupby('tradeDate')['f_short','f_long'].mean()
        r1 = r.groupby('tradeDate')['f_short','f_long'].sum()
        tmp = r.groupby('tradeDate')['f_short','f_long'].apply(lambda x:(x.abs()>0).sum())
        r1 = r1/tmp
        r1.fillna(0,inplace=True)
        r1.sort_index(inplace=True)
       
        r1.sort_index(inplace=True)
        r1.rename(columns = dict(zip(['f_short','f_long'],['%s_short' % sub_index_id,'%s_long' % sub_index_id])),inplace=True)
        r0 =x[x.ticker==sub_index_ticker][['tradeDate','close']].copy()
        r0.sort_values('tradeDate',inplace=True)
        r0.drop_duplicates(subset=['tradeDate'],inplace=True)
        r0.set_index('tradeDate',inplace=True,drop=True)
        r0.sort_index(inplace = True)
        r0[sub_index_id] = r0.close.pct_change()
        del r0['close']        
        r1 = r1.merge(r0[[sub_index_id]],left_index=True,right_index=True)
        r1['long-short'] = (r1['%s_long' % sub_index_id] - r1['%s_short' % sub_index_id])/2
        r1['long-%s' % sub_index_id] = (r1['%s_long' % sub_index_id]-r1[sub_index_id])/2
        #r1['%s_short' % sub_index_id] = - r1['%s_short' % sub_index_id]        
        tmp=(1+r1).cumprod().plot(rot=30,title=sub_index_id)
        fig=tmp.get_figure()
        fig.savefig(os.path.join('Figure','%s.png' % sub_index_id),bbox_inches='tight',dpi=300)


