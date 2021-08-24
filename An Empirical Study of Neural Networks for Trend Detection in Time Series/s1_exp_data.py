import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# %%
df = pd.read_csv('./data/hs_300.csv', index_col=0)
df.index = df.pop('tradeDate')

# %%
# df['CHGPct'].hist(bins=50, alpha=0.3)

# %% 用以估计 均值与方差
s = df['CHGPct'].values
mu, sigma = s.mean(), s.std()
lap = np.abs((s - s.mean())).mean()

simulate = np.random.normal(mu, sigma, size=(s.shape[0],))
simulate_lap = np.random.laplace(mu, lap, size=(s.shape[0],))
plt.hist(s, bins=50, alpha=0.3, label='hs_300')
plt.hist(simulate, bins=50, alpha=0.3, label='simulate normal dis')
# plt.hist(simulate_lap, bins=50, alpha=0.3, label='simulate lap dis')
plt.legend()
plt.show()

# %% 用AR1 估计 均值与方差
import statsmodels.api as sm

s = df['closeIndex'].values
step = 500
n = s.shape[0] // step
for i in range(n):
    model = sm.OLS(s[1 + i * step: (i + 1) * step + 1], sm.add_constant(s[i * step: (i + 1) * step]))
    result = model.fit()

    a, b = result.params
    c = result.resid.std()

    theta = - np.log(b)
    mu = a / (1 - b)
    sigma = c * np.sqrt(2 * theta / (1 - b ** 2))

    print(theta, mu, sigma, s[1 + i * step])
