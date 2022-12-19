"""
判断低点，执行策略
"""

import pandas as pd
from yq_toolsS45_linux import MktIdxdGet


pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数

# 封装MACD计算函数，方便后续调用
def cal_macd(df_ma, short=12, long=26, dea=9, close='收盘价_复权'):
    df_ma['EMA_short'] = df_ma[close].ewm(span=short, adjust=False).mean()
    df_ma['EMA_long'] = df_ma[close].ewm(span=long, adjust=False).mean()
    df_ma['DIF'] = df_ma['EMA_short'] - df_ma['EMA_long']
    df_ma['DEA'] = df_ma['DIF'].ewm(span=dea, adjust=False).mean()
    df_ma['MACD'] = (df_ma['DIF'] - df_ma['DEA']) * 2
    del df_ma['EMA_short'], df_ma['EMA_long']
    return df_ma

# 将高点时间段定为30日，可自己修改参数把玩
days = 30  # 计算均线和斜率的时候需要的
# 后续计算N日后涨跌幅所需参数
day_list = [1, 5, 10, 20]
# 指数代码，可变更后把玩。
# 如需最新的常用指数数据，请至www.quantclass.cn/data/stock/stock-main-index-data，添加数据管家-耶伦微信获取。
symbol = 'sh000300'
# 测试时间段，可根据数据时间更改
start_time = '2007-01-01'
end_time = '2099-03-31'

#'''
df = MktIdxdGet('000001',start_time,end_time,'tradeDate,openIndex,closeIndex')
df.tradeDate = df.tradeDate.astype(str)
df.sort_values(by='tradeDate',inplace = True)
#df.to_pickle('data1.pkl')
#'''
#df = pd.read_pickle('data1.pkl')
df.rename(columns={'closeIndex': 'close', 'openIndex': 'open', 'tradeDate': 'candle_end_time'}, inplace=True)
df = df[['candle_end_time','open','close']]
# 0计算MACD指标
df = cal_macd(df , close = 'close')
# 计算开盘和收盘的最低价
df['min'] = df[['open', 'close']].min(axis=1)
# 谷值条件：min小于前后两天，且小于最近30天所有的min
df.loc[(df['min'].shift(1) < df['min']) & (df['min'].shift(1) < df['min'].shift(2)) & (
        df['min'].shift(1) == df['min'].rolling(days).min()), 'price_new_low'] = 1
# 计算DIF高低点
df.loc[df['DIF'] == df['DIF'].rolling(days).max(), 'DIF_new_high'] = 1
df.loc[df['DIF'] == df['DIF'].rolling(days).min(), 'DIF_new_low'] = 1
# 记录前后的高低点
df.loc[df['price_new_low'] == 1, 'last_valley_price'] = df['close']
df.loc[df['price_new_low'] == 1, 'last_valley_dif'] = df['DIF']
# 2.3、填充空值 & 取前值
df['last_peak_price'].fillna(method='ffill', inplace=True)
df['last_peak_dif'].fillna(method='ffill', inplace=True)
df['last_peak_price'] = df['last_peak_price'].shift(1)
df['last_peak_dif'] = df['last_peak_dif'].shift(1)
df['last_valley_price'].fillna(method='ffill', inplace=True)
df['last_valley_dif'].fillna(method='ffill', inplace=True)
df['last_valley_price'] = df['last_valley_price'].shift(1)
df['last_valley_dif'] = df['last_valley_dif'].shift(1)
# 3、计算顶底背离
cond1 = df['price_new_high'] == 1  # 条件1：在拐点处判断
cond2 = df['price_new_low'] == 1
cond3 = df['close'] > df['last_peak_price']  # 条件2：当前均值比上一次拐点高（股价创新高）
cond4 = df['close'] < df['last_valley_price']  # 条件3：当前均值比上一次拐点低（股价创新低）
cond5 = df['DIF'] > df['last_valley_dif']  # 条件4：当前DEA比上一次拐点高（DEA创新高）
cond6 = df['DIF'] < df['last_peak_dif']  # 条件4：当前DEA比上一次拐点低（DEA创新低）

df.loc[cond1 & cond3 & cond6, 'state'] = '顶背离'
df.loc[cond2 & cond4 & cond5, 'state'] = '底背离'
df.loc[cond1 & cond3 & cond6, 'signal'] = 0  # 卖出信号（顶背离）
df.loc[cond2 & cond4 & cond5, 'signal'] = 1  # 买入信号（底背离）

# 计算N日后涨跌幅，统计涨跌幅>0时间段
for day in day_list:
    df['%s日后涨跌幅' % day] = df['close'].shift(0 - day) / df['close'] - 1
    df['%s日后是否上涨' % day] = df['%s日后涨跌幅' % day] > 0
    df['%s日后是否上涨' % day].fillna(value=False, inplace=True)

v=df.loc[df.signal.shift(3)==1,'%s日后涨跌幅' % 5]
(1+v).cumprod().plot()

