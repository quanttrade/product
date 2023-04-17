# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 09:32:53 2023
回测
@author: adair2019
"""

from yq_toolsS45_linux import time_use_tool
from yq_toolsS45_linux import get_db_data
import pandas as pd
from yq_toolsS45_linux import get_MktEqudAdjAfGet
import quant_utilS73 as qutil
from yq_toolsS45_linux import get_MktEqumAdjGet_update
from yq_toolsS45_linux import create_db
import os
from yq_toolsS45_linux import get_file_name
from yq_toolsS45_linux import get_inidata


obj_t = time_use_tool()
eg37 = create_db('s37')
f_cols = ['width_factor1', 'bias_factor3', 'width_factor2','bias_factor4'] + \
        ['revs_20', 'revs_overnight_20','revs_intraday_20', 'corr_overnight_20', 'abs_overnight_20']

dn = 's37'
tn1 = 'symbol_pool_s109p1'
tn2 = 'symbol_pool_s109p2'
tn3 = 'symbol_pool_s109f'
tn4 = 's109_return'
ngrp = 10
pool_dir = 'pool_s109'
if not os.path.exists(pool_dir):
    os.mkdir(pool_dir)
info_dic0 = {0:'未中性化',1:'市值中性化',2:'全风格中性化'}    

    
if __name__ == "__main__":
    
    tmp1 = get_inidata(tn1,eg = eg37)
    tmp2 = get_inidata(tn2,eg = eg37)
    tmp3 = get_inidata(tn3,eg = eg37)
    tmp4 = get_file_name(pool_dir,'.xlsx')
    if len(tmp4[-1])>0:
        tmp4 = os.path.splitext( tmp4[-1][-1])[0][-10:]
    else:
        tmp4 = '1990-01-01'
    
    if tmp1 > tmp3 or tmp2> tmp3 or tmp3 != tmp4:   
        X = []
        for tn in [tn1,tn2]:
            X.append(get_db_data(dn,'select * from %s order by tradeDate' % tn))
            
        #chg
        r = get_MktEqudAdjAfGet('2010-01-01', '3099-0101', 'ticker, tradeDate, closePrice/preClosePrice-1 as r')
        r.tradeDate = r.tradeDate.astype(str)
        tref = r.tradeDate.unique().tolist()
        t_map = dict(zip(tref[:-2], tref[2:]))
        
        
        #因子处理
        #股票池
        sql_tmp = 'select tradingdate as tradeDate,symbol as ticker from idxcloseweightget where ticker="%s"'
        symbol_pool = {}
        for pool in ['000300','000905']:
            tmp = get_db_data('yuqerdata', sql_tmp % pool)
            tmp.tradeDate = tmp.tradeDate.astype(str)
            symbol_pool[pool] = tmp
        
        
        fac_re = []
        y1 = []
        for f in X:
            f.tradeDate = f.tradeDate.astype(str)
            tmp_fac = list(set(f_cols) & set(f.columns.tolist()))
            #获取股票池 f_pool
            for pre in range(3):
                sub_f = f[f.pre==pre]
                for pool in ['A','000300','000905']:
                    if pool in symbol_pool.keys():
                        sub_sub_f = symbol_pool[pool].merge(sub_f,on=['ticker', 'tradeDate'],how='inner')
                    else:
                        sub_sub_f = sub_f                
                    for sub_fac in tmp_fac:                
                        sub_pool = qutil.signal_grouping(sub_sub_f, factor_name=sub_fac, ngrp=ngrp)
                        tmp = sub_pool[sub_pool.group.isin([0,9])]
                        tmp.drop_duplicates(subset=['tradeDate','ticker'],inplace = True)
                        tmp = tmp.pivot('tradeDate','ticker','group')
                        fn_pool = os.path.join(pool_dir,'%s-%s-%s-%s.xlsx' % (sub_fac,pool,info_dic0[pre],tmp.index.max()))
                        tmp.to_excel(fn_pool)
                        sub_pool_l = sub_pool[sub_pool.group==9].groupby('tradeDate').apply(lambda x:','.join(x.ticker.tolist()))
                        sub_pool_l.name = 'l'
                        sub_pool_s = sub_pool[sub_pool.group==0].groupby('tradeDate').apply(lambda x:','.join(x.ticker.tolist()))
                        sub_pool_s.name = 's'
                        sub_pool = pd.concat([sub_pool_s,sub_pool_l],axis=1)
                        sub_pool['fac_name'] = sub_fac
                        sub_pool['pre'] = pre
                        sub_pool['pool'] = pool
                        fac_re.append(sub_pool)
            #选股结果完成
            #月度
            mret_df = get_MktEqumAdjGet_update(min(tref), max(tref))
            mret_df.rename(columns={'endDate':'tradeDate', 'chgPct':'curr_ret'}, inplace=True)  # 交易日列和收益率列
            mret_df['tradeDate'] = mret_df['tradeDate'].astype(str)
            mret_df.sort_values(['ticker', 'tradeDate'], inplace=True)
            mret_df['nxt_ret'] = mret_df.groupby('ticker')['curr_ret'].shift(-1)
            for pre in range(3):
                sub_f = f[f.pre==pre]
                for pool in ['A','000300','000905']:
                    if pool in symbol_pool.keys():
                        sub_sub_f = symbol_pool[pool].merge(sub_f,on=['ticker', 'tradeDate'],how='inner')
                    else:
                        sub_sub_f = sub_f.copy() 
                    for fac_name in tmp_fac:
                        a1, a2 = qutil.simple_group_backtest(sub_sub_f, mret_df, fac_name, 'nxt_ret', ngrp=10, commission=0)
                        a3 = a1.pivot_table(values='period_ret', index='tradeDate', columns='group')
                        sub_a = pd.DataFrame({'l':a3[9],'s':a3[0]}, index = a3.index)
                        sub_a['ls'] = sub_a.l - sub_a.s
                        sub_a['fac_name'] = fac_name
                        sub_a['pre'] = pre
                        sub_a['pool'] = pool
                        
                        (1+sub_a.ls).cumprod().plot(title='%s-%d' % (fac_name,pre))
                        y1.append(sub_a)
        fac_re = pd.concat(fac_re)
        y1 = pd.concat(y1)
        #保存
        
        fac_re.index.name = 'tradeDate'
        fac_re.reset_index(inplace = True)
        fac_re.to_sql(tn3,eg37, if_exists = 'replace' ,index=False, chunksize=10000)
        
        
        y1.index.name = 'tradeDate'
        y1.reset_index(inplace = True)
        y1.to_sql(tn4,eg37, if_exists = 'replace' ,index=False, chunksize=10000)
    
    obj_t.use()