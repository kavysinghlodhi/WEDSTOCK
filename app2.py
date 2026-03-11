import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

# Page config for a professional data-heavy terminal feel
st.set_page_config(page_title="Trader Query Terminal", layout="wide", page_icon="📟")

# Dark Terminal CSS
st.markdown("""
    <style>
    .main { background-color: #0b0e11; }
    .stMetric { background-color: #1e2329; border-radius: 4px; padding: 15px; border-left: 5px solid #f0b90b; }
    .stTextInput>div>div>input { font-family: 'Courier New', Courier, monospace; color: #f0b90b; background-color: #2b3139; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- ADVANCED TRADING FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_terminal_data(symbol, start, end):
    try:
        # Ticker resolution
        if symbol.upper() == "NIFTY": symbol = "^NSEI"
        elif symbol.upper() == "BANKNIFTY": symbol = "^NSEBANK"
        elif not symbol.startswith("^") and not symbol.endswith((".NS", ".BO")):
            symbol = f"{symbol.upper()}.NS"
            
        df = yf.download(symbol, start=start, end=end, auto_adjust=True)
        if df.empty: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        df = df.reset_index()
        
        # --- Advanced Pre-Calculated Columns for Traders ---
        df['Day'] = df['Date'].dt.day_name()
        df['Month'] = df['Date'].dt.month_name()
        
        # Price Action Basics
        df['Body'] = df['Close'] - df['Open']
        df['Candle'] = ["Green" if x > 0 else "Red" for x in df['Body']]
        df['Prev_Close'] = df['Close'].shift(1)
        df['Gap'] = df['Open'] - df['Prev_Close']
        df['Change_Pct'] = (df['Close'] / df['Prev_Close'] - 1) * 100
        
        # Technicals for Queries
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
        df['High_Low_Range'] = df['High'] - df['Low']
        
        return df.dropna()
    except Exception as e:
        st.error(f"Data Link Failure: {e}")
        return None

# --- UI HEADER ---
st.title("📟 Trader Query Terminal")
st.caption("Advanced Logic-Based Analysis for Indian Markets")

# --- SIDEBAR: ASSET CONFIG ---
st.sidebar.title("📡 Data Stream")
ticker = st.sidebar.text_input("SYMBOL (NIFTY, BANKNIFTY, SBIN, TCS)", "NIFTY")
time_range = st.sidebar.selectbox("TIMELINE", ["Last 1 Year", "Last 3 Years", "Last 5 Years", "Max"])

# Date Calculation
end_date = date.today()
years_map = {"Last 1 Year": 1, "Last 3 Years": 3, "Last 5 Years": 5, "Max": 20}
start_date = end_date - timedelta(days=years_map[time_range]*365)

data = get_terminal_data(ticker, start_date, end_date)

# --- HELP SYSTEM ---
with st.expander("❓ How to Build Advanced Queries (Cheat Sheet)"):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        **Basic Syntax**
        - `Day == 'Wednesday'` : Only Wednesdays
        - `Candle == 'Green'` : Bullish days
        - `Close > MA20` : Above 20-day moving average
        - `Volume > Vol_MA20 * 2` : Volume breakout (2x avg)
        """)
    with col_b:
        st.markdown("""
        **Complex Logic**
        - `(Day == 'Thursday') & (Gap > 0)` : Expiry day gap-ups
        - `(Change_Pct > 2) & (Volume > Vol_MA20)` : High momentum
        - `(Month == 'October') & (Candle == 'Red')` : Bearish Octobers
        """)
    st.info("💡 Pro Tip: Use `&` for AND, `|` for OR. Always use single quotes for text.")

# --- QUERY ENGINE ---
if data is not None:
    st.subheader("⚙️ Logic Input")
    query_str = st.text_input("Enter Trader Logic Query:", value="Day == 'Wednesday' and Gap > 0")

    try:
        results = data.query(query_str).copy()
        
        # Statistics & Probability
        total = len(data)
        matches = len(results)
        prob_win = (len(results[results['Candle'] == 'Green']) / matches * 100) if matches > 0 else 0
        
        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Records", total)
        m2.metric("Matches Found", matches)
        m3.metric("Occurrence Rate", f"{(matches/total*100):.1f}%")
        m4.metric("Bullish Edge", f"{prob_win:.1f}%")

        # Visualization
        if not results.empty:
            tab1, tab2, tab3 = st.tabs(["📊 Performance Chart", "📋 Data Terminal", "📈 Distribution"])
            
            with tab1:
                # Cumulative return simulation
                results['Signal_Return'] = results['Body']
                results['Cumulative'] = results['Signal_Return'].cumsum()
                fig_perf = px.line(results, x='Date', y='Cumulative', title="Cumulative Points Capture of this Logic")
                fig_perf.update_traces(line_color='#f0b90b')
                st.plotly_chart(fig_perf, use_container_width=True)
                
            with tab2:
                st.dataframe(results.style.format(subset=['Change_Pct', 'Gap', 'Body'], formatter="{:.2f}"), use_container_width=True)
                st.download_button("💾 Export Results", results.to_csv(index=False), f"{ticker}_query_results.csv")
                
            with tab3:
                c1, c2 = st.columns(2)
                with c1:
                    # Explicitly rename columns after value_counts to avoid 'index' vs 'Candle' errors
                    candle_dist = results['Candle'].value_counts().reset_index()
                    candle_dist.columns = ['Candle_Type', 'Count']
                    
                    fig_pie = px.pie(candle_dist, names='Candle_Type', values='Count', title="Green vs Red Distribution",
                                    color='Candle_Type', color_discrete_map={'Green': '#00ffad', 'Red': '#ff5050'})
                    st.plotly_chart(fig_pie, use_container_width=True)
                with c2:
                    # Explicitly rename columns for day distribution
                    day_dist = results['Day'].value_counts().reset_index()
                    day_dist.columns = ['Day_Name', 'Count']
                    
                    fig_day = px.bar(day_dist, x='Day_Name', y='Count', 
                                    title="Frequency by Day", color='Day_Name',
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig_day, use_container_width=True)
        else:
            st.warning("⚠️ No data matches this specific logic. Try relaxing the filters.")

    except Exception as e:
        st.error(f"Syntax Error in Logic: {e}")
        st.info("Check the Help section above for correct query formatting.")

else:
    st.error("Connection failed. Ensure ticker is valid (e.g., NIFTY, SBIN).")
