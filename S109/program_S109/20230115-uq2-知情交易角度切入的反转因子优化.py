'''

导读
A. 研究目的：本文利用优矿提供的数据和分析函数，参考国盛证券量化专题报告《“量价淘金”选股因子系列研究（一）如何将隔夜涨跌变为有效的选股因子？》(原作者：刘富兵等)的思路，系统梳理和测试了对反转因子进行隔夜切分后的因子表现，以及从知情交易的角度切入对隔夜因子进行优化后的表现

B. 研究结论：

新因子corr_overnight_20与反转因子revs_20、revs_intraday_20, 以及隔夜因子revs_overnight_20、abs_overnight_20的相关性均低于0.2，较低，说明新因子具有增量信息。
对传统隔夜因子的改进中，abs_overnight_20的收益大幅提升，但是全中性化后，因子效果减弱，接近失效，说明该因子的收益大部分来源于风险因子。
新因子corr_overnight_20，虽然在收益率方面，不如传统反转因子，但是大幅提高了因子稳定性，使得全中性化后多空组合夏普比率达到1.94，最大回撤仅4%，远优于传统反转因子。
新因子corr_overnight_20, 其实刻画的是市场的非有效性。新因子corr_overnight_20越大，说明知情交易者信息优势越大，加剧了市场追涨杀跌的不对称效应，对股票未来的收益造成负面影响。
测试了不同的回溯期，回溯期越大，因子效果有一定程度的下降，但不影响因子的稳定性，依然具有较高的夏普率。
C. 文章结构：本文共分为4个部分，具体如下

一、基础数据准备、因子值计算。
二、因子测试
三、因子逻辑分析
四、总结
D. 时间说明

一、第一部分运行需要11分钟
二、第二部分运行需要3分钟
三、第三部分运行需要7分钟
总耗时21分钟左右 (为了方便修改程序，文中将很多中间数据存储下来以缩短运行时间)
特别说明
为便于阅读，本文将部分和文章主题无关的函数放在函数库里面：
https://uqer.datayes.com/v3/community/share/eLNeQy0p3r0lRu9I5WoZ5YOw2ng0/private；密码：6278
请在运行之前，克隆上面的代码，并存成lib（右上角->另存为lib,不要修改名字）

(深度报告版权归优矿所有，禁止直接转载或编辑后转载。)

'''

import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import time
import scipy.stats as st
from CAL.PyCAL import *
import seaborn as sns
import lib.quant_util as qutil

save_folder = "./reverse_factor_202210"  # 建立文件夹保存数据量大的数据文件
if not os.path.exists(save_folder):
    os.mkdir(save_folder)


'''

第一部分：基础数据准备、因子值计算
该部分耗时约10分钟
该部分内容为：

1.1 获取交易日历、行情数据、股票禁止池等基础数据
1.2 计算各类因子数据
通过修改 <sdate_backtest>和<edate_backtest>来修改测试区间

(深度报告版权归优矿所有，禁止直接转载或编辑后转载。)


'''

start_time = time.time()
print"该部分进行基础参数设置和数据准备..."

sdate_backtest = '20100101'
edate_backtest = '20221001'
cal_dates_df = DataAPI.TradeCalGet(exchangeCD=u"XSHG", beginDate=sdate_backtest, endDate=edate_backtest, field=u"", pandas="1").sort('calendarDate')
cal_dates_df['calendarDate'] = cal_dates_df['calendarDate'].apply(lambda x: x.replace('-', ''))
cal_dates_df['prevTradeDate'] = cal_dates_df['prevTradeDate'].apply(lambda x: x.replace('-', ''))

month_end_list = cal_dates_df[cal_dates_df['isMonthEnd']==1]['calendarDate'].values

# 全A投资域
a_universe_list = DataAPI.EquGet(equTypeCD=u"A",listStatusCD=u"L,S,DE",field=u"secID",pandas="1")['secID'].tolist()

# 个股日度行情数据
if not os.path.exists(os.path.join(save_folder, 'dmkt.pkl')):
    sdate_data = (pd.to_datetime(sdate_backtest) - pd.offsets.DateOffset(100)).strftime('%Y%m%d')
    dmkt_df = DataAPI.MktEqudAdjGet(secID=a_universe_list, beginDate=sdate_data, endDate=edate_backtest, isOpen="", field=u"ticker,tradeDate,preClosePrice,openPrice,closePrice,turnoverRate", pandas="1")
    dmkt_df['tradeDate'] = dmkt_df['tradeDate'].apply(lambda x: x.replace('-', ''))
    dmkt_df.sort_values(['ticker', 'tradeDate'], inplace=True)
    dmkt_df.to_pickle(os.path.join(save_folder, 'dmkt.pkl'))
else:
    dmkt_df = pd.read_pickle(os.path.join(save_folder, 'dmkt.pkl'))
print "个股日度行情数据:", dmkt_df.head().to_html()

