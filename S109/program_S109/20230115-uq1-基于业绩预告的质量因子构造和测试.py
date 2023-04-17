
'''
导读
A. 研究目的：本文利用优矿提供的数据和分析函数，参考申万宏源研究报告《业绩预告信息披露质量因子的构建与改进》(原作者：杨俊文)的思路，系统梳理分析了业绩预告数据，并测试了对应的因子表现。

B. 研究结论：

随着更多上市公司公布业绩预告数据，作为一个全新的角度，业绩预告的偏离度、准确性是不错的衡量公司质量的代理变量；
从测试结果来看，对齐报告期的宽度因子width_factor1、偏离度因子bias_factor2, 行业和市值中性化后的IC分别为2.95%，1.83%，对应的ICIR为1.63和1.64，多空对冲年化收益为10.36%、7.11%，夏普为1.5和1.32，具有不错的选股效果；而如果不对齐报告期得到的宽度因子及偏离度因子width_factor3，bias_factor4IC分别为2.03%，2.71%，对应的ICIR为1.81和2.94，多空对冲年化收益为11.37%、13.74%，夏普为1.47和2.22,选股效果更好；
如果进一步进行全中性化处理，最好的bias_factor4因子，在全中性化后依然具有2.25%的IC、2.6的ICIR、8.82%的多空对冲收益，其它3个因子,width_factor1的IC为1.88%，width_factor2的IC为1.86%，bias_factor3的IC为1.52%，也都有一定的选股作用
C. 文章结构：本文共分为3个部分，具体如下

一、数据准备和数据分析
二、因子计算
三、因子测试
D. 时间说明

一、第一部分运行需要5分钟
二、第二部分运行需要2分钟
三、第三部分运行需要8分钟
总耗时15分钟左右 (为了方便修改程序，文中将很多中间数据存储下来以缩短运行时间)
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
import statsmodels.api as sm

save_folder = "./quality_factor_202212"  # 建立文件夹保存数据量大的数据文件
if not os.path.exists(save_folder):
    os.mkdir(save_folder)
'''
第一部分：数据准备和数据分析
该部分耗时约5分钟
该部分内容为：

1.1 获取历年业绩预告数据并进行数量、覆盖度的分析
1.2 画图展示业绩预告数据的特征
1.3 统计业绩预告数据在不同投资域的覆盖度
1.4 业绩预告数据的对齐
(深度报告版权归优矿所有，禁止直接转载或编辑后转载。)

1.1 获取历年业绩预告数据并进行数量、覆盖度的分析
公司在业绩预告中会公布多类预告值，会有不同的口径，如净利润/营收绝对值，利润/营收相对值，或者EPS值等，本部分利用API获取所有的预告数据，而在本文后面会将所有同归母净利润相关的值进行换算、对齐，转换成归母净利润的绝对数值以便于因子计算



'''
# 获取历年的业绩预告情况
ef_df_list = []
for year in range(2007, 2023):
    enddate_start = '%s0331'%year
    enddate_end = '%s1231'%year
    fore_df = DataAPI.FdmtEfNewGet(reportType=u"Q1,S1,Q3,CQ3,Q2,A",endDate=enddate_end,beginDate=enddate_start,pandas="1")
    ef_df_list.append(fore_df)
ef_df = pd.concat(ef_df_list, axis=0).query("mergedFlag=='1'")
ef_df['reportType'] = np.where((ef_df['fiscalPeriod']=='9') & (ef_df['reportType']=='Q3'), 'CQ3', ef_df['reportType'])
ef_df['reportType'] = np.where((ef_df['fiscalPeriod']=='3') & (ef_df['reportType']=='S1'), 'Q2', ef_df['reportType'])
ef_df = ef_df.query("endDate<'2022-12-31'")
print("业绩预告原始数据如下:")
ef_df.head()

'''
1.2 画图展示业绩预告数据的特征

'''
import matplotlib.pyplot as plt
from CAL.PyCAL import *
fig1 = ef_df.groupby(['endDate'])['secID'].count().plot.bar(figsize=(18,5),title='Number of Forecast Report(No ticker deduplication)')
_ = plt.show()
_ = plt.close()
fig2 = ef_df.groupby(['endDate'])['secID'].nunique().plot.bar(figsize=(18,5),title='Number of Forecast Report(After ticker deduplication)')

# 统计各个财报期的预告数量
print(ef_df.groupby(['reportType'])['secID'].count().reset_index().to_html())

'''
从上图和统计数据可以看出：

