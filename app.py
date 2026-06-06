import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime

st.set_page_config(
    page_title="Euphoria Terminal AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Kustomisasi CSS
st.markdown("""
    <style>
    .stApp { background-color: #05080f; color: #e2e8f0; }
    .kpi-card { background-color: #0a0e17; border: 1px solid #1e293b; padding: 15px; border-radius: 8px; text-align: center; }
    .kpi-value { font-size: 20px; font-weight: bold; color: #3b82f6; }
    .kpi-label { font-size: 11px; color: #64748b; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def fetch_real_market_data(ticker):
    # Mengambil data 2022-2024
    ticker_symbol = f"{ticker}.JK"
    df = yf.download(ticker_symbol, start="2022-01-01", end="2024-12-31", progress=False)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df = df.reset_index()
    # Pastikan kolom Date ada
    if 'Date' not in df.columns:
        df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
    
    # Indikator
    df['MA20'] = df['Close'].rolling(window=20).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Simulasi data Tweet/Sentimen (Placeholder Riset)
    df['tweet_count'] = np.random.randint(10, 100, size=len(df))
    df['is_euphoric'] = 0
    df['prob'] = np.random.uniform(0.0, 0.5, size=len(df))
    
    # Anomali simulasi untuk demo
    spike_indices = np.random.choice(df.index, 5, replace=False)
    df.loc[spike_indices, 'tweet_count'] = np.random.randint(500, 2000, size=5)
    df.loc[spike_indices, 'is_euphoric'] = 1
    df.loc[spike_indices, 'prob'] = np.random.uniform(0.8, 0.99, size=5)
    
    return df

tickers_list = ['KARW', 'FORU', 'SRAJ', 'PANI', 'DSSA', 'SGER', 'TPIA', 'BRMS', 'MLPT', 'BRPT', 'TOBA', 'AUTO', 'IMAS', 'PSAB', 'KONI']

st.markdown("### ⚡ EuphoriaTerminal <span style='color:#64748b; font-size:14px'>Pro Analytics v3.0</span>", unsafe_allow_html=True)

selected_ticker = st.selectbox("Pilih Saham", tickers_list)
df = fetch_real_market_data(selected_ticker)

# Layout Grafik 4 Row
fig = make_subplots(rows=4, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.03, 
                    row_heights=[0.4, 0.2, 0.2, 0.2])

# Row 1: Candlestick
fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], name="MA20", line=dict(color='orange', width=1)), row=1, col=1)

# Row 2: Stock Volume
fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name="Stock Vol", marker_color='gray'), row=2, col=1)

# Row 3: Tweet Volume
fig.add_trace(go.Bar(x=df['Date'], y=df['tweet_count'], name="Tweet Vol", marker_color='indigo'), row=3, col=1)

# Row 4: RSI
fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name="RSI", line=dict(color='cyan', width=1)), row=4, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=4, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=4, col=1)

fig.update_layout(
    plot_bgcolor='#0a0e17', paper_bgcolor='#0a0e17', font_color='#e2e8f0',
    height=800, margin=dict(l=0, r=0, t=20, b=0),
    xaxis_rangeslider_visible=False,
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
```

**Tips untuk GitHub:**
*   Jangan lupa untuk memutakhirkan `requirements.txt` Anda dengan `yfinance` agar *server* Streamlit Cloud bisa menarik data bursa.
*   Jika Anda memiliki file CSV data asli Anda sendiri, Anda bisa mengganti fungsi `fetch_real_market_data` di atas dengan `pd.read_csv('data_anda.csv')` dan menyesuaikan kolomnya agar hasil prediksinya lebih akurat.
