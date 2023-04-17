#知情交易角度切入的反转因子优化


import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import time
import scipy.stats as st
#from CAL.PyCAL import *
import seaborn as sns
import quant_utilS73 as qutil
from yq_toolsS45_linux import TradeCalGet
from yq_toolsS45_linux import get_symbol_A
from yq_toolsS45_linux import get_MktEqudAdjAfGet_com
from yq_toolsS45_linux import get_MktEqumAdjGet_update
from yq_toolsS45_linux import get_db_data
from yq_toolsS45_linux import get_inidata
import os
import matplotlib
from yq_toolsS45_linux import time_use_tool
from yq_toolsS45_linux import get_delta_date
from sqlalchemy.types import NVARCHAR, Float,DATE,Integer
from yq_toolsS45_linux import create_db


obj_t = time_use_tool()
v = ['ticker', 'tradeDate', 'revs_20', 'revs_overnight_20',
       'revs_intraday_20', 'corr_overnight_20', 'abs_overnight_20', 'pre']

v_t = [Float] * len(v)
d = dict(zip(v,v_t))
d.update({'ticker':NVARCHAR(10)})
d.update({'tradeDate':DATE})
d.update({'pre':Integer})
eg37 = create_db('s37')
tn = 'symbol_pool_s109p2'
font =matplotlib.font_manager.FontProperties(fname='C:\Windows\Fonts\simkai.ttf')


# 因子测试函数准备
def proc_float_scale(df, col_name, format_str):
    """
    格式化输出
    参数：
        df: DataFrame, 需要格式化的数据
        col_name： list, 需要格式化的列名
        format_str：格式类型
    """
    for col in col_name:
        for index in df.index:
            df.loc[index, col] = format(df.loc[index, col], format_str)
    return df


def factor_process(factor_df, factor_list, exclude_style_list):
    '''
    因子处理函数
    '''
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
    #计算各类因子数据
    sdate_backtest = get_inidata(tn, eg = eg37)
    sdate_backtest = get_delta_date(sdate_backtest, -1)
    edate_backtest = '3099-01-01'
    cal_dates_df = TradeCalGet(sdate_backtest, edate_backtest, '*')
    cal_dates_df.sort_values(by = 'calendarDate', inplace = True)
    cal_dates_df['calendarDate'] = cal_dates_df['calendarDate'].astype(str)
    cal_dates_df['prevTradeDate'] = cal_dates_df['prevTradeDate'].astype(str)
    
    month_end_list = cal_dates_df[cal_dates_df['isMonthEnd']==1]['calendarDate'].values
    if len(month_end_list) > 0:
        # 个股日度行情数据
        sdate_data = (pd.to_datetime(sdate_backtest) - pd.offsets.DateOffset(100)).strftime('%Y-%m-%d')
        field= "ticker,tradeDate,preClosePrice,openPrice,closePrice,turnoverRate"
        dmkt_df = get_MktEqudAdjAfGet_com(sdate_data, edate_backtest, field)
        dmkt_df['tradeDate'] = dmkt_df['tradeDate'].astype(str)
        dmkt_df.sort_values(['ticker', 'tradeDate'], inplace=True)
        # 股票池筛选(剔除上市不满60个交易日的次新股、st股、停牌个股、一字板个股)及保存pkl文件
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
        #1.2 计算因子值
        dmkt_df['openPrice'] = np.where(dmkt_df['turnoverRate'] == 0, dmkt_df['closePrice'], dmkt_df['openPrice'])
        # 因子1：revs_20: 传统反转因子，过去20个交易日的close2close收益率累乘
        dmkt_df['ret'] = dmkt_df['closePrice']/dmkt_df['preClosePrice'] - 1
        dmkt_df['revs_20'] = dmkt_df.groupby(['ticker'])['ret'].rolling(20).apply(lambda x: (x+1).prod() - 1).values
        
        # 因子2：revs_intraday_20:传统日内因子，过去20个交易日的open2close收益率累乘
        dmkt_df['intraday_ret'] = dmkt_df['closePrice']/dmkt_df['openPrice'] - 1
        dmkt_df['revs_intraday_20'] = dmkt_df.groupby(['ticker'])['intraday_ret'].rolling(20).apply(lambda x: (x+1).prod() - 1).values
        
        # 因子3：revs_overnight_20:传统隔夜因子，过去20个交易日的close2open收益率累乘
        dmkt_df['overnight_ret'] = dmkt_df['openPrice']/dmkt_df['preClosePrice'] - 1
        dmkt_df['revs_overnight_20'] = dmkt_df.groupby(['ticker'])['overnight_ret'].rolling(20).apply(lambda x: (x+1).prod() - 1).values
        
        # 因子4：abs_overnight_20:取绝对值的隔夜跳空因子, 过去20个交易日的open2close收益率取平均值
        dmkt_df['abs_overnight_ret'] = dmkt_df['overnight_ret'].abs()
        dmkt_df['abs_overnight_20'] = dmkt_df.groupby(['ticker'])['abs_overnight_ret'].rolling(20).mean().values
        
        # 因子5：corr_overnight_20: 从知情交易角度切入的优化后的隔夜跳空因子
        dmkt_df['pre_turnoverrate'] = dmkt_df.groupby('ticker')['turnoverRate'].shift(1)
        dmkt_df['corr_overnight_20'] = dmkt_df.groupby(['ticker']).apply(lambda x: x['abs_overnight_ret'].rolling(20).corr(x['pre_turnoverrate'])).values
        
        factor_list = ['revs_20', 'revs_overnight_20', 'revs_intraday_20', 'corr_overnight_20', 'abs_overnight_20']
        all_factor_df = dmkt_df[['ticker', 'tradeDate'] + factor_list]
        # 月末因子值
        month_factor_df = all_factor_df[all_factor_df['tradeDate'].isin(month_end_list)]
        # 因子方向调整
        adj_factor_list = ['revs_20', 'revs_intraday_20', 'abs_overnight_20', 'corr_overnight_20']
        month_factor_df[adj_factor_list] = -month_factor_df[adj_factor_list]
        
        month_factor_df = month_factor_df.merge(forbidden_pool[['ticker', 'tradeDate', 'special_flag']], 
                                                on=['ticker', 'tradeDate'], how='left')
        month_factor_df = month_factor_df[month_factor_df['special_flag'].isnull()]
        month_factor_df = month_factor_df.drop(['special_flag'], axis=1)
        f0 = month_factor_df.copy()
        # 市值中性化
        factor_list = ['revs_20', 'revs_overnight_20', 'revs_intraday_20', 'abs_overnight_20', 'corr_overnight_20']
        exclude_style_list=['BETA', 'MOMENTUM', 'EARNYILD', 'RESVOL', 'GROWTH', 'BTOP', 'LEVERAGE', 'LIQUIDTY', 'SIZENL']
        f1 = factor_process(month_factor_df, factor_list, exclude_style_list=exclude_style_list)
        # 行业市值中性化
        factor_list = ['revs_20', 'revs_overnight_20', 'revs_intraday_20', 'abs_overnight_20', 'corr_overnight_20']
        exclude_style_list=[]
        f2 = factor_process(month_factor_df, factor_list, exclude_style_list=exclude_style_list)
        F = pd.concat([f0,f1,f2])
        F = F[F.tradeDate>=sdate_backtest]
        if len(F) > 0:
            F.to_sql(tn,eg37,index=False,if_exists='append',chunksize=10000,dtype=d)
        obj_t.use('com')