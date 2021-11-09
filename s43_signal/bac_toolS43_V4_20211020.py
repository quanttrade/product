# coding: utf-8
'''
双底策略，补充结果
20210509
1）美国股票 SPX
2）香港股票 HSI
3）外汇日线和分钟线 

升级
记录信号位置，为后续寻找信号做准备
V2
信号延迟7天发送
20210510
增加彭博社数据

V3
结果加入一列signal，便于导出信号
V4
泰国 买11/10000，卖出22/10000

v4 v2版本中信号判断采用的是回头看的方法，这个主要是用来统计方法收益如何，如果能获取
信号的前提下，策略收益如何，不能获取信号
我们需要升级 能自动判断信号

20211018 test price on 1200 and 1455
20211020
获取数据后，发出信号
#只导出近10天的信号

'''
from M_S43_get_data import update_tdx_now
import os
from bac_toolS43_V4 import fee1,fee2
from bac_toolS43_V4_up20211014 import get_db_data
from yq_toolsS45_linux import get_us_daytick_adj,time_use_tool
from tqdm import tqdm
import pandas as pd
import numpy as np

from scipy import signal
#import statsmodels.api as sm
#import math
from yq_toolsS45_linux import save_pickle,get_IdxConsGet
from yq_toolsS45_linux import table_in_database
from yq_toolsS45_linux import chg_factor as chs_factor #载入日线数据
#from yq_tools import get_IdxCons as IdxConsGet #载入成分股数据
from yq_toolsS45_linux import get_index_tradeDate as MktIdxdGet #载入指数数据
from yq_toolsS45_linux import get_symbol_A
from yq_toolsS45_linux import create_table
from datetime import datetime
from yq_toolsS45_linux import get_spx_com
import multiprocessing
import warnings
warnings.filterwarnings("ignore")

result_str = '1200'
num_core2 = int(multiprocessing.cpu_count()/2)
from yq_toolsS45_linux import create_db

db_name = 's37'
ab_para = 0
engine37 = create_db(db_name,'localhost')
engine = create_db('yuqerdata','localhost')
eg_plg = create_db('polygon','localhost')
eg_pro = create_db('data_pro','localhost')

tn_sig= 's43_signal0'
para_sel = True  #是否并行
is_plot = False
bac_sel = False
signal_keepday = 10
obj_t = time_use_tool()
if is_plot:
    import matplotlib.pyplot as plt    
    
point_sel = 1
if point_sel == 1:
    deley_num = 1
else:
    deley_num = 6    

index_id_zx02 = ['kosdaq', 'kospi', 'msci', 'ndx', 'nifty', 'nky', 'RTY', 'set50', 'sx5e',
                       'ukx', 'xin9i']
index_id_zx02_info = ['KOSDAQ','KOSPI2','TAMSCI','NDX','NIFTY','NKY','RTY','SET50','SX5E',
                      'UKX','XIN9I']

para_sig_d = dict(zip(['US','HK','forex_day','as51','topix','twse','csi','hsce','hk_ggt']+index_id_zx02,
                      [15,15,5,10,10,10,15,15,15]+[15]*len(index_id_zx02)))


index_tdx = {'as51':'AS51','topix':'TPX','twse':'TWSE','hsce':'HSCEI','hk_ggt':'hk_ggt'}
index_tdx.update(dict(zip(index_id_zx02,index_id_zx02_info)))

tn_tdx = 'main_index_s68'
#tn_tdx = 'main_index_zx02'
#point e判断不对的
def get_points(n, index_down, index_up, s_ori ,back_w = 1):
    qsdu_e = index_up[n]
    point_b, point_d = index_down[n - 2 :n]
    point_a, point_c = index_up[n - 2 :n]
    point_a, point_c = s_ori.loc[point_a -back_w - 1 : point_a + back_w].idxmax(), \
                                        s_ori.loc[point_c -back_w - 1: point_c + back_w].idxmax() 
    point_b, point_d = s_ori.loc[point_b -back_w - 1: point_b + back_w].idxmin(), \
                                        s_ori.loc[point_d -back_w - 1: point_d + back_w].idxmin()
    qsdu_e = s_ori.loc[qsdu_e - back_w - 1: qsdu_e + back_w].idxmax()
    #pre_a = index_down[n - 4]
    return point_a, point_b, point_c, point_d, qsdu_e

