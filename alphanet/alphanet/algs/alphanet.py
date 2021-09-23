import torch
from torch import nn, optim
from torch.nn import functional as F
import numpy as np
from multiprocessing import Pool


# %%
def get_cov_tensor(x):
    b, m, n = x.shape
    x_mean = x - torch.mean(x, keepdim=True, dim=-1)
    x_cov = torch.bmm(x_mean, x_mean.transpose(-2, -1)) / n
    return x_cov


def get_cov(x):
    m, n = x.shape
    x_mean = x - torch.mean(x, keepdim=True, dim=1)
    x_cov = x_mean @ x_mean.T / n
    return x_cov


# %%
class cov_layer(nn.Module):

    def __init__(self, size=10, col_n=9):
        super(cov_layer, self).__init__()
        self.size = size
        # self.mask = torch.triu(torch.ones(col_n, col_n), diagonal=1)
        self.register_buffer('mask', torch.triu(torch.ones(col_n, col_n), diagonal=1))

    def forward(self, X):
        batch, m, n = X.shape
        x_covs = []
        for i in range(n - self.size):
            x_sub = X[:, :, i: i + self.size]
            x_cov = get_cov_tensor(x_sub)
            x_cov = x_cov * self.mask
            x_cov = x_cov.reshape(batch, m * m)
            x_covs.append(x_cov[:, x_cov.sum(axis=0) != 0])
        return torch.stack(x_covs, dim=1)


class corr_layer(nn.Module):

    def __init__(self, size=10, col_n=9):
        super(corr_layer, self).__init__()
        self.size = size
        # self.mask = torch.triu(torch.ones(col_n, col_n), diagonal=1)
        self.register_buffer('mask', torch.triu(torch.ones(col_n, col_n), diagonal=1))
        self.register_buffer('eye', torch.eye(col_n))

    def forward(self, X):
        batch, m, n = X.shape
        x_cors = []
        for i in range(n - self.size):
            x_sub = X[:, :, i: i + self.size]
            x_cov = get_cov_tensor(x_sub)
            # get corr
            x_sigma = (x_cov * self.eye).sum(axis=-1, keepdim=True)
            x_sigma = torch.sqrt(torch.bmm(x_sigma, x_sigma.transpose(-2, -1)))
            # x_cor = x_cov/ x_sigma
            x_cor = (x_cov + 10e-6) / (x_sigma + 10e-6)  # make sure nozero
            # choose up trial
            x_cor = x_cor * self.mask
            x_cor = x_cor.reshape(batch, m * m)
            x_cors.append(x_cor[:, x_cor.sum(axis=0) != 0])

        return torch.stack(x_cors, dim=1)


class SingalValue_layer(nn.Module):

    def __init__(self, size=10):
        super(SingalValue_layer, self).__init__()
        self.size = size
        decay = torch.arange(1, self.size + 1, dtype=torch.float
                             ).reshape(1, 1, -1) / torch.arange(1, self.size + 1,
                                                                dtype=torch.float).sum()
        self.register_buffer('decay', decay)

    def forward(self, X):
        b, m, n = X.shape
        x_stds, x_zss, x_rets, x_decays, x_mins, x_maxs, x_sums = [], [], [], [], [], [], []
        for i in range(n - self.size):
            x_sub = X[:, :, i: i + self.size]
            x_std = x_sub.std(axis=-1)
            x_mean = x_sub.mean(axis=-1)
            x_zs = x_mean / (x_std + 10e-5) # make sure nozero
            x_ret = x_sub[:, -1, :] / (x_sub[:, 0, :] + 10e-4) - 1 # make sure nozero
            decay = torch.arange(1, self.size + 1, dtype=torch.float
                                 ).reshape(1, 1, -1) / torch.arange(1, self.size + 1,
                                                                    dtype=torch.float).sum()
            x_decay = (x_sub * self.decay).sum(axis=-1)
            x_min = x_sub.min(axis=-1)[0]
            x_max = x_sub.max(axis=-1)[0]
            x_sum = x_sub.sum(axis=-1)
            # append data
            x_stds.append(x_std)
            x_zss.append(x_zs)
            x_rets.append(x_ret)
            x_decays.append(x_decay)
            x_mins.append(x_min)
            x_maxs.append(x_max)
            x_sums.append(x_sum)
        return torch.stack(x_stds, dim=1), torch.stack(x_zss, dim=1), torch.stack(x_rets, dim=1), \
               torch.stack(x_decays, dim=1), \
               torch.stack(x_mins, dim=1), torch.stack(x_maxs, dim=1), torch.stack(x_sums, dim=1),


