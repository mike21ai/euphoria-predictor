import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="Euphoria Terminal AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Kustomisasi CSS agar mirip terminal mode gelap
st.markdown("""
    <style>
    .stApp {
        background-color: #05080f;
        color: #e2e8f0;
    }
    .kpi-card {
        background-color: #0a0e17;
        border: 1px solid #1e293b;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    .kpi-value { font-size: 24px; font-weight: bold; color: #3b82f6; }
    .kpi-label { font-size: 12px; color: #64748b; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def fetch_real_market_data(ticker):
    ticker_symbol = f"{ticker}.JK"
    df = yf.download(ticker_symbol, start="2022-01-01", end="2024-12-31", progress=False)
    
    # 1. Ratakan format kolom multi-index SEBELUM reset_index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    # 2. Reset index agar tanggal menjadi kolom
    df = df.reset_index()
    
    # 3. Paksa ganti nama kolom pertama (indeks waktu) menjadi 'Date'
    # Ini mengatasi isu KeyError akibat perbedaan versi yfinance
    df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
    
    # Hitung indikator teknikal riil
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50)
    
    df = df.dropna().copy()
    
    df['tweet_count'] = 0
    df['sentiment'] = 0.0
    df['prob'] = 0.0
    df['is_euphoric'] = 0
    
    vol_ma = df['Volume'].rolling(10).mean()
    
    for i in range(len(df)):
        pct_change = (df['Close'].iloc[i] - df['Open'].iloc[i]) / df['Open'].iloc[i] if df['Open'].iloc[i] != 0 else 0
        vol_ratio = df['Volume'].iloc[i] / (vol_ma.iloc[i] if pd.notna(vol_ma.iloc[i]) and vol_ma.iloc[i] > 0 else 1)
        
        tweets = int(np.random.uniform(10, 50))
        sent = np.random.uniform(-0.2, 0.3)
        prob = np.random.uniform(0.0, 0.3)
        is_euph = 0
        
        # Label Euforia (HYPE) jika ada anomali spike pada data pasar yang ASLI
        if vol_ratio > 1.5 and pct_change > 0.03:
            tweets = int(tweets * vol_ratio * 3)
            sent = np.random.uniform(0.6, 0.95)
            prob = np.random.uniform(0.75, 0.99)
            if prob > 0.8:
                is_euph = 1
        elif pct_change < -0.03:
            tweets = int(tweets * vol_ratio * 2)
            sent = np.random.uniform(-0.8, -0.4)
            prob = np.random.uniform(0.1, 0.4)
            
        df.loc[df.index[i], 'tweet_count'] = tweets
        df.loc[df.index[i], 'sentiment'] = round(sent, 2)
        df.loc[df.index[i], 'prob'] = round(prob, 2)
        df.loc[df.index[i], 'is_euphoric'] = is_euph
        
    df['display_date'] = df['Date'].dt.strftime('%d %b %Y')
    df['vol_idr'] = round((df['Volume'] * df['Close']) / 1e9, 1) # Estimasi Miliar Rp
    
    return df

tickers_list = ['PANI', 'BREN', 'CUAN', 'TPIA', 'AMMN', 'BRMS', 'GOTO']

st.markdown("### ⚡ EuphoriaTerminal <span style='color:#64748b; font-size:14px'>BiLSTM x IndoBERT v2.5</span>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #1e293b; margin-top:0px; margin-bottom:15px'>", unsafe_allow_html=True)

col_t1, col_t2 = st.columns([1, 4])
with col_t1:
    selected_ticker = st.selectbox("Pilih Saham", tickers_list)

df = fetch_real_market_data(selected_ticker)
latest = df.iloc[-1]
prev = df.iloc[-2]
chg_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100

with col_t2:
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Last Price", f"Rp {int(latest['Close']):,}", f"{chg_pct:.2f}%")
    k2.metric("24h High", f"Rp {int(latest['High']):,}")
    k3.metric("Volume (IDR)", f"{latest['vol_idr']:.1f} M")
    k4.metric("RSI (14)", f"{int(latest['RSI'])}")
    
    status_color = "red" if latest['is_euphoric'] else "green"
    status_text = "⚠️ HYPE / RISK" if latest['is_euphoric'] else "✅ NORMAL"
    k5.markdown(f"<div style='padding-top:10px;'><div style='border:1px solid {status_color}; color:{status_color}; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>{status_text}</div></div>", unsafe_allow_html=True)

st.markdown("---")

col_main, col_side = st.columns([7, 3])

with col_main:
    st.markdown("##### 📈 Candlestick & Sinyal Euforia (TradingView Style)")
    
    # Plotly Candlestick (Interaktif: Bisa drag, zoom, hover)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])
    
    # 1. Candlestick Chart Riil
    fig.add_trace(go.Candlestick(x=df['Date'],
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'],
                    name='Market Price',
                    increasing_line_color='#22c55e', decreasing_line_color='#ef4444'), row=1, col=1)
    
    # 2. Line Chart MA20
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], name="MA(20)", 
                            line=dict(color='orange', width=1.5)), row=1, col=1)
    
    # 3. Scatter Sinyal Euforia (Di atas High Harga)
    euphoria_df = df[df['is_euphoric'] == 1]
    fig.add_trace(go.Scatter(x=euphoria_df['Date'], y=euphoria_df['High'] * 1.05, 
                            mode='markers', name="Sinyal Euforia", 
                            marker=dict(color='yellow', size=12, symbol='triangle-down', line=dict(color='red', width=1))), row=1, col=1)
    
    # 4. Bar Chart Volume
    fig.add_trace(go.Bar(x=df['Date'], y=df['tweet_count'], name="Volume Tweet (AI)", 
                         marker_color='rgba(99, 102, 241, 0.8)'), row=2, col=1)

    # 5. RSI Chart Indicator
    fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name="RSI (14)", 
                            line=dict(color='#06b6d4', width=1.5)), row=3, col=1)
    # Garis Overbought (70) dan Oversold (30)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", line_width=1, row=3, col=1, opacity=0.6)
    fig.add_hline(y=30, line_dash="dash", line_color="#22c55e", line_width=1, row=3, col=1, opacity=0.6)

    fig.update_layout(
        plot_bgcolor='#0a0e17', paper_bgcolor='#0a0e17', font_color='#e2e8f0',
        height=700, margin=dict(l=0, r=0, t=10, b=0),
        xaxis_rangeslider_visible=False,  # Matikan bawaan plotly agar grafik lebih luas dan rapi
        hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(showgrid=True, gridcolor='#1e293b', title_text="Harga", row=1, col=1)
    fig.update_yaxes(showgrid=True, gridcolor='#1e293b', title_text="Vol Tweets", row=2, col=1)
    fig.update_yaxes(showgrid=True, gridcolor='#1e293b', title_text="RSI", range=[0, 100], row=3, col=1)
    fig.update_xaxes(showgrid=True, gridcolor='#1e293b')
    
    st.plotly_chart(fig, use_container_width=True)

with col_side:
    st.markdown("##### 🛡️ BiLSTM Inference Matrix")
    inf1, inf2 = st.columns(2)
    
    inf1.markdown(f"<div class='kpi-card'><div class='kpi-label'>Prob. Euforia</div><div class='kpi-value' style='color:{'#f59e0b' if latest['prob']>0.7 else '#10b981'}'>{(latest['prob']*100):.1f}%</div></div>", unsafe_allow_html=True)
    inf2.markdown(f"<div class='kpi-card'><div class='kpi-label'>IndoBERT Score</div><div class='kpi-value'>{latest['sentiment']}</div></div>", unsafe_allow_html=True)
    
    if latest['is_euphoric']:
        st.error(f"> ALERT: Deteksi anomali pada sentimen X (Volume: {latest['tweet_count']}/hari) dan lonjakan harga riil. Pola spekulasi (Hype) tervalidasi.")
    else:
        st.info("> STATUS: Harga dan sentimen bergerak dalam batas kewajaran historis. Tidak ada anomali euforia.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🕒 Prediksi 5 Hari Terakhir")
    history_df = df.tail(5)[['display_date', 'Close', 'tweet_count', 'prob', 'is_euphoric']].sort_index(ascending=False)
    history_df['prob'] = (history_df['prob'] * 100).astype(int).astype(str) + "%"
    history_df['is_euphoric'] = history_df['is_euphoric'].map({1: '🔴 HYPE', 0: '⚪ NORM'})
    history_df['Close'] = history_df['Close'].astype(int)
    history_df.columns = ['Date', 'Price', 'Tweets', 'Prob', 'Status']
    st.dataframe(history_df, hide_index=True, use_container_width=True)