# 获取个股月度收益率
mret_df = DataAPI.MktEqumAdjGet(beginDate=sdate_backtest, endDate=edate_backtest, secID=a_universe_list, field=u"ticker,endDate,chgPct", pandas="1")
mret_df.rename(columns={'endDate':'tradeDate', 'chgPct':'curr_ret'}, inplace=True)  # 交易日列和收益率列
mret_df['tradeDate'] = mret_df['tradeDate'].apply(lambda x: x.replace('-', ''))
mret_df.sort_values(['ticker', 'tradeDate'], inplace=True)
mret_df['nxt_ret'] = mret_df.groupby('ticker')['curr_ret'].shift(-1)
print "个股收益率:", mret_df.head().to_html()

# 股票池筛选(剔除上市不满60个交易日的次新股、st股、停牌个股、一字板个股)及保存pkl文件
if not os.path.exists(os.path.join(save_folder, 'forbidden_pool.pkl')):
    forbidden_pool = qutil.stock_special_tag(sdate_backtest, edate_backtest, pre_new_length=60)  # 次新股、st股、停牌个股
    # 筛选一字板个股
    mkt_df = DataAPI.MktEqudGet(beginDate=sdate_backtest, endDate=edate_backtest, secID=a_universe_list, field=u"ticker,tradeDate,highestPrice,lowestPrice", pandas="1")
    mkt_df['tradeDate'] = mkt_df['tradeDate'].apply(lambda x: x.replace('-', ''))
    limit_df = mkt_df[(mkt_df['highestPrice'] == mkt_df['lowestPrice']) & (mkt_df['highestPrice']>0)][['ticker', 'tradeDate']]
    limit_df['special_flag'] = 'limit'
    forbidden_pool = forbidden_pool.append(limit_df)
    forbidden_pool = forbidden_pool.merge(cal_dates_df, left_on=['tradeDate'], right_on=['calendarDate'])
    forbidden_pool = forbidden_pool[['ticker', 'tradeDate', 'prevTradeDate', 'special_flag']]
    forbidden_pool.to_pickle(os.path.join(save_folder, 'forbidden_pool.pkl'))
else:
    forbidden_pool = pd.read_pickle(os.path.join(save_folder, 'forbidden_pool.pkl'))
print "禁止股票池:", forbidden_pool.head().to_html()

# 在月行情数据中剔除个股
mret_df = mret_df.merge(forbidden_pool[['ticker', 'prevTradeDate', 'special_flag']], left_on=['ticker',
'tradeDate'], right_on=['ticker', 'prevTradeDate'], how='left')
mret_df = mret_df[mret_df['special_flag'].isnull()]
mret_df = mret_df.drop(['prevTradeDate', 'special_flag'], axis=1)

end_time = time.time()
print "耗时: %s seconds" % (end_time - start_time)


'''
1.2 计算因子值
因子1：revs_20: 传统反转因子，过去20个交易日的close2close收益率累乘
因子2：revs_intraday_20:传统日内因子，过去20个交易日的open2close收益率累乘
因子3：revs_overnight_20:传统隔夜因子，过去20个交易日的close2open收益率累乘
因子4：abs_overnight_20:取绝对值的隔夜跳空因子, 过去20个交易日的open2close收益率取平均值
因子5：corr_overnight_20: 从知情交易角度切入的优化后的隔夜跳空因子， 过去20个交易日因子的隔夜收益绝对值和上日换手率的相关系数

'''

start_time = time.time()
print"该部分计算各类反转因子..."

# 停牌时，开盘价处理
dmkt_df['openPrice'] = np.where(dmkt_df['turnoverRate'] == 0, dmkt_df['closePrice'], dmkt_df['openPrice'])

