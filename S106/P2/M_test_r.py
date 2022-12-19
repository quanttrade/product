# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 13:05:08 2022
r 语言测试
@author: adair2019
"""

import pandas as pd


df = pd.DataFrame({'Girdled':[46,22,17,15,15],'Logged':[88,22,16,15,13]})
df.info()

from rpy2.robjects import r
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
pandas2ri.activate()

inext = importr("iNEXT") #library R package

result = inext.iNEXT(df)
result


