# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 13:05:08 2022
r 语言测试
@author: adair2019
"""

import rpy2.robjects as robjects
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from rpy2.robjects import pandas2ri


pandas2ri.activate()

X50 = pd.read_csv('aa.csv',index_col=0)

X50 = X50.iloc[:,:20]

_,n = X50.shape

robjects.r.source('S106.R')

w0 = np.ones(n)/n
a = robjects.r.MVSKT(X50.values,w0)
w = a[0]

b = robjects.r.MVSK(X50.values)
w1 = b[0]

plt.bar(np.array(range(n)),w)
plt.bar(np.array(range(n)),w1)