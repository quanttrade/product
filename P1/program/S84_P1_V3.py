# -*- coding: utf-8 -*-
"""
Created on Sun Apr 26 22:18:24 2020
可以计算成分股
可以并行
使用后复权数据计算
数据有升级
1)我们之前是用的每天技术分析的信号，做出的结果一般
2）我想用s78周度的数据加上双聚类的方法试试是不是可以提高效果
3）基本的思想使用双聚类的方法用在因子上面

这样只能使用CSI300的数据来计算
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
from yq_toolsS45 import yq_MktStockFactorsOneDayProGet_seri
from yq_toolsS45 import get_symbol_A


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

def get_signal(df,x,ticker):
    if len(df)>1500:
        df_factor = pd.DataFrame(index= df.index)
        # sma
        for n in [10]:#[10, 20, 30, 40]:
            df_factor['sma_' + str(n)] = mean_index(df['closePrice'], n= n)
        #df_factor = pd.concat([df_factor,x],axis=1).sort_index()  
        df_factor = df_factor.merge(x,how='left',left_index=True,right_index=True)
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
    
    x = yq_MktStockFactorsOneDayProGet_seri(ticker,'2009-01-01','2099-01-01','*')
    x.tradeDate = x.tradeDate.astype(str)
    x.set_index('tradeDate',inplace=True)
    x = x[x.columns.tolist()[2:]]
    #nan过多的全部删除
    n1 = x.shape[0]
    n2 = x.isna().sum()
    n2 = n2[n2<n1*0.05] #nan必须小于0.05
    x = x[n2.index.tolist()]
    x.fillna(method='ffill',inplace=True)
    x.dropna(inplace=True)
    #不是连续的变量需要去掉
    c = x.columns.tolist()
    c1 = []
    for sub_c in c:
        v=x[sub_c].unique()
        if len(v)>40:
            c1.append(sub_c)
    x = x[c1]
    
    df = get_MktEqudAdjAfGet_update(ticker,'2009-01-01','2099-01-01','*')
    df.tradeDate = df.tradeDate.astype(str)
    df.set_index('tradeDate',inplace=True)
    df.sort_index(inplace=True)
    df['chgPct'] = df.closePrice.pct_change()
    _,y2 = get_signal(df.copy(),x,ticker)
    print('S %s' % ticker)
    return y2


def get_csi_data(index = '000300'):
    fn = 's84p1_csi%s_V2.pkl' % index
    if not os.path.exists(fn):
        if len(index)==6:
            tickers,_ = get_IdxConsGet(index,'2010-01-01')
        else:
            tickers = get_symbol_A()
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


if __name__ == "__main__":
    ## 选取股票测试
    for index in ['000300','000905','A']:
        get_csi_data(index)
    
    