#加上前期30%的这个条件，找不到信号
def is_bottom(a, b, c, d, e, s_ori, s_high, s_vol):
    cond6 = (b-a)>=ab_para #20211003
    ## 前期30% 涨幅
    ## 给定一个时间，在时间内与最低点差30%即可
    #pre_day = a - 200
    #r_pre = s_ori[a] / s_ori[pre_day: a].min() - 1
    #cond1 = r_pre > 0.3  ## bug
    ## a点高于c点 第一个高点大于第二个高点
    cond2 = s_high[a] > s_high[c]
    ## d低于b点 第一个低点大于第二个低点
    cond3 = s_ori[b] > s_ori[d]
    ## ad之间的限制  下降50%以内
    cond5 = s_ori[a] / s_ori[d] - 1 < 0.5
    ## 判断是否出现突破
    ## 其中e点为伪e 第三个高点大于第二个高点
    cond4 = s_ori[e] > s_ori[c]
    if cond2 and cond3 and cond4 and cond5 and cond6:
        ## 判断e点
        ## 最高点
        e_cond1 = s_high.loc[d:e] > s_high[c]
        e_supply = np.arange(d, e+1)[e_cond1.values]
        # 判断成交量
        # 成交量判断无效
        for i in e_supply:
            if s_vol[i] > s_vol.loc[c:i].mean()*1.2:
                e = i
                return [a, b, c, d], e
                break

def get_stock_signal(df , window = 5, is_plot = True):
    ### 数据获取
    s_ori = df['closePrice'] * df['accumAdjFactor']
    s_high = df['highestPrice'] * df['accumAdjFactor']
    s_vol = df['turnoverVol']
    ## 去噪过程
    trend = s_ori.rolling(window).mean()
    #做完平滑后，信号会晚发出来，主要是判断点的位置会延迟
    back_w = int(window / 2.0)
    # trend.plot()
    ## 获取去噪之后的高低点
    index_down = signal.find_peaks(-trend)[0]
    index_up = signal.find_peaks(trend)[0]
    
    if len(index_down)<4 or len(index_up)<5:
        return [],[]
    else:
        index_down = index_down[index_down > index_up[0]]
        if len(index_up)==len(index_down):
            index_up = np.append(index_up,len(df))
        ## 获取信号
        e_list = []
        lenth_w = []
        #这里需要重点升级
        for n in range(5, index_up.shape[0]):
            a,b,c,d,qsdu_e = get_points(n, index_down, index_up, s_ori, back_w)
            if is_bottom(a, b, c, d, qsdu_e, s_ori, s_high, s_vol):
                [a, b ,c, d] , e = is_bottom(a, b, c, d, qsdu_e, s_ori, s_high, s_vol)
                #实际情况，信号不要提前发送
                if n==index_up.shape[0]-1 & e<index_up[n]:
                    e = index_up[n]
                e_list.append(e)
                lenth_w.append(e - a)
        if is_plot:
            s_ori.plot()
            plt.plot(e_list, s_ori[e_list], 'r*')
        return np.array(lenth_w), np.array(e_list)

## 统计盈利
def stat_ratio(e_list, df, n):
    
    tmp_ind = e_list+n
    tmp_ind = tmp_ind[tmp_ind<len(df)]
    tmp_ind = tmp_ind-n
    
    return df.loc[tmp_ind + n]['closePrice'].values / df.loc[tmp_ind + 1]['openPrice'].values - 1
## 统计到df
def stock_df(df, e_list, lenth_w, n_list = [5, 10, 15, 30]):
    df_1 = df.loc[e_list][['tradeDate', 'ticker']]
    ratio_list = [stat_ratio(e_list, df, n) for n in [5, 10, 15, 30]]
    df_new = pd.DataFrame(ratio_list + [lenth_w], index = ['r_5', 'r_10', 'r_15','r_30', 'lenth']).T
    df_1.index = df_new.index
    return pd.concat([df_1, df_new], axis = 1)

