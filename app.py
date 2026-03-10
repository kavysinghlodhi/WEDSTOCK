import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="India Market Pro", layout="wide")

# --- DATA FETCHING ---
@st.cache_data
def get_clean_data(symbol, start, end):
    try:
        # Fetching data with auto_adjust to avoid multi-index issues
        df = yf.download(symbol, start=start, end=end, auto_adjust=True)
        if df.empty: return None
        
        # Ensure columns are flat
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.reset_index()
        df['Day'] = df['Date'].dt.day_name()
        df['Candle_Type'] = ["Green" if c > o else "Red" for o, c in zip(df['Open'], df['Close'])]
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# --- UI ---
st.sidebar.header("Analyzer Settings")
ticker_raw = st.sidebar.text_input("NSE Ticker (e.g. NIFTYBEES, SBIN)", "SBIN")
ticker = f"{ticker_raw}.NS" if not ticker_raw.endswith((".NS", ".BO")) else ticker_raw

start = st.sidebar.date_input("Start", value=pd.to_datetime("2021-01-01"))
end = st.sidebar.date_input("End", value=date.today())

data = get_clean_data(ticker, start, end)

if data is not None:
    # Filter for Wednesdays
    wed_df = data[data['Day'] == 'Wednesday'].copy()
    
    st.title(f"📊 Wednesday Deep-Dive: {ticker_raw}")
    
    # Comparisons
    green_wed = wed_df[wed_df['Candle_Type'] == "Green"]
    red_wed = wed_df[wed_df['Candle_Type'] == "Red"]
    
    # Dashboard Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Wednesdays", len(wed_df))
    m2.metric("Open < Close (Bullish)", len(green_wed))
    m3.metric("Open > Close (Bearish)", len(red_wed))

    # Automatic Visualization
    chart_tab, data_tab = st.tabs(["📈 Visualization", "📋 Raw Data"])
    
    with chart_tab:
        fig_type = st.segmented_control("Chart Style", ["Bar", "Pie"], default="Bar")
        counts = wed_df['Candle_Type'].value_counts().reset_index()
        
        if fig_type == "Bar":
            fig = px.bar(counts, x='Candle_Type', y='count', color='Candle_Type',
                         color_discrete_map={'Green': '#26a69a', 'Red': '#ef5350'})
        else:
            fig = px.pie(counts, names='Candle_Type', values='count',
                         color='Candle_Type', color_discrete_map={'Green': '#26a69a', 'Red': '#ef5350'})
        st.plotly_chart(fig, use_container_width=True)

    with data_tab:
        st.dataframe(wed_df, use_container_width=True)
        st.download_button("Download Wednesday Stats", wed_df.to_csv(), "wednesday_data.csv")
else:
    st.warning("Please enter a valid ticker and date range.")