if not os.path.exists(os.path.join(save_folder, 'all_factor_df.pkl')):
    # 因子1：revs_20: 传统反转因子，过去20个交易日的close2close收益率累乘
    dmkt_df['ret'] = dmkt_df['closePrice']/dmkt_df['preClosePrice'] - 1
    dmkt_df['revs_20'] = dmkt_df.groupby(['ticker'])['ret'].rolling(20).apply(lambda x: (x+1).prod() - 1).values

    # 因子2：revs_intraday_20:传统日内因子，过去20个交易日的open2close收益率累乘
    dmkt_df['intraday_ret'] = dmkt_df['closePrice']/dmkt_df['openPrice'] - 1
    dmkt_df['revs_intraday_20'] = dmkt_df.groupby(['ticker'])['intraday_ret'].rolling(20).apply(lambda x: (x+1).prod() - 1).values

    # 因子3：revs_overnight_20:传统隔夜因子，过去20个交易日的close2open收益率累乘
    dmkt_df['overnight_ret'] = dmkt_df['openPrice']/dmkt_df['preClosePrice'] - 1
    dmkt_df['revs_overnight_20'] = dmkt_df.groupby(['ticker'])['overnight_ret'].rolling(20).apply(lambda x: (x+1).prod() - 1).values

    # 因子4：abs_overnight_20:取绝对值的隔夜跳空因子, 过去20个交易日的open2close收益率取平均值
    dmkt_df['abs_overnight_ret'] = dmkt_df['overnight_ret'].abs()
    dmkt_df['abs_overnight_20'] = dmkt_df.groupby(['ticker'])['abs_overnight_ret'].rolling(20).mean().values

    # 因子5：corr_overnight_20: 从知情交易角度切入的优化后的隔夜跳空因子
    dmkt_df['pre_turnoverrate'] = dmkt_df.groupby('ticker')['turnoverRate'].shift(1)
    dmkt_df['corr_overnight_20'] = dmkt_df.groupby(['ticker']).apply(lambda x: x['abs_overnight_ret'].rolling(20).corr(x['pre_turnoverrate'])).values

    factor_list = ['revs_20', 'revs_overnight_20', 'revs_intraday_20', 'corr_overnight_20', 'abs_overnight_20']
    all_factor_df = dmkt_df[['ticker', 'tradeDate'] + factor_list]
    all_factor_df.to_pickle(os.path.join(save_folder, 'all_factor_df.pkl'))
else:
    all_factor_df = pd.read_pickle(os.path.join(save_folder, 'all_factor_df.pkl'))
print "全部反转因子数据:", all_factor_df.tail().to_html()

end_time = time.time()
print "耗时: %s seconds" % (end_time - start_time)
'''
第二部分：因子测试
该部分耗时约3分钟
该部分内容为：

2.1
因子测试函数
2.2
行业市值中性化因子测试
2.3
全中性因子测试
该部分分析了各个因子的IC、ICIR、十分组表现、十分组多空组合表现等

(深度报告版权归优矿所有，禁止直接转载或编辑后转载。)

文档
2.1
因子测试函数

'''


# 因子测试函数准备

def proc_float_scale(df, col_name, format_str):
    """
    格式化输出
    参数：
        df: DataFrame, 需要格式化的数据
        col_name： list, 需要格式化的列名
        format_str：格式类型
    """
    for col in col_name:
        for index in df.index:
            df.ix[index, col] = format(df.ix[index, col], format_str)
    return df


def factor_process(factor_df, factor_list, exclude_style_list):
    '''
    因子处理函数
    '''
    # 去极值
    w_factor_df = qutil.mad_winsorize(factor_df, factor_list, sigma_n=3)

    # 完全中性化
    n_factor_df = qutil.neutralize_dframe(w_factor_df.copy(), factor_list, exclude_style=exclude_style_list)

    # 标准化
    s_factor_df = n_factor_df.copy()
    s_factor_df[factor_list] = s_factor_df.groupby('tradeDate')[factor_list].apply(
        lambda df: (df - df.mean()) / df.std())
    return s_factor_df


def factor_test_summary(factor_df, factor_list, ngrp):
    """
    综合因子测试方法：回归法、IC分析法、分组测试分析法
    参数：
        factor_df: DataFrame, 因子值
        factor_df: list, 因子列表
    返回：
        因子收益率和t值、IC序列、分组收益率序列
    """
    # IC测试
    ic_res = qutil.calc_ic(factor_df, mret_df, factor_list, return_col_name='nxt_ret', ic_type='spearman')
    # 分层回测测试
    perf_list = []
    for fn in factor_list:
        perf, _ = qutil.simple_group_backtest(factor_df, mret_df, factor_name=fn, return_name='nxt_ret', commission=0,
                                              ngrp=ngrp)
        perf_list.append(perf.pivot_table(values='period_ret', index='tradeDate', columns='group'))
    perf_df = pd.concat(perf_list, axis=1)
    perf_df.columns = pd.MultiIndex.from_tuples([(fn, col) for fn in factor_list for col in range(ngrp)])
    return ic_res, perf_df


def ic_describe(ic_df, factor_list, annual_len):
    """
    统计IC的均值、标准差、IC_IR、大于0的比例
    参数:
        ic_df: DataFrame, IC值， index为日期， columns为因子名， values为各个因子的IC值
        factor_df: list, 因子列表
        annual_len: int, 年化周期数。若是月频结果，则通常为12；若是周频结果，则通常为52
    返回:
        DataFrame, IC统计
    """
    ic_df = ic_df.dropna()

    # 记录因子个数和因子名
    n = len(factor_list)
    # IC均值
    ic_mean = ic_df[factor_list].mean()
    # IC标准差
    ic_std = ic_df[factor_list].std()
    # IC均值的T统计量
    ic_t = pd.Series(st.ttest_1samp(ic_df[factor_list], 0)[0], index=factor_list)
    # IC_IR
    ic_ir = ic_mean / ic_std * np.sqrt(annual_len)
    # IC大于0的比例
    ic_p_pct = (ic_df[factor_list] > 0).sum() / len(ic_df)

    # IC统计
    ic_table = pd.DataFrame([ic_mean, ic_std, ic_t, ic_ir, ic_p_pct],
                            index=['平均IC', 'IC标准差', 'IC均值T统计量', 'IC_IR', 'IC大于0的比例']).T
    ic_table = proc_float_scale(ic_table, ['平均IC', 'IC标准差', 'IC大于0的比例'], ".2%")
    ic_table = proc_float_scale(ic_table, ['IC均值T统计量', 'IC_IR'], ".2f")
    return ic_table


