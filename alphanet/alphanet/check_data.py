import pandas as pd
import os
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from algs.alphanet import *
from units import *
from tqdm import tqdm
torch.manual_seed(2020)
# %%

basic_dir = './processing_data/date_feat_sig'
ms = os.listdir(basic_dir)
ms = [os.path.join(basic_dir, i) for i in ms if '.csv' in i]
ms.sort()

data = alpha_data(ms[0:250])
data_load = DataLoader(data, batch_size= 256)
for i in tqdm(data_load):
    x, y = i
    model_feat = Alpha_Net_feat()
    a, b, c, d = model_feat(x)
    model_out = Alpha_Net_out(a.shape, b.shape, c.shape, d.shape)
    y_pred = model_out(a, b, c, d)


# %%
cov_model = cov_layer()
corr_model = corr_layer()
bn_layer = nn.BatchNorm1d(20)
sin_layer = SingalValue_layer()
x_cov = cov_model(x)
x_corr = corr_model(x)
x_sigs = sin_layer(x)
# %%
bn_cov = bn_layer(x_cov)
bn_corr = bn_layer(x_corr)
for x_sig in x_sigs: print(x_sig.max())

# %%
x_sub = x[:, :, 1:11]