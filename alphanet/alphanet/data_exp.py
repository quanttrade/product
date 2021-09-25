import pandas as pd
import numpy as np
import os
from tqdm import tqdm

if not os.path.exists('./stk_data'): os.makedirs('./stk_data')
# %%
df = pd.read_csv('./data/stock.csv', index_col=0, dtype={'symbol': str})
tickers = df['symbol'].unique()

with open('./data/date_index.npy', 'wb') as f:
    np.save(f, df['tradeDate'].unique())

# %%
def save_tickers(name):
    sub_df = df[df['symbol'] == name]
    sub_df.sort_values('tradeDate')
    sub_df.to_csv('./stk_data/%s.csv' % name, index=False)


for name in tqdm(tickers): save_tickers(name)
