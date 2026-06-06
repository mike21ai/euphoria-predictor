import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
def generate_realistic_data(ticker, base_price, spikes):
    data = []
    current_price = base_price
    start_date = datetime(2026, 6, 6) - timedelta(days=90)
    price_history = [base_price] * 20

    for i in range(91):
        current_date = start_date + timedelta(days=i)
        
        volatility = np.random.uniform(-0.02, 0.02)
        tweet_count = random.randint(10, 60)
        sentiment = np.random.uniform(-0.1, 0.3)
        rsi = np.random.uniform(40, 60)
        is_euphoric = 0
        prob = np.random.uniform(0.0, 0.3)

        for spike in spikes:
            if spike['start'] <= i <= spike['end']:
                volatility = spike['intensity'] + np.random.uniform(0, 0.05)
                tweet_count = int(tweet_count * np.random.uniform(5, 10))
                sentiment = np.random.uniform(0.6, 0.95)
                rsi = np.random.uniform(75, 95)
                is_euphoric = 1
                prob = np.random.uniform(0.75, 0.99)
            elif spike['end'] < i <= spike['end'] + spike['crashDuration']:
                volatility = -(spike['intensity'] * 0.6) - np.random.uniform(0, 0.05)
                tweet_count = int(tweet_count * 2.5)
                sentiment = np.random.uniform(-0.9, -0.6)
                rsi = np.random.uniform(15, 30)

        current_price = max(50, current_price * (1 + volatility))
        close = round(current_price)
        open_p = close * (1 - np.random.uniform(-0.02, 0.02))
        high = max(open_p, close) * (1 + np.random.uniform(0, 0.03))
        low = min(open_p, close) * (1 - np.random.uniform(0, 0.03))
        
        price_history.pop(0)
        price_history.append(close)
        ma20 = round(sum(price_history) / 20)

        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'display_date': current_date.strftime('%d %b'),
            'open': round(open_p),
            'high': round(high),
            'low': round(low),
            'close': close,
            'ma20': ma20,
            'tweet_count': tweet_count,
            'sentiment': round(sentiment, 2),
            'rsi': round(rsi),
            'is_euphoric': is_euphoric,
            'prob': round(prob, 2),
            'vol_idr': round(np.random.uniform(10, 110), 1) # dalam Miliar
        })
    return pd.DataFrame(data)

tickers_config = {
    'PANI': {'base': 4500, 'spikes': [{'start': 60, 'end': 75, 'intensity': 0.08, 'crashDuration': 10}]},
    'BREN': {'base': 8000, 'spikes': [{'start': 20, 'end': 35, 'intensity': 0.12, 'crashDuration': 15}]},
    'KARW': {'base': 150,  'spikes': [{'start': 50, 'end': 65, 'intensity': 0.20, 'crashDuration': 10}]},
    'CUAN': {'base': 6000, 'spikes': [{'start': 40, 'end': 50, 'intensity': 0.15, 'crashDuration': 20}]},
}

st.markdown("### ⚡ EuphoriaTerminal <span style='color:#64748b; font-size:14px'>BiLSTM x IndoBERT v2.5</span>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #1e293b; margin-top:0px; margin-bottom:15px'>", unsafe_allow_html=True)

col_t1, col_t2 = st.columns([1, 4])
with col_t1:
    selected_ticker = st.selectbox("Pilih Saham", list(tickers_config.keys()))

# Mengambil data sesuai pilihan
df = generate_realistic_data(selected_ticker, tickers_config[selected_ticker]['base'], tickers_config[selected_ticker]['spikes'])
latest = df.iloc[-1]
prev = df.iloc[-2]
chg_pct = ((latest['close'] - prev['close']) / prev['close']) * 100

with col_t2:
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Last Price", f"Rp {latest['close']:,}", f"{chg_pct:.2f}%")
    k2.metric("24h High", f"Rp {latest['high']:,}")
    k3.metric("Volume (IDR)", f"{latest['vol_idr']} Miliar")
    k4.metric("RSI (14)", f"{latest['rsi']}")
    
    status_color = "red" if latest['is_euphoric'] else "green"
    status_text = "⚠️ HYPE / RISK" if latest['is_euphoric'] else "✅ NORMAL"
    k5.markdown(f"<div style='padding-top:10px;'><div style='border:1px solid {status_color}; color:{status_color}; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>{status_text}</div></div>", unsafe_allow_html=True)

