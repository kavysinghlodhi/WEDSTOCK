import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="India Market Pro Analyzer", layout="wide")
st.title("🇮🇳 Indian Stock Market: Wednesday Logic Pro")

# --- SIDEBAR: Settings ---
st.sidebar.header("Configuration")
# Automatically adds .NS for NSE stocks if the user forgets
ticker_input = st.sidebar.text_input("Enter NSE Ticker (e.g., RELIANCE, SBIN, HDFCBANK)", "RELIANCE")
ticker = f"{ticker_input}.NS" if not ticker_input.endswith((".NS", ".BO")) else ticker_input

start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End Date", value=date.today())

# --- DATA LOADING ---
@st.cache_data
def get_india_data(symbol, start, end):
    df = yf.download(symbol, start=start, end=end)
    if df.empty: return df
    
    # Process Dates & Weekdays
    df = df.reset_index()
    df['Day'] = df['Date'].dt.day_name()
    # Logic: 1 if Close > Open (Green), -1 if Close < Open (Red)
    df['Candle_Type'] = df.apply(lambda x: "Green" if x['Close'] > x['Open'] else "Red", axis=1)
    return df

df = get_india_data(ticker, start_date, end_date)

if df.empty:
    st.error("No data found. Please check the ticker symbol.")
else:
    # --- ANALYSIS: Wednesday Specifics ---
    wed_data = df[df['Day'] == 'Wednesday'].copy()
    
    st.header(f"Wednesday Performance Analysis: {ticker_input}")
    
    # Calculate Stats
    green_wed = wed_data[wed_data['Candle_Type'] == "Green"]
    red_wed = wed_data[wed_data['Candle_Type'] == "Red"]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Wednesdays", len(wed_data))
    col2.metric("Green Wednesdays (Open < Close)", len(green_wed), delta_color="normal")
    col3.metric("Red Wednesdays (Open > Close)", len(red_wed), delta_color="inverse")

    # --- AUTOMATIC VISUALIZATION ---
    chart_type = st.radio("Select Visualization", ["Bar Chart", "Pie Chart"], horizontal=True)

    summary_df = wed_data['Candle_Type'].value_counts().reset_index()
    summary_df.columns = ['Result', 'Count']

    if chart_type == "Bar Chart":
        fig = px.bar(summary_df, x='Result', y='Count', color='Result',
                     color_discrete_map={'Green': '#26a69a', 'Red': '#ef5350'})
    else:
        fig = px.pie(summary_df, names='Result', values='Count', 
                     color='Result', color_discrete_map={'Green': '#26a69a', 'Red': '#ef5350'})

    st.plotly_chart(fig, use_container_width=True)

    # --- COMPARISON VIEW ---
    with st.expander("View Data Comparison Table"):
        st.subheader("Raw Wednesday Data")
        st.dataframe(wed_data[['Date', 'Open', 'Close', 'Candle_Type']])
