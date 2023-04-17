# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 09:34:36 2023
合成因子
合成基础因子值Gu Gd

时间重心偏离（TCD ）因子 构建

结果标记v3
@author: adair2019
"""

from yq_toolsS45_linux import get_db_data
import pandas as pd
#from tqdm import tqdm
import multiprocessing


num_core = 6 #int(multiprocessing.cpu_count())
dn = 'ycz_min_history'
N_limit = 240
t0= '20121101'


def trans2ycz(x):
    if x[0]=='6':
        tmp = 'sh'
    else:
        tmp = 'sz'
    return '%s%s' % (tmp,x)


def get_uq_sec(tn):
    t_tmp = '%s-%s-%s' % (tn[:4],tn[4:6],tn[6:])
    sql_tmp = 'select ticker,preClosePrice,closePrice from yq_mktequdadjafget where tradeDate = "%s"'
    tmp = get_db_data('yuqerdata',sql_tmp % (t_tmp))
    tmp.ticker = tmp.ticker.apply(lambda x:trans2ycz(x))
    return tmp


#获取单日，单个symbol的因子值
def get_factor0_update(sub_x):
    if len(sub_x) >= N_limit+2:
        sub_x = sub_x.copy()
        sub_x.reset_index(drop=True,inplace=True)
        sub_x = sub_x[['symbol', 'close', 't']]
        #求系数
        coef0 = sub_x.iloc[-1].close/sub_x.iloc[-2].close
        #复权
        sub_x.iloc[1:-1,1] = sub_x.iloc[1:-1,1]*coef0        
        sub_r = sub_x['close'].pct_change()
        sub_r = sub_r[1:-1]
        sub_r.name= 'r'
        sub_r = sub_r.to_frame()
        sub_r['U'] = sub_r.index
        sub_r['u'] = sub_r.r>0
        sub_r['d'] = sub_r.r<0        
        sub_r_u = sub_r[sub_r.u]
        Gu = (sub_r_u.U*sub_r_u.r).sum()/sub_r_u.r.abs().sum()        
        sub_r_d = sub_r[sub_r.d]
        Gd = -(sub_r_d.U*sub_r_d.r).sum()/sub_r_d.r.abs().sum()
        
        #mean return
        r_u_bar = sub_r[sub_r.u].r.mean()
        r_d_bar = sub_r[sub_r.d].r.mean()
        #9:31~10:00 R1
        R1 = (1+sub_r[['r']].iloc[:30]).cumprod().iloc[-1].r-1
        #10:01~10:30 R2
        R2 = (1+sub_r[['r']].iloc[30:60]).cumprod().iloc[-1].r-1
        #
        R_night = sub_r.iloc[0].r
    else:
        Gd = pd.np.nan
        Gu = pd.np.nan
        R1 = Gd
        R2 = Gd
        R_night = Gd
        r_u_bar = Gd
        r_d_bar = Gd
    
    return pd.DataFrame({'Gu':[Gu],'Gd':[Gd],'R1':[R1],'R2':[R2],'R_night':R_night,
                         'r_u_bar':[r_u_bar],'r_d_bar':[r_d_bar]})
#获取单日，所有symbol的因子值
def get_factor_section(tn):
    x = get_db_data(dn, 'select symbol,hour(tradingdate)*100+minute(tradingdate) as t,`close` from `%s`' % tn)
    #日内数据
    r_day = get_uq_sec(tn)
    tmp = list(set(x.symbol.unique().tolist()) & set(r_day.ticker.tolist()))
    x = x[x.symbol.isin(tmp)]
    r_day = r_day[r_day.ticker.isin(tmp)]
    x1 = pd.DataFrame({'symbol':r_day.ticker,'close':r_day.preClosePrice})
    x1['t'] = 930    
    x2 = pd.DataFrame({'symbol':r_day.ticker,'close':r_day.closePrice})
    x2['t'] = 1531    
    x = pd.concat([x1,x,x2])
    x = x.sort_values(by = ['symbol', 't']).reset_index(drop=True)
    y = x.groupby('symbol').apply(lambda x: get_factor0_update(x))
    y = y.droplevel(1)
    y = y.dropna()
    y['tradeDate'] = '%s-%s-%s' % (tn[:4],tn[4:6],tn[6:])
    print('complete %s' % tn)
    return y.reset_index()



if __name__ == "__main__":
    tns = get_db_data(dn,'show tables from %s' % dn)
    tns = tns[tns.columns[0]].tolist()
    tns = [i for i in tns if i >=t0]
    pool = multiprocessing.Pool(num_core)
    Y = pool.map(get_factor_section,tns)
    pool.close()
    pool.join()
    Y1=pd.concat(Y)
    Y1.to_pickle('factor_sec_v3.pkl')