年报的预告数量最多，半年报和三季报预告数量接近，一季报最少；
不去重的话，峰值为一个财报期有3500条记录，去重之后为2500，说明有相当一部分公司会发多次预告，也就意味着会对预告数据进行修正


1.3 统计业绩预告数据在不同投资域的覆盖度
'''
## HS300, ZZ800, ZZ1000的覆盖度
univ_dict = {
    "HS300": "000300",
    "ZZ800": "000906",
    "ZZ1000": "000852"
}

univ_df_dict = {}  # 存储成分股datafarme
for univ_name in univ_dict.keys():
    univ_code = univ_dict[univ_name]
    df_list = []
    for tyear in range(2007, 2023):
        univ_tmp_df = \
        DataAPI.IdxConsGet(ticker=univ_code, isNew=u"", intoDate=u"%s0101" % tyear, field=u"", pandas="1")[
            ['consTickerSymbol']]
        univ_tmp_df['year'] = str(tyear)[:4]
        df_list.append(univ_tmp_df)
    univ_df = pd.concat(df_list, axis=0)
    univ_df_dict[univ_name] = univ_df

for univ_name in univ_df_dict.keys():
    total_univ_num = int(univ_name.replace("HS", "").replace("ZZ", ""))  # 指数成分股全集个数
    univ_df = univ_df_dict[univ_name].rename(columns={"consTickerSymbol": "ticker"})
    coverage_ef_df = ef_df[['endDate', 'ticker']]
    coverage_ef_df['year'] = coverage_ef_df['endDate'].apply(lambda x: str(x)[:4])
    coverage_ef_df = coverage_ef_df.merge(univ_df, how='inner').groupby(['endDate'])[
                         'ticker'].nunique() / total_univ_num
    _ = coverage_ef_df.plot.bar(figsize=(18, 5), title='coverage of %s' % univ_name)
    _ = plt.show()


'''

从上图可以看出，ZZ800的覆盖度最高，ZZ1000近几年的覆盖度明显逐渐走低

    
文档
1.4 业绩预告数据的对齐
该部分非常繁琐，但是对于因子计算非常关键，最主要的原因为上述的，上市公司进行业绩预告披露时有多个口径，需要非常小心的对数据进行”结构化和标准化处理“，该部分的内容包括:

只考虑对净利润有预告的数据；
取财报期当日的上市公司股本数据，将EPS转成利润时用
对齐去年同期的数据，用来将预告中的同比增幅口径转换成绝对数值
对齐截止上个季度的累计数据，用来获取业绩预告为累计值时，转换成单季度值
对齐预告期的真实财务数据，计算因子时用
数据经过上述处理，并进行对齐后的样式如下：

图片注释