#记录信号功能
def back_test_v2(df, e_list, hold_days = 5, is_plot = True):
    ini_day = deley_num
    e_signal = np.hstack([e_list + i for i in range(ini_day, hold_days + ini_day)])
    e_signal = np.unique(e_signal)
    e_signal = e_signal[e_signal < df.shape[0]]
    e_signal.sort()
    v = np.zeros(df.shape[0])
    v[e_signal] = 1 
    
    df['sig'] = v
    if bac_sel:
        df['r'] = df['sig'].shift(1)*df.chgPct
        df['r'].fillna(0,inplace=True)
        if is_plot:
            r = (df.r + 1).cumprod()
            r.plot()
            (df['chgPct'] + 1).cumprod().plot()
            plt.show()
        return df[['tradeDate','ticker','r','sig']]
    else:
        return df[['tradeDate','ticker','sig']]


#直接给出最终结果
def back_test_more_v2(df, e_list, hold_days = 15):
    df_back = back_test_v2(df, e_list, hold_days, is_plot= is_plot)
    df_back['tradeDate'] = df['tradeDate']
    df_back['ticker'] = df['ticker']
    return df_back

def get_single_data(ticker,begin,end,dtype):
    print(result_str)
    #这里涉及一个数据对接的问题
    #数据先更新，然后再对接
    if dtype=='csi':
        #chgpct update
        if  ticker[0]=='6':
            tmp = 'sh%s' % ticker
        else:
            tmp = 'sz%s' % ticker
        sql_tmp = 'select * from %s where symbol = "%s" and tradingdate>="%s" and tradingdate<="%s" order by symbol,tradingdate'
        
        x1 = get_db_data('data_pro',sql_tmp % ('ycz_data_%s' % result_str,tmp,begin,end))
        #对接
        x1_tdx = get_db_data('data_pro',sql_tmp % ('tdx_data_s43',tmp,str(x1.tradingdate.max()),end))
        x1 = pd.concat([x1,x1_tdx.iloc[1:]])
        
        sql_str_fq = """select tradeDate,accumAdjFactor from mktequdadjafget where 
                        ticker = "%s" order by tradeDate"""
        sql_str_fq = sql_str_fq % ticker
        y = get_db_data('yuqerdata',sql_str_fq)
        
        x1.rename(columns={'tradingdate':'tradeDate'},inplace=True)
        
        x1 = x1.merge(y,on='tradeDate',how='left')
        x1.sort_values('tradeDate',inplace=True)
        x1.accumAdjFactor.fillna(method='ffill',inplace=True)
        x1.rename(columns = {'open':'openPrice','close':'closePrice',
                             'high':'highestPrice','low':'lowestPrice',
                             'volume':'turnoverVol'},inplace=True)    
        x1['closePrice'] = x1['closePrice']*x1['accumAdjFactor']
        x1['openPrice'] = x1['openPrice']*x1['accumAdjFactor']
        x1['lowestPrice'] = x1['lowestPrice']*x1['accumAdjFactor']
        x1['highestPrice'] = x1['highestPrice']*x1['accumAdjFactor']
        
        if bac_sel:
            xf = get_db_data('data_pro',sql_tmp % ('ycz_data_1500',tmp,begin,end))
            xf.rename(columns={'tradingdate':'tradeDate'},inplace=True)
            xf = xf.merge(y,on='tradeDate')
            xf['closePrice_f'] = xf['close']*xf['accumAdjFactor']            
            df = x1.merge(xf[['tradeDate','closePrice_f']])
            df.sort_values('tradeDate',inplace=True)
            df['chgPct'] = df.closePrice_f.pct_change()
            df.chgPct.fillna(0,inplace=True)
        else:
            df = x1.copy()
        df['ticker'] = ticker
        df['accumAdjFactor'] = 1    
            
    elif dtype=="US":
        df = get_us_daytick_adj(ticker,begin,end)
        df = df[['ticker','tradeDate','openPrice_adj',
       'closePrice_adj', 'highPrice_adj', 'lowPrice_adj','turnoverVol']]
        df.columns = ['ticker','tradeDate','openPrice',
       'closePrice', 'highestPrice', 'lowestPrice','turnoverVol']
        df['chgPct'] = df.closePrice.pct_change()
        df['chg0'] = df.closePrice / df.openPrice-1
        df['chg1'] = df.openPrice / df.closePrice.shift(1)-1
        df['accumAdjFactor'] = 1
    elif dtype in ["HK",'hsce','hk_ggt']:
        sql_tmp = '''select * from mkthkequdgets54 where ticker = "%0.5d" 
        and tradeDate>="%s" and tradeDate<="%s" and closePrice is not null order by tradeDate'''
        df = get_db_data('yuqerdata',sql_tmp % (int(ticker),begin,end))
        df['chg0'] = df.closePrice /df.openPrice-1
        df['chg1'] = df.openPrice / df.preClosePrice-1
        df['accumAdjFactor'] = 1
    elif dtype == "forex_day":
        sql_tmp = '''select * from forex_day where ticker = "%s" 
        and tradeDate>="%s" and tradeDate<="%s" and closePrice is not null order by tradeDate'''
        df = get_db_data('polygon',sql_tmp % (ticker,begin,end))        
        df.rename(columns={'highPrice':'highestPrice','lowPrice':'lowestPrice'},inplace=True)
        df['chgPct'] = df.closePrice.pct_change()
        df['chg0'] = df.closePrice / df.openPrice-1
        df['chg1'] = df.openPrice / df.closePrice.shift(1)-1
        df['accumAdjFactor'] = 1
    elif dtype in index_tdx.keys():
        sql_tmp = '''select * from %s where ticker = "%s" and index_id="%s" 
        and tradeDate>="%s" and tradeDate<="%s" and closePrice is not null order by tradeDate'''
        df = get_db_data('data_pro',sql_tmp % (tn_tdx,ticker,dtype,begin,end))
        df.drop_duplicates(subset=['ticker','tradeDate'],inplace=True)
        df.reset_index(drop=True,inplace=True)
        df.rename(columns={'highPrice':'highestPrice','lowPrice':'lowestPrice','Volume':'turnoverVol'},inplace=True)
        df['chgPct'] = df.closePrice.pct_change()
        df['chg0'] = df.closePrice / df.openPrice-1
        df['chg1'] = df.openPrice / df.closePrice.shift(1)-1
        df['accumAdjFactor'] = 1
    return df

