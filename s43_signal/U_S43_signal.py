# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 14:10:40 2021
S43使用tdx的中午数据发送信号
@author: adair-9960
"""
from yq_toolsS45 import time_use_tool
import os
from M_S43_get_data import update_tdx_now

obj_t = time_use_tool()

OK = update_tdx_now()
os.system('python bac_toolS43_V4_20211020.py')
os.system('python bac_toolS43_V5_20211020.py')
os.system('python bac_toolS43_V6_20211020.py')

obj_t.use('一共耗时')
os.system("pause")