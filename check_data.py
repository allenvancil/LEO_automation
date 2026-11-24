import pandas as pd

df = pd.read_csv('../data/DA_10MHz_squar_10-20prev.csv')
df = pd.DataFrame(df)
col = df.columns
print(col)
for i in range(len(col)):
    print(i, col[i])