# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 09:34:36 2023
合成因子
基于M02合成基础因子值Gu Gd，做20日平滑，合成涨幅、跌幅因子
按照自然月执行，效果不如文献上的好，还是需要20天测试结果
@author: adair2019
"""

import pandas as pd
from yq_toolsS45_linux import get_week_month_tradeDate_update
from yq_toolsS45_linux import get_MktEqumAdjGet_update
from quant_utilS73 import simple_group_backtest
import matplotlib.pyplot as plt
import matplotlib as mpl

colors_ = ['xkcd:purple','xkcd:green','xkcd:blue','xkcd:pink',
           'xkcd:brown','xkcd:light blue','xkcd:teal','xkcd:orange',
           'xkcd:light green','xkcd:magenta','xkcd:red']
cmap = mpl.colors.LinearSegmentedColormap.from_list('cmap',colors_)

tref = get_week_month_tradeDate_update('1990-01-01','3099-01-01')
tref_month = tref[2]

f = pd.read_pickle('factor_sec_smoothing_ols_tgd.pkl')
f.symbol = f.symbol.apply(lambda x:x[2:])
tref_f = f.tradeDate.unique().tolist()
tref_f.sort()
tref_map = dict(zip(tref_f[1:],tref_f[:-1]))
f.rename(columns = {'symbol':'ticker'},inplace=True)

ret = get_MktEqumAdjGet_update(tref_f[0],tref_f[-1])
ret.endDate = ret.endDate.astype(str)
ret['tradeDate'] = ret.endDate.map(tref_map)
ret.dropna(inplace=True)
ret.rename(columns = {'chgPct':'r'},inplace = True)

for fac in ['f','tgd']:
    r1,r2 = simple_group_backtest(f,ret,fac,'r',5)    
    r1 = r1.pivot('tradeDate','group','period_ret')
    r1['long-short'] = (r1[4] - r1[0])/2
    #plt.subplot(1,2,1)
    (1+r1).cumprod().plot(rot=30,colormap = cmap, title = fac)
    #plt.plot((1+r1).cumprod(),colormap = cmap)
    plt.legend(r1.columns.tolist(),loc='center left',bbox_to_anchor=(1,0.5))
    plt.show()
