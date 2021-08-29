import pandas as pd
import numpy as np
from glob import glob
import torch
from torch.utils.data import Dataset, DataLoader

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
    df_ = df.iloc[:, 3:-3]
    return (torch.tensor(df_.values[:, :-1], dtype=torch.float32),
            torch.tensor(df_.values[:, -1], dtype=torch.float32),
            df.loc[:, ['tradeDate', 'real_return', 'market_value']])


# %%
xs, ys, infos = [], [], []
for path in data_list:
    img_x, y, df_info = read_month_data(path)
    xs.append(img_x)
    ys.append(y)
    infos.append(df_info)

xs = torch.stack(xs)


# %%
class market_data_set(Dataset):

    def __init__(self, xs, ys, time_step=10):
        self.xs = xs
        self.ys = ys
        self.time_step = time_step
        self.max_item = (xs.shape[0] - time_step) * xs.shape[1]

        self.t, self.m = time_step, xs.shape[1]

    def __getitem__(self, ind):
        date_idx = ind // self.m
        stock_idx = ind % self.m
        x_cube = xs[date_idx: date_idx + self.t, :, :]
        x_m = x_cube[:, stock_idx, :]
        s_m = torch.tensor([stock_idx + 1], dtype=torch.long)
        y_m = torch.tensor([self.ys[date_idx + self.t - 1][stock_idx]], dtype=torch.float32)
        return x_cube, x_m, s_m, y_m

    def __len__(self):
        return self.max_item


# %%
time_step = 10
begin_idx, val_idx, test_idx = 70, 80, 120
train_data, val_data, test_data = market_data_set(xs[:begin_idx], ys[:begin_idx], time_step), \
                                  market_data_set(xs[begin_idx - time_step: val_idx],
                                                  ys[begin_idx - time_step: val_idx], time_step), \
                                  market_data_set(xs[val_idx - time_step: test_idx],
                                                  ys[val_idx - time_step: test_idx], time_step)

# %%
from algs.ma_rnn import *
from tqdm import tqdm
import matplotlib.pyplot as plt

torch.random.manual_seed(2020)
model = ma_rnn(t=10, n=243, m=500, rnn_size=25)
model.to(device)
opt = torch.optim.Adam(model.parameters())
loss_func = nn.MSELoss()
loss_func.to(device)


# %%
def train(train_data, batch_size=64):
    data = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    loss_, flag = 0, 0
    for i in tqdm(data):
        x_cube, x_m, s_m, y_m = i
        x_cube, x_m, s_m, y_m = x_cube.transpose(1, 2).to(device), x_m.to(device), s_m.to(device), y_m.to(device)
        y_pred = model(x_m, x_cube, s_m)
        loss = loss_func(y_m, y_pred)

        # add l2
        # for p in model.conv_layer.parameters():
        #     loss += 0.001 * (p ** 2).sum()

        opt.zero_grad()
        loss.backward()
        opt.step()
        loss_ += loss.item()
        flag += 1
    loss_ = loss_ / flag
    return loss_


def test(test_data, batch_size=256):
    data = DataLoader(test_data, batch_size=batch_size, shuffle=False)
    loss_, flag = 0, 0
    for i in tqdm(data):
        x_cube, x_m, s_m, y_m = i
        x_cube, x_m, s_m, y_m = x_cube.transpose(1, 2).to(device), x_m.to(device), s_m.to(device), y_m.to(device)
        with torch.no_grad():
            y_pred = model(x_m, x_cube, s_m)
            loss = loss_func(y_m, y_pred)
            loss_ += loss.item()
            flag += 1
    loss_ = loss_ / flag
    return loss_


def predict(test_data, batch_size=256):
    data = DataLoader(test_data, batch_size=batch_size, shuffle=False)
    preds = []
    for i in tqdm(data):
        x_cube, x_m, s_m, y_m = i
        x_cube, x_m, s_m, y_m = x_cube.transpose(1, 2).to(device), x_m.to(device), s_m.to(device), y_m.to(device)
        with torch.no_grad():
            y_pred = model(x_m, x_cube, s_m)
            preds.append(y_pred)
    pred_y = torch.cat(preds, dim=0)
    return pred_y


def trans_to_numpy(pred):
    if pred.device.type == 'cuda':
        pred_ = pred.cpu().numpy()
    else:
        pred_ = pred.numpy()
    return pred_


# %%
n_round = 10
# 此处减1的原因在68行构建y进行了减1操作
# 68行减去1是因为，[:n]不会取到n，而是取到n-1.而我们数据的y是当前时间已经做好的标签。
df_info = pd.concat(infos[val_idx - 1: test_idx - 1])

y_ms = []
data = DataLoader(test_data, batch_size=256, shuffle=False)
for i in data:
    x_cube, x_m, s_m, y_m = i
    y_ms.append(y_m.numpy())

corr = np.corrcoef(df_info['real_return'].values, np.vstack(y_ms).ravel())
print(corr)
# %%


# %%
for i in range(n_round):
    train_loss = train(train_data)
    val_loss = test(val_data)
    pred = predict(test_data)
    pred_ = trans_to_numpy(pred)
    df_info['pred_%s' % i] = pred_
    print('train loss: %.4f | val loss: %.4f' % (train_loss, val_loss))


# %%
def get_charge_ret(x, n=100, col='pred'):
    index = x[col].sort_values(ascending=False).index
    top = x.loc[index[:n], 'real_return'].mean()
    bot = x.loc[index[-n:], 'real_return'].mean()
    return top - bot


rets = []
for i in range(n_round):
    test_ret = df_info.groupby('tradeDate').apply(lambda x: get_charge_ret(x, n=100, col='pred_%s' % i))
    rets.append((test_ret + 1).prod() - 1)
    (test_ret + 1).cumprod().plot(label='pred_%s' % i)
plt.legend()
plt.show()

# %%
plt.bar(np.arange(n_round), rets)
plt.show()

# %%
