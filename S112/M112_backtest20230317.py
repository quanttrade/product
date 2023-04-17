# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 11:22:09 2023
回测，并保存曲线结果

升级程序，list copy问题
@author: adair2019
"""

import quant_utilS73 as qutil
import pandas as pd
from yq_toolsS45_linux import mIdxCloseWeightGet
from yq_toolsS45_linux import get_delta_date
from yq_toolsS45_linux import get_week_month_tradeDate_update
from yq_toolsS45_linux import get_db_data

ticker_300 = mIdxCloseWeightGet('000300','1990-01-01','3099-01-01','consTickerSymbol,effDate as tradeDate')
ticker_300.tradeDate = ticker_300.tradeDate.astype(str)
ticker_300.rename(columns ={'consTickerSymbol':'ticker'},inplace = True)
ticker_300['m'] = ticker_300.tradeDate.apply(lambda x:get_delta_date(x,-10)[:7])
del ticker_300['tradeDate']
ticker_300 = list(ticker_300.groupby('m'))
ticker_300 = dict(zip([i[0] for i in ticker_300],[i[1] for i in ticker_300]))

ticker_500 = mIdxCloseWeightGet('000905','1990-01-01','3099-01-01','consTickerSymbol,effDate as tradeDate')
ticker_500.tradeDate = ticker_500.tradeDate.astype(str)
ticker_500.rename(columns ={'consTickerSymbol':'ticker'},inplace = True)
ticker_500['m'] = ticker_500.tradeDate.apply(lambda x:get_delta_date(x,-10)[:7])
del ticker_500['tradeDate']
ticker_500 = list(ticker_500.groupby('m'))
ticker_500 = dict(zip([i[0] for i in ticker_500],[i[1] for i in ticker_500]))


tn1 = 'symbol_pool_s112'
tn2 = '%s_ner' % tn1

tnr_1 = 's112_return_d2'
tnr_2 = 's112_return_d5'
tmp_t0 = '1990-01-01'
sql_tmp1 = 'select * from %s where tradeDate >="%s"'
f1 = get_db_data('s37',sql_tmp1 % (tn1,tmp_t0))
f2 = get_db_data('s37',sql_tmp1 % (tn2,tmp_t0))
f1.tradeDate = f1.tradeDate.astype(str)
f2.tradeDate = f2.tradeDate.astype(str)
r1 = get_db_data('s37',sql_tmp1 % (tnr_1,tmp_t0))
r2 = get_db_data('s37',sql_tmp1 % (tnr_2,tmp_t0))
r1.tradeDate = r1.tradeDate.astype(str)
r2.tradeDate = r2.tradeDate.astype(str)
fr1 = f1.merge(r1,how = 'left', on = ['ticker','tradeDate']).merge(r2,how = 'left', on = ['ticker','tradeDate'])
fr2 = f2.merge(r1,how = 'left', on = ['ticker','tradeDate']).merge(r2,how = 'left', on = ['ticker','tradeDate'])


R = []
for info0 in ['原因子','中性化']:
    if info0 == '中性化':
        F = fr2
    else:
        F = fr1
    F = F[F.tradeDate>='2006-01-01']
    F = F[F.tradeDate <='2023-01-01']
    
    tref = get_week_month_tradeDate_update('2006-01-01','3099-01-01')
    tref = tref[0]
    tref.sort()
    x0 = pd.DataFrame({'tradeDate':tref})
    
    x2 = x0[x0.index%2==0]
    x5 = x0[x0.index%5==0]
    
    tref_pool = [x2.tradeDate.tolist(),x5.tradeDate.tolist()]
    tref_info = dict(zip([0,1],['2d','5d']))
    r_info = dict(zip([0,1],['rcc2','rcc5']))
    for i,sub_t in enumerate(tref_pool) :    
        sub_F0 = F[F.tradeDate.isin(sub_t)]
        for sub_pool in ['A','000300','000905']:
            if sub_pool =='A':
                sub_F = sub_F0
            else:
                if sub_pool == '000300':
                    sub_p = ticker_300
                else:
                    sub_p = ticker_500
                #合并，计算集合
                #这里有问题！！！
                tmp = []
                for sub_sub_t in sub_t:
                    tmp0 = sub_p[sub_sub_t[:7]].copy()
                    tmp0['tradeDate'] = sub_sub_t
                    tmp.append(tmp0)
                tmp = pd.concat(tmp)
                sub_F = sub_F0.merge(tmp,on=['ticker','tradeDate'])
            for factor in ['HB','RVS','NewRVS']:
                a1, a2 = qutil.simple_group_backtest_adair(sub_F, factor, r_info[i], ngrp=5, commission=0)
                r = a1.pivot('tradeDate','group','period_ret')
                r = r.reset_index()
                r['fac_info'] = '%s-%s-%s-%s-%s' % (info0,factor,tref_info[i], r_info[i],sub_pool)
                R.append(r)
R = pd.concat(R)
R.to_excel('bacre_0317.xlsx')