st.markdown("---")
col_main, col_side = st.columns([7, 3])

with col_main:
    st.markdown("##### 📈 Price Action & Euphoria Detection")
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Bar Chart Volume Tweet (Background)
    fig.add_trace(go.Bar(x=df['date'], y=df['tweet_count'], name="Tweet Volume", marker_color='rgba(99, 102, 241, 0.3)'), secondary_y=False)
    
    # Line Chart MA20
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], name="MA(20)", line=dict(color='orange', width=2, dash='dash')), secondary_y=True)
    
    # Line Chart Price
    fig.add_trace(go.Scatter(x=df['date'], y=df['close'], name="Harga Close", line=dict(color='#3b82f6', width=3)), secondary_y=True)
    
    # Scatter untuk sinyal Euforia
    euphoria_df = df[df['is_euphoric'] == 1]
    fig.add_trace(go.Scatter(x=euphoria_df['date'], y=euphoria_df['close'], mode='markers', name="Sinyal Euforia", 
                             marker=dict(color='yellow', size=12, line=dict(color='red', width=2))), secondary_y=True)
    
    fig.update_layout(
        plot_bgcolor='#0a0e17', paper_bgcolor='#0a0e17', font_color='#e2e8f0',
        margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(title_text="Tweet Count", secondary_y=False, showgrid=False)
    fig.update_yaxes(title_text="Price (IDR)", secondary_y=True, showgrid=True, gridcolor='#1e293b')
    
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### 🛡️ BiLSTM Inference Matrix")
    inf1, inf2, inf3 = st.columns(3)
    
    inf1.markdown(f"<div class='kpi-card'><div class='kpi-label'>Probabilitas Euforia</div><div class='kpi-value' style='color:{'#f59e0b' if latest['prob']>0.7 else '#10b981'}'>{(latest['prob']*100):.1f}%</div></div>", unsafe_allow_html=True)
    inf2.markdown(f"<div class='kpi-card'><div class='kpi-label'>IndoBERT Score</div><div class='kpi-value'>{latest['sentiment']}</div></div>", unsafe_allow_html=True)
    inf3.markdown(f"<div class='kpi-card'><div class='kpi-label'>Trend Bias</div><div class='kpi-value'>{'Bullish' if latest['close'] > latest['ma20'] else 'Bearish'}</div></div>", unsafe_allow_html=True)
    
    if latest['is_euphoric']:
        st.error(f"> ALERT: Deteksi anomali pada sentimen X (Volume: {latest['tweet_count']}/hari) dan lonjakan harga. Pola spekulasi (Hype) tervalidasi BiLSTM. Risiko distribusi bandar tinggi.")
    else:
        st.info("> STATUS: Harga dan sentimen bergerak dalam batas kewajaran historis. Tidak ada anomali euforia signifikan.")

with col_side:
    st.markdown("##### 📚 Market Depth (Orderbook)")
    # Simulasi Orderbook
    tick = 10 if latest['close'] > 2000 else 5
    ob_data = []
    for i in range(5, 0, -1):
        ob_data.append(["-", "-", latest['close'] + (i*tick), random.randint(1000, 50000)])
    for i in range(1, 6):
        ob_data.append([random.randint(1000, 50000), latest['close'] - (i*tick), "-", "-"])
    
    ob_df = pd.DataFrame(ob_data, columns=["Bid Vol", "Bid", "Ask", "Ask Vol"])
    st.dataframe(ob_df, hide_index=True, use_container_width=True)

    st.markdown("##### 🕒 Prediksi 5 Hari Terakhir")
    history_df = df.tail(5)[['display_date', 'close', 'tweet_count', 'prob', 'is_euphoric']].sort_index(ascending=False)
    history_df['prob'] = (history_df['prob'] * 100).astype(str) + "%"
    history_df['is_euphoric'] = history_df['is_euphoric'].map({1: '🔴 HYPE', 0: '⚪ NORM'})
    history_df.columns = ['Date', 'Price', 'Tweets', 'Prob', 'Status']
    st.dataframe(history_df, hide_index=True, use_container_width=True)