'''

# 只处理净利润口径
profit_ef_df = ef_df[['ticker','publishDate','endDate','reportType','fiscalPeriod','NIncAPChgrLL','NIncAPChgrUPL','expnIncAPLL','expnIncAPUPL','expEPSLL','expEPSUPL']]

# 业绩预告数据处理，把eps预告、预告增幅等都统一换算为绝对值
stime = time.time()
print("开始取公司的历年财报数据...")
## 获取公司的财报数据
fin_df_list = []
for year in range(2007, 2023):
    enddate_start = '%s0331'%year
    enddate_end = '%s1231'%year
    fore_df = DataAPI.FdmtISGet(reportType=u"Q1,S1,CQ3,Q3,Q2,Q4,A",endDate=enddate_end,beginDate=enddate_start,pandas="1")
    fin_df_list.append(fore_df)
fin_rpt_df = pd.concat(fin_df_list, axis=0).query("mergedFlag=='1'")[['ticker','publishDate','endDate','reportType','fiscalPeriod','NIncomeAttrP']]
etime = time.time()
print("取数完成,用时:%s s"%(round(etime-stime,2)))
fin_rpt_df.head()


s_time = time.time()
ticker_list = profit_ef_df['ticker'].unique().tolist()

enddate_df = pd.DataFrame(profit_ef_df['endDate'].unique().tolist(), columns=['end_date']).sort_values(by=['end_date'])

share_df_list = []
for year in range(2007, 2023):
    share_df = DataAPI.EquSharesChgGet(ticker=ticker_list, beginDate=u"%s0101"%year,endDate=u"%s1231"%year,field=u"ticker,changeDate,totalShares",pandas="1")
    share_df_list.append(share_df)
share_df = pd.concat(share_df_list, axis=0)
print("得到股本pit的原始数据:")
print(share_df.head().to_html())

# 把一个日期转换成 >= 该日的最近的财报日期
def tranf2enddate(input_date):
    '''
    input_date:%Y-%m-%d
    '''
    input_year = input_date[:4]
    input_date = input_date[5:]
    if input_date <= '03-31':
        end_date = '%s-03-31'%input_year
    elif input_date <= '06-30':
        end_date = '%s-06-30'%input_year
    elif input_date <='09-30':
        end_date = '%s-09-30'%input_year
    else:
        end_date = '%s-12-31'%input_year
    return end_date

share_df['end_date'] = share_df['changeDate'].apply(lambda x:tranf2enddate(x))
share_df = share_df.sort_values(by=['ticker','end_date', 'changeDate'], ascending=True)
share_df = share_df.drop_duplicates(subset=['ticker','end_date'], keep='last')
share_df = share_df.groupby(['ticker']).apply(lambda x: x.merge(enddate_df,
                                                                           on=['end_date'], how='outer'))[['totalShares','end_date']]
share_df.reset_index(inplace=True)
del share_df['level_1']
share_df = share_df.sort_values(by=['ticker', 'end_date'], ascending=True)
share_df = share_df.groupby(['ticker']).apply(lambda x: x.fillna(method='ffill'))
share_df.dropna(inplace=True)
print("衍生得到会计日，股票的最新股本数据:")
print(share_df.head().to_html())
print("共耗时:%s s"%(round(time.time()-s_time, 2)))


# ## 合并财务报表
fin_rpt_df = fin_rpt_df.rename(columns={"publishDate":"rpt_publishDate"})
profit_ef_df['pre_endDate'] = profit_ef_df['endDate'].apply(lambda x: "%s%s"%(int(str(x)[:4])-1, str(x[4:])))
merge_rpt_df = fin_rpt_df.rename(columns={"publishDate":"rpt_publishDate",'endDate':"pre_endDate",'NIncomeAttrP':"pre_NIncomeAttrP"})[['ticker','rpt_publishDate','pre_endDate','pre_NIncomeAttrP','reportType']]
# ## 合并去年同期的财报值
profit_ef_df = profit_ef_df.merge(merge_rpt_df, on=['ticker','pre_endDate','reportType'],how='left').sort_values(by=['ticker','publishDate','endDate','rpt_publishDate'], ascending=True)
# ## 剔除掉去年同期数据中，发布日期在预告发布日期之后的记录
profit_ef_df = profit_ef_df.query("publishDate>=rpt_publishDate")
## 同一个预告，只保留一条记录（合并去年同期业绩最新的记录）
profit_ef_df = profit_ef_df.drop_duplicates(subset=['ticker','publishDate','endDate'], keep='last')
## 合并会计日的总股本数据
profit_ef_df = profit_ef_df.merge(share_df[['ticker','end_date','totalShares']].rename(columns={"end_date":"endDate"}),how='left')

## 根据同比增幅，计算得到当期的绝对数值
profit_ef_df['NIncLL_abs_from_growth'] = (profit_ef_df['NIncAPChgrLL']/100+1)*profit_ef_df['pre_NIncomeAttrP']
profit_ef_df['NIncUPL_abs_from_growth'] = (profit_ef_df['NIncAPChgrUPL']/100+1)*profit_ef_df['pre_NIncomeAttrP']
## 根据每股收益，计算得到当期的绝对数值
profit_ef_df['NIncLL_abs_from_EPS'] = profit_ef_df['expEPSLL']*profit_ef_df['totalShares']
profit_ef_df['NIncUPL_abs_from_EPS'] = profit_ef_df['expEPSUPL']*profit_ef_df['totalShares']
## 合并到预告净利润列
profit_ef_df['expnIncAPLL'] = profit_ef_df['expnIncAPLL'].fillna(profit_ef_df['NIncLL_abs_from_growth']).fillna(profit_ef_df['NIncLL_abs_from_EPS'])
profit_ef_df['expnIncAPUPL'] = profit_ef_df['expnIncAPUPL'].fillna(profit_ef_df['NIncUPL_abs_from_growth']).fillna(profit_ef_df['NIncUPL_abs_from_EPS'])

## 剔除掉净利润上下限都为空的情况
profit_ef_df = profit_ef_df.dropna(subset=['expnIncAPLL','expnIncAPUPL'], how='all')[['ticker','publishDate','endDate','reportType','expnIncAPLL', 'expnIncAPUPL']]

## 增加一个dummy变量，标识预告是在财报期前还是财报期后发布的
profit_ef_df['in_advance'] = np.where(profit_ef_df['publishDate']<profit_ef_df['endDate'], 0, 1)


print("预告口径对齐后的原始预告数据如下:")
print(profit_ef_df.head().to_html())
profit_ef_df.to_pickle(os.path.join(save_folder, '净利润业绩预告数据.pkl'))


# 获取x的上个季度的季度值
def get_last_enddate(x):
    '''
    x: %Y-%m-%d
    '''
    year = x[:4]
    date = x[5:]
    if date == '03-31':
        return_x = '0'
    elif date == '06-30':
        return_x = '%s-03-31' % year
    elif date == '09-30':
        return_x = '%s-06-30' % year
    elif date == '12-31':
        return_x = '%s-09-30' % year
    else:
        return_x = None
    return return_x


## 截止上个季度的累计值，用来算预测季度的单季度值
profit_ef_df['last_endDate'] = profit_ef_df['endDate'].apply(lambda x: get_last_enddate(x))
## 合并累计的财务真实值
last_fin_rpt_df = fin_rpt_df[fin_rpt_df['reportType'].isin(['Q1', 'S1', 'CQ3', 'A'])]  # 只取累计值
last_fin_rpt_df = last_fin_rpt_df[['ticker', 'rpt_publishDate', 'endDate', 'NIncomeAttrP']]
last_fin_rpt_df.columns = ['ticker', 'last_publishDate', 'last_endDate', 'last_cum_NIncomeAttrP']
profit_ef_df = profit_ef_df.merge(last_fin_rpt_df, on=['ticker', 'last_endDate'], how='left')
# 特殊处理，如果当前是单季度预告，则上个季度的日期设置为自己，以及上个季度的值设置为0
profit_ef_df['last_publishDate'] = np.where(profit_ef_df['reportType'].isin(['Q1', 'Q2', 'Q3']),
                                            profit_ef_df['publishDate'], profit_ef_df['last_publishDate'])
profit_ef_df['last_cum_NIncomeAttrP'] = np.where(profit_ef_df['reportType'].isin(['Q1', 'Q2', 'Q3']), 0,
                                                 profit_ef_df['last_cum_NIncomeAttrP'])
profit_ef_df = profit_ef_df.query('publishDate>=last_publishDate')
profit_ef_df = profit_ef_df.sort_values(by=['ticker', 'publishDate', 'endDate', 'last_publishDate'], ascending=True)
profit_ef_df = profit_ef_df.drop_duplicates(subset=['ticker', 'publishDate', 'endDate'], keep='last')
## 计算单季度的预告值
profit_ef_df['fore_inc_L'] = profit_ef_df['expnIncAPLL'] - profit_ef_df['last_cum_NIncomeAttrP']
profit_ef_df['fore_inc_H'] = profit_ef_df['expnIncAPUPL'] - profit_ef_df['last_cum_NIncomeAttrP']
profit_ef_df.head()


# 合并上单季度的真实值

print("获取股票历年单季度的PIT归母净利润值...")
stime = time.time()
## 单季度的财报真实值
q_fin_rpt_list = []
for year in range(2007, 2023):
    q_df = DataAPI.FdmtISQPIT2018Get(endDate="%s-12-31"%year,beginDate="%s-01-01"%year,isCalc=u"",isNew=u"",field=u"",pandas="1")[['ticker','publishDate','endDate','nIncomeAttrP']]
    q_fin_rpt_list.append(q_df)
q_fin_df = pd.concat(q_fin_rpt_list, axis=0)

# 每个单季报保留发布时间最早的记录
q_fin_df = q_fin_df.sort_values(by=['ticker','endDate','publishDate'], ascending=True)
q_fin_df = q_fin_df.drop_duplicates(subset=['ticker','endDate'],keep='first')
etime = time.time()
print("取数并保留最早发布日期记录，处理好后的单季度真实财务数据如下:，共耗时:%s"%(round(etime-stime,2)))
print(q_fin_df.head().to_html())

q_fin_df.columns = ['ticker','real_publishDate','endDate','real_inc']
profit_ef_df = profit_ef_df.merge(q_fin_df, on=['ticker','endDate'], how='left').query("publishDate<=real_publishDate")
profit_ef_df.to_pickle(os.path.join(save_folder, 'merged_profit_ef_df.pkl'))
print('合并单季度真实值的数据如下：')
print(profit_ef_df.head().to_html())

'''
第二部分：因子计算
该部分耗时约2分钟
计算对齐财报期、不对齐财报期口径下的 业绩预告宽度、业绩预告偏离度两类因子
从逻辑上来看，预告宽度越小/业绩预告偏离度越低的公司，公司治理能力更强，因此这些因子属于负向因子；而对于因子值为空的公司，有可能是达不到业绩预告的强制规定，公司未披露，也可能是预告了营业收入等导致在净利润类公司上因子值为空，这部分公司是否比披露质量较差的因子更差，没有明显的逻辑性，因此本部分计算时会保留值为空的记录，在后续因子测试中会对比分析应该如何处理空值 最终的因子数据格式如下： 图片注释
(深度报告版权归优矿所有，禁止直接转载或编辑后转载。)



