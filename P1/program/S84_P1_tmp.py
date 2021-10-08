# -*- coding: utf-8 -*-
"""
Created on Sun Apr 26 22:18:24 2020
可以计算成分股
可以并行
使用后复权数据计算
@author: Asus
"""
from tqdm import tqdm
import pandas as pd
import numpy as np
from sklearn.cluster import SpectralCoclustering as bicluster
from sklearn.preprocessing import MinMaxScaler
import os
from yq_toolsS45 import get_MktEqudAdjAfGet_update
from yq_toolsS45 import get_IdxConsGet
from yq_toolsS45 import create_db
from yq_toolsS45 import time_use_tool
from yq_toolsS45 import save_pickle
import multiprocessing
num_core = int(multiprocessing.cpu_count()/2)


import warnings
warnings.filterwarnings('ignore')
BX = True

eg_pro = create_db('data_pro')
eg_37 = create_db('s37')

def refine_adjfactor(df):
    df_new = df.copy()
    df_new.set_index('tradeDate', inplace= True)
    define_cols = [col for col in df_new.columns if 'Price' in col]
    for col in define_cols:
        ## 价格修正复权
        df_new[col] = df_new[col] * df_new['accumAdjFactor']
        # 对价格缺失日期价格修正
        df_new[col] = df_new[col].replace(0, np.nan).fillna(method = 'ffill')
    return df_new

def mean_index(s, n = 5):
    return s.rolling(n).mean()

def rsi_index(s, n = 5):
    gain = s.rolling(n).apply(lambda x: x[x > 0].mean() if (x > 0).sum() != 0 else 0)
    loss = s.rolling(n).apply(lambda x: - x[x < 0].mean() if (x < 0).sum() != 0 else 0)
    return gain / (gain + loss)

def wr_index(s_h, s_l, s_c, n = 5):
    h_n = s_h.rolling(n).apply(lambda x: x.max())
    l_n = s_l.rolling(n).apply(lambda x: x.min())
    return (h_n - s_c) / (h_n - l_n)

def roc_index(s, n= 5):
    return s / s.shift(n) - 1

def ema_index(s, n=5):
    return s.ewm(n, min_periods= n).mean()

def atr_index(s_h, s_l, s_c, n=5):
    sc_shift = s_c.shift(1)
    tr = pd.concat([s_h - s_l, (s_h - sc_shift ).abs(), (s_l - sc_shift ).abs()], axis= 1).max(axis = 1)
    return tr.rolling(n).mean()

def adx_index(s_h, s_l, s_c, n=5):
    sc_shift = s_c.shift(1)
    tr = pd.concat([s_h - s_l, (s_h - sc_shift).abs(), (s_l - sc_shift).abs()], axis=1).max(axis=1)
    ## 计算hd与ld
    hd = s_h - s_h.shift(1)
    ld = s_l.shift(1) - s_l
    hd_index = hd[(hd <= 0) | (hd < ld)].index
    hd.loc[hd_index] = 0
    ld_index = ld[(ld <= 0) | (ld < hd)].index
    ld.loc[ld_index] = 0

    ## 计算hdi与ldi
    hdi = hd.rolling(n).sum() / tr
    ldi = ld.rolling(n).sum() / tr

    adx = (hdi - ldi).abs() / (hdi + ldi)
    return adx.ewm(span = n).mean()

def label_func(x, thr = 0.005):
    if x> thr:
        l = 1
    elif x < -thr:
        l = -1
    else:
        l = 0
    return l

