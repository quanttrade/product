import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from algs.alphanet import *
from tqdm import tqdm
# %%
class alpha_data(Dataset):

    def __init__(self, paths, type = 'next_5'):
        self.data = [pd.read_csv(path, index_col= 0).iloc[:, :273] for path in paths]
        self.data = pd.concat(self.data, axis= 0)
        self.y = (self.data[type] / self.data['close_0'] - 1).values
        self.x = self.data.iloc[:, 3:273].values


    def __getitem__(self, key):
        y = torch.FloatTensor([self.y[key]])
        x = self.x[key]
        x_mat = torch.FloatTensor(x.reshape(9, -1))
        return x_mat, y

    def __len__(self):
        return len(self.y)
# early stop
class EarlyStopping:
    """Early stops the training if validation loss doesn't improve after a given patience."""
    def __init__(self, patience=7, verbose=False, delta=0, checkpoint = 'checkpoint.pt'):
        """
        Args:
            patience (int): How long to wait after last time validation loss improved.
                            Default: 7
            verbose (bool): If True, prints a message for each validation loss improvement.
                            Default: False
            delta (float): Minimum change in the monitored quantity to qualify as an improvement.
                            Default: 0
        """
        self.patience = patience
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.Inf
        self.delta = delta
        self.checkpoint = checkpoint

    def __call__(self, val_loss, model):

        score = -val_loss

        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
        elif score < self.best_score + self.delta:
            self.counter += 1
            print(f'EarlyStopping counter: {self.counter} out of {self.patience}')
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
            self.counter = 0

    def save_checkpoint(self, val_loss, model):
        '''Saves model when validation loss decrease.'''
        if self.verbose:
            print(f'Validation loss decreased ({self.val_loss_min:.6f} --> {val_loss:.6f}).  Saving model ...')
        torch.save(model.state_dict(), self.checkpoint)
        self.val_loss_min = val_loss

# %%
if __name__ == '__main__':

    # data = alpha_data()
    import os
    basic_dir = './processing_data/date_feat'
    ms = os.listdir(basic_dir)
    ms = [os.path.join(basic_dir, i) for i in ms if '.csv' in i]
    ms.sort()

    data = alpha_data(ms[0:500])
    data_load = DataLoader(data, batch_size= 256)
    for i in tqdm(data_load):
        x, y = i
        # model = Alpha_Net()
        # y_pred = model(x)
        model_feat = Alpha_Net_feat()
        a, b, c, d = model_feat(x)
        model_out = Alpha_Net_out(a.shape, b.shape, c.shape, d.shape)
        y_pred = model_out(a, b, c, d)


# %%
