import pandas as pd
import numpy as np

df = pd.read_csv("G:\\github repo\\product\\s43_signal\\backup\\S43框架EA修正_signal_S43框架EA修正-全市场_csi_2021-09-08.csv")
df.fillna(0,inplace=True)
for col in df.columns[1:]:
    df[col] = pd.to_numeric(df[col])
df.drop(columns="Row", inplace=True)
#print(df)
signal1 = df.diff()
#print(signal1)
new_df = signal1.iloc[-1]
new_df = new_df[new_df != 0.0]
new_df = new_df[new_df != -1.0]
new_df.index = [x[1:] for x in new_df.index]
new_df.index = [x+" CH Equity" for x in new_df.index]
new_df.to_csv("list.csv")

print(new_df)