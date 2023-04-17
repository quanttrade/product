# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 09:34:36 2023
验证基础因子合成对错
和M01.m联用作图
@author: adair2019
"""

from yq_toolsS45_linux import get_db_data
import pandas as pd
from tqdm import tqdm


dn = 'ycz_min_history'
N_limit = 50


def get_factor0(sub_x):
    if len(sub_x) >= N_limit:
        sub_x = sub_x.copy()
        sub_x.reset_index(drop=True,inplace=True)
        sub_r = sub_x['close'].pct_change()
        sub_r.iloc[0] = sub_x.iloc[0].close/sub_x.iloc[0].open - 1
        sub_r.name= 'r'
        sub_r = sub_r.to_frame()
        sub_r['U'] = sub_r.index+1
        sub_r['u'] = sub_r.r>0
        sub_r['d'] = sub_r.r<0
        
        sub_r_u = sub_r[sub_r.u]
        Gu = (sub_r_u.U*sub_r_u.r).sum()/(sub_r_u.r.abs().sum())
        
        sub_r_d = sub_r[sub_r.d]
        Gd = -(sub_r_d.U*sub_r_d.r).sum()/(sub_r_d.r.abs().sum())
    else:
        Gd = pd.np.nan
        Gu = pd.np.nan
    
    return pd.DataFrame({'Gu':[Gu],'Gd':[Gd]})


tns = get_db_data(dn,'show tables from %s' % dn)
tns = tns[tns.columns[0]].tolist()
#tns = [i for i in tns if i >=t0]
#tns.sort()
for tn in tqdm(['20160107', '20130301', '20130311']):
    t0 = tn
    x = get_db_data(dn, 'select symbol,hour(tradingdate)*100+minute(tradingdate) as t,`open`,`close` from `%s`' % tn)
    x.sort_values(by = ['symbol', 't'], inplace=True)
    y = x.groupby('symbol').apply(lambda x: get_factor0(x))
    y = y.droplevel(1)
    y.dropna().to_excel('%s.xlsx' % t0)