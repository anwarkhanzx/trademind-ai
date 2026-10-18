import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(
page_title="TradeMind AI",
page_icon="📈",
layout="wide"
)

BASE_URL = "https://openapi.blofin.com"
PAIRS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]

st.title("📈 TradeMind AI")
st.caption("Crypto Futures Signal Dashboard")
st.warning("Educational signals only. Trades must be placed manually.")

timeframe = st.sidebar.selectbox(
"Timeframe",
["5m", "15m", "1H", "4H"],
index=1
)

selected_pairs = st.sidebar.multiselect(
"Select Coins",
PAIRS,
default=PAIRS
)

@st.cache_data(ttl=60)
def get_candles(symbol, timeframe):
url = BASE_URL + "/api/v1/market/candles"
params = {
"instId": symbol,
"bar": timeframe,
"limit": "100"
}

response = requests.get(
    url,
    params=params,
    timeout=15
)
response.raise_for_status()
result = response.json()

if result.get("code") != "0":
    raise ValueError(
        result.get("msg", "BloFin API error")
    )

rows = result.get("data", [])

if not rows:
    raise ValueError("No market data received")

df = pd.DataFrame(rows)

if df.shape[1] < 5:
    raise ValueError("Unexpected candle format")

df = df.iloc[:, :min(df.shape[1], 9)]

names = [
    "time", "open", "high", "low", "close",
    "volume", "volCurrency", "volCurrencyQuote",
    "confirm"
]
df.columns = names[:df.shape[1]]

for column in ["open", "high", "low", "close"]:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

df = df.dropna(subset=["close"])
df = df.iloc[::-1].reset_index(drop=True)

if len(df) < 51:
    raise ValueError("Insufficient candles")

return df

def analyze(df):
df = df.copy()

df["ema20"] = df["close"].ewm(
    span=20,
    adjust=False
).mean()

df["ema50"] = df["close"].ewm(
    span=50,
    adjust=False
).mean()

change = df["close"].diff()
gains = change.clip(lower=0)
losses = -change.clip(upper=0)

avg_gain = gains.ewm(
    alpha=1 / 14,
    min_periods=14,
    adjust=False
).mean()

avg_loss = losses.ewm(
    alpha=1 / 14,
    min_periods=14,
    adjust=False
).mean()

rs = avg_gain / avg_loss.replace(0, float("nan"))
df["rsi"] = 100 - (100 / (1 + rs))

last = df.iloc[-1]

price = float(last["close"])
ema20 = float(last["ema20"])
ema50 = float(last["ema50"])

rsi = (
    float(last["rsi"])
    if pd.notna(last["rsi"])
    else 50.0
)

signal = "WAIT"
reason = "Conditions not confirmed"

if ema20 > ema50 and 50 < rsi < 70:
    signal = "BUY"
    reason = "Bullish EMA trend and RSI confirmation"

elif ema20 < ema50 and 30 < rsi < 50:
    signal = "SELL"
    reason = "Bearish EMA trend and RSI confirmation"

stop_loss = None
take_profit = None

if signal == "BUY":
    stop_loss = price * 0.99
    take_profit = price * 1.02

elif signal == "SELL":
    stop_loss = price * 1.01
    take_profit = price * 0.98

return {
    "price": price,
    "ema20": ema20,
    "ema50": ema50,
    "rsi": rsi,
    "signal": signal,
    "reason": reason,
    "sl": stop_loss,
    "tp": take_profit
}

if st.button("Refresh Market Data"):
st.cache_data.clear()

st.caption(
"Updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
)

if not selected_pairs:
st.info("Select at least one coin from the sidebar.")

for symbol in selected_pairs:
st.divider()
st.subheader(symbol)

try:
    candles = get_candles(symbol, timeframe)
    data = analyze(candles)

    col1, col2, col3 = st.columns(3)

    col1.metric("Last Candle Close", f'{data["price"]:,.4f}')
    col2.metric("RSI (14)", f'{data["rsi"]:.2f}')
    col3.metric("Signal", data["signal"])

    st.write("**Reason:**", data["reason"])

    col4, col5 = st.columns(2)
    col4.metric("EMA 20", f'{data["ema20"]:,.4f}')
    col5.metric("EMA 50", f'{data["ema50"]:,.4f}')

    if data["signal"] != "WAIT":
        col6, col7, col8 = st.columns(3)

        col6.metric("Entry Reference", f'{data["price"]:,.4f}')
        col7.metric("Stop Loss", f'{data["sl"]:,.4f}')
        col8.metric("Take Profit", f'{data["tp"]:,.4f}')

        st.info(
            "Illustrative 1:2 risk/reward levels. "
            "Verify the setup before trading."
        )
    else:
        st.info("WAIT: No confirmed setup.")

except Exception as error:
    st.error("Could not load " + symbol + ": " + str(error))

st.divider()
st.subheader("Risk Disclaimer")

st.write(
"This experimental rule-based scanner does not guarantee profit. "
"The API endpoint and candle format must be verified. "
"Test with historical data and paper trading before using real money. "
"Fees, slippage and leverage affect results. "
"This website does not execute trades."
)
