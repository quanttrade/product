# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 15:01:17 2023

写入历史数据
#F = F.replace([np.inf, -np.inf], np.nan)
#F.to_sql(tn1,eg,if_exists='replace',index=False,chunksize=10000,dtype=d)
tn1 = 'symbol_pool_s112'

F1 = F1.replace([np.inf, -np.inf], np.nan)
tn2 = '%s_ner' % tn1
F1.to_sql(tn2,eg,if_exists='replace',index=False,chunksize=10000,dtype=d)



R = pd.read_excel('bacre_0315.xlsx', index_col=0)    
R.rename(columns = {0:'r0',1:'r1',2:'r2',3:'r3',4:'r4'},inplace = True)
R.to_sql(tn_r,eg,if_exists='replace',index=False,chunksize=10000,dtype=d_tn2)

浓度需要单独保存，就不用每次都删除数据了
@author: adair2019
"""

from yq_toolsS45_linux import get_db_data
import pandas as pd
import os
from yq_toolsS45_linux import create_db
from sqlalchemy.types import NVARCHAR, Float,DATE,Integer
import numpy as np
from yq_toolsS45_linux import get_inidata
from yq_toolsS45_linux import get_week_month_tradeDate_update
from yq_toolsS45_linux import do_sql_order
import quant_utilS73 as qutil
import pandas as pd
from yq_toolsS45_linux import mIdxCloseWeightGet
from yq_toolsS45_linux import get_delta_date
from yq_toolsS45_linux import time_use_tool


obj_t = time_use_tool()
d1 = ['tradeDate', 'ticker','O', 'C', 'H', 'L', 'V', 'r', 'RVS', 'Vmax',
       'HB', 'NewRVS']
dr1 = ['tradeDate', 'ticker','c2',  'o2', 'rcc2', 'rco2']
dr2 = ['tradeDate', 'ticker', 'c5', 'rcc5', 'rco5']
d_tn2 = ['tradeDate', 'r0', 'r1', 'r2', 'r3', 'r4', 'fac_info']


d_tn2 = dict(zip(d_tn2,[Float] * len(d_tn2)))
d_tn2.update({'tradeDate':DATE})
d_tn2.update({'fac_info':NVARCHAR(30)})

eg = create_db('s37')
tn1 = 'symbol_pool_s112'
tn2 = '%s_ner' % tn1

tnr_1 = 's112_return_d2'
tnr_2 = 's112_return_d5'

tn_r = 's112_return'
t0_tn1 = get_inidata(tn1,'tradeDate',eg)
t0_tn2 = get_inidata(tn2,'tradeDate',eg)

t0_tnr_1 = get_inidata(tnr_1,'tradeDate',eg)
t0_tnr_2 = get_inidata(tnr_2,'tradeDate',eg)


#获取日期
tref0 = get_week_month_tradeDate_update('1990-01-01','2099-01-01')
tref0 = tref0[0]
tref0.sort()
x0 = tref0.copy()
t0_tn1_ini = x0[ x0.index(t0_tn1) - 5]
x0 = x0[x0.index(t0_tn1)-15:]
x0 = pd.DataFrame({'tradeDate':x0})


def my_format(d = ['tradeDate', 'ticker', 'O', 'C', 'H', 'L', 'V', 'r', 'RVS', 'Vmax',
       'HB', 'NewRVS', 'c2', 'c5', 'o2', 'rcc2', 'rco2', 'rcc5', 'rco5']):
    d = dict(zip(d,[Float] * len(d)))
    d.update({'tradeDate':DATE})
    d.update({'ticker':NVARCHAR(6)})
    return d

#step1
def cal_factor(sub_x):
    sub_x = x0.merge(sub_x,how = 'left', on='tradeDate')    
    sub_x.sort_values(by = 'tradeDate', inplace = True)
    sub_x['RVS'] = sub_x.rolling(5).r.mean()
    sub_x['Vmax'] = sub_x.rolling(5).V.max()
    sub_x['HB'] = (1-(sub_x.C-sub_x.O).abs()/(sub_x.H-sub_x.L))*(sub_x.V/sub_x.Vmax)
    sub_x['NewRVS'] = sub_x.RVS * sub_x.HB
    return sub_x


# step2
def get_return(sub_x):
    sub_x = x0.merge(sub_x,how = 'left', on='tradeDate')    
    sub_x.sort_values(by = 'tradeDate', inplace = True)
    sub_x['c2'] = sub_x.C.shift(-2)
    sub_x['c5'] = sub_x.C.shift(-5)
    sub_x['o2'] = sub_x.O.shift(-1)
    sub_x['rcc2'] = sub_x.c2 / sub_x.C - 1
    sub_x['rco2'] = sub_x.c2 / sub_x.o2 - 1
    sub_x['rcc5'] = sub_x.c5 / sub_x.C - 1
    sub_x['rco5'] = sub_x.c5 / sub_x.o2 - 1
    return sub_x


#更新因子
def update_factor():
    if x0.iloc[-1].tradeDate > t0_tn1:
        #执行
        sql_tmp = '''select symbol as ticker,tradeDate, openPrice,closePrice,HighestPrice,lowestPrice,
                turnoverVol,chgPct from yq_dayprice where tradeDate>="%s" order by ticker,tradeDate'''
        r =  get_db_data('yuqerdata',sql_tmp % x0.iloc[0].tradeDate)
        r.tradeDate = r.tradeDate.astype(str)
        tmpd1= dict(zip(['openPrice', 'closePrice', 'HighestPrice',
               'lowestPrice', 'turnoverVol', 'chgPct'],['O','C','H','L','V','r']))
        r.rename(columns = tmpd1, inplace = True)
        F = r.groupby('ticker').apply(lambda x:cal_factor(x))
        F = F.reset_index(drop = True)
        F2 = F.groupby('ticker').apply(lambda x:get_return(x))
        F2.dropna(subset=['C','H','RVS','NewRVS'],inplace = True)
        F2.reset_index(inplace = True,drop = True)
        F2 = F2.replace([np.inf, -np.inf], np.nan)
        #factor
        F1 = F2[d1]
        F1 = F1[F1.tradeDate >t0_tn1]
        F1.dropna(subset=['O'],inplace = True)
        if len(F1) > 0:
            #st
            o= qutil.stock_special_tag(F1.tradeDate.min(), F1.tradeDate.max(), 
                                                     pre_new_length=60, dateformat = 1)  # 次新股、st股、停牌个股
            F1 = F1.merge(o, on = ['ticker', 'tradeDate'], how = 'left')
            F1 = F1[F1.special_flag.isna()]
            del F1['special_flag']
            F1.to_sql(tn1,eg,if_exists='append',index=False,chunksize=10000,dtype=my_format(d1))
            #r2
            F3 = F2[dr1][F2.tradeDate>t0_tnr_1]
            F3.dropna(subset=['c2'], inplace = True)
            F3.to_sql(tnr_1,eg,if_exists='append',index=False,chunksize=10000,dtype=my_format(dr1))
            #r5
            F4 = F2[dr2][F2.tradeDate>t0_tnr_2]
            F4.dropna(subset=['c5'], inplace = True)
            F4.to_sql(tnr_2,eg,if_exists='append',index=False,chunksize=10000,dtype=my_format(dr2))
    else:
        print('S112因子已经是最新')

def update_factor_ner():
    t0_ner = get_inidata('rmexposuredaygets73','tradeDate',create_db('yuqerdata'))
    #中性化
    if t0_tn1 > t0_tn2 and t0_ner > t0_tn2:
        sql_tmp = 'select * from %s where tradeDate > "%s"' % (tn1,t0_tn2)
        f0 = get_db_data('s37',sql_tmp)
        f0.tradeDate = f0.tradeDate.astype(str)
        fac_name  = ['HB','RVS','NewRVS']
        f0 = f0[f0.tradeDate<=t0_ner]
        F1 = qutil.neutralize_dframeV3(f0, fac_name,[])
        F1.to_sql(tn2,eg,if_exists='append',index=False,chunksize=10000,dtype=my_format(d1))


def export_curve():
    #导出曲线
    sql_tmp = 'select * from %s order by fac_info,tradeDate'
    x = get_db_data('s37',sql_tmp % (tn_r))
    x.tradeDate = x.tradeDate.astype(str)
    x['mark'] = x.fac_info.apply(lambda x: '-2d-' in x)
    x['tradeDate_true'] = 0
    #时间映射
    tmp = pd.DataFrame({'t':tref0})
    tmp['t2'] = tmp.t.shift(-2)
    tmp['t5'] = tmp.t.shift(-5)
    tmp_d1 = dict(zip(tmp.t,tmp.t2))
    tmp_d2 = dict(zip(tmp.t,tmp.t5))
    x.loc[x.mark,'tradeDate_true'] = x.loc[x.mark,'tradeDate'].map(tmp_d1)
    x.loc[~ x.mark,'tradeDate_true'] = x.loc[~x.mark,'tradeDate'].map(tmp_d2)
    x[['tradeDate_true', 'r0', 'r1', 'r2', 'r3', 'r4', 'fac_info']].to_excel('S112_back.xlsx')

def bac_test():
    #查看回测部分
    tref = [i for i in tref0 if i >="2006-01-01"]
    tref.sort()
    tmp_x0 = pd.DataFrame({'tradeDate':tref})
    x2 = tmp_x0[tmp_x0.index%2==0]
    x5 = tmp_x0[tmp_x0.index%5==0]
    t0_tn2 = 'select fac_info,max(tradeDate) as t from %s group by fac_info'
    t0_tn2 = get_db_data('s37', t0_tn2 % tn_r)
    t0_tn2.set_index('fac_info',inplace = True)
    t0_tn2.t = t0_tn2.t.astype(str)
    #时间
    t0_tnr_1 = get_inidata(tnr_1,'tradeDate',eg)
    t0_tnr_2 = get_inidata(tnr_2,'tradeDate',eg)
    
    t_test1 = t0_tn2.loc['中性化-HB-2d-rcc2-A'].t
    t_test2 = t0_tn2.loc['中性化-HB-5d-rcc5-A'].t
    
    t0_tnr_1 = get_inidata(tnr_1,'tradeDate',eg)
    t0_tnr_2 = get_inidata(tnr_2,'tradeDate',eg)
    if t0_tnr_1 > t_test1 or t0_tnr_2 > t_test2:
        #获取数据
        #对接数据
        #计算结果
        #保存结果
        tmp_t0 =  t0_tn2.t.min()
        #前一个月
        tmp_t0_m = get_delta_date(tmp_t0,65)
        tmp_t0_m1 = get_delta_date(tmp_t0,20)
        sql_tmp1 = 'select * from %s where tradeDate >="%s"'
        f1 = get_db_data('s37',sql_tmp1 % (tn1,tmp_t0_m1))
        f2 = get_db_data('s37',sql_tmp1 % (tn2,tmp_t0_m1))
        f1.tradeDate = f1.tradeDate.astype(str)
        f2.tradeDate = f2.tradeDate.astype(str)
        r1 = get_db_data('s37',sql_tmp1 % (tnr_1,tmp_t0_m1))
        r2 = get_db_data('s37',sql_tmp1 % (tnr_2,tmp_t0_m1))
        r1.tradeDate = r1.tradeDate.astype(str)
        r2.tradeDate = r2.tradeDate.astype(str)
        fr1 = f1.merge(r1,how = 'left', on = ['ticker','tradeDate']).merge(r2,how = 'left', on = ['ticker','tradeDate'])
        fr2 = f2.merge(r1,how = 'left', on = ['ticker','tradeDate']).merge(r2,how = 'left', on = ['ticker','tradeDate'])
        ####这里不对
        
        #股票池
        ticker_300 = mIdxCloseWeightGet('000300',tmp_t0_m,'3099-01-01','consTickerSymbol,effDate as tradeDate')
        ticker_300.tradeDate = ticker_300.tradeDate.astype(str)
        ticker_300.rename(columns ={'consTickerSymbol':'ticker'},inplace = True)
        ticker_300['m'] = ticker_300.tradeDate.apply(lambda x:get_delta_date(x,-10)[:7])
        del ticker_300['tradeDate']
        ticker_300 = list(ticker_300.groupby('m'))
        ticker_300 = dict(zip([i[0] for i in ticker_300],[i[1] for i in ticker_300]))

        ticker_500 = mIdxCloseWeightGet('000905',tmp_t0_m,'3099-01-01','consTickerSymbol,effDate as tradeDate')
        ticker_500.tradeDate = ticker_500.tradeDate.astype(str)
        ticker_500.rename(columns ={'consTickerSymbol':'ticker'},inplace = True)
        ticker_500['m'] = ticker_500.tradeDate.apply(lambda x:get_delta_date(x,-10)[:7])
        del ticker_500['tradeDate']
        ticker_500 = list(ticker_500.groupby('m'))
        ticker_500 = dict(zip([i[0] for i in ticker_500],[i[1] for i in ticker_500]))
        R = []
        for info0 in ['原因子','中性化']:
            if info0 == '中性化':
                F = fr2
            else:
                F = fr1
            F = F[F.tradeDate>='2006-01-01']
            
            tref = get_week_month_tradeDate_update('2006-01-01','3099-01-01')
            tref = tref[0]
            tref.sort()
            x0 = pd.DataFrame({'tradeDate':tref})
            x2 = x0[x0.index%2==0]
            x5 = x0[x0.index%5==0]
            
            tmp = F.tradeDate.tolist()
            x2 = x2[x2.tradeDate.isin(tmp)]
            x5 = x5[x5.tradeDate.isin(tmp)]
            
            tref_pool = [x2.tradeDate.tolist(),x5.tradeDate.tolist()]
            tref_info = dict(zip([0,1],['2d','5d']))
            r_info = dict(zip([0,1],['rcc2','rcc5']))
            for i,sub_t in enumerate(tref_pool) :    
                sub_F0 = F[F.tradeDate.isin(sub_t)]
                for sub_pool in ['A','000300','000905']:
                    if sub_pool =='A':
                        sub_F = sub_F0
                    else:
                        if sub_pool == '000300':
                            sub_p = ticker_300
                        else:
                            sub_p = ticker_500
                        #合并，计算集合
                        #这里有问题！！！
                        tmp = []
                        for sub_sub_t in sub_t:
                            tmp0 = sub_p[sub_sub_t[:7]].copy()
                            tmp0['tradeDate'] = sub_sub_t
                            tmp.append(tmp0)
                        tmp = pd.concat(tmp)
                        sub_F = sub_F0.merge(tmp,on=['ticker','tradeDate'])
                    for factor in ['HB','RVS','NewRVS']:
                        a1, a2 = qutil.simple_group_backtest_adair(sub_F, factor, r_info[i], ngrp=5, commission=0)
                        r = a1.pivot('tradeDate','group','period_ret')
                        r = r.reset_index()
                        r['fac_info'] = '%s-%s-%s-%s-%s' % (info0,factor,tref_info[i], r_info[i],sub_pool)
                        R.append(r)
        R = pd.concat(R)
        R = R[R.tradeDate>tmp_t0]
        if len(R) > 0:
            R.rename(columns = {0:'r0',1:'r1',2:'r2',3:'r3',4:'r4'},inplace = True)
            #最简单的方法，删除，然后增加
            do_sql_order('delete from %s where tradeDate >"%s"' % (tn_r,tmp_t0),'s37')
            R.to_sql(tn_r,eg,if_exists='append',index=False,chunksize=10000,dtype=d_tn2)
            export_curve()
            
def export_position(t0,tt='3099-01-01'):
    #仓位  
    pn0 = '仓位结果'
    if not os.path.exists(pn0):
        os.mkdir(pn0)
    #t0 = '2023-01-01'
    #tt  ='2099-01-01'
    t0_ini = get_delta_date(t0,31)
    sql_tmp = 'select * from %s where tradeDate >="%s" and tradeDate <="%s"' % (tn1,t0,tt)
    f1 = get_db_data('s37', sql_tmp)
    f1.tradeDate = f1.tradeDate.astype(str)
    sql_tmp = 'select * from %s where tradeDate >="%s" and tradeDate <="%s"' % (tn2,t0,tt)
    f2 = get_db_data('s37', sql_tmp)
    f2.tradeDate = f2.tradeDate.astype(str)
    #股票池
    ticker_300 = mIdxCloseWeightGet('000300',t0_ini,'3099-01-01','consTickerSymbol,effDate as tradeDate')
    ticker_300.tradeDate = ticker_300.tradeDate.astype(str)
    ticker_300.rename(columns ={'consTickerSymbol':'ticker'},inplace = True)
    ticker_300['m'] = ticker_300.tradeDate.apply(lambda x:get_delta_date(x,-10)[:7])
    del ticker_300['tradeDate']
    ticker_300 = list(ticker_300.groupby('m'))
    ticker_300 = dict(zip([i[0] for i in ticker_300],[i[1] for i in ticker_300]))
    ticker_500 = mIdxCloseWeightGet('000905',t0_ini,'3099-01-01','consTickerSymbol,effDate as tradeDate')
    ticker_500.tradeDate = ticker_500.tradeDate.astype(str)
    ticker_500.rename(columns ={'consTickerSymbol':'ticker'},inplace = True)
    ticker_500['m'] = ticker_500.tradeDate.apply(lambda x:get_delta_date(x,-10)[:7])
    del ticker_500['tradeDate']
    ticker_500 = list(ticker_500.groupby('m'))
    ticker_500 = dict(zip([i[0] for i in ticker_500],[i[1] for i in ticker_500]))
    for info0 in ['原因子','中性化']:
        if info0 == '中性化':
            F = f1
        else:
            F = f2
        F = F[F.tradeDate>='2006-01-01']
        
        tref = get_week_month_tradeDate_update('2006-01-01','3099-01-01')
        tref = tref[0]
        tref.sort()
        x0 = pd.DataFrame({'tradeDate':tref})
        x2 = x0[x0.index%2==0]
        x5 = x0[x0.index%5==0]
        
        tmp = F.tradeDate.tolist()
        x2 = x2[x2.tradeDate.isin(tmp)]
        x5 = x5[x5.tradeDate.isin(tmp)]
        
        tref_pool = [x2.tradeDate.tolist(),x5.tradeDate.tolist()]
        tref_info = dict(zip([0,1],['2d','5d']))
        for i,sub_t in enumerate(tref_pool) :    
            sub_F0 = F[F.tradeDate.isin(sub_t)]
            for sub_pool in ['A','000300','000905']:
                if sub_pool =='A':
                    sub_F = sub_F0
                else:
                    if sub_pool == '000300':
                        sub_p = ticker_300
                    else:
                        sub_p = ticker_500
                    #合并，计算集合
                    #这里有问题！！！
                    tmp = []
                    for sub_sub_t in sub_t:
                        tmp0 = sub_p[sub_sub_t[:7]].copy()
                        tmp0['tradeDate'] = sub_sub_t
                        tmp.append(tmp0)
                    tmp = pd.concat(tmp)
                    sub_F = sub_F0.merge(tmp,on=['ticker','tradeDate'])
                for factor in ['HB','RVS','NewRVS']:
                    bt_df = qutil.signal_grouping(sub_F, factor_name=factor, ngrp=5)
                    bt_df = bt_df[bt_df.group.isin([0,4])]
                    bt_df = bt_df.pivot('tradeDate','ticker','group')
                    #写入文件
                    fn = '股票池%s-%s-%s-%s-%s.xlsx' % (info0,tref_info[i],sub_pool,factor,bt_df.index.max())
                    fn = os.path.join(pn0,fn)
                    bt_df.to_excel(fn)
#因子中性化
if __name__ == "__main__":
    #更新基础因子
    update_factor()
    #更新中性化因子
    update_factor_ner()
    #更新曲线
    bac_test() 