因子1：width_same_period: 

计算业绩预告的宽度,
factor=2∗abs(预测上限值−预测下限值)abs(预测上限值)+abs(预测下限值)
在1，2，3月末，只取对去年Q3有预告的股票进行计算因子；
在4，5，6，7月末，只取对今年Q1有预告的股票计算因子；
在8，9月末，只取对今年中报有预告的股票进行计算因子；
在10，11，12月末，只取对今年Q3有预告的股票进行计算因子；
上下限有一个为空时，因子值为3；
上下限符号相反时，因子值为2；
因子2：width_latest_period: 

计算业绩预告的宽度,
factor=2∗abs(预测上限值−预测下限值)abs(预测上限值)+abs(预测下限值)
在1，2，3月末，取对今年Q1、去年Q4、去年Q3、去年Q2任意一个季度有预告的股票计算因子值（取离今最近的预告期）；
在4，5，6，7月末，取对今年Q2、今年Q1、去年Q4、去年Q3任意一个季度有预告的股票计算因子值（取离今最近的预告期）；
在8，9，10，11，12月末，取对今年Q3、今年Q2、今年Q1、去年Q4任意一个季度有预告的股票计算因子值（取离今最近的预告期）；
上下限有一个为空时，因子值为3；
上下限符号相反时，因子值为2；
因子3：bias_same_period:

