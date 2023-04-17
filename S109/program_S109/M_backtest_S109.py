# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 09:32:53 2023
回测
@author: adair2019
"""


from yq_toolsS45_linux import get_db_data
import pandas as pd
from yq_toolsS45_linux import get_MktEqudAdjAfGet
import quant_utilS73 as qutil
from yq_toolsS45_linux import get_MktEqumAdjGet_update


f_cols = ['width_factor1', 'bias_factor3', 'width_factor2','bias_factor4'] + \
        ['revs_20', 'revs_overnight_20','revs_intraday_20', 'corr_overnight_20', 'abs_overnight_20']

dn = 's37'
tn1 = 'symbol_pool_s109p1'
tn2 = 'symbol_pool_s109p2'
ngrp = 10


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
y = []
f = X[0]
f.tradeDate = f.tradeDate.astype(str)
tmp_fac = list(set(f_cols) & set(f.columns.tolist()))
fac_re = []
#获取股票池 f_pool
for pre in range(3):
    sub_f = f[f.pre==pre]
    for sub_fac in tmp_fac:
        sub_pool = qutil.signal_grouping(sub_f, factor_name=sub_fac, ngrp=ngrp)
        sub_pool_l = sub_pool[sub_pool.group==9].groupby('tradeDate').apply(lambda x:','.join(x.ticker.tolist()))
        sub_pool_l.name = 'l'
        sub_pool_s = sub_pool[sub_pool.group==0].groupby('tradeDate').apply(lambda x:','.join(x.ticker.tolist()))
        sub_pool_s.name = 's'
        sub_pool = pd.concat([sub_pool_s,sub_pool_l],axis=1)
        sub_pool['fac_name'] = sub_fac
        sub_pool['pre'] = pre
        fac_re.append(sub_pool)
fac_re = pd.concat(fac_re)
#选股结果完成

#回测结果确认-- 月度和日度
f_list = list(f.groupby('tradeDate'))
f_dict = dict(zip([i[0] for i in f_list],[i[1] for i in f_list]))
tmp = pd.DataFrame(index = tref)
tmp['t1'] = pd.np.nan
tmp.loc[f.tradeDate.unique().tolist(),'t1'] = f.tradeDate.unique().tolist()
tmp.sort_index(inplace = True)
tmp.fillna(method="ffill", inplace = True)
tmp.dropna(inplace = True)
tmp.index.name = 'fDate'
tmp.reset_index(inplace = True)
f_t_map = dict(zip(tmp.fDate.tolist(),tmp.t1.tolist()))
f_back = []
for sub_t in f_t_map.keys():
    if sub_t in (t_map.keys()):
        sub_t_ = f_t_map[sub_t]
        tmp = f_dict[sub_t_].copy()
        tmp['fDate'] = sub_t
        tmp['tradeDate'] = t_map[sub_t]
        f_back.append(tmp)
f_back = pd.concat(f_back)

for fac_name in tmp_fac[:1]:
    for pre in range(3)[:1]:
        b1, b2 = qutil.simple_group_backtest(f_back[f_back.pre==pre].copy(), r, fac_name, 'r', ngrp=10, commission=0)
        b3 = b1.pivot_table(values='period_ret', index='tradeDate', columns='group')
        sub_b = pd.DataFrame({'l':b3[9],'s':b3[0],'ls':b3[9]-b3[0]}, index = b3.index)
        sub_b['fac_name'] = fac_name
        sub_b['pre'] = pre
        y.append(sub_b)
        
#月度
mret_df = get_MktEqumAdjGet_update(min(tref), max(tref))
mret_df.rename(columns={'endDate':'tradeDate', 'chgPct':'curr_ret'}, inplace=True)  # 交易日列和收益率列
mret_df['tradeDate'] = mret_df['tradeDate'].astype(str)
mret_df.sort_values(['ticker', 'tradeDate'], inplace=True)
mret_df['nxt_ret'] = mret_df.groupby('ticker')['curr_ret'].shift(-1)

y1 = []
for fac_name in tmp_fac[:1]:
    for pre in range(3)[:1]:
        a1, a2 = qutil.simple_group_backtest(f[f.pre==pre].copy(), mret_df, fac_name, 'nxt_ret', ngrp=10, commission=0)
        a3 = a1.pivot_table(values='period_ret', index='tradeDate', columns='group')
        sub_a = pd.DataFrame({'l':a3[9],'s':a3[0]}, index = a3.index)
        sub_a['ls'] = sub_a.l - sub_a.s
        (1+sub_a.ls).cumprod().plot(title='%s-%d' % (fac_name,pre))
        y1.append(sub_a)