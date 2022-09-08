#UTF-8
#adair
#粒子群优化指数
#
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from IPython.display import display
from pyswarms.utils.search.grid_search import GridSearch
from pyswarms.single.global_best import GlobalBestPSO
from yq_toolsS45 import create_db,engine,get_IdxCons,list_to_str_f
from yq_toolsS45 import read_pickle,save_pickle

def date_trans0(t):
    return datetime.datetime.strptime(t,'%Y-%m-%d')

t_t0='2018-01-01'
t_t1='2018-05-11'
t_v0='2018-05-12'
t_v1='2019-03-31'
t_test0='2019-04-01'
t_test1='2019-04-30'

#获取数据
#获取成分股
index_sel = '000300'
max_symbol_sel = 10
ticker_pool = get_IdxCons(t_t0,index_sel)
#市值最大的10个
sql_tmp = 'select tradeDate from yq_dayprice where tradeDate<="%s" order by tradeDate desc limit 1'
t_tmp = pd.read_sql(sql_tmp % t_t0,engine)
t_tmp = t_tmp.tradeDate.astype(str).values[0]
sql_tmp = 'select symbol,marketValue from yq_dayprice where tradeDate="%s" order by marketValue desc'
sub_symbol = pd.read_sql(sql_tmp % t_tmp,engine)
sub_symbol=sub_symbol[sub_symbol.symbol.isin(ticker_pool.tolist())]
sub_symbol= sub_symbol.symbol.tolist()[:max_symbol_sel]
#获取数据
#1 com
sql_tmp = """select tradeDate,ticker,closePrice from yq_mktequdadjafget where tradeDate>="%s" 
    and tradeDate<="%s" and ticker in (%s)"""
df = pd.read_sql(sql_tmp %(t_t0,t_test1,list_to_str_f(sub_symbol)),engine)
df.set_index(['tradeDate','ticker'],inplace=True)
df = df.unstack()
df.fillna(method='ffill',inplace=True)
df.columns=[i[1] for i in df.columns]
#2 index
sql_tmp = 'select tradeDate,closeIndex from yq_index where symbol = "%s" and tradeDate>="%s" and tradeDate<="%s"'
RUI = pd.read_sql(sql_tmp % (index_sel,t_t0,t_test1),engine)
RUI.set_index(['tradeDate'],inplace=True)
df['Actual Close'] = RUI['closeIndex']
# <--
# Train Val Test split
train = df[df.index <= date_trans0(t_t1)]
val = df[(df.index >= date_trans0(t_v0)) & (df.index <= date_trans0(t_v1))]
test = df[(df.index >= date_trans0(t_test0)) & (df.index <= date_trans0(t_test1))]

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

def evaluate(df, portfolio_col):
    df2 = pd.DataFrame({
        'Actual Daily Return': df['Actual Close'].pct_change()
    })
    index_hpr = (df['Actual Close'][-1] - df['Actual Close'][0]) / df['Actual Close'][0]
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
cost, pos = optimizer.optimize(swarm,iters=100,n_processes=4)
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
evaluate(valY,'PSO Close')
# <--
testY['PSO Close'] = leverage_factor*testX.dot(list(weights.values()))
evaluate(testY,'PSO Close')


