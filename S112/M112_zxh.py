# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 11:22:09 2023
中性化操作

neutralize_dframeV3(dframe, col_list,exclude_style)
@author: adair2019
"""

import quant_utilS73 as qutil
import pandas as pd


if __name__ == "__main__":
    o = pd.read_pickle('forbidden_pool.pkl')
    F = pd.read_pickle('S112_F02.pkl')
    F = F[F.tradeDate>='2007-01-04']

    F = F.merge(o[['ticker','tradeDate','special_flag']],how ='left', on = ['ticker', 'tradeDate'])
    F = F[F.special_flag.isna()]
    F.dropna(subset=['O'],inplace = True)
    fac_name  = ['HB','RVS','NewRVS']
    F1 = qutil.neutralize_dframeV3(F, fac_name,[])
    F1.to_pickle('S112_F02_neutralized.pkl')