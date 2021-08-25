import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from algs.fin_simulate import markov_switch, piece_noisy_line, piece_ou_process
import copy

# %%
mk = markov_switch(up_switch=[0.005, 0.005, 0.99],
                   down_switch=[0.99, 0.005, 0.005],
                   flat_switch=[0.005, 0.99, 0.005], noisy_level=0.01)
ou = piece_ou_process()


def generate_data(size=1000, random_state=2021):
    if random_state:
        np.random.seed(random_state)
    # markov process
    mk_stat, mk_ret = mk.simulate(size)

    lines = []
    for ind, i in enumerate(mk_stat):
        if ind == 0:
            last_state = i
        cur_state = i
        if cur_state != last_state:
            lines.append(ind)
        last_state = i

    # mean reverse process
    ou_lines = np.array([0] + lines + [size])
    sizes = np.diff(ou_lines)
    stats = [mk_stat[i - 1] for i in lines + [size]]

    ## simulate by state
    flag = 0
    ss = []
    for stat, size in zip(stats, sizes):
        if flag == 0:
            y0 = 2500
            flag = 1
            ss.append(np.array([y0]))

        if stat == 0:
            s = ou.flat_simulate(y0=y0, size=size)

        if stat == 1:
            fl = np.random.choice([0, 1])
            if fl == 0:
                s = ou.up_high_simulate(y0=y0, size=size)
            if fl == 1:
                s = ou.up_slow_simulate(y0=y0, size=size)

        if stat == -1:
            fl = np.random.choice([0, 1])
            if fl == 0:
                s = ou.down_high_simulate(y0=y0, size=size)
            if fl == 1:
                s = ou.down_slow_simulate(y0=y0, size=size)

        y0 = s[-1]
        ss.append(s)
    ou_index = np.hstack(ss)
    ou_ret = np.diff(ou_index) / ou_index[:-1]

    return mk_ret, ou_ret, mk_stat, sizes


# %%
# mk_x, ou_x, y = [], [], []
# for i in range(100):
#     mk_ret, ou_ret, mk_stat, bins = generate_data(random_state=i)
#     mk_x.append(mk_ret)
#     ou_x.append(ou_ret)
#     y.append(mk_stat + 1)
# mk_x = np.vstack(mk_x)
# ou_x = np.vstack(ou_x)
# y = np.vstack(y)


# %%
flag = True


def generate_train_data(size=32, random_state=1):
    global flag
    global mk_xs, ou_xs, ys
    np.random.seed(random_state)
    ind = np.random.randint(0, 100)
    if flag:
        mk_xs, ou_xs, ys = [], [], []
        for i in range(100 + size):
            mk_ret, ou_ret, mk_stat, bins = generate_data(random_state=i)
            mk_xs.append(mk_ret)
            ou_xs.append(ou_ret)
            ys.append(mk_stat + 1)
        mk_xs = np.vstack(mk_xs)
        ou_xs = np.vstack(ou_xs)
        ys = np.vstack(ys)
        flag = False
    return mk_xs[ind: ind + size], ou_xs[ind: ind + size], ys[ind: ind + size].ravel()


# %%
import torch.nn as nn
import torch

torch.random.manual_seed(2021)


# %%

class GRU_mdoel(nn.Module):

    def __init__(self, hidden_size=4):
        torch.random.manual_seed(2021)
        super(GRU_mdoel, self).__init__()
        self.layer_rnn = nn.GRU(1, hidden_size, 1, batch_first=True)
        self.linear = nn.Linear(hidden_size, 3)

    def forward(self, X):
        output, _ = self.layer_rnn(X)
        y_out = torch.softmax(self.linear(output), dim=-1).reshape(-1, 3)
        return y_out


# %%
model = GRU_mdoel(4)
loss_func = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
for i in model.parameters():
    print(i)

# %%
best_score = 100
for i in range(1000):
    mk_x, _, y = generate_train_data(size=8, random_state=i)
    mk_ten = torch.as_tensor(mk_x, dtype=torch.float32).unsqueeze(-1)
    y_ten = torch.as_tensor(y, dtype=torch.long)
    y_out = model(mk_ten)
    loss = loss_func(y_out, y_ten)
    # for i in model.parameters():
    #     loss += torch.norm(i) * 0.0001

    if loss.item() < best_score:
        best_score = loss.item()
        best_model = copy.deepcopy(model)

    if loss.item() < 0.9:
        optimizer.lr = 0.01
    if loss.item() < 0.8:
        optimizer.lr = 0.001

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    print(loss.item())

# %%
df = pd.read_csv('./data/hs_300.csv', index_col=0)
df.index = df.pop('tradeDate')
s = df['CHGPct'].values

hs_ten = torch.as_tensor(s.reshape(1, -1, 1), dtype=torch.float32)

hs_pred = model(hs_ten).detach().numpy()

# %%
signal_up, signal_down = hs_pred[:, -1] > 0.5, hs_pred[:, 0] > 0.9
plt.plot((s[1:] + 1).cumprod())
plt.plot((s[1:] * signal_up[:-1] - 0 * s[1:] * signal_down[:-1] + 1).cumprod())
plt.show()

# %%
model(hs_ten)[:100] == model(hs_ten[:, :100, :])[:100]