def get_signal(df,ticker):
    if len(df)>1500:
        df_factor = pd.DataFrame(index= df.index)
        # roc
        for n in [12, 24, 36]:
            df_factor['roc_' + str(n)] = roc_index(df['closePrice'], n= n)
        # ema
        for n in [12, 24, 36]:
            df_factor['ema_' + str(n)] = ema_index(df['closePrice'], n= n)
        # adx
        for n in [14, 28, 42]:
            df_factor['adx_' + str(n)] = adx_index(df['highestPrice'], df['lowestPrice'],
                                                   df['closePrice'], n= n)
        # atr
        for n in [14, 28, 42]:
            df_factor['atr_' + str(n)] = atr_index(df['highestPrice'], df['lowestPrice'],
                                                   df['closePrice'], n= n)
        # sma
        for n in [10, 20, 30, 40]:
            df_factor['sma_' + str(n)] = mean_index(df['closePrice'], n= n)
        # wr
        for n in [9, 18, 27, 36]:
            df_factor['wr_' + str(n)] = wr_index(df['highestPrice'], df['lowestPrice'],
                                                 df['closePrice'], n= n)
        # rsi
        for n in [6, 12, 18, 24, 30, 36]:
            df_factor['rsi_' + str(n)] = rsi_index(df['chgPct'], n= n)
            
            
        # 标准化
        df_factor.dropna(inplace= True)
        if len(df_factor)>220:
            std_model = MinMaxScaler()
            x_scale = std_model.fit_transform(df_factor)
            #df_scale = pd.DataFrame(x_scale, columns= df_factor.columns, index= df_factor.index )
            # 构成
            frv = df_factor['sma_10'] / df['closePrice'] - 1
            df_factor['label'] = frv.apply(lambda x: label_func(x, thr= 0.005))
            model = bicluster(n_clusters= 5, random_state=0)
            model.fit(x_scale)
            df_factor['clus'] = model.row_labels_
            #print(df_factor.groupby('clus')['label'].mean())
            
            set_b = df_factor.groupby('clus')['label'].apply(lambda x: np.array([x == 1]).sum() / np.float(x.shape[0]))
            set_h = df_factor.groupby('clus')['label'].apply(lambda x: np.array([x == 0]).sum() / np.float(x.shape[0]))
            set_s = df_factor.groupby('clus')['label'].apply(lambda x: np.array([x == -1]).sum() / np.float(x.shape[0]))
            
            set_bhs = pd.concat([set_b, set_h, set_s], axis = 1)
            set_bhs.columns = ['b', 'h', 's']
            
            sup_dict = set_bhs.apply(lambda x: x.argmax(), axis = 1).to_dict()
            
            tmp = set_bhs.columns.tolist()
            for i in sup_dict.keys():
                sup_dict[i] = tmp[sup_dict[i]]
            dec_df = df_factor['clus'].map(sup_dict).map({'s':-1, 'b':1, 'h':np.nan})
        
            
            ## 原文测试有问题，信号的过程是一个滞后过程，出现信号后第二天才能根据信号进行测试。
            signal_df = dec_df.fillna(method= 'ffill').apply(lambda x: 0 if x > 0 else 1).shift(1)
            signal0 = dec_df.fillna(method= 'ffill').apply(lambda x: 0 if x > 0 else 1)
            z = df['chgPct'].loc[signal_df.index] * signal_df
            p = df['chgPct'].loc[signal_df.index]
            z.name='cc'
            p.name = 'chg'
            signal0.name = 'sig'
            z = z.to_frame()
            p = p.to_frame()
            #(pd.concat([z,p],axis=1) + 1).cumprod().plot()
            y1 = pd.concat([z,p,signal0],axis=1)
            y1['ticker'] = ticker
            ### adair added
            o_chpPct = df['openPrice']/df['openPrice'].shift(1) - 1
            ## 按开盘价操作
            signal_df = dec_df.fillna(method= 'ffill').apply(lambda x: 0 if x > 0 else 1).shift(2)
            z = o_chpPct.loc[signal_df.index] * signal_df
            p = o_chpPct.loc[signal_df.index]
            z.name='oo'
            p.name = 'chg'
            y2 = pd.concat([z,p,signal0],axis=1)
            y2['ticker'] = ticker
            #(z + 1).cumprod().plot(legend ='strategy')
            #(p + 1).cumprod().plot(legend ='original')
            #plt.show()
            return y1,y2
        else:
            return pd.DataFrame(),pd.DataFrame()
    else:
        return pd.DataFrame(),pd.DataFrame()

def get_result_ticker(ticker = '000001'):
    print('B %s' % ticker)    
    df = get_MktEqudAdjAfGet_update(ticker,'2009-01-01','2099-01-01','*')
    df.set_index('tradeDate',inplace=True)
    df.sort_index(inplace=True)
    df['chgPct'] = df.closePrice.pct_change()
    _,y2 = get_signal(df.copy(),ticker)
    print('S %s' % ticker)
    return y2


def get_csi_data(index = '000300'):
    fn = 's84p1_csi%s.pkl' % index
    if not os.path.exists(fn):
        tickers,_ = get_IdxConsGet(index,'2010-01-01')
        if BX:
            pool = multiprocessing.Pool(num_core)
            Y = pool.map(get_result_ticker,tickers)
            pool.close()
            pool.join()   
        else:
            Y = []
            for ticker in tqdm(tickers):
                Y.append(get_result_ticker(ticker))
        Y=pd.concat(Y)
        Y.to_pickle(fn)