def get_single_s43_v2(x):
    ticker,begin,end,dtype=x    
    df = get_single_data(ticker,begin,end,dtype)
    if len(df)==0:
        return pd.DataFrame()
    if df.shape[0]<240:
        return pd.DataFrame()
    lenth_w, e_list = get_stock_signal(df , window = 3, is_plot = is_plot)
    if len(e_list)==0:
        return pd.DataFrame()
    try:
        if dtype in para_sig_d.keys():
            tmp = para_sig_d[dtype]
        else:
            tmp = 15
        df_back = back_test_more_v2(df, e_list,tmp) 
        df_back['mark_date'] = pd.np.nan
        df_back.mark_date.loc[e_list]=1        
        if bac_sel:
            #手续费
            sub_fee1 = fee1[dtype]/10000
            sub_fee2 = fee2[dtype]/10000
            
            tmp = (df_back.sig.shift(1)==1)&(df_back.sig.shift(2)==0) #开仓前一刻0，当前1
            df_back.r[tmp] = df_back.r[tmp]-sub_fee1
            tmp = (df_back.sig.shift(1)==1)&(df_back.sig==0) #当前1，下一天0
            df_back.r[tmp] = df_back.r[tmp]-sub_fee2
        else:
            df_back = df_back.iloc[-signal_keepday:]
        print('S43 %s update %s' % (dtype,ticker))
        return df_back
    except:
        print('S43 %s stock E %s' % (dtype,ticker))
        return pd.DataFrame()

  

