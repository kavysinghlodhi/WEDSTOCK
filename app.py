import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

# --- SETTINGS & THEME ---
st.set_page_config(page_title="QuantSearch Terminal v2.0", layout="wide", page_icon="🔍")

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    [data-testid="stMetricValue"] { color: #f0b90b; font-family: 'Courier New'; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #161b22; border-radius: 4px; padding: 10px; color: white; }
    .stTabs [aria-selected="true"] { background-color: #f0b90b !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE CORE ---
@st.cache_data(ttl=3600)
def fetch_and_process(symbol, period="2y"):
    try:
        # Ticker Normalization
        if symbol.upper() == "NIFTY": symbol = "^NSEI"
        elif symbol.upper() == "BANKNIFTY": symbol = "^NSEBANK"
        elif not symbol.startswith("^") and not symbol.endswith((".NS", ".BO")):
            symbol = f"{symbol.upper()}.NS"
            
        df = yf.download(symbol, period=period, interval="1d", auto_adjust=True)
        if df.empty: return None
        
        # Clean MultiIndex if it exists
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # --- TECHNICAL INDICATOR ENGINE (pandas_ta) ---
        df.ta.strategy(ta.CommonStrategy) # Adds RSI, MACD, SMA, EMA, Bollinger, etc.
        
        # Custom Trading Columns
        df['Body_Pct'] = ((df['Close'] - df['Open']) / df['Open']) * 100
        df['Day'] = df.index.day_name()
        df['Month'] = df.index.month_name()
        df['Candle'] = df['Body_Pct'].apply(lambda x: 'Green' if x > 0 else 'Red')
        df['Gap_Pct'] = ((df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
        
        # Cleanup column names for easier querying
        df.columns = [c.replace('RSI_14', 'RSI').replace('BBP_20_2.0', 'BB_Pct').replace('MACDh_12_26_9', 'MACD_Hist') for c in df.columns]
        
        return df.dropna().reset_index()
    except Exception as e:
        return None

# --- UI COMPONENTS ---
st.title("🔍 QuantSearch: Trader's Logic Engine")
st.caption("2026 Edition | Full-Spectrum Market Analysis via Boolean Logic")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📡 Command Center")
    mode = st.radio("Search Mode", ["Single Asset Scan", "Multi-Ticker Screener"])
    
    if mode == "Single Asset Scan":
        ticker = st.text_input("SYMBOL", "NIFTY")
    else:
        ticker_list = st.text_area("TICKER LIST (Comma separated)", "RELIANCE, TCS, INFY, SBIN, HDFCBANK, AXISBANK, ICICIBANK").split(",")
    
    timeline = st.selectbox("LOOKBACK", ["2y", "5y", "10y", "max"], index=0)

# --- HELP DICTIONARY ---
with st.expander("📖 Logic Dictionary (Query Cheat Sheet)"):
    t1, t2, t3 = st.tabs(["Momentum", "Volatility", "Trend"])
    with t1:
        st.code("""
# RSI Logic
RSI < 30 (Oversold)
RSI > 70 (Overbought)

# MACD Logic
MACD_Hist > 0 (Bullish Momentum)
MACD_Hist < MACD_Hist.shift(1) (Momentum Fading)
        """, language="python")
    with t2:
        st.code("""
# Bollinger Bands
Close > BBU_20_2.0 (Above Upper Band)
Close < BBL_20_2.0 (Below Lower Band)

# Gap Analysis
Gap_Pct > 1.5 (Gap up more than 1.5%)
        """, language="python")
    with t3:
        st.code("""
# Moving Averages
Close > SMA_50 (Short-term uptrend)
SMA_50 > SMA_200 (Golden Cross)
        """, language="python")

# --- EXECUTION ENGINE ---
query = st.text_input("⌨️ Search Logic Input:", value="(RSI < 35) & (Body_Pct > 0.5)")

if mode == "Single Asset Scan":
    data = fetch_and_process(ticker, period=timeline)
    if data is not None:
        try:
            results = data.query(query)
            
            # Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Matches", f"{len(results)}")
            c2.metric("Hit Rate", f"{(len(results)/len(data)*100):.1f}%")
            
            # Charting
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name='Price', line=dict(color='gray', width=1)))
            fig.add_trace(go.Scatter(x=results['Date'], y=results['Close'], mode='markers', name='Query Match', marker=dict(color='#f0b90b', size=8)))
            fig.update_layout(template="plotly_dark", title=f"Visualizing Matches on {ticker}")
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(results, use_container_width=True)
        except Exception as e:
            st.error(f"Syntax Error: {e}")

else: # Multi-Ticker Screener
    if st.button("🚀 Run Market Scan"):
        screener_results = []
        progress = st.progress(0)
        for i, t in enumerate(ticker_list):
            stock_data = fetch_and_process(t.strip())
            if stock_data is not None:
                # Check if the LAST row matches the logic
                try:
                    match = stock_data.query(query).tail(1)
                    if not match.empty:
                        match['Ticker'] = t.strip()
                        screener_results.append(match)
                except: pass
            progress.progress((i + 1) / len(ticker_list))
        
        if screener_results:
            final_df = pd.concat(screener_results)
            st.success(f"Found {len(final_df)} stocks matching your logic!")
            st.dataframe(final_df[['Ticker', 'Date', 'Close', 'RSI', 'Body_Pct']], use_container_width=True)
        else:
            st.warning("No stocks currently match this logic.")

st.markdown("---")
st.info("💡 **Pro Tip:** Combine technicals with time logic: `(RSI < 40) & (Day == 'Monday')` to see if Monday blues offer buying opportunities.")
