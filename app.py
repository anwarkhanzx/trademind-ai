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
st.info("Rule-based signals for analysis only. Trades are placed manually.")

st.sidebar.header("Settings")

timeframe = st.sidebar.selectbox(
"Timeframe",
["5m", "15m", "1H", "4H"],
index=1
)

selected_pairs = st.sidebar.multiselect(
"Trading Pairs",
PAIRS,
default=PAIRS
)

if st.sidebar.button("🔄 Refresh Market Data"):
st.cache_data.clear()
st.rerun()

@st.cache_data(ttl=60)
def get_candles(symbol, timeframe):
url = f"{BASE_URL}/api/v1/market/candles"

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
        result.get("msg", "Market data unavailable")
    )

rows = result.get("data", [])

if not rows:
    raise ValueError("No candle data received")

columns = [
    "time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "volCurrency",
    "volCurrencyQuote",
    "confirm"
]

df = pd.DataFrame(rows)

if df.shape[1] < 5:
    raise ValueError("Unexpected candle data format")

df = df.iloc[:, :min(len(columns), df.shape[1])]
df.columns = columns[:df.shape[1]]

for col in ["open", "high", "low", "close"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["close"])
df = df.iloc[::-1].reset_index(drop=True)

if len(df) < 51:
    raise ValueError("Not enough candles for EMA analysis")

return df

def analyze_market(df):
df = df.copy()

df["ema20"] = df["close"].ewm(
    span=20,
    adjust=False
).mean()

df["ema50"] = df["close"].ewm(
    span=50,
    adjust=False
).mean()

delta = df["close"].diff()

gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.ewm(
    alpha=1 / 14,
    min_periods=14,
    adjust=False
).mean()

avg_loss = loss.ewm(
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
reason = "No confirmed setup"

if ema20 > ema50 and 50 < rsi < 70:
    signal = "BUY"
    reason = "EMA20 above EMA50 and RSI bullish"

elif ema20 < ema50 and 30 < rsi < 50:
    signal = "SELL"
    reason = "EMA20 below EMA50 and RSI bearish"

entry = price
sl = None
tp = None

if signal == "BUY":
    sl = entry * 0.99
    tp = entry * 1.02

elif signal == "SELL":
    sl = entry * 1.01
    tp = entry * 0.98

return {
    "price": price,
    "ema20": ema20,
    "ema50": ema50,
    "rsi": rsi,
    "signal": signal,
    "reason": reason,
    "entry": entry,
    "sl": sl,
    "tp": tp
}

st.caption(
"Page generated at: "
+ datetime.now().strftime("%Y-%m-%d %H:%M:%S")
)

if not selected_pairs:
st.warning("Select at least one trading pair.")

for symbol in selected_pairs:
st.divider()
st.subheader(symbol)

try:
    candles = get_candles(symbol, timeframe)
    result = analyze_market(candles)

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Last Candle Close",
        f'{result["price"]:,.4f}'
    )

    c2.metric(
        "RSI (14)",
        f'{result["rsi"]:.2f}'
    )

    c3.metric(
        "Signal",
        result["signal"]
    )

    st.write("**Analysis:**", result["reason"])

    a, b, c = st.columns(3)

    a.metric("EMA 20", f'{result["ema20"]:,.4f}')
    b.metric("EMA 50", f'{result["ema50"]:,.4f}')

    if result["signal"] != "WAIT":
        st.subheader("Trade Setup")

        x, y, z = st.columns(3)

        x.metric(
            "Entry Reference",
            f'{result["entry"]:,.4f}'
        )

        y.metric(
            "Stop Loss",
            f'{result["sl"]:,.4f}'
        )

        z.metric(
            "Take Profit",
            f'{result["tp"]:,.4f}'
        )

        st.warning(
            "Verify the setup before trading. "
            "These are illustrative price levels, "
            "not guaranteed profitable signals."
        )

    else:
        st.info("WAIT: No setup confirmed by this strategy.")

except Exception as error:
    st.error(
        f"Could not load {symbol}: {error}"
    )

st.divider()

st.subheader("⚠️ Risk Disclaimer")

st.write(
"This is an experimental rule-based signal dashboard, "
"not a guarantee of profit. The market data endpoint and "
"response format must be verified. Signals may be wrong. "
"Backtest and paper-trade before risking real money. "
"Fees, slippage and leverage affect results. "
"No trades are executed by this website."
)
