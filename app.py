import streamlit as st

st.set_page_config(
page_title="TradeMind AI",
page_icon="📈",
layout="wide"
)

st.title("📈 TradeMind AI")
st.caption("Crypto Futures Signal Dashboard")

st.sidebar.header("Settings")

symbol = st.sidebar.selectbox(
"Trading Pair",
["BTC-USDT", "ETH-USDT", "SOL-USDT"]
)

timeframe = st.sidebar.selectbox(
"Timeframe",
["5m", "15m", "1h"]
)

st.subheader(f"{symbol} | {timeframe}")

col1, col2, col3 = st.columns(3)

col1.metric("Market Trend", "WAIT")
col2.metric("RSI (14)", "--")
col3.metric("Signal", "WAIT")

st.info(
"Market data connect hone ke baad yahan "
"BUY / SELL signals aur technical analysis dikhega."
)

st.subheader("Trade Setup")

col1, col2, col3 = st.columns(3)

col1.write("Entry Price")
col1.write("Waiting for market data")

col2.write("Stop Loss")
col2.write("--")

col3.write("Take Profit")
col3.write("--")

st.warning(
"Demo dashboard: abhi live market data ya "
"verified trading signals available nahi hain."
)
