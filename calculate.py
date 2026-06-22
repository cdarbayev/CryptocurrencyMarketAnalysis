import numpy as np
import pandas as pd


def calculate_metrics(df, ma_fast=7, ma_slow=30):
    # Calculating
    if df.empty or len(df) < ma_slow:
        #If not enough data, return what we have to avoid error
        return df

    # Sort by date(just in case :D )
    df = df.sort_values("timestamp").reset_index(drop=True)

    # 1)Daily Return
    df["daily_return"] = df["close"].pct_change() * 100

    # 2)Moving Averages
    df["ma_fast"] = df["close"].rolling(window=ma_fast).mean()
    df["ma_slow"] = df["close"].rolling(window=ma_slow).mean()

    # 3) Volatility
    df["volatility_7d"] = df["daily_return"].rolling(window=ma_fast).std()

    return df


# Check locally
if __name__ == "__main__":
    from app import fetch_crypto_data

    df_raw = fetch_crypto_data(symbol="BTCUSDT", limit=100)
    df_analyzed = calculate_metrics(df_raw)

    print(df_analyzed[["timestamp", "close", "daily_return", "ma_fast", "volatility_7d"]].tail(5))