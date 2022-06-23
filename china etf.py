# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 22:16:18 2022

@author: caifeng
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
df = pd.read_excel('china_etf1.xlsx')
print(df)
df_return = df[['512000_return','512170_return','512200_return','512290_return','512400_return','512480_return','512690_return','512980_return','515210_return','515220_return','512800_return','512660_return']]
df_return = df_return[1:]
print(df_return)
id_min = df_return.idxmin(axis=1)
print(id_min)
x = len(df_return)
ret = []
for i in range(x-1):
    print(i)
    col =id_min.iloc[i]
    print(col)
    ret.append((df_return.loc[i+2,[col]].values[0]))
print(ret)
plt.plot(np.cumsum(ret))