class Alpha_Net_feat(nn.Module):

    def __init__(self, input_size=(9, 30), size=10, n_cols=9):
        m, n = input_size
        super(Alpha_Net_feat, self).__init__()
        self.size = size
        self.n_cols = n_cols
        self.cov_layer = cov_layer(self.size, self.n_cols)
        self.corr_layer = corr_layer(self.size, self.n_cols)
        self.vals_layer = SingalValue_layer(self.size)

        for i in range(7):
            self.__setattr__('bn_%s' % i, nn.BatchNorm1d(n - self.size))
            self.__setattr__('bn_mean_%s' % i, nn.BatchNorm1d(n - self.size))
            self.__setattr__('bn_max_%s' % i, nn.BatchNorm1d(n - self.size))
            self.__setattr__('bn_min_%s' % i, nn.BatchNorm1d(n - self.size))

        self.bn_cov = nn.BatchNorm1d(n - self.size)
        self.bn_corr = nn.BatchNorm1d(n - self.size)
        self.bn_mean_cov = nn.BatchNorm1d(n - self.size)
        self.bn_mean_corr = nn.BatchNorm1d(n - self.size)
        self.bn_max_cov = nn.BatchNorm1d(n - self.size)
        self.bn_max_corr = nn.BatchNorm1d(n - self.size)
        self.bn_min_cov = nn.BatchNorm1d(n - self.size)
        self.bn_min_corr = nn.BatchNorm1d(n - self.size)

    def forward(self, X):
        x_cov = self.bn_cov(self.cov_layer(X))
        x_corr = self.bn_corr(self.corr_layer(X))
        x_vals = self.vals_layer(X)

        bn_xvals = []
        for i, val in enumerate(x_vals):
            bn_xvals.append(self.__getattr__('bn_%s' % i)(val))

        # pooling mean + bn

        x_cov_pmean = self.bn_mean_cov(F.avg_pool1d(x_cov, kernel_size=3))
        x_corr_pmean = self.bn_mean_corr(F.avg_pool1d(x_corr, kernel_size=3))
        x_vals_pmean = []
        for i, val in enumerate(bn_xvals):
            x_vals_pmean.append(self.__getattr__('bn_mean_%s' % i)(F.avg_pool1d(val, kernel_size=3)))

        # pooling max + bn
        x_cov_pmax = self.bn_max_cov(F.max_pool1d(x_cov, kernel_size=3))
        x_corr_pmax = self.bn_max_corr(F.max_pool1d(x_corr, kernel_size=3))
        x_vals_pmax = []
        for i, val in enumerate(bn_xvals):
            x_vals_pmax.append(self.__getattr__('bn_max_%s' % i)(F.max_pool1d(val, kernel_size=3)))

        # pooling min + bn
        x_cov_pmin = self.bn_min_cov(-F.max_pool1d(-x_cov, kernel_size=3))
        x_corr_pmin = self.bn_min_corr(-F.max_pool1d(-x_corr, kernel_size=3))
        x_vals_pmin = []
        for i, val in enumerate(bn_xvals):
            x_vals_pmin.append(self.__getattr__('bn_min_%s' % i)(-F.max_pool1d(-val, kernel_size=3)))

        x_feat = torch.cat([x_cov, x_corr] + bn_xvals, dim=-1)
        x_feat_mean = torch.cat([x_cov_pmean, x_corr_pmean] + x_vals_pmean, dim=-1)
        x_feat_max = torch.cat([x_cov_pmax, x_corr_pmax] + x_vals_pmax, dim=-1)
        x_feat_min = torch.cat([x_cov_pmin, x_corr_pmin] + x_vals_pmin, dim=-1)

        return x_feat, x_feat_mean, x_feat_max, x_feat_min


class Alpha_Net_out(nn.Module):

    def __init__(self, input_bn_size, input_mean_size, input_max_size, input_min_size,
                 fc_size=30, out_size=1, drop_rate=0.5):
        super(Alpha_Net_out, self).__init__()
        b1, m1, n1 = input_bn_size
        b2, m2, n2 = input_mean_size
        b3, m3, n3 = input_max_size
        b4, m4, n4 = input_min_size
        self.batch = b1
        self.drop_rate = drop_rate

        self.fc_len = m1 * n1 + m2 * n2 + m3 * n3 + m4 * n4
        self.fc = nn.Linear(self.fc_len, fc_size)
        self.out = nn.Linear(fc_size, out_size)

    def forward(self, X_bn, X_mean, X_max, X_min):
        X = torch.cat([X_bn, X_mean, X_max, X_min], dim=-1)
        X = X.reshape(-1, self.fc_len)
        fc = F.relu(self.fc(X))
        fc = F.dropout(fc, self.drop_rate)
        out = self.out(fc)
        return out


class Alpha_Net(nn.Module):

    def __init__(self, input_size=(9, 30), size=10, n_cols=9,
                 input_bn_size=(1, 20, 136), input_val_size=(1, 20, 45)):
        super(Alpha_Net, self).__init__()
        self.feat_model = Alpha_Net_feat(input_size, size, n_cols)

        self.input_bn_size = input_bn_size
        self.input_val_size = input_val_size

        # self.input_bn_size = (batch_size, 20, 135)
        # self.input_val_size = (batch_size, 20, 45)
        self.out_model = Alpha_Net_out(self.input_bn_size,
                                       self.input_val_size,
                                       self.input_val_size,
                                       self.input_val_size)

    def forward(self, X):
        a, b, c, d = self.feat_model(X)
        y_pred = self.out_model(a, b, c, d)

        return y_pred


# %%
if __name__ == '__main__':
    batch = 345
    x = torch.rand(size=(batch, 9, 30), dtype=torch.float)

    model = Alpha_Net()
    y_pred = model(x)
    # model_feat = Alpha_Net_feat()
    # a, b, c, d = model_feat(x)
    # model_out = Alpha_Net_out(a.shape, b.shape, c.shape, d.shape)
    # y_pred = model_out(a, b, c, d)

    print('test is pass')
