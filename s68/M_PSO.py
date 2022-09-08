#UTF-8
#adair
#粒子群优化指数
#
import math
import numpy as np
import pandas as pd
import yfinance as yf
import seaborn as sns
import pingouin as pg
import matplotlib.pyplot as plt
import pyswarms as ps
from scipy.optimize import nnls
from datetime import date
from sklearn.metrics import mean_squared_error
from IPython.display import display, HTML
from sklearn.decomposition import NMF
from tslearn.metrics import dtw
from pyswarms.utils.search.grid_search import GridSearch
from pyswarms.utils.search.random_search import RandomSearch
from pyswarms.single.global_best import GlobalBestPSO
from pyswarms.utils.plotters import (plot_cost_history, plot_contour, plot_surface)
import os
import pickle
def save_pickle(fn,x):
    with open(fn, 'wb') as f:
        pickle.dump(x, f)
def read_pickle(fn):
    with open(fn, 'rb') as f:
        return pickle.load(f)

#from yq_toolsS45 import create_db
#from yq_toolsS45 import read_pickle
#eg_US = create_db('us_stock')

rank_day17 = "2017-05-12"
effect_day17 = "2017-06-26"
rank_day18 = "2018-05-11"
effect_day18_minus1 = "2018-06-24"
effect_day18 = "2018-06-25"
train_end = "2019-02-28"
val_start = "2019-03-01" # validate on a 1-month-before hold-out set
val_end = "2019-03-31"
test_start = "2019-04-01"
test_end = "2019-04-30"

top10of17_cap = {'AAPL':813.9,'GOOG':644.9,'MSFT':527.9,'AMZN':459.5,'FB':435.7,'BRK-B':402.9,'XOM':349.8,'JNJ':333.1,'JPM':308.8,'WFC':265}
top10of18_cap = {'AAPL':926.9,'AMZN':777.8,'GOOG':762.8,'MSFT':750.6,'FB':541.3,'BRK-B':491.8,'JPM':387.7,'XOM':344.1,'JNJ':341.3,'BAC':313.5}

components18_query = " ".join(list(top10of18_cap.keys()))
top10of17_shares = {}
top10of18_shares = {}

components17_query = " ".join(list(top10of17_cap.keys()))
components18_query = " ".join(list(top10of18_cap.keys()))

rank_day17_data = read_pickle('rank_day17_data.pkl')

rank_day18_data = read_pickle('rank_day18_data.pkl')

for component in top10of17_cap.keys():
    top10of17_shares[component] = math.ceil(top10of17_cap[component] * 10 ** 9 / rank_day17_data[component]['Close'])

for component in top10of18_cap.keys():
    top10of18_shares[component] = math.ceil(top10of18_cap[component] * 10 ** 9 / rank_day18_data[component]['Close'])

print("\nMarket Cap of Top 10 in 2017", top10of17_shares)
print("\nMarket Cap of Top 10 in 2018", top10of18_shares)


#for component in top10of18_cap.keys():
#    top10of18_shares[component] = math.ceil(top10of18_cap[component] * 10**9 / rank_day18_data[component]['Close'])
if os.path.exists('RUI.pkl'):
    RUI=read_pickle('RUI.pkl')
# Components
if os.path.exists('components17.pkl'):
    components17=read_pickle('components17.pkl')
if os.path.exists('components18.pkl'):
    components18=read_pickle('components18.pkl')

market_value17 = pd.DataFrame({'Market Value':np.zeros(len(components17.index))}, index=components17.index)
market_value18 = pd.DataFrame({'Market Value':np.zeros(len(components18.index))}, index=components18.index)
for component in top10of17_cap.keys():
    market_value17['Market Value'] =  market_value17['Market Value'] + components17[component] * top10of17_shares[component]
for component in top10of18_cap.keys():
    market_value18['Market Value'] = market_value18['Market Value'] + components18[component] * top10of18_shares[component]
benchmark = pd.concat([market_value17,market_value18])
benchmark['EMV/BMV'] = benchmark['Market Value'] / benchmark['Market Value'].shift(1)
# not rolling but just use price return = emv/bmv - 1 as the first IV only
current_IV = benchmark['Market Value'].pct_change()[1]
IVs = [np.nan, current_IV]
# updating and adding IVs for each subsequent day
for ratio in benchmark['EMV/BMV'][2:]:
    IVs.append(current_IV*ratio)
    current_IV *= ratio
benchmark['IV'] = IVs
benchmark['Return'] = benchmark['IV'].pct_change() * 100
benchmark['Daily Compounded Return'] = benchmark['Return'].cumsum()
benchmark['Benchmark Close'] = benchmark['Daily Compounded Return'] + 1341.03
benchmark.head()
benchmark.dropna(inplace=True)
benchmark_close = benchmark['Benchmark Close']
RUI['Actual Close'] = RUI['Close']
index_close = RUI[(benchmark.index[0] <= RUI.index) & (RUI.index <= benchmark.index[-1])]['Actual Close']
closes = pd.concat([index_close,benchmark_close], axis=1)
closes.plot()
# <--
# Train Val Test split
df = components18.copy()
df.dropna(inplace=True)
df['Actual Close'] = RUI['Actual Close']

train = df[df.index <= train_end]
val = df[(df.index >= val_start) & (df.index <= val_end)]
test = df[(df.index >= test_start) & (df.index <= test_end)]