def get_ticker_pool(dtype):
    if dtype=="csi":
        hs_300_pool = get_symbol_A()
    elif dtype == "US":
        hs_300_pool = get_spx_com('2021-05-09')    
    elif dtype == "HK":
        hs_300_pool = ' select distinct(ticker) from main_index_s68 where index_id = "HSI" and ticker != "HSI"'
        hs_300_pool = pd.read_sql(hs_300_pool,eg_pro)
        hs_300_pool = hs_300_pool.ticker.tolist()
    elif dtype == 'hsce':
        hs_300_pool = ' select distinct(ticker) from main_index_s68 where index_id = "hsce" and ticker != "HSCEI"'
        hs_300_pool = pd.read_sql(hs_300_pool,eg_pro)
        hs_300_pool = hs_300_pool.ticker.tolist()
        hs_300_pool = ['%0.5d' % int(i) for i in hs_300_pool]
    elif dtype == 'hk_ggt':
        hs_300_pool = pd.read_csv('港股通股票池20210513.csv',encoding='gbk')
        hs_300_pool = hs_300_pool.ticker.tolist()
        hs_300_pool = ['%0.5d' % i for i in hs_300_pool]
        
        tmp1 = get_ticker_pool('HK')
        tmp2 = get_ticker_pool('hsce')
        hs_300_pool = list(set(hs_300_pool+tmp1+tmp2))
    elif dtype in index_tdx.keys():
        hs_300_pool = ' select distinct(ticker) from %s where index_id = "%s" and ticker != "%s"'
        hs_300_pool = pd.read_sql(hs_300_pool % (tn_tdx,dtype,index_tdx[dtype]),eg_pro)
        hs_300_pool = hs_300_pool.ticker.tolist()    
    elif dtype in ["forex_day","forex_min"]:
        hs_300_pool = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'NZDUSD', 'USDCAD',
               'USDCHF', 'EURGBP', 'EURCHF', 'EURAUD', 'EURNZD', 'EURCAD', 'AUDJPY', 'NZDJPY',
               'EURJPY', 'CHFJPY', 'GBPJPY', 'CADJPY', 'USDCNH', 'USDINR', 'USDTRY', 'USDRUB',
               'USDZAR'] 
    else:
        hs_300_pool = []
    return hs_300_pool


def write_signal(signal_re,key_str = 'S43原始框架'):
    pool_code=['A','000300','000905','00852']
    for sub_pool in pool_code:   
        signal_fn = '%s_csi_%s_%s.csv' % (key_str,sub_pool,str(signal_re.index[-1])[:10])
        signal_path = 's43_信号'
        if not os.path.exists(signal_path):
            os.mkdir(signal_path)
            
        p,_ = get_IdxConsGet(sub_pool,datetime.strftime(datetime.now(),'%Y-%m-%d'))        
        p = set(signal_re.columns.tolist())&set(p.tolist())
        #
        sub_re = signal_re[p].copy()        
        v = ['sh%s' % i if i[0]=='6' else 'sz%s' % i  for i in sub_re.columns ]
        sub_re.columns = v
        sub_re.to_csv(os.path.join(signal_path,signal_fn))


if __name__ == "__main__":
    time_start = datetime.now()
    dtype = 'csi'
    begin = '2010-10-01'    
    end = datetime.strftime(datetime.now(),'%Y-%m-%d')
    
    print('dealing with %s' % dtype)
    hs_300_pool=get_ticker_pool(dtype)
        
    T_symbols = len(hs_300_pool)
    if para_sel:
        p1 = hs_300_pool
        p2 = T_symbols*[begin]
        p3 = T_symbols*[end]
        p4 = T_symbols*[dtype]
        pool = multiprocessing.Pool(num_core2)
        back_dfs = pool.map(get_single_s43_v2, zip(p1,p2,p3,p4))
        pool.close()
        pool.join() 
    else:    
        back_dfs = []
        for ticker in tqdm(hs_300_pool):
            df_back = get_single_s43_v2([ticker,begin,end,dtype])
            back_dfs.append(df_back)
    back_df = pd.concat(back_dfs)
    #导出信号
    signal_re = back_df.set_index(['tradeDate','ticker'])
    signal_re = signal_re[['sig']].unstack().droplevel(0,axis=1)
    signal_re = signal_re.iloc[-10:]
    #signal_re.to_pickle('tmp.pkl')
    #获取各个股票池的结果
    key_str = 'S43原始框架'
    write_signal(signal_re,key_str)
    
    obj_t.use()