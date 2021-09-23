import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from tqdm import tqdm
import shutil
with open('./data/date_index.npy', 'rb') as f:
    date_ind = np.load(f, allow_pickle=True)
date_ind.sort()
date_ind = date_ind[date_ind > '2004-01-01']


# %%
def reindex_data(sub_df, date_ind):
    begin_ind = sub_df.index[0]
    ind = date_ind[np.where(date_ind >= begin_ind)[0][0]:]
    new_df = pd.DataFrame(index=ind)
    for col in sub_df.columns:
        new_df[col] = sub_df[col]
    return new_df


def get_feat_data(sub_df):
    # get return
    sub_df['return'] = sub_df['closePrice'].diff() / sub_df['closePrice'].shift(1)
    sub_df['vwap'] = sub_df['turnoverValue'] / sub_df['turnoverVol']
    sub_df['turn'] = sub_df['turnoverValue'] / sub_df['marketValue']
    sub_df['free_turn'] = sub_df['turnoverValue'] / sub_df['negMarketValue']
    sub_df['next_5'] = sub_df['closePrice'].shift(-5)
    sub_df['next_10'] = sub_df['closePrice'].shift(-10)
    new_df = sub_df[['symbol', 'next_5', 'next_10']]

    for i in range(30):
        new_df['open_%s' % (30 - 1 - i)] = sub_df['openPrice'].shift(30 - 1 - i)

    for i in range(30):
        new_df['high_%s' % (30 - 1 - i)] = sub_df['highestPrice'].shift(30 - 1 - i)

    for i in range(30):
        new_df['low_%s' % (30 - 1 - i)] = sub_df['lowestPrice'].shift(30 - 1 - i)

    for i in range(30):
        new_df['close_%s' % (30 - 1 - i)] = sub_df['closePrice'].shift(30 - 1 - i)

    for i in range(30):
        new_df['return_%s' % (30 - 1 - i)] = sub_df['return'].shift(30 - 1 - i)

    for i in range(30):
        new_df['vwap_%s' % (30 - 1 - i)] = sub_df['vwap'].shift(30 - 1 - i)

    for i in range(30):
        new_df['vol_%s' % (30 - 1 - i)] = sub_df['turnoverVol'].shift(30 - 1 - i)

    for i in range(30):
        new_df['turn_%s' % (30 - 1 - i)] = sub_df['turn'].shift(30 - 1 - i)

    for i in range(30):
        new_df['freeturn_%s' % (30 - 1 - i)] = sub_df['free_turn'].shift(30 - 1 - i)

    return new_df


# %%
stock_list = os.listdir('./stk_data')
for name in tqdm(stock_list):
    sub_df = pd.read_csv('./stk_data/%s' % name, index_col='tradeDate', dtype={'symbol': str})
    if sub_df.index[-1] > '2004-01-01' and sub_df.shape[0] > 100:
        sub_df = reindex_data(sub_df, date_ind)
        sub_df = sub_df[sub_df['highestPrice'] != sub_df['lowestPrice']] # 去掉涨跌停
        new_df = get_feat_data(sub_df)
        # if new_df.index[0] > '2010-01-15':  # 简单标准判断在2010后上市股票
        #     new_df = new_df.iloc[60:]  # 简单判断次新股

        if not os.path.exists('./processing_data/stk_feat'): os.makedirs('./processing_data/stk_feat')
        new_df.to_csv('./processing_data/stk_feat/%s' % name)

# %%
basic_dir = './processing_data/stk_feat'
stock_list = os.listdir(basic_dir)
stock_list.sort()

def read_feat_df(name):
    basic_dir = './processing_data/stk_feat'
    path = os.path.join(basic_dir, name)
    df = pd.read_csv(path, index_col=0, dtype={'symbol': str})
    return df.dropna()

def get_save_split_date_data(dfs, part = 1, save_dir = './processing_data/date_feat'):
    df = dfs.copy()
    date_ind = df.index.unique()
    for date in date_ind:
        sub_df = df.loc[[date]]
        sub_df.to_csv(os.path.join(save_dir, date +'_part_%s.csv'%part))

    
# %%
batch = 300
n_round = int(len(stock_list) / batch) + 1
save_dir = './processing_data/date_feat'
if not os.path.exists(save_dir):os.makedirs(save_dir)

# %%
for i in tqdm(range(n_round)):
    dfs = [read_feat_df(name) for name in stock_list[batch * i: batch * (i + 1)]]
    dfs = pd.concat(dfs)
    get_save_split_date_data(dfs, part = i)

# %%
date_files = os.listdir(save_dir)
date_set = set([i[:10] for i in date_files])
for date in tqdm(date_set):
    date_part = [os.path.join(save_dir, i) for i in date_files if date in i]
    dfs = [pd.read_csv(date_, index_col= 0, dtype={'symbol': str}) for date_ in date_part]
    dfs = pd.concat(dfs)
    if not os.path.exists('./processing_data/date_feat_sig'): os.makedirs('./processing_data/date_feat_sig')
    dfs.to_csv('./processing_data/date_feat_sig/%s.csv'%date)
    # for path in date_part:
    #     os.remove(path)
