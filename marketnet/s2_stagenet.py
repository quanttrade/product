import pandas as pd
import numpy as np
from glob import glob
import torch
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# %%
data_list = glob('L:\\Dropbox\\Dropbox\\project folder from my asua computer\\Project\\Adaboost\\month_data\\*.csv')
data_list.sort()

# %% get chs ticker
df = pd.read_csv(data_list[0], index_col=0)
df_, df_info = df.iloc[:, 3:-3], \
               df.loc[:, ['ticker', 'tradeDate', 'real_return', 'market_value']]

infos = []
for path in data_list:
    df = pd.read_csv(path, index_col=0)
    df_, df_info = df.iloc[:, 3:-3], \
                   df.loc[:, ['ticker', 'tradeDate', 'real_return', 'market_value']]
    infos.append(df_info)

# %%
df_info = pd.concat(infos)
chs_index = df_info['ticker'].value_counts().sort_values(ascending=False).iloc[:500].index


# %%
def read_month_data(path):
    df = pd.read_csv(path, index_col=0).set_index('ticker')
    df = df.loc[chs_index, :]
    df_ = df.iloc[:, 3: 243]
    return (torch.tensor(df_.values, dtype=torch.float32),
            df.loc[:, ['tradeDate', 'real_return', 'market_value']])


# %%
xs, infos = [], []
for path in data_list:
    img_x, df_info = read_month_data(path)
    xs.append(img_x)
    infos.append(df_info)
xs = torch.stack(xs)

# %%
from algs.marketsegnet import *

model = autoencoder(in_channels=500)
opt = torch.optim.Adam(model.parameters())
loss_func = nn.MSELoss()

# %%
train_losses, val_losses = [], []
n_round = 1000
for i in range(n_round):
    loss = loss_func(xs[:100], model(xs[:100]))
    opt.zero_grad()
    loss.backward()
    opt.step()
    with torch.no_grad():
        val_loss = loss_func(xs[100:], model(xs[100:]))
    print('autoencoder train loss: %.4f | val loss: %.4f' %(loss.item(), val_loss.item()))
    train_losses.append(loss.item())
    val_losses.append(val_loss.item())

# %%

plt.plot(train_losses, label='training')
plt.plot(val_losses, label='validation')
plt.legend()
plt.show()
