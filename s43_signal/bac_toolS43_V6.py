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
V5
测试一下只有当e点超过a最高点的时候触发交易，我们之前是超过c点就触发。请您帮忙改一下。
我们就试一下csi300看看结果是不是好些

V6
测试一下超过c点触发交易（和原来的一样，只是加多一个条件）并且d点的rsi要大过b点rsi
保存在 s43_csi_20210701
'''
from bac_toolS43_V4 import fee1,fee2
from yq_toolsS45 import get_us_daytick_adj
from tqdm import tqdm
import pandas as pd
import numpy as np

from scipy import signal
#import statsmodels.api as sm
#import math
from yq_toolsS45 import save_pickle
from yq_toolsS45 import table_in_database
from yq_tools import chg_factor as chs_factor #载入日线数据
#from yq_tools import get_IdxCons as IdxConsGet #载入成分股数据
from yq_tools import get_index_tradeDate as MktIdxdGet #载入指数数据
from yq_tools import get_symbol_A
from yq_tools import create_table_update
from datetime import datetime
from yq_toolsS45 import get_spx_com
import multiprocessing
import warnings
warnings.filterwarnings("ignore")


num_core2 = int(multiprocessing.cpu_count()/2)
from yq_toolsS45 import create_db

db_name = 's37'
ab_para = 0
engine37 = create_db(db_name,'localhost')
engine = create_db('yuqerdata','localhost')
eg_plg = create_db('polygon','localhost')
eg_pro = create_db('data_pro','localhost')


tn_sig= 's43_signal0'
para_sel = True  #是否并行
is_plot = False
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
#手续费

# RSI
def RSI(t, periods=10):
    length = len(t)
    rsies = [np.nan]*length
    #数据长度不超过周期，无法计算；
    if length <= periods:
        return rsies
    #用于快速计算；
    up_avg = 0
    down_avg = 0

    #首先计算第一个RSI，用前periods+1个数据，构成periods个价差序列;
    first_t = t[:periods+1]
    for i in range(1, len(first_t)):
        #价格上涨;
        if first_t[i] >= first_t[i-1]:
            up_avg += first_t[i] - first_t[i-1]
        #价格下跌;
        else:
            down_avg += first_t[i-1] - first_t[i]
    up_avg = up_avg / periods
    down_avg = down_avg / periods
    rs = up_avg / down_avg
    rsies[periods] = 100 - 100/(1+rs)
    
    
    #后面的将使用快速计算；
    for j in range(periods+1, length):
        up = 0
        down = 0
        if t[j] >= t[j-1]:
            up = t[j] - t[j-1]
            down = 0
        else:
            up = 0
            down = t[j-1] - t[j]
        #类似移动平均的计算公式;
        up_avg = (up_avg*(periods - 1) + up)/periods
        down_avg = (down_avg*(periods - 1) + down)/periods
        rs = up_avg/down_avg
        rsies[j] = 100 - 100/(1+rs)
    return rsies
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
def is_bottom(a, b, c, d, e, s_ori, s_high, s_vol,rsi_v):
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
    #cond4 = s_ori[e] > s_ori[c]
    cond4 = s_ori[e] > s_ori[a]
    #测试一下超过c点触发交易（和原来的一样，只是加多一个条件）并且d点的rsi要大过b点rsi
    cond6 = rsi_v[d]>rsi_v[b]
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
    rsi_v = RSI(df.closePrice.values)
    
    
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
            if is_bottom(a, b, c, d, qsdu_e, s_ori, s_high, s_vol,rsi_v):
                [a, b ,c, d] , e = is_bottom(a, b, c, d, qsdu_e, s_ori, s_high, s_vol,rsi_v)
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

def back_test(df, e_list, hold_days = 5, is_plot = True):
    ini_day = deley_num+1
    e_signal = np.hstack([e_list + i for i in range(ini_day, hold_days + ini_day)])
    e_signal = np.unique(e_signal)
    e_signal = e_signal[e_signal < df.shape[0]]
    e_signal.sort()
    v = np.zeros(df.shape[0])
    v[e_signal] = 1    
    if is_plot:
        r = ((v * df['chgPct']) + 1).cumprod()
        r.plot()
        (df['chgPct'] + 1).cumprod().plot()
        plt.show()
    return (v * df['chgPct']) + 1

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
    df['r'] = df['sig'].shift(1)*df.chgPct
    df['r'].fillna(0,inplace=True)
    if is_plot:
        r = (df.r + 1).cumprod()
        r.plot()
        (df['chgPct'] + 1).cumprod().plot()
        plt.show()
    return df[['tradeDate','ticker','r','sig']]


def back_test_more(df, e_list, hold_days = [5, 7, 10 ,15, 20, 30, 35, 60]):
    df_back = pd.DataFrame([back_test(df, e_list, day, is_plot= False) for day in hold_days], index= ['r_%s'%i for i in hold_days]).T
    df_back['tradeDate'] = df['tradeDate']
    df_back['ticker'] = df['ticker']
    return df_back


def get_single_s43(x):
    ticker,begin,end,dtype=x    
    if dtype=='csi':
        df = chs_factor(ticker= ticker ,begin = begin ,end = end)
    elif dtype=="US":
        df = get_us_daytick_adj(ticker,begin,end)
        df = df[['ticker','tradeDate','openPrice_adj',
       'closePrice_adj', 'highPrice_adj', 'lowPrice_adj','turnoverVol']]
        df.columns = ['ticker','tradeDate','openPrice',
       'closePrice', 'highestPrice', 'lowestPrice','turnoverVol']
        df['chgPct'] = df.closePrice.pct_change()
        df.chgPct.fillna(0,inplace=True)
        df['accumAdjFactor'] = 1
    elif dtype == "HK":
        sql_tmp = '''select * from mkthkequdgets54 where ticker = "%s" 
        and tradeDate>="%s" and tradeDate<="%s" and closePrice is not null order by tradeDate'''
        df = pd.read_sql(sql_tmp % (ticker,begin,end),engine)
        df.chgPct.fillna(0,inplace=True)
        df['accumAdjFactor'] = 1
    elif dtype == "forex_day":
        sql_tmp = '''select * from forex_day where ticker = "%s" 
        and tradeDate>="%s" and tradeDate<="%s" and closePrice is not null order by tradeDate'''
        df = pd.read_sql(sql_tmp % (ticker,begin,end),eg_plg)
        df.rename(columns={'highPrice':'highestPrice','lowPrice':'lowestPrice'},inplace=True)
        df['chgPct'] = df.closePrice.pct_change()
        df.chgPct.fillna(0,inplace=True)
        df['accumAdjFactor'] = 1
    elif dtype in index_tdx.keys():
        sql_tmp = '''select * from %s where ticker = "%s" and index_id="%s" 
        and tradeDate>="%s" and tradeDate<="%s" and closePrice is not null order by tradeDate'''
        df = pd.read_sql(sql_tmp % (tn_tdx,ticker,dtype,begin,end),eg_pro)
        df.rename(columns={'highPrice':'highestPrice','lowPrice':'lowestPrice','Volume':'turnoverVol'},inplace=True)
        df['chgPct'] = df.closePrice.pct_change()
        df.chgPct.fillna(0,inplace=True)
        df['accumAdjFactor'] = 1
    if len(df)==0:
        return pd.DataFrame(),pd.DataFrame()
    if df.shape[0]<240*2:
        return pd.DataFrame(),pd.DataFrame()
    lenth_w, e_list = get_stock_signal(df , window = 3, is_plot = is_plot)
    if len(e_list)==0:
        return pd.DataFrame(),pd.DataFrame()
    try:
        df_back = back_test_more(df, e_list) 
        print('S43 %s update %s' % (dtype,ticker))
        return df_back,df.iloc[e_list][['ticker','tradeDate']]
    except:
        print('S43 %s stock E %s' % (dtype,ticker))
        return pd.DataFrame(),pd.DataFrame()


#直接给出最终结果
def back_test_more_v2(df, e_list, hold_days = 15):
    df_back = back_test_v2(df, e_list, hold_days, is_plot= is_plot)
    df_back['tradeDate'] = df['tradeDate']
    df_back['ticker'] = df['ticker']
    return df_back

def get_single_s43_v2(x):
    ticker,begin,end,dtype=x    
    if dtype=='csi':
        df = chs_factor(ticker= ticker ,begin = begin ,end = end)
    elif dtype=="US":
        df = get_us_daytick_adj(ticker,begin,end)
        df = df[['ticker','tradeDate','openPrice_adj',
       'closePrice_adj', 'highPrice_adj', 'lowPrice_adj','turnoverVol']]
        df.columns = ['ticker','tradeDate','openPrice',
       'closePrice', 'highestPrice', 'lowestPrice','turnoverVol']
        df['chgPct'] = df.closePrice.pct_change()
        df.chgPct.fillna(0,inplace=True)
        df['accumAdjFactor'] = 1
    elif dtype in ["HK",'hsce','hk_ggt']:
        sql_tmp = '''select * from mkthkequdgets54 where ticker = "%0.5d" 
        and tradeDate>="%s" and tradeDate<="%s" and closePrice is not null order by tradeDate'''
        df = pd.read_sql(sql_tmp % (int(ticker),begin,end),engine)
        df.chgPct.fillna(0,inplace=True)
        df['accumAdjFactor'] = 1
    elif dtype == "forex_day":
        sql_tmp = '''select * from forex_day where ticker = "%s" 
        and tradeDate>="%s" and tradeDate<="%s" and closePrice is not null order by tradeDate'''
        df = pd.read_sql(sql_tmp % (ticker,begin,end),eg_plg)
        df.rename(columns={'highPrice':'highestPrice','lowPrice':'lowestPrice'},inplace=True)
        df['chgPct'] = df.closePrice.pct_change()
        df.chgPct.fillna(0,inplace=True)
        df['accumAdjFactor'] = 1
    elif dtype in index_tdx.keys():
        sql_tmp = '''select * from %s where ticker = "%s" and index_id="%s" 
        and tradeDate>="%s" and tradeDate<="%s" and closePrice is not null order by tradeDate'''
        df = pd.read_sql(sql_tmp % (tn_tdx,ticker,dtype,begin,end),eg_pro)
        df.drop_duplicates(subset=['ticker','tradeDate'],inplace=True)
        df.reset_index(drop=True,inplace=True)
        df.rename(columns={'highPrice':'highestPrice','lowPrice':'lowestPrice','Volume':'turnoverVol'},inplace=True)
        df['chgPct'] = df.closePrice.pct_change()
        df.chgPct.fillna(0,inplace=True)
        df['accumAdjFactor'] = 1
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
        
        #手续费
        sub_fee1 = fee1[dtype]/10000
        sub_fee2 = fee2[dtype]/10000
        
        tmp = (df_back.sig.shift(1)==1)&(df_back.sig.shift(2)==0) #开仓前一刻0，当前1
        df_back.r[tmp] = df_back.r[tmp]-sub_fee1
        tmp = (df_back.sig.shift(1)==1)&(df_back.sig==0) #当前1，下一天0
        df_back.r[tmp] = df_back.r[tmp]-sub_fee2
        
        print('S43 %s update %s' % (dtype,ticker))
        return df_back
    except:
        print('S43 %s stock E %s' % (dtype,ticker))
        return pd.DataFrame()

def create_s43_tb():
    var_name = ['tradeDate', 'ticker','r_5', 'r_7', 'r_10', 'r_15', 'r_20', 'r_30', 'r_35', 'r_60']
    var_type = []
    for i in var_name:
        var_type.append('float')
    var_type[0] = 'date'
    var_type[1] = 'varchar(8)'
    key_str = 'tradeDate,ticker'            
    create_table_update(db_name,tn,var_name,var_type,key_str,1) 
    
def create_s43_tb_v2():
    var_name = ['index0','tradeDate', 'ticker','r','sig','mark_date']
    var_type = []
    for i in var_name:
        var_type.append('float')
    var_type[0] = 'varchar(12)'
    var_type[1] = 'date'
    var_type[2] = 'varchar(12)'
    var_type[-1] = 'int'
    var_type[-2] = 'int'
    key_str = 'tradeDate,ticker,index0'            
    create_table_update(db_name,tn,var_name,var_type,key_str,1)     

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

if __name__ == "__main__":
    time_start = datetime.now()
    for dtype in index_id_zx02+['hk_ggt','csi','US','HK','forex_day','as51', 'topix', 'twse','hsce']:
        
        tn = 's43_%s_20210701' % dtype.lower()
        begin = '2010-10-01'    
        end = datetime.strftime(datetime.now(),'%Y-%m-%d')
        if table_in_database(db_name,tn):
            t0 = pd.read_sql('select tradeDate from %s where index0 = "%s" order by tradeDate desc limit 1' % (tn,dtype),engine37)
            if len(t0)>0:
                t0 = t0.tradeDate.astype(str)[0]
            else:
                t0 = begin
        else:
            create_s43_tb_v2()
            t0 = begin
        if dtype == "csi":
            tt = pd.read_sql('select tradeDate from yq_dayprice order by tradeDate desc limit 1',engine)
        elif dtype== "US":
            tt = pd.read_sql('select tradeDate from  usastock_day order by tradeDate desc limit 1',eg_plg)    
        elif dtype in ["HK",'hsce','hk_ggt']:
            tt = pd.read_sql('select tradeDate from mkthkequdgets54 order by tradeDate desc limit 1',engine)
        elif dtype in index_tdx.keys():
            tt = pd.read_sql('select tradeDate from main_index_s68 where index_id="%s" order by tradeDate desc limit 1' % dtype,eg_pro)
        elif dtype == "forex_day":
            tt = pd.read_sql('select tradeDate from  forex_day order by tradeDate desc limit 1',eg_plg)   
        tt = tt[tt.columns[0]].astype(str).values[0]
        if tt> t0:
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
            #sig0 = [i[1] for i in back_dfs]
            #back_dfs = [i[0] for i in back_dfs]
            #记录了信号的初始位置
            #sig0 = pd.concat(sig0)   
            #save_pickle('tmp.pkl',back_dfs)
            back_df = pd.concat(back_dfs)
            
            back_df=back_df[back_df.tradeDate.astype(str)>t0]
            #sig0=sig0[sig0.tradeDate.astype(str)>t0]
            if len(back_df)>0:
                back_df['index0'] = dtype
                #sig0['index0'] = dtype
                back_df.to_sql(tn,engine37,if_exists='append',index=False,chunksize=3000)
                #sig0.to_sql(tn_sig,engine37,if_exists='append',index=False,chunksize=3000)
                
            time_end = datetime.now()
            print('Time used %s' % (time_end-time_start))
        else:
            print('S45 %s 数据已经是最新，无需更新' % dtype)