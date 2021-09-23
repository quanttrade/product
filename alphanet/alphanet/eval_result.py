import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# %%
basic_dir = './processing_data/res_data'
ms = os.listdir(basic_dir)
ms = [i for i in ms if '.csv' in i]
ms.sort()

# %%
df = pd.concat(pd.read_csv(os.path.join(basic_dir, i), index_col=0, dtype={'symbol': str}) for i in ms)
df['ret'] = df['next_10'] / df['close_0'] - 1
df.sort_index(inplace= True)

# %%
def get_group_df(sub_df, n_group=5):
    ret_dict = {}
    df = sub_df.copy()
    df.sort_values('pred', inplace=True)
    n = df.shape[0]
    r = int(n / n_group)
    ret_dict['mean'] = df['ret'].mean()
    for i in range(n_group):
        if i == n_group - 1:
            g_df = df.iloc[i * r:, :]
        else:
            g_df = df.iloc[i * r: (i + 1) * r]
        ret_dict[i] = g_df['ret'].mean()
    return ret_dict


# %%
ret_dict = {}
date_list = df.index.unique()
for date in date_list:
    sub_df = df.loc[[date]]
    group_ret = get_group_df(sub_df)
    ret_dict[date] = group_ret
    
# %%
def get_shape_ratio(ret_ser):
    return_mean = ret_ser.mean()
    return_std = ret_ser.std()
    return return_mean / return_std * np.sqrt(252)

def get_year_ret(ret_ser, l = 1):
    cum = (ret_ser + 1).prod()
    n_days = len(ret_ser) * l
    return cum ** (252 / n_days) - 1

# %% 此处假设了：共分成10分资产，每份资产操作一天。每十天对其中一份资产换仓操作
res_df = pd.DataFrame(ret_dict).T
ret = (res_df.iloc[:, -1] - res_df.iloc[:, 1]) / 10
( ret + 1).cumprod().plot(figsize=(16, 8))
plt.title('charge return')
plt.show()
print('sharpe ratio: %.4f , year return: %.4f'% (get_shape_ratio(ret), get_year_ret(ret)))
# %%
( res_df / 10 + 1).cumprod().plot(figsize = (16,8))
plt.title('group return')
plt.show()

# %% 第二种回测
beg = 0
res_10 = res_df.iloc[0::10, ]
ret = res_10.iloc[:, -1] - res_10.iloc[:, 1]
(ret + 1).cumprod().plot(figsize = (16,8))
plt.show()
print('sharpe ratio: %.4f , year return: %.4f'% (get_shape_ratio(ret), get_year_ret(ret, l= 10)))

( res_10 + 1).cumprod().plot(figsize = (16,8))
plt.title('group return')
plt.show()