def get_iso_index_info():
    index_id_zx02 = ['kosdaq', 'kospi', 'msci', 'ndx', 'nifty', 'nky', 'RTY', 'set50', 'sx5e',
                       'ukx', 'xin9i']
    index_id_zx02_info = ['KOSDAQ','KOSPI2','TAMSCI','NDX','NIFTY','NKY','RTY','SET50','SX5E',
                          'UKX','XIN9I']
    fee1_tmp = [3/10000,3/10000,2/10000,1/10000,1/1000,1/10000,1/10000,11/10000,1/10000,1/10000,2/10000]
    fee2_tmp = [3/1000,3/1000,32/10000,1/10000,1/1000,1/10000,1/10000,22/10000,1/10000,1/10000,12/10000]
    
    index_tdx = {'as51':'AS51','topix':'TPX','twse':'TWSE','hsce':'HSCEI','hsi':'HSI'}
    index_tdx.update(dict(zip(index_id_zx02,index_id_zx02_info)))
    
    fee1 = dict(zip(['US','HK','forex_day','as51','topix','twse','csi','hsce'],[1,11,0.25,1,1,2,2,11,11]))
    fee2 = dict(zip(['US','HK','forex_day','as51','topix','twse','csi','hsce'],[1,11,0.25,1,1,32,12,11,11]))
    
    fee1_1 = dict(zip(index_id_zx02,[i*10000 for i in fee1_tmp]))
    fee2_1 = dict(zip(index_id_zx02,[i*10000 for i in fee2_tmp]))
    fee1.update(fee1_1)
    fee2.update(fee2_1)    
    return index_tdx,fee1,fee2

#国际指数数据    
def get_iso_index_data(index_code,t1='2000-01-01'):
    iso_info,_,_ = get_iso_index_info()
    sql_f = 'select tradeDate,openPrice,closePrice,highPrice as highestPrice,lowPrice as lowestPrice from main_index_s68 where index_id = "%s" and ticker = "%s" order by tradeDate'
    x = pd.read_sql(sql_f % (index_code,iso_info[index_code]),eg_pro)
    x.sort_values('tradeDate',inplace=True)
    x['chgPct'] = x.closePrice.pct_change()
    x.dropna(inplace=True)
    x.tradeDate = x.tradeDate.astype(str)
    x.set_index('tradeDate',inplace=True)
    x = x[~x.index.duplicated()]
    return x




def get_iso_single(data):
    sub_x,sub_ticker= data
    try:
        _,y2 = get_signal(sub_x,sub_ticker)
    except:
        y2 = sub_ticker
    print('Complete %s' % sub_ticker)
    return y2


def get_iso_index_tickers(index_code):
    fn = 's84p1_csi%s.pkl' % index_code
    if not os.path.exists(fn):
        iso_info,_,_ = get_iso_index_info()
        data = pd.read_sql('''select index_id,ticker,tradeDate,openPrice,closePrice,
                           highPrice as highestPrice, lowPrice as lowestPrice from main_index_s68   
                           where index_id = "%s" and ticker !="%s" order by ticker, 
                           tradeDate''' % (index_code,iso_info[index_code]),eg_pro)
        data.tradeDate = data.tradeDate.astype(str)
        data.set_index('tradeDate',inplace=True)
        tickers = data.ticker.unique().tolist()
        if BX:
            p1 = []
            p2 = []
            for sub_ticker in tqdm(tickers,desc=index_code):
                sub_x = data[data.ticker==sub_ticker].copy()
                sub_x = sub_x[~sub_x.index.duplicated()]
                sub_x.sort_index(inplace=True)
                sub_x['chgPct'] = sub_x.closePrice.pct_change()
                sub_x.chgPct.fillna(0,inplace=True)
                p1.append(sub_x)
                p2.append(sub_ticker)
            pool = multiprocessing.Pool(num_core)
            Y = pool.map(get_iso_single,zip(p1,p2))
            pool.close()
            pool.join() 
        else:
            Y = []
            for sub_ticker in tqdm(tickers,desc=index_code):
                sub_x = data[data.ticker==sub_ticker].copy()
                sub_x = sub_x[~sub_x.index.duplicated()]
                sub_x.sort_index(inplace=True)
                sub_x['chgPct'] = sub_x.closePrice.pct_change()
                sub_x.chgPct.fillna(0,inplace=True)
                _,y2 = get_signal(sub_x,sub_ticker)
                Y.append(y2)
        #Y=pd.concat(Y)
        #Y.to_pickle(fn)
        save_pickle(fn,Y)
    
if __name__ == "__main__":
    ## 选取股票测试
    #get_csi_data()
    obj_t = time_use_tool()
    index_tdx,fee1,fee2 = get_iso_index_info()
    index_iso = list(index_tdx.keys())
    index_iso.reverse()
    #index_iso.remove("topix")
    #index_iso.remove("RTY")
    for sub_index in index_iso:
        get_iso_index_tickers(sub_index)
        obj_t.use(sub_index)
    