trainX = train.drop('Actual Close', axis=1)
trainY = train['Actual Close']
valX = val.drop('Actual Close', axis=1)
valY = pd.DataFrame({'Actual Close':val['Actual Close']})
testX = test.drop('Actual Close', axis=1)
testY = pd.DataFrame({'Actual Close':test['Actual Close']})

def find_particle_loss(coeffs):
    trainX_returns = trainX.pct_change().dropna()
    trainY_returns = trainY.pct_change().dropna()
    benchmark_tracking_error = np.std(trainX.dot(coeffs) - trainY)
    return benchmark_tracking_error

def swarm(x):
    n_particles = x.shape[0]
    particle_loss = [find_particle_loss(x[i]) for i in range(n_particles)]
    return particle_loss


def evaluate(df, portfolio_col, is_test):
    df2 = pd.DataFrame({
        'Actual Daily Return': df['Actual Close'].pct_change()
    })

    index_hpr = (df['Actual Close'][-1] - df['Actual Close'][0]) / df['Actual Close'][0]

    if is_test:
        benchmark_hpr = (df['Benchmark Close'][-1] - df['Benchmark Close'][0]) / df['Benchmark Close'][0]
        benchmark_active_return = benchmark_hpr - index_hpr
        benchmark_return = df['Benchmark Close'].pct_change().dropna()
        actual_return = df['Actual Close'].pct_change().dropna()
        benchmark_tracking_error = np.std(benchmark_return - actual_return)
        info_ratio = benchmark_active_return / benchmark_tracking_error
        df2['Benchmark Daily Return'] = df['Benchmark Close'].pct_change()
        print("Benchmark")
        print("*" * 30)
        print("Active Return:", round(benchmark_active_return, 5))
        print("Tracking Error:", round(benchmark_tracking_error * 10000), " bps")
        print("Information Ratio:", round(info_ratio, 5))
        print("Price RMSE:", mean_squared_error(df['Benchmark Close'], df['Actual Close'], squared=False))
        df2['Benchmark Daily Return'] = df['Benchmark Close'].pct_change()
        df2.dropna(inplace=True)
        print("Returns RMSE:",
              mean_squared_error(df2['Benchmark Daily Return'], df2['Actual Daily Return'], squared=False))

    if portfolio_col:
        portfolio_hpr = (df[portfolio_col][-1] - df[portfolio_col][0]) / df[portfolio_col][0]
        portfolio_active_return = portfolio_hpr - index_hpr

        portfolio_return = df[portfolio_col].pct_change().dropna()
        actual_return = df['Actual Close'].pct_change().dropna()
        portfolio_tracking_error = np.std(portfolio_return - actual_return)
        info_ratio = portfolio_active_return / portfolio_tracking_error
        print("\nCurrent Portfolio")
        print("*" * 30)
        print("Active Return:", round(portfolio_active_return, 5))
        print("Tracking Error:", round(portfolio_tracking_error * 10000), " bps")
        print("Information Ratio:", round(info_ratio, 5))
        print("Price RMSE:", mean_squared_error(df[portfolio_col], df['Actual Close'], squared=False))
        colname = portfolio_col[:-6] + " Daily Return"
        df2[colname] = df[portfolio_col].pct_change()
        df2.dropna(inplace=True)
        print("Returns RMSE:", mean_squared_error(df2[colname], df2['Actual Daily Return'], squared=False))

    fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(16, 5))
    df.plot(ax=axs[0])
    df2.plot(ax=axs[1])
    fig.show()

options = {'c1': [1.5,2.5],
           'c2': [1,2],
           'w': [0.4,0.5]}

feature_count = len(trainX.columns)
min_bound = feature_count*[0]
max_bound = feature_count*[1]

g = GridSearch(GlobalBestPSO,
               objective_func=swarm,
               n_particles=100,
               dimensions=len(trainX.columns),
               options=options,
               bounds=(min_bound,max_bound),
               iters=100)
# Perform optimization, cost=lowest particle_loss among all iterations
best_cost, best_pos = g.search()

optimizer = GlobalBestPSO(n_particles=1000,
               dimensions=len(trainX.columns),
               options=best_pos,
               bounds=(min_bound,max_bound))
# Perform optimization, cost=lowest particle_loss among all iterations
cost, pos = optimizer.optimize(swarm,iters=100)

# <--
leverage_factor = sum(pos)
weights = pos/leverage_factor
weights = dict(zip(list(trainX.columns), list(weights)))

s1 = str(round(leverage_factor,5))+"("
for component,weight in weights.items():
    s1 += str(round(weight,5))+'*'+component+" + "
s1 = s1[:-3]+")"

print("\nPortfolio Allocation:")
allocation = pd.DataFrame({'Component':trainX.columns, 'Weight(%)':np.multiply(list(weights.values()),100)}).sort_values('Weight(%)',ascending=False)
allocation.set_index('Component',inplace=True)
allocation.plot.pie(y='Weight(%)',legend=None)
allocation.reset_index(inplace=True)
display(allocation)
plt.show()
print('\nPortfolio Simulated Close = ')
print(s1)

valY['PSO Close'] = leverage_factor*valX.dot(list(weights.values()))
evaluate(valY,'PSO Close',is_test=False)

# <--
testY['Benchmark Close'] = benchmark['Benchmark Close']
testY['PSO Close'] = leverage_factor*testX.dot(list(weights.values()))
evaluate(testY,'PSO Close',is_test=True)