计算业绩预告的偏离度，
factor=2∗abs(归母净利润真实值−归母净利润预测值)abs(归母净利润真实值)+abs(归母净利润预测值)

归母净利润预测值=归母净利润预测值上限+归母净利润预测值下限2
在1，2，3月末，只取对去年Q3有预告的股票进行计算因子；

在4，5，6，7月末，只取对今年Q1有预告的股票计算因子；

在8，9月末，只取对今年中报有预告的股票进行计算因子；

在10，11，12月末，只取对今年Q3有预告的股票进行计算因子；

上下限有一个为空时，因子值为3；

因子4：bias_latest_period:

计算业绩预告的偏离度，
factor=2∗abs(归母净利润真实值−归母净利润预测值)abs(归母净利润真实值)+abs(归母净利润预测值)
归母净利润预测值=归母净利润预测值上限+归母净利润预测值下限2
在1，2，3月末，取对今年Q1、去年Q4、去年Q3、去年Q2任意一个季度有预告的股票计算因子值（取离今最近的预告期）；
在4，5，6，7月末，取对今年Q2、今年Q1、去年Q4、去年Q3任意一个季度有预告的股票计算因子值（取离今最近的预告期）；
在8，9，10，11，12月末，取对今年Q3、今年Q2、今年Q1、去年Q4任意一个季度有预告的股票计算因子值（取离今最近的预告期）；
上下限有一个为空时，因子值为3；