def group_perf_describe(perf_df, factor_list, annual_len):
    """
    统计因子的回测绩效， 包括年化收益率、年化波动率、夏普比率、最大回撤
    参数:
        perf_df: DataFrame, 回测的期间收益率， index为日期， columns为因子名， values为因子回测的期间收益率
        factor_df: list, 因子列表
        annual_len: int, 年化周期数。若是月频结果，则通常为12；若是周频结果，则通常为52
    返回:
        DataFrame, 返回回测绩效
    """
    # 记录因子个数
    n = len(factor_list)
    group_res = (perf_df.mean() * annual_len).reset_index()
    group_res.columns = ['factor_name', 'group', 'value']
    group_res = group_res.pivot_table(values='value', index='factor_name', columns='group')
    ngrp = group_res.columns.max() + 1

    sub_res = pd.concat([perf_df[(fn, ngrp - 1)] - perf_df[(fn, 0)] for fn in factor_list], axis=1)
    sub_res.columns = factor_list

    # 年化收益率
    ret_mean = sub_res.mean() * annual_len
    # 年化波动率
    ret_std = sub_res.std() * np.sqrt(annual_len)
    # 年化IR
    ir = ret_mean / ret_std
    # 最大回撤
    maxdrawdown = {}
    for i in range(n):
        fname = factor_list[i]
        cum_ret = pd.DataFrame((sub_res[fname] + 1).cumprod())
        cum_max = cum_ret.cummax()
        maxdrawdown[fname] = ((cum_max - cum_ret) / cum_max).max().values[0]
    maxdrawdown = pd.Series(maxdrawdown)
    # 月度胜率
    win_ret = (sub_res > 0).sum() / (len(sub_res) - 1)

    ls_res = pd.DataFrame([ret_mean, ret_std, ir, maxdrawdown, win_ret],
                          index=['ls_ret', 'ls_std', 'ls_ir', 'ls_md', 'ls_win']).T

    group_table = pd.concat([ls_res, group_res], axis=1)
    group_table.columns = ['多空组合年化收益率', '多空组合年化波动率', '多空组合夏普比率', '多空组合最大回撤', '多空组合月度胜率'] + ['第%s组年化收益率' % i for i in
                                                                                            range(1, ngrp + 1)]
    group_table = proc_float_scale(group_table,
                                   ['第%s组年化收益率' % i for i in range(1, ngrp + 1)] + ['多空组合年化收益率', '多空组合年化波动率',
                                                                                    '多空组合最大回撤', '多空组合月度胜率'], ".2%")
    group_table = proc_float_scale(group_table, ['多空组合夏普比率'], ".2f")
    return group_table.loc[factor_list, :]


def test_discribe(ic_res, perf_df, factor_list, annual_len=12, show_pic=True):
    """
    综合因子分析结果统计
    参数:
        ic_res: DataFrame, IC值， index为日期， columns为因子名， values为各个因子的IC值
        perf_df: DataFrame, 回测的期间收益率， index为日期， columns为因子名， values为因子回测的期间收益率
        factor_df: list, 因子列表
    """
    ic_table = ic_describe(ic_res, factor_list, annual_len=annual_len)
    group_table = group_perf_describe(perf_df, factor_list, annual_len=annual_len)
    print
    'IC结果分析', ic_table.to_html()
    print
    '分组回测结果分析', group_table.to_html()

    if show_pic:
        for factor_name in factor_list:
            ngrp = max(perf_df[factor_name].columns) + 1
            ec_perf_df = perf_df[[(factor_name, col) for col in range(int(ngrp))]]
            ec_perf_df.columns = range(int(ngrp))
            long_short_cumret = ec_perf_df[int(ngrp) - 1] - ec_perf_df[0]

            fig = plt.figure(figsize=(18, 5))
            ax1 = fig.add_subplot(121)
            ax1.plot(pd.to_datetime(ec_perf_df.index), (ec_perf_df[range(int(ngrp))] + 1).cumprod())
            ax1.legend(np.arange(int(ngrp)) + 1, loc=2)
            ax1.set_title(u'%s分组回测收益表现' % factor_name, fontsize=16, fontproperties=font)
            ax3 = ax1.twinx()
            ax3.plot(pd.to_datetime(long_short_cumret.index), (long_short_cumret + 1).cumprod(), 'r--')
            ax3.legend([u'多空对冲'], loc=1, prop=font)
            plt.grid(b=None)

            ax2 = fig.add_subplot(122)
            plot_baseline = np.arange(int(ngrp))
            ax2.bar(plot_baseline, (ec_perf_df[range(int(ngrp))] + 1).cumprod().iloc[-1] - 1)
            ax2.grid(False)
            ax2.set_title(u'%s分组累计收益柱状图' % factor_name, fontsize=16, fontproperties=font)
            ax2.set_xticks(plot_baseline + 0.3)
            ax2.set_xticklabels([u'第%s组' % str(i + 1) for i in range(int(ngrp))], fontproperties=font, rotation=0)
        plt.show()


