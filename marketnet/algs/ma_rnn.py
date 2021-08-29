import torch
import torch.nn as nn
import numpy as np

# %%
# batch = 64
# t, m, n = 10, 100, 30
# x_cube = torch.randn(size=(batch, m, t, n))
# x_m = x_cube[:, 2, :, :]
# s_m = torch.ones(batch, dtype=torch.long).reshape(batch, 1)
# y = torch.randn(size=(m, 1))
#
# conv = nn.Conv2d(m, 192, 1, stride=1)
# lstm = nn.LSTM(n, 25, 1, batch_first=True)
# mb = nn.Embedding(100, t)
#
# # %%
# market_cube = conv(x_cube).sum(dim=-1)
# qms, hid = lstm(x_m)
# qm = qms[:, -1, :]
# sm = mb(s_m)
#
# # %% att
# zm = torch.tanh(sm)
# val = torch.bmm(zm, market_cube.transpose(-1, 1))
# att = torch.softmax(val, dim=0)
# pm = torch.bmm(att, market_cube).squeeze(1)
#

# %%
class ma_rnn(nn.Module):

    def __init__(self, filters=192, t=10, n=30, m=100, rnn_size=25):
        super().__init__()
        self.filters = filters
        self.t = t
        self.n = n
        self.m = m
        self.rnn_size = rnn_size

        self.activate = nn.ReLU()
        self.conv_layer = self.conv_model()
        self.lstm = self.rnn_model()
        self.sm = nn.Embedding(m + 1, t, padding_idx=0)

        self.out_layer = nn.Linear(t + rnn_size, 1)

    def conv_model(self):
        conv = nn.Conv2d(in_channels=self.m, out_channels=self.filters,
                         kernel_size=1, stride=1)
        return conv

    def rnn_model(self):
        lstm = nn.LSTM(self.n, self.rnn_size, 1, batch_first=True)
        return lstm

    def attention(self, query, value):
        zm = torch.tanh(query)
        val = torch.bmm(zm, value.transpose(-1, 1))
        att = torch.softmax(val, dim=0)
        pm = torch.bmm(att, value).squeeze(1)
        return pm

    def forward(self, x_m, x_cube, s_m):
        sm_vec = self.sm(s_m)
        market_cube = self.activate(self.conv_layer(x_cube).sum(dim=-1))
        qm_vecs, h = self.lstm(x_m)
        qm = qm_vecs[:, -1, :]
        pm = self.attention(sm_vec, market_cube)
        x_vec = torch.cat([pm, qm], dim=-1)
        out = self.out_layer(x_vec)
        return out

# %%
if __name__ == '__main__':
    batch = 64
    t, m, n = 10, 100, 30
    x_cube = torch.randn(size=(batch, m, t, n))
    x_m = x_cube[:, 2, :, :]
    s_m = torch.ones(batch, dtype=torch.long).reshape(batch, 1)
    y = torch.randn(size=(m, 1))
    model = ma_rnn()
    model(x_m, x_cube, s_m)