'''

start_time = time.time()


def get_end_date(indate, date_type='same'):
    '''
    indate: 日期,%Y-%m-%d
    date_type:same/latest
    '''
    year = indate[:4]
    last_year = int(year) - 1
    month = indate.split("-")[1]
    if date_type == 'same':
        end_date_dict = {
            "01": "%s-09-30" % last_year,
            "02": "%s-09-30" % last_year,
            "03": "%s-09-30" % last_year,
            "04": "%s-03-31" % year,
            "05": "%s-03-31" % year,
            "06": "%s-03-31" % year,
            "07": "%s-03-31" % year,
            "08": "%s-06-30" % year,
            "09": "%s-06-30" % year,
            "10": "%s-09-30" % year,
            "11": "%s-09-30" % year,
            "12": "%s-09-30" % year,
        }
    elif date_type == 'latest':
        end_date_dict = {
            "01": ["%s-03-30" % year, "%s-06-30" % last_year],  # [最大日期，最小日期]
            "02": ["%s-03-30" % year, "%s-06-30" % last_year],
            "03": ["%s-03-30" % year, "%s-06-30" % last_year],
            "04": ["%s-06-30" % year, "%s-09-30" % last_year],
            "05": ["%s-06-30" % year, "%s-09-30" % last_year],
            "06": ["%s-06-30" % year, "%s-09-30" % last_year],
            "07": ["%s-06-30" % year, "%s-09-30" % last_year],
            "08": ["%s-09-30" % year, "%s-12-31" % last_year],
            "09": ["%s-09-30" % year, "%s-12-31" % last_year],
            "10": ["%s-09-30" % year, "%s-12-31" % last_year],
            "11": ["%s-09-30" % year, "%s-12-31" % last_year],
            "12": ["%s-09-30" % year, "%s-12-31" % last_year],
        }
    else:
        raise Exception("无效的date_type值:%s" % date_type)
    return end_date_dict[month]


print
"该部分计算因子..."
trade_df = DataAPI.TradeCalGet(exchangeCD=u"XSHG", beginDate=u"20100101", endDate='2022-12-01', isOpen=u"1", field=u"",
                               pandas="1").query("isOpen==1").query("isMonthEnd==1")
factor_list = []
for tdate in trade_df['calendarDate'].tolist():
    raw_ef_df = profit_ef_df.query("publishDate<=@tdate").sort_values(by=['ticker', 'endDate', 'publishDate'],
                                                                      ascending=True)
    # 同一报告期条件下计算因子，对应的endDate
    same_end_date = get_end_date(tdate, date_type='same')
    same_ef_df = raw_ef_df.query("endDate==@same_end_date")
    same_ef_df = same_ef_df.drop_duplicates(subset=['ticker'], keep='last')[
        ['ticker', 'fore_inc_L', 'fore_inc_H', 'real_inc']]
    # 最新报告期条件下计算因子，对应的endDate区间
    latest_max_date, latest_min_date = get_end_date(tdate, date_type='latest')
    latest_ef_df = raw_ef_df.query("endDate>=@latest_min_date and endDate<=@latest_max_date")
    latest_ef_df = latest_ef_df.drop_duplicates(subset=['ticker'], keep='last')[
        ['ticker', 'fore_inc_L', 'fore_inc_H', 'real_inc', 'in_advance']]

    ## 因子1
    same_ef_df['width_factor1'] = abs(same_ef_df['fore_inc_H'] - same_ef_df['fore_inc_L']) * 2.0 / (
                same_ef_df['fore_inc_H'].abs() + same_ef_df['fore_inc_L'].abs())
    same_ef_df['width_factor1'] = np.where(np.sign(same_ef_df['fore_inc_H']) * np.sign(same_ef_df['fore_inc_L']) < 0, 2,
                                           same_ef_df['width_factor1'])
    ## 因子2
    latest_ef_df['width_factor2'] = abs(latest_ef_df['fore_inc_H'] - latest_ef_df['fore_inc_L']) * 2.0 / (
                latest_ef_df['fore_inc_H'].abs() + latest_ef_df['fore_inc_L'].abs())
    latest_ef_df['width_factor2'] = np.where(
        np.sign(latest_ef_df['fore_inc_H']) * np.sign(latest_ef_df['fore_inc_L']) < 0, 2, latest_ef_df['width_factor2'])

    ## 因子3
    same_ef_df['bias_factor3'] = abs(
        same_ef_df['real_inc'] - same_ef_df[['fore_inc_H', 'fore_inc_L']].mean(axis=1, skipna=False)) * 2.0 / (
                                             same_ef_df['real_inc'].abs() + same_ef_df[
                                         ['fore_inc_H', 'fore_inc_L']].mean(axis=1, skipna=False).abs())
    ## 因子4
    latest_ef_df['bias_factor4'] = abs(
        latest_ef_df['real_inc'] - latest_ef_df[['fore_inc_H', 'fore_inc_L']].mean(axis=1, skipna=False)) * 2.0 / (
                                               latest_ef_df['real_inc'].abs() + latest_ef_df[
                                           ['fore_inc_H', 'fore_inc_L']].mean(axis=1, skipna=False).abs())

    factor_df = pd.concat([same_ef_df[['width_factor1', 'bias_factor3', 'ticker']].set_index('ticker'),
                           latest_ef_df[['width_factor2', 'bias_factor4', 'ticker']].set_index('ticker')],
                          axis=1).reset_index()

    factor_df['date'] = tdate
    factor_list.append(factor_df)
    # break
end_time = time.time()
all_factor_df = pd.concat(factor_list, axis=0)
all_factor_df['tradeDate'] = all_factor_df['date'].replace("-", "", regex=True)
all_factor_df = all_factor_df.rename(columns={"index": "ticker"})
all_factor_df.to_pickle(os.path.join(save_folder, 'all_factor_df.pkl'))
print
"耗时: %s seconds" % (end_time - start_time)

'''
第三部分：因子测试
该部分耗时约8分钟
该部分内容为：