def calc_factor_corr(factor_frame, factor_list, show_corr_plot=True, corr_method='spearman'):
    """
    计算因子相关性
    参数:
        factor_frame: DataFrame, 因子值
        factor_list: list, 因子列表
        show_corr_plot: bool, 是否显示图片
        corr_method: str, spearman/pearson, 相关性类型
    """

    dates_list = factor_frame['tradeDate'].unique()
    date_corr_df = factor_frame.groupby('tradeDate')[factor_list].corr(method=corr_method)
    corr_df = sum([date_corr_df.loc[date].fillna(0) for date in dates_list]) / sum(
        [~date_corr_df.loc[date].isnull() for date in dates_list])

    if show_corr_plot:
        fig, ax = plt.subplots(figsize=(len(factor_list) * 0.9, len(factor_list) * 0.6))
        sns.heatmap(corr_df, linewidths=0.05, ax=ax, vmax=1, vmin=-1, cmap='RdYlGn_r', annot=True)
        ax.set_title(u'因子相关性', fontproperties=font, fontsize=16)
        plt.show()
    return corr_df


def year_perf_describe(f_perf_df, annual_len=12):
    """
    分年度收益统计
    参数:
        f_perf_df: DataFrame, 因子分组收益表现
    """
    ngrp = max(f_perf_df.columns)
    f_perf_df['year'] = [x[:4] for x in f_perf_df.index]
    f_perf_df['ls'] = f_perf_df[ngrp] - f_perf_df[0]

    top_ann_ret = f_perf_df.groupby('year')[ngrp].mean() * annual_len
    bottom_ann_ret = f_perf_df.groupby('year')[0].mean() * annual_len
    ls_ann_ret = f_perf_df.groupby('year')['ls'].mean() * annual_len

    # 年化波动率
    ls_ret_std = f_perf_df.groupby('year')['ls'].std() * np.sqrt(annual_len)
    # 年化IR
    ls_ir = ls_ann_ret / ls_ret_std
    # 最大回撤
    cum_ret = f_perf_df.groupby('year')['ls'].apply(lambda x: (x + 1).cumprod()).reset_index()
    cum_ret['year'] = cum_ret['tradeDate'].apply(lambda x: x[:4])
    cum_ret['cummax'] = cum_ret.groupby('year')['ls'].cummax()
    cum_ret['dd'] = 1 - cum_ret['ls'] / cum_ret['cummax']
    max_dd = cum_ret.groupby('year')['dd'].max()
    # 月度胜率
    ls_win_ret = f_perf_df.groupby('year')['ls'].apply(lambda x: 1.0 * sum(x > 0) / len(x))

    year_perf = pd.concat([top_ann_ret, bottom_ann_ret, ls_ann_ret, ls_ret_std, ls_ir, ls_win_ret, max_dd], axis=1)
    year_perf.columns = ['多头年化收益', '空头年化收益', '多空年化收益', '多空年化波动率', '多空信息比率', '多空月度胜率', '多空最大回撤']
    year_perf = proc_float_scale(year_perf, ['多头年化收益', '空头年化收益', '多空年化收益', '多空年化波动率', '多空月度胜率', '多空最大回撤'], ".2%")
    year_perf = proc_float_scale(year_perf, ['多空信息比率'], ".2f")
    return year_perf

'''
2.2 行业市值中性化因子测试
revs_20, revs_intraday_20, abs_overnight_20, corr_overnight_20本身是负向因子，因此在测试前，想进行因子方向调整。
对所有因子进行去极值、行业市值中性化处理。

'''

start_time = time.time()
print "对行业市值中性化因子进行IC测试分析和分组测试分析"

# 月末因子值
month_factor_df = all_factor_df[all_factor_df['tradeDate'].isin(month_end_list)]
# 因子方向调整
adj_factor_list = ['revs_20', 'revs_intraday_20', 'abs_overnight_20', 'corr_overnight_20']
month_factor_df[adj_factor_list] = -month_factor_df[adj_factor_list]
print(','.join(adj_factor_list) + '为负向因子，进行方向调整')

