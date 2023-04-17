# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 09:31:05 2023
S109合成因子部分
两部分因子合并，保留因子合成部分
@author: adair2019
"""

import pandas as pd
import os
from yq_toolsS45_linux import FdmtEfNewGet
import numpy as np
from yq_toolsS45_linux import get_db_data
from yq_toolsS45_linux import get_IdxCons
import time
from yq_toolsS45_linux import FdmtISGet
from yq_toolsS45_linux import FdmtISQPIT2018Get
from yq_toolsS45_linux import get_week_month_tradeDate_update
import matplotlib.pyplot as plt
import scipy.stats as st
import matplotlib
import seaborn as sns
from yq_toolsS45_linux import get_symbol_A
from yq_toolsS45_linux import EquSharesChgGet
from yq_toolsS45_linux import time_use_tool
from yq_toolsS45_linux import get_MktEqumAdjGet_update
import quant_utilS73 as qutil


obj_t = time_use_tool()
font =matplotlib.font_manager.FontProperties(fname='C:\Windows\Fonts\simkai.ttf')
save_folder = "dataS109_f1"  # 建立文件夹保存数据量大的数据文件
if not os.path.exists(save_folder):
    os.mkdir(save_folder)

def datetime_2_str(X,info = ['publishDate','endDate']):
    if isinstance(info, str):
        info = [info]
    for sub_info in info:
        X[sub_info] = X[sub_info].astype(str)
    

# 把一个日期转换成 >= 该日的最近的财报日期
def tranf2enddate(input_date):
    '''
    input_date:%Y-%m-%d
    '''
    input_year = input_date[:4]
    input_date = input_date[5:]
    if input_date <= '03-31':
        end_date = '%s-03-31'%input_year
    elif input_date <= '06-30':
        end_date = '%s-06-30'%input_year
    elif input_date <='09-30':
        end_date = '%s-09-30'%input_year
    else:
        end_date = '%s-12-31'%input_year
    return end_date

# 获取x的上个季度的季度值
def get_last_enddate(x):
    '''
    x: %Y-%m-%d
    '''
    year = x[:4]
    date = x[5:]
    if date == '03-31':
        return_x = '0'
    elif date == '06-30':
        return_x = '%s-03-31' % year
    elif date == '09-30':
        return_x = '%s-06-30' % year
    elif date == '12-31':
        return_x = '%s-09-30' % year
    else:
        return_x = None
    return return_x

def get_end_date(indate, date_type='same'):
    '''
    indate: 日期,%Y-%m-%d
    date_type:same/latest
    '''
    year = indate[:4]
    last_year = int(year) - 1
    month = indate.split("-")[1]
    if date_type == 'same':
        end_date_dict = {
            "01": "%s-09-30" % last_year,
            "02": "%s-09-30" % last_year,
            "03": "%s-09-30" % last_year,
            "04": "%s-03-31" % year,
            "05": "%s-03-31" % year,
            "06": "%s-03-31" % year,
            "07": "%s-03-31" % year,
            "08": "%s-06-30" % year,
            "09": "%s-06-30" % year,
            "10": "%s-09-30" % year,
            "11": "%s-09-30" % year,
            "12": "%s-09-30" % year,
        }
    elif date_type == 'latest':
        end_date_dict = {
            "01": ["%s-03-30" % year, "%s-06-30" % last_year],  # [最大日期，最小日期]
            "02": ["%s-03-30" % year, "%s-06-30" % last_year],
            "03": ["%s-03-30" % year, "%s-06-30" % last_year],
            "04": ["%s-06-30" % year, "%s-09-30" % last_year],
            "05": ["%s-06-30" % year, "%s-09-30" % last_year],
            "06": ["%s-06-30" % year, "%s-09-30" % last_year],
            "07": ["%s-06-30" % year, "%s-09-30" % last_year],
            "08": ["%s-09-30" % year, "%s-12-31" % last_year],
            "09": ["%s-09-30" % year, "%s-12-31" % last_year],
            "10": ["%s-09-30" % year, "%s-12-31" % last_year],
            "11": ["%s-09-30" % year, "%s-12-31" % last_year],
            "12": ["%s-09-30" % year, "%s-12-31" % last_year],
        }
    else:
        raise Exception("无效的date_type值:%s" % date_type)
    return end_date_dict[month]


# 因子测试函数准备
def proc_float_scale(df, col_name, format_str):
    #格式化输出
    #参数：
    #    df: DataFrame, 需要格式化的数据
    #    col_name： list, 需要格式化的列名
    #    format_str：格式类型
    for col in col_name:
        for index in df.index:
            df.loc[index, col] = format(df.loc[index, col], format_str)
    return df


def factor_process(factor_df, factor_list, exclude_style_list):
    #因子处理函数
    # 去极值
    w_factor_df = qutil.mad_winsorize(factor_df, factor_list, sigma_n=3)

    # 完全中性化
    n_factor_df = qutil.neutralize_dframeV2(w_factor_df.copy(), factor_list, exclude_style=exclude_style_list)

    # 标准化
    s_factor_df = n_factor_df.copy()
    s_factor_df[factor_list] = s_factor_df.groupby('tradeDate')[factor_list].apply(
        lambda df: (df - df.mean()) / df.std())
    return s_factor_df



if __name__ == "__main__":
    t0='2007-01-01'
    tt = '2023-02-20'
    
    ef_df = FdmtEfNewGet(t0,tt,'*','endDate')
    ef_df = ef_df[ef_df.reportType.isin('Q1,S1,Q3,CQ3,Q2,A'.split(','))]
    ef_df['reportType'] = np.where((ef_df['fiscalPeriod']==9) & (ef_df['reportType']=='Q3'), 'CQ3', ef_df['reportType'])
    ef_df['reportType'] = np.where((ef_df['fiscalPeriod']==3) & (ef_df['reportType']=='S1'), 'Q2', ef_df['reportType'])
    datetime_2_str(ef_df, ['endDate','publishDate'])
    
    
    # 只处理净利润口径
    profit_ef_df = ef_df[['ticker','publishDate','endDate','reportType','fiscalPeriod',
                          'NIncAPChgrLL','NIncAPChgrUPL','expnIncAPLL','expnIncAPUPL','expEPSLL','expEPSUPL']]
    # 业绩预告数据处理，把eps预告、预告增幅等都统一换算为绝对值
    ## 获取公司的财报数据
    fin_rpt_df = FdmtISGet(t0,tt,'*',key_words = 'endDate')
    fin_rpt_df = fin_rpt_df.query("mergedFlag==1")[['ticker','publishdate','enddate','reportType','fiscalPeriod','NIncomeAttrP']]
    fin_rpt_df.rename(columns = {'enddate':'endDate','publishdate':'publishDate'},inplace = True)
    datetime_2_str(fin_rpt_df, ['endDate', 'publishDate'])
    ticker_list = profit_ef_df['ticker'].unique().tolist()
    enddate_df = pd.DataFrame(profit_ef_df['endDate'].unique().tolist(), columns=['end_date']).sort_values(by=['end_date'])
    
    #这里有过拟合风险！！！publishDate晚于changeDate
    share_df = EquSharesChgGet(t0,tt,'ticker,changeDate,totalShares')
    datetime_2_str(share_df, 'changeDate')
    share_df['end_date'] = share_df['changeDate'].apply(lambda x:tranf2enddate(x))
    share_df = share_df.sort_values(by=['ticker','end_date', 'changeDate'], ascending=True)
    share_df = share_df.drop_duplicates(subset=['ticker','end_date'], keep='last')
    share_df = share_df.groupby(['ticker']).apply(lambda x: x.merge(enddate_df,on=['end_date'], how='outer'))[['totalShares','end_date']]
    share_df.reset_index(inplace=True)
    del share_df['level_1']
    share_df = share_df.sort_values(by=['ticker', 'end_date'], ascending=True)
    share_df = share_df.groupby(['ticker']).apply(lambda x: x.fillna(method='ffill'))
    share_df.dropna(inplace=True)
    #合并财务报表
    fin_rpt_df = fin_rpt_df.rename(columns={"publishDate":"rpt_publishDate"})
    profit_ef_df['pre_endDate'] = profit_ef_df['endDate'].apply(lambda x: "%s%s"%(int(str(x)[:4])-1, str(x[4:])))
    merge_rpt_df = fin_rpt_df.rename(columns={"publishDate":"rpt_publishDate",
                                  'endDate':"pre_endDate",'NIncomeAttrP':"pre_NIncomeAttrP"})[[
                                      'ticker','rpt_publishDate','pre_endDate','pre_NIncomeAttrP','reportType']]
    # 合并去年同期的财报值
    profit_ef_df = profit_ef_df.merge(merge_rpt_df, 
                                      on=['ticker','pre_endDate','reportType'],
                                      how='left').sort_values(by=['ticker',
                                      'publishDate','endDate','rpt_publishDate'], ascending=True)
    # ## 剔除掉去年同期数据中，发布日期在预告发布日期之后的记录
    profit_ef_df = profit_ef_df.query("publishDate>=rpt_publishDate")
    ## 同一个预告，只保留一条记录（合并去年同期业绩最新的记录）
    profit_ef_df = profit_ef_df.drop_duplicates(subset=['ticker','publishDate','endDate'], keep='last')
    ## 合并会计日的总股本数据
    profit_ef_df = profit_ef_df.merge(share_df[['ticker','end_date','totalShares']].rename(columns={"end_date":"endDate"}),how='left')
    ## 根据同比增幅，计算得到当期的绝对数值
    profit_ef_df['NIncLL_abs_from_growth'] = (profit_ef_df['NIncAPChgrLL']/100+1)*profit_ef_df['pre_NIncomeAttrP']
    profit_ef_df['NIncUPL_abs_from_growth'] = (profit_ef_df['NIncAPChgrUPL']/100+1)*profit_ef_df['pre_NIncomeAttrP']
    ## 根据每股收益，计算得到当期的绝对数值
    profit_ef_df['NIncLL_abs_from_EPS'] = profit_ef_df['expEPSLL']*profit_ef_df['totalShares']
    profit_ef_df['NIncUPL_abs_from_EPS'] = profit_ef_df['expEPSUPL']*profit_ef_df['totalShares']
    ## 合并到预告净利润列
    profit_ef_df['expnIncAPLL'] = profit_ef_df['expnIncAPLL'].fillna(profit_ef_df['NIncLL_abs_from_growth']).fillna(profit_ef_df['NIncLL_abs_from_EPS'])
    profit_ef_df['expnIncAPUPL'] = profit_ef_df['expnIncAPUPL'].fillna(profit_ef_df['NIncUPL_abs_from_growth']).fillna(profit_ef_df['NIncUPL_abs_from_EPS'])
    ## 剔除掉净利润上下限都为空的情况
    profit_ef_df = profit_ef_df.dropna(subset=['expnIncAPLL','expnIncAPUPL'],
                                       how='all')[['ticker','publishDate','endDate',
                                                   'reportType','expnIncAPLL', 'expnIncAPUPL']]
    
    ## 增加一个dummy变量，标识预告是在财报期前还是财报期后发布的
    profit_ef_df['in_advance'] = np.where(profit_ef_df['publishDate']<profit_ef_df['endDate'], 0, 1)
    print("预告口径对齐后的原始预告数据如下:")
    print(profit_ef_df.head())
    profit_ef_df.to_pickle(os.path.join(save_folder, '净利润业绩预告数据.pkl'))
    ## 截止上个季度的累计值，用来算预测季度的单季度值
    profit_ef_df['last_endDate'] = profit_ef_df['endDate'].apply(lambda x: get_last_enddate(x))
    ## 合并累计的财务真实值
    last_fin_rpt_df = fin_rpt_df[fin_rpt_df['reportType'].isin(['Q1', 'S1', 'CQ3', 'A'])]  # 只取累计值
    last_fin_rpt_df = last_fin_rpt_df[['ticker', 'rpt_publishDate', 'endDate', 'NIncomeAttrP']]
    last_fin_rpt_df.columns = ['ticker', 'last_publishDate', 'last_endDate', 'last_cum_NIncomeAttrP']
    profit_ef_df = profit_ef_df.merge(last_fin_rpt_df, on=['ticker', 'last_endDate'], how='left')
    # 特殊处理，如果当前是单季度预告，则上个季度的日期设置为自己，以及上个季度的值设置为0
    profit_ef_df['last_publishDate'] = np.where(profit_ef_df['reportType'].isin(['Q1', 'Q2', 'Q3']),
                                                profit_ef_df['publishDate'], profit_ef_df['last_publishDate'])
    profit_ef_df['last_cum_NIncomeAttrP'] = np.where(profit_ef_df['reportType'].isin(['Q1', 'Q2', 'Q3']), 0,
                                                     profit_ef_df['last_cum_NIncomeAttrP'])
    profit_ef_df = profit_ef_df.query('publishDate>=last_publishDate')
    profit_ef_df = profit_ef_df.sort_values(by=['ticker', 'publishDate', 'endDate', 'last_publishDate'], ascending=True)
    profit_ef_df = profit_ef_df.drop_duplicates(subset=['ticker', 'publishDate', 'endDate'], keep='last')
    ## 计算单季度的预告值
    profit_ef_df['fore_inc_L'] = profit_ef_df['expnIncAPLL'] - profit_ef_df['last_cum_NIncomeAttrP']
    profit_ef_df['fore_inc_H'] = profit_ef_df['expnIncAPUPL'] - profit_ef_df['last_cum_NIncomeAttrP']
    profit_ef_df.head()
    ###########
    # 合并上单季度的真实值
    ## 单季度的财报真实值
    key_str = ','.join(['ticker','publishDate','endDate','nIncomeAttrP'])
    q_fin_df = FdmtISQPIT2018Get('2007-01-01','2023-12-31',key_str)
    datetime_2_str(q_fin_df)
    # 每个单季报保留发布时间最早的记录
    q_fin_df = q_fin_df.sort_values(by=['ticker','endDate','publishDate'], ascending=True)
    q_fin_df = q_fin_df.drop_duplicates(subset=['ticker','endDate'],keep='first')
    etime = time.time()
    q_fin_df.columns = ['ticker','real_publishDate','endDate','real_inc']
    profit_ef_df = profit_ef_df.merge(q_fin_df, on=['ticker','endDate'], how='left').query("publishDate<=real_publishDate")
    profit_ef_df.to_pickle(os.path.join(save_folder, 'merged_profit_ef_df.pkl'))
    #该部分计算因子
    #获取月度日期
    tmp = get_week_month_tradeDate_update('2010-01-01','2023-12-31')
    tref_month = tmp[2]
    tref_month.sort()
    factor_list = []
    for tdate in tref_month:
        raw_ef_df = profit_ef_df.query("publishDate<=@tdate").sort_values(by=['ticker', 'endDate', 'publishDate'],
                                                                          ascending=True)
        # 同一报告期条件下计算因子，对应的endDate
        same_end_date = get_end_date(tdate, date_type='same')
        same_ef_df = raw_ef_df.query("endDate==@same_end_date")
        same_ef_df = same_ef_df.drop_duplicates(subset=['ticker'], keep='last')[
            ['ticker', 'fore_inc_L', 'fore_inc_H', 'real_inc']]
        # 最新报告期条件下计算因子，对应的endDate区间
        latest_max_date, latest_min_date = get_end_date(tdate, date_type='latest')
        latest_ef_df = raw_ef_df.query("endDate>=@latest_min_date and endDate<=@latest_max_date")
        latest_ef_df = latest_ef_df.drop_duplicates(subset=['ticker'], keep='last')[
            ['ticker', 'fore_inc_L', 'fore_inc_H', 'real_inc', 'in_advance']]
        ## 因子1
        same_ef_df['width_factor1'] = abs(same_ef_df['fore_inc_H'] - same_ef_df['fore_inc_L']) * 2.0 / (
                    same_ef_df['fore_inc_H'].abs() + same_ef_df['fore_inc_L'].abs())
        same_ef_df['width_factor1'] = np.where(np.sign(same_ef_df['fore_inc_H']) * np.sign(same_ef_df['fore_inc_L']) < 0, 2,
                                               same_ef_df['width_factor1'])
        ## 因子2
        latest_ef_df['width_factor2'] = abs(latest_ef_df['fore_inc_H'] - latest_ef_df['fore_inc_L']) * 2.0 / (
                    latest_ef_df['fore_inc_H'].abs() + latest_ef_df['fore_inc_L'].abs())
        latest_ef_df['width_factor2'] = np.where(
            np.sign(latest_ef_df['fore_inc_H']) * np.sign(latest_ef_df['fore_inc_L']) < 0, 2, latest_ef_df['width_factor2'])
        ## 因子3
        same_ef_df['bias_factor3'] = abs(
            same_ef_df['real_inc'] - same_ef_df[['fore_inc_H', 'fore_inc_L']].mean(axis=1, skipna=False)) * 2.0 / (
                                                 same_ef_df['real_inc'].abs() + same_ef_df[
                                             ['fore_inc_H', 'fore_inc_L']].mean(axis=1, skipna=False).abs())
        ## 因子4
        latest_ef_df['bias_factor4'] = abs(
            latest_ef_df['real_inc'] - latest_ef_df[['fore_inc_H', 'fore_inc_L']].mean(axis=1, skipna=False)) * 2.0 / (
                                                   latest_ef_df['real_inc'].abs() + latest_ef_df[
                                               ['fore_inc_H', 'fore_inc_L']].mean(axis=1, skipna=False).abs())
        factor_df = pd.concat([same_ef_df[['width_factor1', 'bias_factor3', 'ticker']].set_index('ticker'),
                               latest_ef_df[['width_factor2', 'bias_factor4', 'ticker']].set_index('ticker')],
                              axis=1).reset_index()
        factor_df['date'] = tdate
        factor_list.append(factor_df)
        # break
    all_factor_df = pd.concat(factor_list, axis=0)
    #all_factor_df['tradeDate'] = all_factor_df['date'].replace("-", "", regex=True)
    all_factor_df['tradeDate'] = all_factor_df['date']
    all_factor_df = all_factor_df.rename(columns={"index": "ticker"})
    all_factor_df.to_pickle(os.path.join(save_folder, 'all_factor_df.pkl'))
    obj_t.use('all time')
    
    #因子中性化
    sdate_backtest = '2010-01-01'
    edate_backtest = '2022-11-30'
    tmp = get_week_month_tradeDate_update(sdate_backtest,edate_backtest)
    cal_dates_df = tmp[-1]
    datetime_2_str(cal_dates_df,['calendarDate', 'prevTradeDate']) 
    month_end_list = cal_dates_df[cal_dates_df['isMonthEnd']==1]['calendarDate'].values
    
    
    
    # 股票池筛选(剔除上市不满60个交易日的次新股、st股、停牌个股、一字板个股)及保存pkl文件
    fn_data2 = os.path.join(save_folder, 'forbidden_pool.pkl')
    if not os.path.exists(fn_data2):
        forbidden_pool = qutil.stock_special_tag(sdate_backtest, edate_backtest, 
                                                 pre_new_length=60, dateformat = 1)  # 次新股、st股、停牌个股
        # 筛选一字板个股
        sql_tmp = '''select symbol as ticker, tradeDate from yq_dayprice where 
            highestPrice = lowestPrice and highestPrice > 0 and 
            tradeDate >="%s" and tradeDate <="%s"''' % (sdate_backtest, edate_backtest)
        limit_df = get_db_data('yuqerdata',sql_tmp)
        limit_df['special_flag'] = 'limit'
        limit_df.tradeDate = limit_df.tradeDate.astype(str)
        forbidden_pool = forbidden_pool.append(limit_df)
        forbidden_pool = forbidden_pool.merge(cal_dates_df, left_on=['tradeDate'], right_on=['calendarDate'])
        forbidden_pool = forbidden_pool[['ticker', 'tradeDate', 'prevTradeDate', 'special_flag']]
        forbidden_pool.to_pickle(fn_data2)
    else:
        forbidden_pool = pd.read_pickle(fn_data2)
    print("禁止股票池:", forbidden_pool.head())

    all_factor_df = all_factor_df.merge(forbidden_pool[['ticker', 'prevTradeDate', 'special_flag']], left_on=['ticker',
                                                          'tradeDate'], right_on=['ticker', 'prevTradeDate'], how='left')
    all_factor_df = all_factor_df[all_factor_df['special_flag'].isnull()]
    all_factor_df = all_factor_df.drop(['prevTradeDate', 'special_flag'], axis=1)
    #3.3 测试结果
    # 月末因子值
    month_factor_df = all_factor_df[all_factor_df['tradeDate'].isin(month_end_list)]
    # 因子方向调整
    adj_factor_list = ["width_factor1","width_factor2","bias_factor3","bias_factor4"]
    month_factor_df[adj_factor_list] = -month_factor_df[adj_factor_list]
    print(','.join(adj_factor_list) + '为负向因子，进行方向调整')
    f0 = month_factor_df.copy()
    del f0['date']
    f0['pre'] = 0
    # 行业市值中性化
    fn = os.path.join(save_folder,'pa_factor_df1.pkl')
    if os.path.exists(fn):
        f1 = pd.read_pickle(fn)
    else:
        factor_list = ["width_factor1","width_factor2","bias_factor3","bias_factor4"]
        exclude_style_list=['BETA', 'MOMENTUM', 'EARNYILD', 'RESVOL', 'GROWTH', 'BTOP', 'LEVERAGE', 'LIQUIDTY', 'SIZENL']
        f1 = factor_process(month_factor_df, factor_list, exclude_style_list=exclude_style_list)
        f1.to_pickle(fn)
    del f1['date']      
    f1['pre']=1
    # 月末因子值
    fn = os.path.join(save_folder,'pa_factor_df3.pkl')
    if os.path.exists(fn):
        f2 = pd.read_pickle(fn)
    else:
        month_factor_df = all_factor_df[all_factor_df['tradeDate'].isin(month_end_list)]
        # 因子方向调整
        adj_factor_list = ["width_factor1","width_factor2","bias_factor3","bias_factor4"]
        month_factor_df[adj_factor_list] = -month_factor_df[adj_factor_list]
        # 行业市值中性化
        factor_list = ["width_factor1","width_factor2","bias_factor3","bias_factor4"]
        exclude_style_list=[]
        f2 = factor_process(month_factor_df, factor_list, exclude_style_list=exclude_style_list)
        f2.to_pickle(fn)
    del f2['date']
    f2['pre']=2
    
    #去掉禁止池
    
    F = pd.concat([f0,f1,f2])
    from yq_toolsS45_linux import create_db
    v = ['ticker', 'width_factor1', 'bias_factor3', 'width_factor2',
           'bias_factor4', 'tradeDate', 'pre']
    from sqlalchemy.types import NVARCHAR, Float,DATE,Integer
    v_t = [Float] * len(v)
    d = dict(zip(v,v_t))
    d.update({'ticker':NVARCHAR(10)})
    d.update({'tradeDate':DATE})
    d.update({'pre':Integer})
    eg37 = create_db('s37')
    tn = 'symbol_pool_s109p1'
    F.to_sql(tn,eg37,index=False,if_exists='replace',chunksize=10000,dtype=d)
    obj_t.use('com')
    
    