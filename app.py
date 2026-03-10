import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

# Page config for professional feel
st.set_page_config(page_title="India Pro Market Analyzer", layout="wide", page_icon="💹")

# Custom CSS for a sleek look
# FIXED: Changed unsafe_allow_index to unsafe_allow_html
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_pro_data(symbol, start, end):
    try:
        # Ticker fix for Indian context
        if symbol.upper() == "NIFTY": symbol = "^NSEI"
        elif symbol.upper() == "SENSEX": symbol = "^BSESN"
        elif not symbol.startswith("^") and not symbol.endswith((".NS", ".BO")):
            symbol = f"{symbol.upper()}.NS"
            
        # Download data
        df = yf.download(symbol, start=start, end=end, auto_adjust=True)
        if df.empty: return None
        
        # FIX: Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Ensure standard columns are present and clean
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            
        df = df.reset_index()
        df['Day'] = df['Date'].dt.day_name()
        
        # Core candle logic
        df['Body_Diff'] = df['Close'] - df['Open']
        df['Candle_Type'] = ["Green" if x > 0 else "Red" for x in df['Body_Diff']]
        
        # Professional metrics
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Range'] = df['High'] - df['Low']
        
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def calculate_probability(df, day_name="Wednesday"):
    target_day = df[df['Day'] == day_name]
    if target_day.empty: return 0, 0, 0
    
    green_count = len(target_day[target_day['Candle_Type'] == "Green"])
    red_count = len(target_day[target_day['Candle_Type'] == "Red"])
    total = len(target_day)
    
    prob_green = (green_count / total) * 100 if total > 0 else 0
    return prob_green, green_count, red_count

# --- SIDEBAR ---
st.sidebar.title("🛠 Settings")
ticker_input = st.sidebar.text_input("Ticker (NIFTY, RELIANCE, TCS)", "NIFTY")
time_range = st.sidebar.selectbox("Timeline", ["Last 1 Year", "Last 3 Years", "Last 5 Years", "Max", "Custom"])

if time_range == "Custom":
    start_dt = st.sidebar.date_input("Start", value=pd.to_datetime("2020-01-01"))
    end_dt = st.sidebar.date_input("End", value=date.today())
else:
    end_dt = date.today()
    years = 1 if "1" in time_range else 3 if "3" in time_range else 5 if "5" in time_range else 20
    start_dt = end_dt - timedelta(days=years*365)

data = get_pro_data(ticker_input, start_dt, end_dt)

# --- MAIN UI ---
if data is not None:
    st.title(f"📈 {ticker_input.upper()} Professional Analysis")
    
    # Probability Score Section
    st.subheader("🎯 Basic Day Probability")
    target_day_select = st.selectbox("Select Day to Analyze", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], index=2)
    
    prob, greens, reds = calculate_probability(data, target_day_select)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"{target_day_select} Bullish Probability", f"{prob:.1f}%")
    with col2:
        st.metric(f"Total {target_day_select}s", f"{greens + reds}")
    with col3:
        trend = "Bullish Bias" if prob > 50 else "Bearish Bias" if prob < 50 else "Neutral"
        st.metric("Historical Bias", trend)

    st.divider()

    # Custom Query Section
    st.subheader("🔍 Advanced Query Engine")
    st.info("Query syntax: `Close > Open` (Green), `Close < Open` (Red), `Open > Close.shift(1)` (Gap Up)")
    user_query = st.text_input("Enter Python-style query:", value=f"Day == '{target_day_select}'")
    
    try:
        filtered_df = data.query(user_query)
        
        # Calculate Query-Specific Probability
        total_records = len(data)
        matches = len(filtered_df)
        occurrence_rate = (matches / total_records) * 100 if total_records > 0 else 0
        
        st.success(f"Found {matches} matches. This setup occurs in {occurrence_rate:.1f}% of the historical data.")
        
        # Comparison Visuals
        if not filtered_df.empty:
            st.subheader("📊 Visual Breakdown of Query Results")
            v_col1, v_col2 = st.columns(2)
            
            with v_col1:
                q_counts = filtered_df['Candle_Type'].value_counts().reset_index()
                q_counts.columns = ['Result', 'Count']
                fig_bar = px.bar(q_counts, x='Result', y='Count', color='Result', 
                                 title="Candle Type Distribution in Results",
                                 color_discrete_map={'Green': '#26a69a', 'Red': '#ef5350'})
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with v_col2:
                fig_pie = px.pie(q_counts, names='Result', values='Count', 
                                 title="Win/Loss Probability for this Query",
                                 color='Result', color_discrete_map={'Green': '#26a69a', 'Red': '#ef5350'})
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("No data matches this query.")

        # Data Preview & Download
        with st.expander("📂 View Matched Data & Download"):
            st.dataframe(filtered_df, use_container_width=True)
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download filtered data as CSV", csv, "market_analysis.csv", "text/csv")
            
    except Exception as e:
        st.error(f"Query Error: {e}")
        st.info("Ensure strings are in quotes, e.g., Day == 'Wednesday'")

else:
    st.error("No data found. Check the ticker and your internet connection.")
