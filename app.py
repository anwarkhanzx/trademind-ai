import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(
page_title="TradeMind AI",
page_icon="📈",
layout="wide"
)

st.title("📈 TradeMind AI")
st.caption("Crypto Futures Market Scanner | Manual Trading Signals")

BASE_URL = "https://openapi.blofin.com"

PAIRS = {
"BTC-USDT": "BTC-USDT",
"ETH-USDT": "ETH-USDT",
"SOL-USDT": "SOL-USDT"
}

@st.cache_data(ttl=60)
def get_candles(symbol, timeframe):
url = f"{BASE_URL}/api/v1/market/candles"
params = {
"instId": symbol,
"bar": timeframe,
"limit": "100"
}

response = requests.get(url, params=params, timeout=15)
response.raise_for_status()
result = response.json()

if result.get("code") != "0":
    raise ValueError(result.get("msg", "Market data unavailable"))

rows = result.get("data", [])
if not rows:
    raise ValueError("No candle data received")

df = pd.DataFrame(
    rows,
    columns=[
        "time", "open", "high", "low",
        "close", "volume", "volCurrency",
        "volCurrencyQuote", "confirm"
    ][:len(rows[0])]
)

df["close"] = pd.to_numeric(df["close"])
df["high"] = pd.to_numeric(df["high"])
df["low"] = pd.to_numeric(df["low"])

return df.iloc[::-1].reset_index(drop=True)

def analyze(df):
df = df.copy()

df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

delta = df["close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

rs = avg_gain / avg_loss.replace(0, float("nan"))
df["rsi"] = 100 - (100 / (1 + rs))

last = df.iloc[-1]
price = float(last["close"])
rsi = float(last["rsi"]) if pd.notna(last["rsi"]) else 50.0

signal = "WAIT"
reason = "Trend confirmation nahi mila"

if last["ema20"] > last["ema50"] and 50 < rsi < 70:
    signal = "BUY"
    reason = "EMA20 above EMA50; RSI bullish zone"
elif last["ema20"] < last["ema50"] and 30 < rsi < 50:
    signal = "SELL"
    reason = "EMA20 below EMA50; RSI bearish zone"

if signal == "BUY":
    sl = price * 0.99
    tp = price * 1.02
elif signal == "SELL":
    sl = price * 1.01
    tp = price * 0.98
else:
    sl = None
    tp = None

return price, rsi, signal, reason, sl, tp

st.sidebar.header("Scanner Settings")

timeframe = st.sidebar.selectbox(
"Timeframe",
["5m", "15m", "1H", "4H"],
index=1
)

if st.sidebar.button("🔄 Refresh Market Data"):
st.cache_data.clear()

st.caption(
f"Last page refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

for symbol in PAIRS:
st.divider()
st.subheader(symbol)

try:
    candles = get_candles(symbol, timeframe)
    price, rsi, signal, reason, sl, tp = analyze(candles)

    c1, c2, c3 = st.columns(3)
    c1.metric("Last Candle Close", f"{price:,.4f}")
    c2.metric("RSI (14)", f"{rsi:.2f}")
    c3.metric("Strategy Signal", signal)

    st.write("**Analysis:**", reason)

    if signal != "WAIT":
        a, b, c = st.columns(3)
        a.metric("Entry Reference", f"{price:,.4f}")
        b.metric("Stop Loss", f"{sl:,.4f}")
        c.metric("Take Profit", f"{tp:,.4f}")
        st.info("Illustrative 1:2 risk/reward levels. Verify before trading.")
    else:
        st.warning("No confirmed setup. Wait for another opportunity.")

except Exception as e:
    st.error(f"Market data load nahi hua: {e}")

st.divider()
st.subheader("⚠️ Risk Disclaimer")
st.write(
"Ye educational rule-based scanner hai, guaranteed AI prediction nahi. "
"Signals ko pehle backtest aur demo par verify karein. "
"Trading fees, slippage aur leverage se results badal sakte hain. "
"Orders manually place karein; is website se koi trade execute nahi hota."
)