3.1 回测数据准备
3.2 行业市值中性化因子测试
3.3 因子测试：测试行业市值中性化后的因子表现、填充空值+行业市值中性化后的表现、全中性的因子表现
该部分分析了各个因子的IC、ICIR、十分组表现、十分组多空组合表现等

(深度报告版权归优矿所有，禁止直接转载或编辑后转载。)

'''


sdate_backtest = '20100101'
edate_backtest = '20221130'

start_time = time.time()
cal_dates_df = DataAPI.TradeCalGet(exchangeCD=u"XSHG", beginDate=sdate_backtest, endDate=edate_backtest, field=u"", pandas="1").sort('calendarDate')
cal_dates_df['calendarDate'] = cal_dates_df['calendarDate'].apply(lambda x: x.replace('-', ''))
cal_dates_df['prevTradeDate'] = cal_dates_df['prevTradeDate'].apply(lambda x: x.replace('-', ''))
month_end_list = cal_dates_df[cal_dates_df['isMonthEnd']==1]['calendarDate'].values

# 全A投资域
a_universe_list = DataAPI.EquGet(equTypeCD=u"A",listStatusCD=u"L,S,DE",field=u"secID",pandas="1")['secID'].tolist()

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
3.2 因子测试函数

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
3.3 测试结果

'''
start_time = time.time()
print "对行业市值中性化因子进行IC测试分析和分组测试分析"

# 月末因子值
month_factor_df = all_factor_df[all_factor_df['tradeDate'].isin(month_end_list)]
# 因子方向调整
adj_factor_list = ["width_factor1","width_factor2","bias_factor3","bias_factor4"]
month_factor_df[adj_factor_list] = -month_factor_df[adj_factor_list]
print(','.join(adj_factor_list) + '为负向因子，进行方向调整')

# 行业市值中性化
factor_list = ["width_factor1","width_factor2","bias_factor3","bias_factor4"]
exclude_style_list=['BETA', 'MOMENTUM', 'EARNYILD', 'RESVOL', 'GROWTH', 'BTOP', 'LEVERAGE', 'LIQUIDTY', 'SIZENL']
pa_factor_df = factor_process(month_factor_df, factor_list, exclude_style_list=exclude_style_list)

