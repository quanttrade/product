# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 13:05:08 2022
通过R获取权重
@author: adair2019
"""

import rpy2.robjects as robjects
import numpy as np
from rpy2.robjects import pandas2ri
pandas2ri.activate()


robjects.r.source('S106.R')


def MVSKT(X50):
    _,n = X50.shape
    w0 = np.ones(n)/n
    a = robjects.r.MVSKT(X50.values,w0)
    w = a[0]
    return w

def MVSKT2(X50,w0):
    a = robjects.r.MVSKT(X50.values,w0)
    w = a[0]
    return w

def MVSK(X50):
    b = robjects.r.MVSK(X50.values)
    w = b[0]
    return w