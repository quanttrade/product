"""
判断低点，执行策略

有两个指标macd柱状图和boll

我们自定义底背离：
1 close 小于 10日前close
2 DEA 大于10日前 DEA


看多条件

1/股票有底背离，股票创新低，但是macd没有创新低
2/macd柱状图在两次新低之间没有大于零
3/在macd第二次低点，第二天macd没有创新低的收盘价建仓

平仓条件
1/boll中轨平一半
2/boll上轨平一半

止损条件
1/创新低止损

"""
import pandas as pd
from yq_toolsS45_linux import get_MktEqudAdjAfGet_update,MktIdxdGet


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

#boll
def calculate_bollinger_bands(df, window = 20, no_of_std = 2, column_name = ''):
    '''
    Parameters
    ----------
    df : 股价数据集
    window : 计算的周期，默认20天
    no_of_std : 标准偏差的倍数，默认2
    column_name : 股价数据集选择的列名，默认为第一列
    '''
    if column_name == '':     
        column_name = df.columns[0]  
    df['Observation']=df[column_name]
    df['RollingMean'] = df[column_name].rolling(window).mean()
    std = df[column_name].rolling(window).std(ddof=0)  
    df['UpperBound'] = df['RollingMean'] + no_of_std * std
    df['LowerBound'] = df['RollingMean'] - no_of_std * std
    #bb = df[['Observation','RollingMean','UpperBound','LowerBound']]
    #bb.plot(title='Observation with Bollinger Bands') #绘制布林带
    return df



# 指数代码，可变更后把玩。
# 如需最新的常用指数数据，请至www.quantclass.cn/data/stock/stock-main-index-data，添加数据管家-耶伦微信获取。
symbol = 'sh000300'
# 测试时间段，可根据数据时间更改
start_time = '2007-01-01'
end_time = '2099-03-31'
#'''
#df = MktIdxdGet('000300',start_time,end_time,'tradeDate,openIndex,closeIndex')
#df = get_MktEqudAdjAfGet_update('SPX',start_time,end_time,'tradeDate,openPrice as openIndex,closePrice as closeIndex')
df = MktIdxdGet('SPX',start_time,end_time,'tradeDate,openIndex,closeIndex')
df.tradeDate = df.tradeDate.astype(str)
df.sort_values(by='tradeDate',inplace = True)
#df.to_pickle('data1.pkl')
#'''
#df = pd.read_pickle('data1.pkl')
df = df[df.tradeDate>="2015-01-01"]
df.reset_index(inplace=True,drop=True)
df.rename(columns={'closeIndex': 'close', 'openIndex': 'open'}, inplace=True)
df = df[['tradeDate','open','close']]
# 0计算MACD指标
df = cal_macd(df , close = 'close')
# 计算开盘和收盘的最低价
# 3、计算顶底背离
N = 5
cond4 = df['close'] < df['close'].shift(N)  # 条件3：当前均值比上一次拐点低（股价创新低）
cond5 = df['DIF'] > df['DIF'].shift(N)  # 条件4：当前DEA比上一次拐点高（DEA创新高）
cond5_r = df['DIF'] < df['DIF'].shift(N)  # 条件4：当前DEA比上一次拐点低（DEA创新低）
cond6 = df.rolling(N).MACD.apply(lambda x:(x<0).all())
df.loc[cond4 & cond5, 'state'] = '底背离'
# macd柱状图在两次新低之间没有大于0
df['macd_sig'] = cond6
cond_buy1 = df.state =='底背离'
df.loc[cond_buy1 & (df.macd_sig==1), 'signal'] = 1  # 买入信号（底背离）
#平仓条件


pos1 = df[df.signal==1]
pos1 = pos1.index.tolist()
pos1.sort()
df['sell_sig4'] = False
df.iloc[[i+5 for i in pos1],df.columns.tolist().index('sell_sig4')] = True


calculate_bollinger_bands(df, column_name = 'close')
df['sell_sig1'] = df.close>=df.RollingMean
df['sell_sig2'] = df.close>=df.UpperBound
#止损条件 创新低止损
df.loc[cond4 & cond5_r,'sell_sig3'] = True
#df.loc[cond2 & (df.signal!=1),'sell_sig3'] = True

#df.loc[df.sell_sig3==True,'signal'] = 0
#df.loc[df.sell_sig2==True,'signal'] = 0
#df.loc[df.sell_sig1==True,'signal'] = 0
df.loc[df.sell_sig4==True,'signal'] = 0
df['r'] = df.close.pct_change()
print(df.signal.sum())
df.signal.fillna(method="ffill",inplace=True)
df.signal.fillna(0,inplace=True)

df.set_index('tradeDate',inplace=True,drop=True)
(1 + df.r*df.signal.shift(2)).cumprod().plot(rot=30)

