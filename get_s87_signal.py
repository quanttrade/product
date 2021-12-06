import pandas as pd
import numpy as np

df = pd.read_excel("G:\\github repo\\product\\s87_signal\\S87_hsce_信号.xlsx")
df.fillna(0,inplace=True)
for col in df.columns[1:]:
    df[col] = pd.to_numeric(df[col])
df.drop(columns="tradeDate", inplace=True)
#print(df)
signal1 = df.diff()
#print(signal1)
new_df = signal1.iloc[-2]
new_df = new_df[new_df != 0.0]
#new_df = new_df[new_df != -1.0]
new_df.index = [x[0:] for x in new_df.index]
new_df.index = [x+" HK Equity" for x in new_df.index]
new_df.to_csv("7.csv")
print(new_df)