# 行业市值中性化
factor_list = ['revs_20', 'revs_overnight_20', 'revs_intraday_20', 'abs_overnight_20', 'corr_overnight_20']
exclude_style_list=['BETA', 'MOMENTUM', 'EARNYILD', 'RESVOL', 'GROWTH', 'BTOP', 'LEVERAGE', 'LIQUIDTY', 'SIZENL']
pa_factor_df = factor_process(month_factor_df, factor_list, exclude_style_list=exclude_style_list)

# 因子相关性分析
_ = calc_factor_corr(pa_factor_df, factor_list)

# 进行IC测试和分组测试
ic_res, perf_df = factor_test_summary(pa_factor_df, factor_list, 10)
test_discribe(ic_res, perf_df, factor_list, annual_len=12)

# 新隔夜因子分年度表现
corr_year_perf = year_perf_describe(perf_df['corr_overnight_20'])
print 'corr_overnight_20分年度表现', corr_year_perf.to_html()

end_time = time.time()
print "耗时: %s seconds" % (end_time - start_time)


'''
从相关性分析可以看出，新因子corr_overnight_20与反转因子revs_20、revs_intraday_20, 以及隔夜因子revs_overnight_20、abs_overnight_20的相关性均低于0.2，较低，说明新因子具有增量信息。
从因子测试结果来看，行业市值中性化后，abs_overnight_20较传统隔夜因子revs_overnight_20，多空组合的收益大幅提升，但同时，也提高了波动率。
新因子corr_overnight_20，行业市值中性化后，虽然在收益率方面，不如传统反转因子，但是大幅提高了因子稳定性，使得多空组合夏普比率达到2.58，最大回撤仅2.38%，远优于传统反转因子。
从分组测试结果可以看出，传统的各个反转因子多头单调性均出现拐头现象；新因子corr_overnight_20具有良好的分组单调性。
从分年度结果来看，新因子corr_overnight_20多空组合均有正收益，表现稳定。
    
文档
2.3 全中性化因子测试
对所有因子进行去极值、全中性化处理。
中性化选择了通联CNE5模型中的10个风格因子以及申万一级行业因子


'''


start_time = time.time()
print "对全中性化因子进行IC测试分析和分组测试分析"

# 行业市值中性化
factor_list = ['revs_20', 'revs_overnight_20', 'revs_intraday_20', 'abs_overnight_20', 'corr_overnight_20']
exclude_style_list=[]
a_factor_df = factor_process(month_factor_df, factor_list, exclude_style_list=exclude_style_list)

# 进行IC测试和分组测试
ic_res, perf_df = factor_test_summary(a_factor_df, factor_list, 10)
test_discribe(ic_res, perf_df, factor_list, annual_len=12)

# 新隔夜因子分年度表现
corr_year_perf = year_perf_describe(perf_df['corr_overnight_20'])
print 'corr_overnight_20分年度表现', corr_year_perf.to_html()

end_time = time.time()
print "耗时: %s seconds" % (end_time - start_time)


'''
从因子测试结果来看，全中性化后，abs_overnight_20的选股效果下降明显，主要体现在分组单调性表现大幅下降，说明该因子的收益大部分来源于风险因子。
全中性化后，所有因子的表现均有一定程度的下降，并且因子多头的拐头效应均加剧。相较而言，新因子corr_overnight_20依然保持较好的分组单调性。
同样地，新因子corr_overnight_20，虽然在收益率方面，不如传统反转因子，但是大幅提高了因子稳定性，使得多空组合夏普比率达到1
.94，最大回撤仅3 %，远优于传统反转因子。
从分年度结果来看，新因子corr_overnight_20多空组合均有正收益，表现稳定。

文档
第三部分：因子逻辑分析
该部分耗时约7分钟
该部分内容为：

3.1
新因子的选股逻辑
3.2
参数敏感性测试
(深度报告版权归优矿所有，禁止直接转载或编辑后转载。)

文档
3.1
新因子的选股逻辑
若隔夜涨跌幅绝对值较大，即个股开盘跳空幅度大，说明个股具有隔夜信息；若同时，昨日换手率高，即隔夜涨跌幅绝对值与昨日换手率的相关系数高，说明，信息泄露可能性较大，知情交易者提前行动。
因此，若隔夜涨跌幅绝对值与昨日换手率的相关系数高，说明该个股的知情交易者多，市场有效性弱。
新因子corr_overnight_20, 其实刻画的是市场的非有效性。
下面，分析新因子为何是一个负向因子。

'''

start_time = time.time()
print "该部分分析新因子的选股逻辑..."

# 月末因子值
month_factor_df = all_factor_df[all_factor_df['tradeDate'].isin(month_end_list)]
merge_factor_df = month_factor_df[['ticker', 'tradeDate', 'revs_20', 'corr_overnight_20']].merge(mret_df[['ticker', 'tradeDate', 'nxt_ret']], on=['ticker', 'tradeDate'])
# 下月超额收益
merge_factor_df['ex_nxt_ret'] = merge_factor_df.groupby('tradeDate')['nxt_ret'].apply(lambda x: x - x.mean())

