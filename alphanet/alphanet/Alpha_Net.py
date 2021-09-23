import torch
from torch import optim, nn
import numpy as np
from tqdm import tqdm
import os
from torch.utils.data import DataLoader

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.random.manual_seed(2020)

from units import *
from algs.alphanet import *

# %%
basic_dir = './processing_data/date_feat_sig'


def get_split_train_test_path(begin_date, train_wondows=1500, test_window=120):
    ms = os.listdir(basic_dir)
    ms = [i for i in ms if '.csv' in i]
    ms.sort()

    begin_file = begin_date + '.csv'
    ind = ms.index(begin_file)
    train_paths = [os.path.join(basic_dir, path) for path in ms[ind: ind + train_wondows]]
    test_paths = [os.path.join(basic_dir, path) for path in ms[ind + train_window:
                                                               ind + train_wondows + test_window]]
    return train_paths, test_paths


def get_train_test_tensor(train_paths, test_paths):
    n = len(train_paths)
    train_paths, valid_paths = train_paths[: int(n / 2)], train_paths[int(n / 2):]
    train_data = alpha_data(train_paths, type='next_10')
    test_data = alpha_data(test_paths, type='next_10')
    val_data = alpha_data(valid_paths, type='next_10')
    return train_data, val_data, test_data, test_data.data


def train(data):
    data_loader = DataLoader(data, batch_size=256, shuffle=True)
    train_loss = 0
    flag = 0

    for (x, y) in tqdm(data_loader):
        opt.zero_grad()
        x = x.to(device)
        y = y.to(device)
        y_pred = model(x)
        loss = criterion(y_pred, y)
        loss.backward()
        opt.step()
        train_loss += loss.item()
        # print(loss.item())
        flag += 1
    return train_loss / flag


def test(data):
    test_loss = 0
    flag = 0
    batch_size = 512
    data_loader = DataLoader(data, batch_size=batch_size)
    y_pred_np = np.zeros(shape=[len(data), 1])
    for (x, y) in tqdm(data_loader):
        x = x.to(device)
        y = y.to(device)
        # model computer
        with torch.no_grad():
            y_pred = model(x)
            loss = criterion(y_pred, y)
            test_loss += loss.item()
            if device.type == 'cpu':
                y_pred_np[batch_size * flag: batch_size * (flag + 1)] = y_pred.numpy()
            else:
                y_pred_np[batch_size * flag: batch_size * (flag + 1)] = y_pred.to('cpu').numpy()
            flag += 1
    return test_loss / flag, y_pred_np


# %%
ms = os.listdir(basic_dir)
ms.sort()
n = len(ms)
train_window, test_window = 1500, 150
model = Alpha_Net()
model = model.to(device)
criterion = nn.MSELoss()
opt = optim.RMSprop(model.parameters(), lr=0.0001)
epoch = 100

# %%
for i in range(0, n - train_window - test_window, test_window):
    begin_date = ms[i].split('.')[0]
    train_paths, test_paths = get_split_train_test_path(begin_date, train_wondows=train_window,
                                                        test_window=test_window)
    train_data, val_data, test_data, test_df = get_train_test_tensor(train_paths, test_paths)
    earlystop = EarlyStopping(patience=10, verbose=False, checkpoint='./processing_data/pair_wise.pt')
    print('training model')
    for r in range(epoch):
        train_loss = train(train_data)
        test_loss, y_pred = test(val_data)
        earlystop(test_loss, model)
        print(f'\tLoss: {train_loss:.4f}(train)\t | \tLoss: {test_loss:.4f}(valid)\t')
        if earlystop.early_stop:
            print('the model has done')
            break

    # check save model to fine-tune
    model.load_state_dict(torch.load('./processing_data/pair_wise.pt'))
    score, y_pred = test(test_data)
    test_df['pred'] = y_pred

    # init model for next train dont fine-tune
    # model = Alpha_Net()
    # model = model.to(device)

    if not os.path.exists('./processing_data/res_data'): os.makedirs('./processing_data/res_data')
    test_df[['symbol', 'close_0', 'next_10', 'next_5', 'pred']].to_csv('./processing_data/res_data/res_%s.csv' % i)
