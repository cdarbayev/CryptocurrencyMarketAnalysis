import pandas as pd

# Reading in DataFrame
df = pd.read_parquet("BTCUSDT_analytics.parquet")
print(df.tail())