# 根据过去20个交易日涨跌幅，分成2组
merge_factor_df['revs_flag'] = merge_factor_df.groupby('tradeDate')['revs_20'].apply(lambda x: np.sign(x - x.mean()))
revs_stat = merge_factor_df.groupby(['tradeDate', 'revs_flag'])['ex_nxt_ret'].mean().reset_index()
stat1 = pd.DataFrame(revs_stat.groupby('revs_flag')['ex_nxt_ret'].mean())
stat1.index = ['下跌', '上涨']
stat1.columns = ['下月平均超额收益']
stat1 = proc_float_scale(stat1, stat1.columns, ".2%")
print '涨跌幅分组测试下月平均超额收益', stat1.to_html()

# 进一步，在涨跌幅分组内，根据corr_overnight_20的大小，等分成2组
merge_factor_df['corr_flag'] = merge_factor_df.groupby(['tradeDate', 'revs_flag'])['corr_overnight_20'].rank(pct=True)
merge_factor_df['corr_flag'] = np.where(merge_factor_df['corr_flag'] < 0.5, 1, 2)
corr_stat = merge_factor_df.groupby(['tradeDate', 'revs_flag', 'corr_flag'])['ex_nxt_ret'].mean().reset_index()
stat2 = corr_stat.groupby(['revs_flag', 'corr_flag'])['ex_nxt_ret'].mean().reset_index()
stat2 = stat2.pivot_table(index='revs_flag', columns='corr_flag', values='ex_nxt_ret')
stat2.index = ['下跌', '上涨']
stat2.columns = ['信息优势小', '信息优势大']
stat2 = proc_float_scale(stat2, stat2.columns, ".2%")
print '涨跌幅+信息优势双分组测试下月平均超额收益', stat2.to_html()

end_time = time.time()
print "耗时: %s seconds" % (end_time - start_time)


'''
从传统反转因子revs_20的测试结果来看，当个股过去的涨幅越大，未来收益越小。同时，从分组回测结果可以看出，反转因子的空头收益明显多于多头，即传统反转因子的多空收益是不对称的。
每个月底，将全市场股票按照过去20个交易日收益分成上涨、下跌两组，统计各组下个月的平均超额收益率。结果可以看出，过去上涨的股票，下月平均超额收益为 - 0.43 %；过去下跌的股票，下月平均超额收益为0
.33 %。说明A股市场上，上涨股票的反转效应更强，追涨效应强于杀跌效应。
而知情者交易会进一步加剧这种不对称效应。将上涨、下跌两组中，根据新因子corr_overnight_20的大小，等分成2组，corr_overnight_20越大，说明知情交易者信息优势越大。从双分组测试结果可以看出，上涨组中，下月平均超额收益为 - 0.43 %，而在信息优势大组中，下月平均超额收益为 - 0.80 %；同样地，下跌组中，下月平均超额收益为0
.33 %，而在信息优势大组中，下月平均超额收益只有0
.14 %；即在信息优势大组中，上涨组跌跟多，下跌组涨更少，加剧了不对称效应。
所以新因子corr_overnight_20越大，知情交易者信息优势越大，对股票未来的收益造成负面影响。

文档
3.2
参数敏感性测试
回溯过去40、60
个交易日，计算因子，测试的参数敏感性。
'''

start_time = time.time()
print
"该部分计算各类反转因子..."

if not os.path.exists(os.path.join(save_folder, 'sensitivity_test_factors_df.pkl')):
    # 停牌时，开盘价处理
    dmkt_df = pd.read_pickle(os.path.join(save_folder, 'dmkt.pkl'))
    dmkt_df['openPrice'] = np.where(dmkt_df['turnoverRate'] == 0, dmkt_df['closePrice'], dmkt_df['openPrice'])

    all_factor_df = []
    for n in [40, 60]:
        # 因子1：revs_n: 传统反转因子，过去n个交易日的close2close收益率累乘
        dmkt_df['ret'] = dmkt_df['closePrice'] / dmkt_df['preClosePrice'] - 1
        dmkt_df['revs_%s' % n] = dmkt_df.groupby(['ticker'])['ret'].rolling(n).apply(
            lambda x: (x + 1).prod() - 1).values

        # 因子3：revs_overnight_n:传统隔夜因子，过去n个交易日的close2open收益率累乘
        dmkt_df['overnight_ret'] = dmkt_df['openPrice'] / dmkt_df['preClosePrice'] - 1
        dmkt_df['revs_overnight_%s' % n] = dmkt_df.groupby(['ticker'])['overnight_ret'].rolling(n).apply(
            lambda x: (x + 1).prod() - 1).values

        # 因子4：abs_overnight_n:取绝对值的隔夜跳空因子, 过去n个交易日的open2close收益率取平均值
        dmkt_df['abs_overnight_ret'] = dmkt_df['overnight_ret'].abs()
        dmkt_df['abs_overnight_%s' % n] = dmkt_df.groupby(['ticker'])['abs_overnight_ret'].rolling(n).mean().values

        # 因子5：corr_overnight_n: 从知情交易角度切入的优化后的隔夜跳空因子
        dmkt_df['pre_turnoverrate'] = dmkt_df.groupby('ticker')['turnoverRate'].shift(1)
        dmkt_df['corr_overnight_%s' % n] = dmkt_df.groupby(['ticker']).apply(
            lambda x: x['abs_overnight_ret'].rolling(n).corr(x['pre_turnoverrate'])).values

        factor_list = ['revs_%s' % n, 'revs_overnight_%s' % n, 'corr_overnight_%s' % n, 'abs_overnight_%s' % n]
        n_factor_df = dmkt_df[['ticker', 'tradeDate'] + factor_list]
        all_factor_df.append(n_factor_df.set_index(['ticker', 'tradeDate']))
    all_factor_df = pd.concat(all_factor_df, axis=1).reset_index()
    all_factor_df.to_pickle(os.path.join(save_folder, 'sensitivity_test_factors_df.pkl'))
