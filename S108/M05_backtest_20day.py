# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 09:34:36 2023
合成因子
基于M02合成基础因子值Gu Gd，做20日平滑，合成涨幅、跌幅因子
按照自然月执行，效果不如文献上的好，还是需要20天测试结果

去掉新股，去掉ST股票！！！
@author: adair2019
"""

import pandas as pd
from yq_toolsS45_linux import get_week_month_tradeDate_update
from yq_toolsS45_linux import get_db_data
from quant_utilS73 import simple_group_backtest
import matplotlib.pyplot as plt
import matplotlib as mpl1
import matplotlib
font =matplotlib.font_manager.FontProperties(fname='C:\Windows\Fonts\simkai.ttf')
from pylab import mpl
 
#mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei'] # 指定默认字体：解决plot不能显示中文问题
mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

colors_ = ['xkcd:purple','xkcd:green','xkcd:blue','xkcd:pink',
           'xkcd:brown','xkcd:light blue','xkcd:teal','xkcd:orange',
           'xkcd:light green','xkcd:magenta','xkcd:red']
cmap = mpl1.colors.LinearSegmentedColormap.from_list('cmap',colors_)


'''
f = pd.read_pickle('factor_sec_smoothing_ols_tgd.pkl')
f.sk = -f.sk
f.symbol = f.symbol.apply(lambda x:x[2:])
f.rename(columns = {'symbol':'ticker'},inplace=True)
'''
f = get_db_data('s37','select * from s108_factor1')
f.tradeDate = f.tradeDate.astype(str)

tref = get_week_month_tradeDate_update('1990-01-01','3099-01-01')
tref = pd.DataFrame({'tradeDate':tref[0]})
tref.sort_values(by = ['tradeDate'], inplace = True)
tref1 = tref[(tref.tradeDate>='2013-01-07')].copy()
tref1 = tref1.iloc[::20]
tref_f = tref1.tradeDate.unique().tolist()
tref_f.sort()
tref_map = dict(zip(tref_f[1:],tref_f[:-1]))

f = f[f.tradeDate.isin(tref_f)]
#截面排序
f.reset_index(inplace=True,drop =True)
f['sk_rank'] = f.groupby('tradeDate').sk.rank()
f['tgd_rank'] = f.groupby('tradeDate').tgd.rank()

f['tgd_skew'] = f.sk_rank+f.tgd_rank

ret = pd.read_pickle('ret20.pkl')
ret.tradeDate = ret.tradeDate.astype(str)
ret.sort_values(by=['ticker', 'tradeDate'],inplace = True)
ret = ret.groupby('ticker').apply(lambda x:x.set_index(['ticker', 'tradeDate']).closePrice.pct_change())
ret = ret.droplevel(0)
ret.name = 'r'
ret = ret.reset_index()
ret.dropna(inplace = True)

ret['t'] = ret.tradeDate.copy()
ret['tradeDate'] = ret.t.map(tref_map)
ret.dropna(inplace=True)

f.rename(columns = {'f':'跌幅时间重心偏离因子'},inplace = True)
for fac in ['跌幅时间重心偏离因子','tgd','tgd_skew']:
    r1,r2 = simple_group_backtest(f,ret,fac,'r',10)    
    r1 = r1.pivot('tradeDate','group','period_ret')
    r1['long-short'] = (r1[9] - r1[0])/2
    #plt.subplot(1,2,1)
    (1+r1).cumprod().plot(rot=30,colormap = cmap, title = fac)
    #plt.plot((1+r1).cumprod(),colormap = cmap)
    plt.legend(r1.columns.tolist(),loc='center left',bbox_to_anchor=(1,0.5))
    plt.show()