# 因子相关性分析
_ = calc_factor_corr(pa_factor_df, factor_list)

# 进行IC测试和分组测试
ic_res, perf_df = factor_test_summary(pa_factor_df, factor_list, 10)
test_discribe(ic_res, perf_df, factor_list, annual_len=12)

end_time = time.time()
print "耗时: %s seconds" % (end_time - start_time)


'''
从上图可以看出，经过行业和市值中性处理后的四个因子都具备一定的选股作用，其中无论是因子IC表现、分组单调性、多空对冲组合的表现，预告偏离度类因子相比预告宽度类因子表现更好，更进一步，同样的因子构造逻辑下，不对齐财报期口径条件下算出的因子效果表现更好。具体来看，bias4因子表现最好，IC为2.71%，ICIR为2.94，多空对冲组合年化收益率13.4%，分组非常单调。

'''

## 如果把因子值中的NAN填充为3，测试效果
start_time = time.time()
print "对因子中NAN填充为3，再对行业市值中性化因子进行IC测试分析和分组测试分析"

# 月末因子值
month_factor_df = all_factor_df[all_factor_df['tradeDate'].isin(month_end_list)]
# 因子方向调整
adj_factor_list = ["width_factor1","width_factor2","bias_factor3","bias_factor4"]
month_factor_df[adj_factor_list] = -1*(month_factor_df[adj_factor_list].fillna(3))
print(','.join(adj_factor_list) + '为负向因子，填充空值为3，并进行方向调整')

# 行业市值中性化
factor_list = ["width_factor1","width_factor2","bias_factor3","bias_factor4"]
exclude_style_list=['BETA', 'MOMENTUM', 'EARNYILD', 'RESVOL', 'GROWTH', 'BTOP', 'LEVERAGE', 'LIQUIDTY', 'SIZENL']
pa_factor_df = factor_process(month_factor_df, factor_list, exclude_style_list=exclude_style_list)

# 因子相关性分析
_ = calc_factor_corr(pa_factor_df, factor_list)

# 进行IC测试和分组测试
ic_res, perf_df = factor_test_summary(pa_factor_df, factor_list, 10)
test_discribe(ic_res, perf_df, factor_list, annual_len=12)

end_time = time.time()
print "耗时: %s seconds" % (end_time - start_time)


'''
如果把因子中的NAN值强行用3填充后，可以看出，对于对齐财报期的因子，效果变化很大，因子方向和不填充NAN都不一样，且ICIR绝对值小于0.5,变成了一个无效的alpha因子，而对于不对齐财报期的因子，填充空值后IC分别从1.83下降到1.48，从2.71下降到2.19，虽然变差了但总体还是一个不错的alpha因子。之所以会有这些影响，主要在于预告数据不披露（如只披露营收但不披露利润）的公司虽然没有高质量披露的公司股价表现好，但也不一定比低质量披露的公司差，逻辑上没有必然关系。

'''

start_time = time.time()
print "对全中性化因子进行IC测试分析和分组测试分析"

# 月末因子值
month_factor_df = all_factor_df[all_factor_df['tradeDate'].isin(month_end_list)]
# 因子方向调整
adj_factor_list = ["width_factor1","width_factor2","bias_factor3","bias_factor4"]
month_factor_df[adj_factor_list] = -month_factor_df[adj_factor_list]
print(','.join(adj_factor_list) + '为负向因子，进行方向调整')

# 行业市值中性化
factor_list = ["width_factor1","width_factor2","bias_factor3","bias_factor4"]
exclude_style_list=[]
pa_factor_df = factor_process(month_factor_df, factor_list, exclude_style_list=exclude_style_list)

# 因子相关性分析
_ = calc_factor_corr(pa_factor_df, factor_list)

# 进行IC测试和分组测试
ic_res, perf_df = factor_test_summary(pa_factor_df, factor_list, 10)
test_discribe(ic_res, perf_df, factor_list, annual_len=12)

end_time = time.time()
print "耗时: %s seconds" % (end_time - start_time)






