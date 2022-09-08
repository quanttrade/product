#UTF-8
#adair
#粒子群优化指数
#
import datetime
import numpy as np
import pandas as pd
from pyswarms.utils.search.grid_search import GridSearch
from pyswarms.single.global_best import GlobalBestPSO
from yq_toolsS45 import create_db,engine,get_IdxCons,list_to_str_f
from yq_toolsS45 import read_pickle,save_pickle,time_use_tool
import os
import multiprocessing
import sys

num_core = int(multiprocessing.cpu_count())

para_pool = 'S68para_pool'
if not os.path.exists(para_pool):
    os.mkdir(para_pool)

def date_trans0(t):
    return datetime.datetime.strptime(t,'%Y-%m-%d')


def get_weight(trainX,trainY):
    def find_particle_loss(coeffs):
        trainX_returns = trainX.pct_change().dropna()
        trainY_returns = trainY.pct_change().dropna()
        benchmark_tracking_error = np.std(trainX.dot(coeffs) - trainY)
        return benchmark_tracking_error

    def swarm(x):
        n_particles = x.shape[0]
        particle_loss = [find_particle_loss(x[i]) for i in range(n_particles)]
        return particle_loss

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
    return weights,leverage_factor


def get_ticker_group_data(sub_symbol,t_t0,t_t1):
    sql_tmp = """select tradeDate,ticker,closePrice from yq_mktequdadjafget where tradeDate>"%s" 
                and tradeDate<="%s" and ticker in (%s)"""
    df = pd.read_sql(sql_tmp % (t_t0, t_t1, list_to_str_f(sub_symbol)), engine)
    df.set_index(['tradeDate', 'ticker'], inplace=True)
    df = df.unstack()
    df.fillna(method='ffill', inplace=True)
    df.columns = [i[1] for i in df.columns]
    return df


def get_s68p2_comdata(index_sel,max_symbol_sel,t_t1):
    t_t0 = '%d%s' % (int(t_t1[:4]) - 1, t_t1[4:])
    # 获取数据
    # 获取成分股
    ticker_pool = get_IdxCons(t_t1, index_sel)
    # 市值最大的10个
    sql_tmp = 'select tradeDate from yq_dayprice where tradeDate<="%s" order by tradeDate desc limit 1'
    t_tmp = pd.read_sql(sql_tmp % t_t1, engine)
    t_tmp = t_tmp.tradeDate.astype(str).values[0]
    sql_tmp = 'select symbol,marketValue from yq_dayprice where tradeDate="%s" order by marketValue desc'
    sub_symbol = pd.read_sql(sql_tmp % t_tmp, engine)
    sub_symbol = sub_symbol[sub_symbol.symbol.isin(ticker_pool.tolist())]
    sub_symbol = sub_symbol.symbol.tolist()[:max_symbol_sel]
    # 获取数据
    # 1 com
    df = get_ticker_group_data(sub_symbol,t_t0,t_t1)
    # 2 index
    sql_tmp = 'select tradeDate,closeIndex from yq_index where symbol = "%s" and tradeDate>"%s" and tradeDate<="%s"'
    RUI = pd.read_sql(sql_tmp % (index_sel, t_t0, t_t1), engine)
    RUI.set_index(['tradeDate'], inplace=True)
    df['Actual Close'] = RUI['closeIndex']
    # <--
    # Train Val Test split
    train = df[df.index <= date_trans0(t_t1)]
    trainX = train.drop('Actual Close', axis=1)
    trainY = train['Actual Close']
    return trainX,trainY

def get_batch_weights(p):
    index_sel, max_symbol_sel, t_t1 = p
    fn1=os.path.join(para_pool,'%s_%0.2d_%s.pkl' % (index_sel,max_symbol_sel,t_t1))
    fn2 = os.path.join(para_pool, '%s_%0.2d_%s.csv' % (index_sel, max_symbol_sel, t_t1))
    print('begin %s' % fn1)
    if not os.path.exists(fn2):
        trainX, trainY = get_s68p2_comdata(index_sel, max_symbol_sel, t_t1)
        result = get_weight(trainX, trainY)
        save_pickle(fn1,result)
        pd.DataFrame(data=result[0], index=['w']).T.to_csv(fn2)
    print('complete %s' % fn1)


if __name__=="__main__":
    obj_clock = time_use_tool()
    # parameter
    if len(sys.argv)>=2:
        index_sel = sys.argv[1]
    else:
        index_sel = '000300'
    if len(sys.argv)>=3:
        max_symbol_sel=int(sys.argv[2])
    else:
        max_symbol_sel = 40
    print('%s-%d' % (index_sel,max_symbol_sel) )
    t_t1 = '2018-12-31'
    tref_month = pd.read_sql("""select endDate from yq_index_month where symbol  = "%s" 
        and endDate>"2009-12-01" order by endDate""" % index_sel, engine)
    tref_month = tref_month.endDate.astype(str).tolist()
    tref_month = tref_month[0:len(tref_month):3]
    tref_len = len(tref_month)
    #for sub_t in tref_month[:1]:
    #   get_batch_weights([index_sel,max_symbol_sel,sub_t])
    pool = multiprocessing.Pool(num_core)
    Y = pool.map(get_batch_weights, zip([index_sel]*tref_len,[max_symbol_sel]*tref_len,tref_month))
    pool.close()
    pool.join()

    obj_clock.use('All time')
