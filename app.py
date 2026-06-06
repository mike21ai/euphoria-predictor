import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS
# ==========================================
st.set_page_config(
    page_title="Euphoria Terminal AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed" # Tutup sidebar secara default
)

# Custom CSS untuk tampilan ala Bloomberg Terminal/TradingView Dark Mode
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    
    /* Panel Containers */
    .panel-container { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    .panel-header { font-size: 13px; font-weight: bold; color: #8b949e; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
    
    /* Top Bar Metrics */
    .metric-box { display: flex; flex-direction: column; }
    .metric-label { font-size: 10px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-val { font-size: 20px; font-weight: 700; color: #f0f6fc; }
    .metric-sub-up { font-size: 11px; color: #3fb950; font-weight: 600; }
    .metric-sub-down { font-size: 11px; color: #f85149; font-weight: 600; }
    
    /* Status Badges */
    .badge-normal { background: rgba(46, 160, 67, 0.15); color: #3fb950; border: 1px solid rgba(46, 160, 67, 0.4); padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 11px; display: inline-block; text-align: center; }
    .badge-euphoria { background: rgba(210, 153, 34, 0.15); color: #d29922; border: 1px solid rgba(210, 153, 34, 0.4); padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 11px; display: inline-block; text-align: center; animation: pulse 2s infinite; }
    
    /* AI Matrix Boxes */
    .matrix-box { background-color: #0d1117; border: 1px solid #21262d; border-radius: 6px; padding: 12px; text-align: center; }
    .matrix-val-high { font-size: 22px; font-weight: 800; color: #d29922; }
    .matrix-val-safe { font-size: 22px; font-weight: 800; color: #3fb950; }
    .matrix-val-neut { font-size: 22px; font-weight: 800; color: #58a6ff; }
    
    /* Custom Table */
    .custom-table { width: 100%; border-collapse: collapse; font-size: 11px; color: #c9d1d9; }
    .custom-table th { text-align: left; padding: 8px 4px; color: #8b949e; border-bottom: 1px solid #30363d; font-weight: 600; }
    .custom-table td { padding: 8px 4px; border-bottom: 1px solid #21262d; }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(210, 153, 34, 0.4); }
        70% { box-shadow: 0 0 0 6px rgba(210, 153, 34, 0); }
        100% { box-shadow: 0 0 0 0 rgba(210, 153, 34, 0); }
    }
    
    /* Sembunyikan elemen bawaan Streamlit agar lebih bersih */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI FETCH DATA BEI + SIMULASI AI
# ==========================================
@st.cache_data(ttl=3600)
def fetch_real_market_data(ticker):
    # Mengambil data 2022-2024
    ticker_symbol = f"{ticker}.JK"
    df = yf.download(ticker_symbol, start="2022-01-01", end="2024-12-31", progress=False)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df = df.reset_index()
    if 'Date' not in df.columns:
        df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
    
    # Indikator Teknikal Klasik
    df['MA20'] = df['Close'].rolling(window=20).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # --- SIMULASI AI (IndoBERT & BiLSTM) ---
    # Di thesis asli, data ini ditarik dari CSV hasil pre-processing.
    # Disini kita simulasikan perilakunya berdasarkan pergerakan harga.
    
    df['tweet_count'] = np.random.randint(10, 50, size=len(df)) # Base tweet
    df['sentiment'] = np.random.uniform(-0.3, 0.3, size=len(df)) # Base sentiment
    df['prob'] = np.random.uniform(0.01, 0.25, size=len(df)) # Base prob
    df['is_euphoric'] = 0
    
    # Deteksi anomali (spike harga & volume) untuk mentrigger sinyal Euforia
    for i in range(20, len(df)):
        price_change = (df['Close'].iloc[i] - df['Close'].iloc[i-5]) / df['Close'].iloc[i-5]
        
        # Jika harga naik > 15% dalam 5 hari, anggap sedang terjadi Hype/Euforia
        if price_change > 0.15:
            df.at[df.index[i], 'tweet_count'] = np.random.randint(200, 800)
            df.at[df.index[i], 'sentiment'] = np.random.uniform(0.6, 0.95)
            df.at[df.index[i], 'prob'] = np.random.uniform(0.75, 0.99)
            df.at[df.index[i], 'is_euphoric'] = 1
            
    return df

# Format angka ke M/B (Millions/Billions)
def format_number(num):
    if num >= 1e9: return f"{num/1e9:.1f} B"
    if num >= 1e6: return f"{num/1e6:.1f} M"
    if num >= 1e3: return f"{num/1e3:.1f} K"
    return str(num)

# ==========================================
# 3. HEADER & TOP BAR METRICS
# ==========================================
st.markdown("<div style='margin-bottom: 20px;'><span style='font-size: 24px; font-weight: 800; color: white;'>⚡ EuphoriaTerminal</span> <span style='font-size: 12px; color: #8b949e; letter-spacing: 1px;'>BiLSTM x IndoBERT v3.5</span></div>", unsafe_allow_html=True)

tickers_list = ['KARW', 'FORU', 'SRAJ', 'PANI', 'DSSA', 'SGER', 'TPIA', 'BRMS', 'MLPT', 'BRPT', 'TOBA', 'AUTO', 'IMAS', 'PSAB', 'KONI']

# Membuat Layout Top Bar menggunakan kolom
top_col1, top_col2, top_col3, top_col4, top_col5, top_col6 = st.columns([1.5, 1.5, 1.5, 1.5, 1, 1.5])

with top_col1:
    selected_ticker = st.selectbox("Pilih Saham", tickers_list, label_visibility="collapsed")

# Tarik Data
df = fetch_real_market_data(selected_ticker)
latest = df.iloc[-1]
prev = df.iloc[-2]

# Kalkulasi Metrik
chg_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
chg_class = "metric-sub-up" if chg_pct >= 0 else "metric-sub-down"
chg_sign = "+" if chg_pct >= 0 else ""

with top_col2:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>Last Price</div><div class='metric-val'>Rp {latest['Close']:,.0f}</div><div class='{chg_class}'>{chg_sign}{chg_pct:.2f}% vs H-1</div></div>", unsafe_allow_html=True)
with top_col3:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>24h High</div><div class='metric-val'>Rp {latest['High']:,.0f}</div></div>", unsafe_allow_html=True)
with top_col4:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>Volume Saham</div><div class='metric-val'>{format_number(latest['Volume'])}</div></div>", unsafe_allow_html=True)
with top_col5:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>RSI (14)</div><div class='metric-val'>{latest['RSI']:.0f}</div></div>", unsafe_allow_html=True)
with top_col6:
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True) # Spacer
    if latest['is_euphoric'] == 1:
        st.markdown("<div style='width: 100%; text-align: right;'><div class='badge-euphoria'>⚠️ EUPHORIA DETECTED</div></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='width: 100%; text-align: right;'><div class='badge-normal'>✅ NORMAL</div></div>", unsafe_allow_html=True)

st.markdown("<hr style='border: 1px solid #21262d; margin: 20px 0;'>", unsafe_allow_html=True)

# ==========================================
# 4. WORKSPACE: CHART (LEFT) & AI PANEL (RIGHT)
# ==========================================
left_col, right_col = st.columns([7, 3])

# --- BAGIAN KIRI: CHART 4 ROW DENGAN SINYAL ---
with left_col:
    st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-header'>📈 Candlestick & Sinyal Euforia (TradingView Style)</div>", unsafe_allow_html=True)
    
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.5, 0.15, 0.15, 0.2])

    # Row 1: Candlestick & MA20
    fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Market Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], name="MA(20)", line=dict(color='rgba(255, 165, 0, 0.6)', width=1.5)), row=1, col=1)
    
    # Sinyal Euforia (Segitiga Kuning di atas harga)
    euphoria_df = df[df['is_euphoric'] == 1]
    if not euphoria_df.empty:
        fig.add_trace(go.Scatter(
            x=euphoria_df['Date'], 
            y=euphoria_df['High'] * 1.05, # Posisi sedikit di atas sumbu High candlestick
            mode='markers',
            marker=dict(symbol='triangle-down', size=10, color='#d29922', line=dict(width=1, color='#0d1117')),
            name='Sinyal Euforia'
        ), row=1, col=1)

    # Row 2: Volume Saham Asli
    colors_vol = ['rgba(248, 81, 73, 0.5)' if row['Open'] > row['Close'] else 'rgba(63, 185, 80, 0.5)' for _, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name="Vol Saham", marker_color=colors_vol), row=2, col=1)

    # Row 3: Volume Tweet (IndoBERT)
    fig.add_trace(go.Bar(x=df['Date'], y=df['tweet_count'], name="Vol Tweet", marker_color='rgba(88, 166, 255, 0.6)'), row=3, col=1)

    # Row 4: RSI Indikator
    fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name="RSI", line=dict(color='#3fb950', width=1)), row=4, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="rgba(248, 81, 73, 0.5)", row=4, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="rgba(63, 185, 80, 0.5)", row=4, col=1)

    # Styling Chart
    fig.update_layout(
        plot_bgcolor='#161b22', paper_bgcolor='#161b22', font_color='#8b949e',
        height=650, margin=dict(l=0, r=0, t=10, b=0),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(gridcolor='#30363d', zerolinecolor='#30363d')
    fig.update_xaxes(gridcolor='#30363d', zerolinecolor='#30363d')

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# --- BAGIAN KANAN: PANEL AI & HISTORICAL LOG ---
with right_col:
    # 1. BiLSTM Inference Matrix
    st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-header'>🛡️ BiLSTM Inference Matrix</div>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    prob_class = "matrix-val-high" if latest['prob'] > 0.7 else "matrix-val-safe"
    with col_a:
        st.markdown(f"<div class='matrix-box'><div class='metric-label'>PROB. EUFORIA</div><div class='{prob_class}'>{latest['prob']*100:.1f}%</div></div>", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"<div class='matrix-box'><div class='metric-label'>INDOBERT SCORE</div><div class='matrix-val-neut'>{latest['sentiment']:.2f}</div></div>", unsafe_allow_html=True)
    
    status_text = "ALERT: Model mendeteksi anomali pada korelasi volume sentimen X dan lonjakan harga. Pola spekulasi (Hype) valid." if latest['is_euphoric'] else "STATUS: Harga dan sentimen bergerak dalam batas kewajaran historis. Tidak ada anomali euforia."
    status_bg = "rgba(210, 153, 34, 0.1)" if latest['is_euphoric'] else "rgba(56, 139, 253, 0.1)"
    status_border = "rgba(210, 153, 34, 0.4)" if latest['is_euphoric'] else "rgba(56, 139, 253, 0.4)"
    status_color = "#d29922" if latest['is_euphoric'] else "#58a6ff"
    
    st.markdown(f"<div style='margin-top: 12px; padding: 12px; background-color: {status_bg}; border: 1px solid {status_border}; border-radius: 6px; font-size: 11px; color: {status_color};'>{status_text}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 2. Historical Table (5 Days)
    st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-header'>🕒 Prediksi 5 Hari Terakhir</div>", unsafe_allow_html=True)
    
    last_5_days = df.tail(5).iloc[::-1] # Ambil 5 hari terakhir dan balik urutannya (terbaru di atas)
    
    table_html = "<table class='custom-table'><thead><tr><th>Date</th><th>Price</th><th>Tweets</th><th>Prob</th><th>Status</th></tr></thead><tbody>"
    for _, row in last_5_days.iterrows():
        date_str = row['Date'].strftime('%d %b %Y')
        status_badge = "<span style='color:#d29922; font-weight:bold;'>⚠️ HYPE</span>" if row['is_euphoric'] else "<span style='color:#8b949e;'>⚪ NORM</span>"
        table_html += f"<tr><td>{date_str}</td><td>{row['Close']:,.0f}</td><td>{row['tweet_count']:.0f}</td><td>{row['prob']*100:.0f}%</td><td>{status_badge}</td></tr>"
    table_html += "</tbody></table>"
    
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
