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
    page_title="Euphoria Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    
    /* Panel Containers */
    .panel-container { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    .panel-header { font-size: 13px; font-weight: bold; color: #8b949e; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #30363d; padding-bottom: 8px;}
    
    /* Overview Top Section */
    .overview-title { font-size: 28px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; margin-bottom: -5px;}
    .overview-subtitle { font-size: 12px; color: #8b949e; margin-bottom: 15px;}
    .stat-label { font-size: 10px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }
    .stat-val { font-size: 22px; font-weight: 700; color: #f0f6fc; }
    .stat-up { font-size: 12px; color: #3fb950; font-weight: 600; margin-left: 5px; }
    .stat-down { font-size: 12px; color: #f85149; font-weight: 600; margin-left: 5px; }
    
    /* AI Matrix Boxes */
    .matrix-box { background-color: #0d1117; border: 1px solid #21262d; border-radius: 6px; padding: 12px; text-align: center; margin-bottom: 10px; }
    .matrix-val-high { font-size: 20px; font-weight: 800; color: #d29922; }
    .matrix-val-safe { font-size: 20px; font-weight: 800; color: #3fb950; }
    .matrix-val-neut { font-size: 20px; font-weight: 800; color: #58a6ff; }
    
    /* Custom Table */
    .table-wrapper { height: 200px; overflow-y: auto; margin-bottom: 10px;}
    .custom-table { width: 100%; border-collapse: collapse; font-size: 11px; color: #c9d1d9; text-align: left;}
    .custom-table th { padding: 6px 4px; color: #8b949e; border-bottom: 1px solid #30363d; font-weight: 600; position: sticky; top: 0; background: #161b22; z-index: 1; }
    .custom-table td { padding: 6px 4px; border-bottom: 1px solid #21262d; }
    .custom-table tr:hover { background-color: #1c2128; }
    
    /* Sembunyikan elemen bawaan Streamlit agar lebih bersih */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Dictionary Nama Perusahaan
COMPANY_DICT = {
    'KARW': 'PT Meratus Jasa Prima Tbk', 'FORU': 'PT Fortune Indonesia Tbk', 
    'SRAJ': 'PT Sejahteraraya Anugrahjaya Tbk', 'PANI': 'PT Pantai Indah Kapuk Dua Tbk', 
    'DSSA': 'PT Dian Swastatika Sentosa Tbk', 'SGER': 'PT Sumber Global Energy Tbk', 
    'TPIA': 'PT Chandra Asri Petrochemical Tbk', 'BRMS': 'PT Bumi Resources Minerals Tbk', 
    'MLPT': 'PT Multipolar Technology Tbk', 'BRPT': 'PT Barito Pacific Tbk', 
    'TOBA': 'PT TBS Energi Utama Tbk', 'AUTO': 'PT Astra Otoparts Tbk', 
    'IMAS': 'PT Indomobil Sukses Internasional Tbk', 'PSAB': 'PT J Resources Asia Pasifik Tbk', 
    'KONI': 'PT Perdana Bangun Pusaka Tbk'
}

# ==========================================
# 2. FUNGSI FETCH DATA BEI + SIMULASI AI
# ==========================================
@st.cache_data(ttl=3600)
def fetch_real_market_data(ticker):
    ticker_symbol = f"{ticker}.JK"
    df = yf.download(ticker_symbol, start="2022-01-01", end="2024-12-31", progress=False)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df = df.reset_index()
    if 'Date' not in df.columns:
        df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
        
    if df.empty:
        return df
    
    # Indikator Teknikal
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Simulasi AI (IndoBERT & BiLSTM)
    df['tweet_count'] = np.random.randint(5, 40, size=len(df)) 
    df['sentiment'] = np.random.uniform(-0.4, 0.4, size=len(df)) 
    df['prob'] = np.random.uniform(0.01, 0.30, size=len(df)) 
    df['is_euphoric'] = 0
    
    # Deteksi anomali untuk men-trigger Euforia
    for i in range(20, len(df)):
        price_change = (df['Close'].iloc[i] - df['Close'].iloc[i-5]) / df['Close'].iloc[i-5]
        if price_change > 0.18:
            df.at[df.index[i], 'tweet_count'] = np.random.randint(150, 900)
            df.at[df.index[i], 'sentiment'] = np.random.uniform(0.65, 0.98)
            df.at[df.index[i], 'prob'] = np.random.uniform(0.75, 0.99)
            df.at[df.index[i], 'is_euphoric'] = 1
            
    return df

def format_number(num):
    if num >= 1e9: return f"{num/1e9:.2f} B"
    if num >= 1e6: return f"{num/1e6:.2f} M"
    if num >= 1e3: return f"{num/1e3:.2f} K"
    return str(num)

# ==========================================
# 3. HEADER & OVERVIEW
# ==========================================
st.markdown("<div style='font-size: 12px; color: #8b949e; letter-spacing: 2px; margin-bottom: 5px;'>⚡ EUPHORIA TERMINAL</div>", unsafe_allow_html=True)

# Ticker Selector diletakkan secara tersembunyi/ringkas
col_sel, _ = st.columns([2, 8])
with col_sel:
    selected_ticker = st.selectbox("Pilih Saham", list(COMPANY_DICT.keys()), label_visibility="collapsed")

df = fetch_real_market_data(selected_ticker)

if not df.empty:
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    chg_val = latest['Close'] - prev['Close']
    chg_pct = (chg_val / prev['Close']) * 100
    chg_class = "stat-up" if chg_pct >= 0 else "stat-down"
    chg_sign = "+" if chg_pct >= 0 else ""
    arrow = "▲" if chg_pct >= 0 else "▼"

    # Baris Overview Metrik
    o_col1, o_col2, o_col3, o_col4, o_col5 = st.columns([2.5, 1.5, 1.5, 1.5, 1.5])
    
    with o_col1:
        st.markdown(f"<div class='overview-title'>{selected_ticker}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='overview-subtitle'>{COMPANY_DICT[selected_ticker]}</div>", unsafe_allow_html=True)
    with o_col2:
        st.markdown(f"<div><div class='stat-label'>Last Price</div><div class='stat-val'>Rp {latest['Close']:,.0f}</div><div class='{chg_class}'>{arrow} {chg_val:,.0f} ({chg_sign}{chg_pct:.2f}%)</div></div>", unsafe_allow_html=True)
    with o_col3:
        st.markdown(f"<div><div class='stat-label'>24h Volume (Shares)</div><div class='stat-val'>{format_number(latest['Volume'])}</div></div>", unsafe_allow_html=True)
    with o_col4:
        st.markdown(f"<div><div class='stat-label'>RSI 14D</div><div class='stat-val'>{latest['RSI']:.1f}</div></div>", unsafe_allow_html=True)
    with o_col5:
        st.markdown(f"<div><div class='stat-label'>Sentiment Trend</div><div class='stat-val' style='color: {'#3fb950' if latest['sentiment'] > 0 else '#f85149'};'>{latest['sentiment']:.2f}</div></div>", unsafe_allow_html=True)

    st.markdown("<hr style='border: 1px solid #21262d; margin: 5px 0 20px 0;'>", unsafe_allow_html=True)

    # ==========================================
    # 4. WORKSPACE: CHART & AI PANEL
    # ==========================================
    left_col, right_col = st.columns([7, 3])

    # --- BAGIAN KIRI: CHART TERMINAL ---
    with left_col:
        st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
        
        # Kontrol Grafik
        ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4 = st.columns([2, 2, 2, 4])
        with ctrl_c1:
            chart_type = st.radio("Type", ["Candlestick", "Line"], horizontal=True, label_visibility="collapsed")
        with ctrl_c2:
            show_ema = st.toggle("EMA 20", value=True)
        with ctrl_c3:
            show_rsi = st.toggle("Show RSI", value=True)
            
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Konfigurasi Subplots dinamis berdasarkan RSI
        rows = 3 if show_rsi else 2
        row_heights = [0.6, 0.2, 0.2] if show_rsi else [0.75, 0.25]
        specs = [[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]] if show_rsi else [[{"secondary_y": True}], [{"secondary_y": False}]]
        
        fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights, specs=specs)

        # 1. Harga (Row 1)
        if chart_type == "Candlestick":
            fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1, secondary_y=False)
        else:
            fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', line=dict(color='#58a6ff', width=1.5), name='Price'), row=1, col=1, secondary_y=False)
        
        # 2. EMA 20 (Row 1)
        if show_ema:
            fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA20'], mode='lines', line=dict(color='#d29922', width=1.5, dash='dot'), name='EMA 20'), row=1, col=1, secondary_y=False)

        # 3. Sinyal Euforia (Row 1)
        euphoria_df = df[df['is_euphoric'] == 1]
        if not euphoria_df.empty:
            fig.add_trace(go.Scatter(
                x=euphoria_df['Date'], y=euphoria_df['High'] * 1.05, 
                mode='markers', marker=dict(symbol='triangle-down', size=12, color='#e3b341', line=dict(width=1, color='#000')),
                name='Euphoria Signal'
            ), row=1, col=1, secondary_y=False)

        # 4. Volume Saham (Row 1, Secondary Y, Ditumpuk di bawah)
        colors_vol = ['rgba(248, 81, 73, 0.3)' if row['Open'] > row['Close'] else 'rgba(63, 185, 80, 0.3)' for _, row in df.iterrows()]
        fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name="Stock Volume", marker_color=colors_vol), row=1, col=1, secondary_y=True)
        # Setting Y-axis untuk volume agar tetap di bawah (max * 4)
        fig.update_yaxes(showgrid=False, secondary_y=True, row=1, col=1, range=[0, df['Volume'].max() * 4], showticklabels=False)

        # 5. Volume Tweet (Row 2)
        fig.add_trace(go.Bar(x=df['Date'], y=df['tweet_count'], name="Tweet Volume", marker_color='rgba(137, 87, 229, 0.7)'), row=2, col=1)

        # 6. RSI (Row 3, Optional)
        if show_rsi:
            fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name="RSI", line=dict(color='#3fb950', width=1.5)), row=3, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="rgba(248, 81, 73, 0.7)", row=3, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="rgba(63, 185, 80, 0.7)", row=3, col=1)
            fig.update_yaxes(range=[0, 100], row=3, col=1)

        # Styling Umum Plotly
        fig.update_layout(
            plot_bgcolor='#0d1117', paper_bgcolor='#161b22', font_color='#8b949e',
            height=680, margin=dict(l=5, r=5, t=10, b=5),
            xaxis_rangeslider_visible=False, hovermode="x unified",
            showlegend=False
        )
        fig.update_yaxes(gridcolor='#30363d', zerolinecolor='#30363d')
        fig.update_xaxes(gridcolor='#30363d', zerolinecolor='#30363d')

        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


    # --- BAGIAN KANAN: PANEL AI & HISTORICAL LOG ---
    with right_col:
        
        # 1. AI Real-time Status
        st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-header'>🧠 AI Inference Engine</div>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        prob_class = "matrix-val-high" if latest['prob'] > 0.7 else "matrix-val-safe"
        with col_a:
            st.markdown(f"<div class='matrix-box'><div class='stat-label'>Euphoria Prob</div><div class='{prob_class}'>{latest['prob']*100:.1f}%</div></div>", unsafe_allow_html=True)
        with col_b:
            indobert_col = "matrix-val-safe" if latest['sentiment'] > 0 else "matrix-val-high" if latest['sentiment'] < 0 else "matrix-val-neut"
            st.markdown(f"<div class='matrix-box'><div class='stat-label'>IndoBERT Score</div><div class='{indobert_col}'>{latest['sentiment']:.2f}</div></div>", unsafe_allow_html=True)
        
        # Status Teks
        trend_status = "Bullish Uptrend" if latest['Close'] > latest['EMA20'] else "Bearish Downtrend"
        sentiment_status = "Positif (Optimisme)" if latest['sentiment'] > 0.3 else "Negatif (Pesimisme)" if latest['sentiment'] < -0.3 else "Netral"
        
        st.markdown(f"""
            <div style='font-size: 11px; color: #c9d1d9; line-height: 1.6;'>
                <div style='margin-bottom: 4px;'><b>Status Harga:</b> <span style='color: #8b949e;'>{trend_status} (vs EMA20)</span></div>
                <div style='margin-bottom: 8px;'><b>Status Sentimen:</b> <span style='color: #8b949e;'>{sentiment_status}</span></div>
            </div>
        """, unsafe_allow_html=True)

        if latest['is_euphoric']:
            st.markdown("<div style='padding: 8px; background: rgba(210, 153, 34, 0.1); border: 1px solid rgba(210, 153, 34, 0.4); border-radius: 4px; color: #d29922; font-size: 11px; font-weight: bold;'>⚠️ WARNING: Extreme Speculation / Hype Detected. Risk of sharp correction.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='padding: 8px; background: rgba(46, 160, 67, 0.1); border: 1px solid rgba(46, 160, 67, 0.4); border-radius: 4px; color: #3fb950; font-size: 11px; font-weight: bold;'>✅ System Normal: No significant hype anomalies detected.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        
        # 2. Prediction Log (Last 10 Days)
        st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-header'>📋 Log Prediksi Terakhir</div>", unsafe_allow_html=True)
        
        last_10 = df.tail(10).iloc[::-1]
        log_html = "<div class='table-wrapper'><table class='custom-table'><thead><tr><th>Date</th><th>Close</th><th>Prob</th><th>Status</th></tr></thead><tbody>"
        for _, row in last_10.iterrows():
            date_str = row['Date'].strftime('%d %b')
            badge = "<span style='color:#d29922; font-weight:bold;'>HYPE</span>" if row['is_euphoric'] else "<span style='color:#8b949e;'>NORM</span>"
            log_html += f"<tr><td>{date_str}</td><td>{row['Close']:,.0f}</td><td>{row['prob']*100:.0f}%</td><td>{badge}</td></tr>"
        log_html += "</tbody></table></div>"
        st.markdown(log_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        
        # 3. Euphoria History Log (Hanya Sinyal)
        st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-header'>⚡ Log Sinyal Euforia</div>", unsafe_allow_html=True)
        
        euphoria_history = euphoria_df.tail(10).iloc[::-1]
        if euphoria_history.empty:
            st.markdown("<div style='font-size: 11px; color: #8b949e; text-align: center; padding: 20px;'>Belum ada riwayat euforia terdeteksi.</div>", unsafe_allow_html=True)
        else:
            eh_html = "<div class='table-wrapper'><table class='custom-table'><thead><tr><th>Date</th><th>Spike Price</th><th>Tweets</th><th>Sentimen</th></tr></thead><tbody>"
            for _, row in euphoria_history.iterrows():
                date_str = row['Date'].strftime('%d %b %y')
                eh_html += f"<tr><td><span style='color:#d29922;'>{date_str}</span></td><td>{row['Close']:,.0f}</td><td>{row['tweet_count']:.0f}</td><td>{row['sentiment']:.2f}</td></tr>"
            eh_html += "</tbody></table></div>"
            st.markdown(eh_html, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.error("Data tidak ditemukan untuk saham ini.")
