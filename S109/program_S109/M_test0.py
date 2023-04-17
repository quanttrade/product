# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 12:55:47 2023

@author: adair2019
"""

tref_m = f.tradeDate.unique().tolist()
tref_m.sort()
tref_m_map = dict(zip(tref_m[:-1],tref_m[1:]))

r11 = []

for sub_t0,sub_tt in zip(tref_m[:-1],tref_m[1:]):
    tmp = b2[(b2.tradeDate>sub_t0) & (b2.tradeDate<=sub_tt)]
    sub_r = tmp[tmp.group==0].pivot('tradeDate','ticker','r')
    sub_r.sort_index(inplace = True)
    sub_r = (1+sub_r).cumprod().mean(axis=1).pct_change()
    sub_r.name = 's'
    
    sub_r1 = tmp[tmp.group==9].pivot('tradeDate','ticker','r')
    sub_r1.sort_index(inplace = True)
    sub_r1 = (1+sub_r1).cumprod().mean(axis=1).pct_change()
    sub_r1.name = 'l'
    
    r11.append(pd.concat([sub_r, sub_r1], axis = 1))
r11 = pd.concat(r11)