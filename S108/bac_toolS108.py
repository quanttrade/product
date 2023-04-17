# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 14:20:38 2023
合成因子程序
@author: adair2019
"""

from yq_toolsS45_linux import get_db_data
import pandas as pd
#from tqdm import tqdm
import multiprocessing
from yq_toolsS45_linux import engine37
from yq_toolsS45_linux import get_inidata
from sqlalchemy.types import NVARCHAR, Float,DATE,Integer
from sqlalchemy.dialects.mysql import DOUBLE
from yq_toolsS45_linux import get_week_month_tradeDate_update
import statsmodels.api as sm
from yq_toolsS45_linux import get_back_date
from tqdm import tqdm
from quant_utilS73 import stock_special_tag
from quant_utilS73 import signal_grouping
from yq_toolsS45_linux import get_IdxConsGet
from quant_utilS73 import simple_group_backtest
import os

num_core =  int(multiprocessing.cpu_count()/2)


data_sel = 'jk'

if data_sel == 'jk':
    dn = 'jk_min_sec'
else:
    dn = 'ycz_min_history'
    
N_limit = 240
smoothing_N = 20
smoothing_N_min = 18
tn1 = 's108_factor0'
dn_tn1 = 's37'
tn2 = 's108_factor_rolling'
tn3 = 's108_factor1'
tn4 = 's108_factor2'
tn_return = 's108_return'
tref = get_week_month_tradeDate_update('1990-01-01','3099-01-01')
tref_month = tref[2]
tref = pd.DataFrame({'tradeDate':tref[0]})
tref.sort_values(by = ['tradeDate'], inplace = True)
tref_list = tref.tradeDate.tolist()
tref_list.sort()
tref_num = [i.replace('-','') for i in tref_list]
#part 1
# com basic factor

def trans2ycz(x):
    if x[0]=='6':
        tmp = 'sh'
    else:
        tmp = 'sz'
    return '%s%s' % (tmp,x)


def get_uq_sec(tn):
    if len(tn) == 8:
        t_tmp = '%s-%s-%s' % (tn[:4],tn[4:6],tn[6:])
    else:
        t_tmp = tn
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
        #skew
        sk = sub_r.r.skew()        
    else:
        Gd = pd.np.nan
        Gu = pd.np.nan
        R1 = Gd
        R2 = Gd
        R_night = Gd
        r_u_bar = Gd
        r_d_bar = Gd
        sk = Gd    
    return pd.DataFrame({'Gu':[Gu],'Gd':[Gd],'R1':[R1],'R2':[R2],'R_night':R_night,
                         'r_u_bar':[r_u_bar],'r_d_bar':[r_d_bar],'sk':[sk]})


#获取单日，所有symbol的因子值
def get_factor_section(tn):
    x = get_db_data(dn, 'select symbol,hour(tradingdate)*100+minute(tradingdate) as t,`close` from `%s`' % tn)
    if data_sel =='jk':
        x.symbol = x.symbol.apply(lambda x:trans2ycz(x[:6]))
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
    if data_sel == 'ycz':
        y['tradeDate'] = '%s-%s-%s' % (tn[:4],tn[4:6],tn[6:])
    else:
        y['tradeDate'] = tn
    print('complete %s' % tn)
    return y.reset_index()

#step 1 合成基础因子
def com_factor01_S108():
    
    tns = get_db_data(dn,'show tables from %s' % dn)
    tns = tns[tns.columns[0]].tolist()
    if data_sel == 'jk':
        t0_tn1= '20121101'
        tns = [i for i in tns if len(i) == 10]
    else:
        t0_tn1 = '2012-11-01'
    tmp = get_inidata(tn1,'tradeDate',engine37)
    if data_sel == 'ycz':
        tmp = tmp.replace('-','')
    if t0_tn1 < tmp:
        t0_tn1 = tmp
    tns = [i for i in tns if i >t0_tn1]
    if len(tns) > 0:
        pool = multiprocessing.Pool(num_core)
        Y = pool.map(get_factor_section,tns)
        pool.close()
        pool.join()
        Y1=pd.concat(Y)
        Y1.rename(columns = {'symbol':'ticker'},inplace = True)
        d = Y1.columns.tolist()
        d = dict(zip(d,[Float]*len(d)))
        d.update({'tradeDate':DATE})
        d.update({'ticker':NVARCHAR(8)})
        Y1.to_sql(tn1,engine37,index=False,chunksize=5000,if_exists = 'append',dtype=d)
    print('完成合成S108基础因子')


#part2 
# rolling mean
def smoothing_factor(sub_x):
    sub_tref = tref[(tref.tradeDate>=sub_x.iloc[0].tradeDate) & (tref.tradeDate<=sub_x.iloc[-1].tradeDate)]
    sub_tref0 = sub_x.tradeDate.tolist()
    sub_x = sub_tref.merge(sub_x, how = 'left', on ='tradeDate')
    sub_x['symbol'] = sub_x.iloc[0].symbol
    sub_x = sub_x.set_index(['symbol','tradeDate']).rolling(smoothing_N, min_periods = smoothing_N_min).mean().reset_index()
    sub_x = sub_x[sub_x.tradeDate.isin(sub_tref0)]
    return sub_x.set_index(['symbol','tradeDate'])
    
def com_ols_factor_tgd(sub_x):
    sub_x = sub_x.copy()
    y = sub_x[['Gu']]
    x = sub_x[['r_u_bar','R1','R2','R_night']]
    x=sm.add_constant(x) #添加常数项
    est=sm.OLS(y,x)
    model=est.fit()#建立最小二乘回归模型
    sub_x['error_u'] = model.resid
    
    y = sub_x[['Gd']]
    x = sub_x[['r_d_bar','R1','R2','R_night']]
    x=sm.add_constant(x) #添加常数项
    est=sm.OLS(y,x)
    model=est.fit()#建立最小二乘回归模型
    sub_x['error_d'] = model.resid
        
    x = sub_x[['error_u']]
    y = sub_x[['error_d']]
    x=sm.add_constant(x) #添加常数项
    est=sm.OLS(y,x)
    model=est.fit()#建立最小二乘回归模型
    sub_x['tgd'] = model.resid
    
    x = sub_x[['Gu']]
    y = sub_x[['Gd']]
    x=sm.add_constant(x) #添加常数项
    est=sm.OLS(y,x)
    model=est.fit()#建立最小二乘回归模型
    sub_x['f'] = model.resid
    return sub_x
def update_rolling_factor():
    t1 = get_inidata(tn1,'tradeDate',engine37)
    t2 = get_inidata(tn2, 'tradeDate', engine37)
    t2 = max(t2,'2012-11-01')
    if t1 > t2:
        t0_ini_tn2 = get_back_date(t2,smoothing_N*2,tref_list)
        F0 = get_db_data(dn_tn1,'select * from %s where tradeDate>="%s" order by ticker,tradeDate' % (tn1,t0_ini_tn2))
        F0.rename(columns = {'ticker':'symbol'},inplace = True)
        F0.tradeDate = F0.tradeDate.astype(str)
        F0 = F0.groupby('tradeDate').apply(lambda x:com_ols_factor_tgd(x))
        F0['tao'] = F0.Gd - F0.Gu
        F0['u'] = F0['tao'].abs()
        F0.sort_values(by = ['symbol', 'tradeDate'], inplace=True)
        #平滑
        F = F0.groupby('symbol').apply(lambda x: smoothing_factor(x)).droplevel(0)
        F.dropna(inplace=True)
        F.reset_index(inplace = True)
        F = F[F.tradeDate > t2]        
        if len(F)>0:
            F.sk = -F.sk
            F.symbol = F.symbol.apply(lambda x:x[2:])
            F.rename(columns = {'symbol':'ticker'},inplace=True)
            F.reset_index(inplace=True,drop =True)
            F['sk_rank'] = F.groupby('tradeDate').sk.rank()
            F['tgd_rank'] = F.groupby('tradeDate').tgd.rank()
            F['tgd_skew'] = F.sk_rank+F.tgd_rank
            F.to_sql(tn2,engine37,index=False, chunksize=5000,if_exists = 'append')
    print('完成合成S108平滑因子')


#save factor
#频率为20日，将因子摘出来保存
def save_factor():
    tref1 = tref[(tref.tradeDate>='2013-01-07')].copy()
    tref1 = tref1.iloc[::20]
    tref1 = tref1.tradeDate.tolist()
    tref1.sort()
    #t2 = get_inidata(tn2,'tradeDate',engine37)
    t3 = get_inidata(tn3, 'tradeDate', engine37)
    if tref1[-1]>t3:
        sql_tmp = 'select * from %s where tradeDate > "%s"' % (tn2,t3)    
        F = get_db_data(dn_tn1,sql_tmp)
        F.tradeDate = F.tradeDate.astype(str)
        F = F[F.tradeDate.isin(tref1)]
        tref_tmp= F.tradeDate.unique().tolist()
        X_del = []
        for sub_t in tqdm(tref_tmp):
            tmp = stock_special_tag(sub_t, sub_t, halt=1, st=1, pre_new=1, pre_new_length=100)
            X_del.append(tmp)
        X_del = pd.concat(X_del)
        X_del.tradeDate = X_del.tradeDate.apply(lambda x:'%s-%s-%s' % (x[:4],x[4:6],x[6:]))
        F = F.merge(X_del,on =['ticker','tradeDate'],how = 'left')
        F = F[F.special_flag.isna()]
        del F['special_flag']
        X_del = []
        for sub_t in tqdm(tref_tmp):
            tmp = get_db_data('yuqerdata','select symbol as ticker,tradeDate from yq_dayprice where tradeDate = "%s" and  abs(chgPct)<0.095' % sub_t)
            X_del.append(tmp)
        X_del = pd.concat(X_del)
        X_del.tradeDate = X_del.tradeDate.astype(str)
        F = F.merge(X_del,on =['ticker','tradeDate'])
        #去除st、停牌
        #去除涨跌幅过高的
        F.to_sql(tn3,engine37,index=False, chunksize=5000,if_exists = 'append')
    print('完成S108因子保存')

def export_pos():
    sql_tmp = 'select * from %s where tradeDate>"%s"' % (tn4,'2010-01-01')
    f = get_db_data(dn_tn1,sql_tmp)
    t_f = str(f.tradeDate.max())
    pn = 'postion_s108'
    if not os.path.exists(pn):
        os.mkdir(pn)
    fn = os.path.join(pn,'s108-%s.xlsx' % t_f)
    for sub_index in ['A','000300','000905']:
        sub_f = f[f.index_code == sub_index]
        for fac in ['f','tgd','tgd_skew']:
            tmp = sub_f[sub_f[fac].isin([0,9])]
            tmp = tmp.pivot('tradeDate','ticker',fac)
            tmp.to_excel(fn,sheet_name = '%s-%s' % (sub_index,fac))
    
    
#生成因子库
def save_group(ngrp = 10):
    t4 = get_inidata(tn4, 'tradeDate', engine37)
    sql_tmp = 'select * from %s where tradeDate>"%s"' % (tn3,t4)
    f = get_db_data(dn_tn1,sql_tmp)
    if len(f)>0:
        index_pool =  ['000300','000905']
        #mark
        f.tradeDate = f.tradeDate.astype(str)
        #300,500 mark
        tref_4 = f.tradeDate.unique().tolist()
        for sub_index in index_pool:
            f_index = []
            for sub_t in tqdm(tref_4,desc='匹配%s成分股' % sub_index):
                tmp,_ =get_IdxConsGet(sub_index,sub_t)
                tmp1 = pd.DataFrame({'ticker':tmp})
                tmp1['tradeDate'] = sub_t
                f_index.append(tmp1)
            f_index = pd.concat(f_index)
            f_index['i%s' % sub_index] = 1
            f = f.merge(f_index,on=['ticker','tradeDate'],how='left')
        f['iA'] = 1
        #分组，并保存
        result0 = []
        for sub_index in ['A'] + index_pool:
            sub_f = f[f['i%s' % sub_index]==1]
            result = []
            for fac in ['f','tgd','tgd_skew']:
                tmp = sub_f[['ticker','tradeDate',fac]].copy()
                bt_df = signal_grouping(tmp, factor_name=fac, ngrp=ngrp)
                bt_df = bt_df.set_index(['ticker','tradeDate'])
                del bt_df[fac]
                bt_df.rename(columns = {'group':fac},inplace=True)
                result.append(bt_df)
            result = pd.concat(result,axis=1)
            result = result.reset_index()
            result['index_code'] = sub_index
            result0.append(result)
        result0 = pd.concat(result0)
        result0.to_sql(tn4,engine37,index=False,chunksize=5000,if_exists='append')
        export_pos()
    print('完成S108因子分组保存')


#计算回测曲线t
def get_chgpct():
    #fee_buy = 0
    #fee_sell = 0
    t_return =  get_inidata(tn_return, 'tradeDate', engine37)
    t_return = max(t_return, '2013-02-04')
    if tref_list[-1] > t_return:
        tmp = get_back_date(t_return,20*2,tref_list)
        r = get_db_data('yuqerdata','select ticker,tradeDate,closePrice/preClosePrice-1 as r from yq_mktequdadjafget where tradeDate>="%s"' % t_return)
        f = get_db_data('s37','select * from %s where tradeDate >="%s"' % (tn4,tmp))    
        #f = get_db_data('s37','select * from %s where tradeDate >="%s"' % (tn3,tmp))    
        r.tradeDate = r.tradeDate.astype(str)
        f.tradeDate = f.tradeDate.astype(str)
        R = []
        for sub_index in ['A','000300','000905']:
            sub_f = f[f.index_code == sub_index]
            sub_tref = sub_f.tradeDate.unique().tolist()
            sub_tref.sort()
            if r.tradeDate.max()>sub_tref[-1]:
                sub_tref.append(r.tradeDate.max())
            for t1,t2 in tqdm(zip(sub_tref[:-1],sub_tref[1:]),desc = '收益计算%s' % (sub_index)):
                sub_sub_f = sub_f[sub_f.tradeDate==t1]
                sub_sub_r = r[(r.tradeDate>t1) & (r.tradeDate<=t2) ]
                ####如何计算每日收益
                v = sub_sub_r.merge(sub_sub_f.rename(columns = {'tradeDate':'t'}),on = 'ticker',how = 'right')
                for fac in ['f','tgd','tgd_skew']:
                    tmp = v[v[fac]==9]
                    
                    sub_sub_r_long = tmp.pivot('tradeDate','ticker','r')
                    sub_sub_r_long.sort_index(inplace=True)
                    sub_sub_r_long = sub_sub_r_long.mean(axis=1)
                    sub_sub_r_long.name = 'r_long'
                    sub_sub_r_long = sub_sub_r_long.to_frame()
                    
                    tmp = v[v[fac]==0]
                    
                    sub_sub_r_s = tmp.pivot('tradeDate','ticker','r')
                    sub_sub_r_s.sort_index(inplace=True)
                    sub_sub_r_s = sub_sub_r_s.mean(axis=1)
                    sub_sub_r_s.name = 'r_short'
                    sub_sub_r_s = sub_sub_r_s.to_frame()
                    
                    tmp = pd.concat([sub_sub_r_long,sub_sub_r_s],axis=1).reset_index()
                    tmp['index_id'] = sub_index
                    tmp['mid'] = fac
                    R.append(tmp)
        R = pd.concat(R)      
        R = R[R.tradeDate>t_return]    
        R.to_sql(tn_return,engine37,index=False,chunksize=5000,if_exists='append')
    print('完成S108分组曲线计算') 
    
    
def check_108_data():
    tns = get_db_data(dn,'show tables from %s' % dn)
    tns = tns[tns.columns[0]].tolist()
    if data_sel == 'jk':
        tns = [i for i in tns if len(i)==10]
        tref_compare = tref_list
        mark_str = '聚宽'
    else:
        tref_compare = tref_num
        mark_str = '预测者'
    if tns[-1] == tref_compare[-1]:
        OK1 = True
    else:
        OK1 = False
        info1 = '%s和uq数据日期不一致，%s为%s,uq为%s' % (mark_str,mark_str,tns[-1],tref_compare[-1])
    tmp = [i for i in tref_compare if i>=tns[0]  and i<=tns[-1]]
    tmp = list(set(tmp) - set(tns))
    if len(tmp) > 0:
        OK2 = False
        info2 ='%s数据缺失，缺失日期为%s' % (mark_str,','.join(tmp))
    else:
        OK2 = True
    if OK1 and OK2:
        OK = True
    else:
        OK = False
        print('S108因数据原因停止计算，原因为：')
        if not OK1:
            print(info1)
        if not OK2:
            print(info2)
    return OK


if __name__ == "__main__":
    if check_108_data():
        com_factor01_S108()
        update_rolling_factor()
        save_factor()
        save_group()
        get_chgpct()