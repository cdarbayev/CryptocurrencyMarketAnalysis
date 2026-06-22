import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
import streamlit as st

sns.set_theme(style="darkgrid")


#1: getting data
@st.cache_data  # cashe, so we not spam
def fetch_crypto_data(symbol, interval="1d", limit=150):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        raw_data = response.json()
    except Exception as e:
        st.error(f"Error of getting data: {e}")
        return pd.DataFrame()

    columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "q_av",
        "num_trades",
        "taker_base",
        "taker_quote",
        "ignore",
    ]
    df = pd.DataFrame(raw_data, columns=columns)
    df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df


#2: Analytics
def calculate_metrics(df, ma_fast=7, ma_slow=30):
    if df.empty or len(df) < ma_slow:
        return df
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["daily_return"] = df["close"].pct_change() * 100
    df["ma_fast"] = df["close"].rolling(window=ma_fast).mean()
    df["ma_slow"] = df["close"].rolling(window=ma_slow).mean()
    df["volatility_7d"] = df["daily_return"].rolling(window=ma_fast).std()
    return df


#3: Streamlit interface
st.title("📈 Cryptocurrency Market Analysis")

# Sidebar
st.sidebar.header("Settings")
ticker = st.sidebar.selectbox(
    "Choose your currency:", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
)
days = st.sidebar.slider("Number of days for analysis:", 40, 150, 100)

# Loading
with st.spinner("Loading data from the API..."):
    df_raw = fetch_crypto_data(symbol=ticker, limit=days)
    df = calculate_metrics(df_raw)

if not df.empty:
    # Print actual widgets and metrics
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    price_diff = last_row["close"] - prev_row["close"]

    col1, col2, col3 = st.columns(3)
    col1.metric(label="Current price", value=f"${last_row['close']:.2f}", delta=f"{price_diff:.2f}$")
    col2.metric(label="Daily return", value=f"{last_row['daily_return']:.2f}%")
    col3.metric(label="Volatility (7d)", value=f"{last_row['volatility_7d']:.2f}%")

    st.subheader("Price and Moving Average")

    # Graph
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=df, x="timestamp", y="close", ax=ax, label="Closing price", color="blue", lw=2)
    sns.lineplot(data=df, x="timestamp", y="ma_fast", ax=ax, label="Fast MA (7 days)", color="orange", linestyle="--")
    sns.lineplot(data=df, x="timestamp", y="ma_slow", ax=ax, label="Slow MA (30 days)", color="red", linestyle=":")

    ax.set_title(f"Trends for {ticker}", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)

    #4: Export to Parquet
    st.subheader("Data Export")

    # Convert a DataFrame to Parquet in memory (to a byte stream)
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    # Download button
    st.download_button(
        label="📥 Download the dataset in Parquet format",
        data=buffer,
        file_name=f"{ticker}_analytics.parquet",
        mime="application/octet-stream"
    )

    # Table under graph
    st.subheader("Raw analytical data")
    st.dataframe(df.tail(10))
else:
    st.error("Unable to display the data")