else:
    all_factor_df = pd.read_pickle(os.path.join(save_folder, 'sensitivity_test_factors_df.pkl'))
print
"不同参数的因子数据:", all_factor_df.tail().to_html()

end_time = time.time()
print
"耗时: %s seconds" % (end_time - start_time)


start_time = time.time()
print "对全中性化因子进行IC测试分析和分组测试分析"

# 月末因子值
month_factor_df = all_factor_df[all_factor_df['tradeDate'].isin(month_end_list)]
# 因子方向调整
adj_factor_list = ['revs_40', 'abs_overnight_40', 'corr_overnight_40',
                   'revs_60', 'abs_overnight_60', 'corr_overnight_60']
month_factor_df[adj_factor_list] = -month_factor_df[adj_factor_list]
print(','.join(adj_factor_list) + '为负向因子，进行方向调整')

# # # 行业市值中性化
factor_list = ['revs_40', 'revs_overnight_40', 'abs_overnight_40', 'corr_overnight_40',
               'revs_60', 'revs_overnight_60', 'abs_overnight_60', 'corr_overnight_60']
exclude_style_list=[]
a_factor_df = factor_process(month_factor_df, factor_list, exclude_style_list=exclude_style_list)

# 进行IC测试和分组测试
ic_res, perf_df = factor_test_summary(a_factor_df, factor_list, 10)
test_discribe(ic_res, perf_df, factor_list, annual_len=12, show_pic=False)

# 画图
for n in [40, 60]:
    fig, ax = plt.subplots(figsize=(10, 5))
    for fn in ['revs_%s' %n, 'revs_overnight_%s' %n, 'abs_overnight_%s' %n, 'corr_overnight_%s' %n]:
        f_perf_df = perf_df[fn]
        ngrp = max(f_perf_df.columns)
        f_perf_df['ls'] = f_perf_df[ngrp] - f_perf_df[0]
        if fn[:4] == 'corr':
            ax.plot(pd.to_datetime(f_perf_df.index), (f_perf_df['ls']+1).cumprod(), label=fn, linewidth=5, linestyle='--', color='r')
        else:
            ax.plot(pd.to_datetime(f_perf_df.index), (f_perf_df['ls']+1).cumprod(), label=fn)
    ax.legend(loc=0)
    ax.set_title(u"回溯%s日多空组合净值" % n, fontsize=16, fontproperties=font)

end_time = time.time()
print "耗时: %s seconds" % (end_time - start_time)


'''
从测试结果来看，回溯期越大，因子效果有一定程度的下降。
不同因子的比较结果看出，不同的回溯期下，新因子的波动率和最大回撤依然稳定低于各类反转因子，具有较高的夏普率。

文档
总结
新因子corr_overnight_20与反转因子revs_20、revs_intraday_20, 以及隔夜因子revs_overnight_20、abs_overnight_20的相关性均低于0
.2，较低，说明新因子具有增量信息。
对传统隔夜因子的改进中，abs_overnight_20的收益大幅提升，但是全中性化后，因子效果减弱，接近失效，说明该因子的收益大部分来源于风险因子。
新因子corr_overnight_20，虽然在收益率方面，不如传统反转因子，但是大幅提高了因子稳定性，使得全中性化后多空组合夏普比率达到1
.94，最大回撤仅3 %，远优于传统反转因子。
新因子corr_overnight_20, 其实刻画的是市场的非有效性。新因子corr_overnight_20越大，说明知情交易者信息优势越大，加剧了市场追涨杀跌的不对称效应，对股票未来的收益造成负面影响。
测试了不同的回溯期，回溯期越大，因子效果有一定程度的下降，但不影响因子的稳定性，依然具有较高的夏普率。

'''