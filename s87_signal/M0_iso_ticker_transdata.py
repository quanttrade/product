# -*- coding: utf-8 -*-
"""
Created on Fri Nov 26 08:21:55 2021
我的打算是将s87的算法用在中国和iso的股票上，但我也知道这个算的比较慢，所以我打算周末用北京的超级计算机算一下。
问题是超级计算机读取数据库的时候比较麻烦，您能不能帮忙改一下原来的代码，读取iso中的nky文件数据之后然后开始计算，
请您假设用全部可用的cpu资源，我可能试试1000个cpu并行。您那边不用算，我来试试超算.

@author: adair-9960
"""

import os
from yq_toolsS45_linux import get_db_data
from yq_toolsS45_linux import get_tdx_index_info
from tqdm import tqdm
X = get_db_data('data_pro','select * from main_index_s68 order by index_id,ticker,tradeDate')

index_info = get_tdx_index_info()
for sub_index in index_info.keys():
    pn0 = os.path.join(os.path.curdir,'csv_%s' % sub_index)
    if not os.path.exists(pn0):
        os.mkdir(pn0)
    x = X[X.index_id==sub_index]
    x = x[x.ticker!=index_info[sub_index]]
    v = list(x.groupby('ticker'))
    for sub_x in tqdm(v):
        tmp = sub_x[0]
        tmp = tmp.replace('/','~')
        sub_fn = os.path.join(pn0,'%s-%s.csv' % (sub_index,tmp))
        if not os.path.exists(sub_fn):
            sub_x[1].to_csv(sub_fn)
    
    
    




