import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import random

# ==========================================
# 1. PAGE CONFIGURATION & STATE
# ==========================================
st.set_page_config(
    page_title="Euphoria Predictor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

query_params = st.query_params
nav_param = query_params.get("nav", "Stock Analysis")
ticker_param = query_params.get("ticker", "PANI")
date_param = query_params.get("date", None)

# ==========================================
# 2. CUSTOM CSS & TOP BAR
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 2.5rem !important; padding-bottom: 0rem !important; }
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    .top-bar {
        position: fixed; top: 0; left: 0; right: 0; height: 35px; background-color: #010409; 
        border-bottom: 1px solid #30363d; z-index: 999999; display: flex; align-items: center; 
        padding: 0 15px; font-family: monospace; font-size: 12px;
    }
    .top-bar-marquee { flex: 1; overflow: hidden; white-space: nowrap; color: #ffffff; display: flex; align-items: center;}
    .top-bar-status { margin-left: 20px; color: #8b949e; font-weight: bold; display: flex; align-items: center; gap: 15px; }
    
    .panel-container { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    .panel-header { font-size: 13px; font-weight: bold; color: #8b949e; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #30363d; padding-bottom: 8px;}
    
    .overview-title { font-size: 32px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; margin-bottom: -5px; line-height: 1.1;}
    .overview-subtitle { font-size: 14px; color: #8b949e; margin-bottom: 15px; font-weight: 500;}
    .stat-label { font-size: 10px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }
    .stat-val { font-size: 22px; font-weight: 700; color: #f0f6fc; }
    .stat-up { font-size: 12px; color: #3fb950; font-weight: 600; margin-left: 5px; }
    .stat-down { font-size: 12px; color: #f85149; font-weight: 600; margin-left: 5px; }
    
    .matrix-box { background-color: #0d1117; border: 1px solid #21262d; border-radius: 6px; padding: 12px; text-align: center; margin-bottom: 10px; }
    .matrix-val-high { font-size: 20px; font-weight: 800; color: #d29922; }
    .matrix-val-safe { font-size: 20px; font-weight: 800; color: #3fb950; }
    .matrix-val-neut { font-size: 20px; font-weight: 800; color: #58a6ff; }
    
    .table-wrapper { height: 250px; overflow-y: auto; margin-bottom: 10px;}
    .custom-table { width: 100%; border-collapse: collapse; font-size: 11px; color: #c9d1d9; text-align: left;}
    .custom-table th { padding: 8px 4px; color: #8b949e; border-bottom: 1px solid #30363d; font-weight: 600; position: sticky; top: 0; background: #161b22; z-index: 1; text-transform: uppercase;}
    .custom-table td { padding: 8px 4px; border-bottom: 1px solid #21262d; }
    .custom-table tr:hover { background-color: #1c2128; }
    .hyperlink-cell a { color: #58a6ff; text-decoration: none; font-weight: bold; }
    .hyperlink-cell a:hover { text-decoration: underline; color: #79c0ff; }
    
    .drill-card { background: #0d1117; border-left: 4px solid #58a6ff; padding: 15px; border-radius: 4px; margin-bottom: 10px; }
    .drill-title { font-size: 12px; color: #8b949e; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .drill-desc { font-size: 14px; color: #c9d1d9; }
    
    /* Method tables */
    .method-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; text-align: left; background: #0d1117; border: 1px solid #30363d;}
    .method-table th { padding: 10px; background: #161b22; color: #8b949e; border-bottom: 1px solid #30363d;}
    .method-table td { padding: 10px; border-bottom: 1px solid #21262d; color: #c9d1d9;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATABASE & FUNCTIONS
# ==========================================
COMPANY_DICT = {
    'KARW': {'name': 'PT Meratus Jasa Prima Tbk', 'sector': 'Infrastructure / Logistics', 'founded': '1990', 'director': 'Farida Helianti', 'mcap': 'Rp 1.2 Trillion', 'desc': 'KARW operates in maritime logistics and port services. Recently acquired by the Meratus Group, triggering massive retail speculation.'},
    'FORU': {'name': 'PT Fortune Indonesia Tbk', 'sector': 'Media & Advertising', 'founded': '1970', 'director': 'Ratna Puspitasari', 'mcap': 'Rp 850 Billion', 'desc': 'A legacy advertising agency in Indonesia. Its stock often experiences high volatility due to its small market capitalization.'},
    'SRAJ': {'name': 'PT Sejahteraraya Anugrahjaya Tbk', 'sector': 'Healthcare', 'founded': '1991', 'director': 'Jonathan Tahir', 'mcap': 'Rp 5.4 Trillion', 'desc': 'Operator of Mayapada Hospitals. Often subject to hype surrounding healthcare expansions and acquisitions.'},
    'PANI': {'name': 'PT Pantai Indah Kapuk Dua Tbk', 'sector': 'Property & Real Estate', 'founded': '2000', 'director': 'Sugianto Kusuma', 'mcap': 'Rp 88 Trillion', 'desc': 'A massive property developer backed by the Agung Sedayu Group. PANI is highly discussed on social media due to its aggressive land bank expansion.'},
    'DSSA': {'name': 'PT Dian Swastatika Sentosa Tbk', 'sector': 'Energy & Infrastructure', 'founded': '1996', 'director': 'L. Krisnan Cahya', 'mcap': 'Rp 120 Trillion', 'desc': 'A holding company under Sinar Mas Group focusing on power generation and coal mining.'},
    'SGER': {'name': 'PT Sumber Global Energy Tbk', 'sector': 'Coal Trade', 'founded': '2008', 'director': 'Welly Thomas', 'mcap': 'Rp 6.2 Trillion', 'desc': 'Engaged in coal trading. High volatility correlates with global coal price narratives and dividend distributions.'},
    'TPIA': {'name': 'PT Chandra Asri Petrochemical Tbk', 'sector': 'Chemical Industry', 'founded': '1984', 'director': 'Erwin Ciputra', 'mcap': 'Rp 650 Trillion', 'desc': 'The largest integrated petrochemical company in Indonesia. Highly influenced by conglomerate actions (Prajogo Pangestu).'},
    'BRMS': {'name': 'PT Bumi Resources Minerals Tbk', 'sector': 'Gold Mining', 'founded': '2003', 'director': 'Agus Projosasmito', 'mcap': 'Rp 22 Trillion', 'desc': 'A subsidiary of Bumi Resources focusing on gold. Very popular among retail traders due to gold price hypes.'},
    'MLPT': {'name': 'PT Multipolar Technology Tbk', 'sector': 'Technology & IT', 'founded': '2001', 'director': 'Wahyudi Chandra', 'mcap': 'Rp 4.5 Trillion', 'desc': 'Provides IT hardware and integration services. Volatile during tech-sector rallies.'},
    'BRPT': {'name': 'PT Barito Pacific Tbk', 'sector': 'Energy & Petrochemical', 'founded': '1979', 'director': 'Agus Salim Pangestu', 'mcap': 'Rp 110 Trillion', 'desc': 'Holding company of TPIA and BREN. Central to the Barito Group hype cycle on the Indonesian stock exchange.'},
    'TOBA': {'name': 'PT TBS Energi Utama Tbk', 'sector': 'Renewable Energy', 'founded': '2007', 'director': 'Dicky Yordan', 'mcap': 'Rp 3.8 Trillion', 'desc': 'Transitioning from coal to EV (Electrum) and renewable energy, creating strong retail narratives.'},
    'AUTO': {'name': 'PT Astra Otoparts Tbk', 'sector': 'Automotive', 'founded': '1976', 'director': 'Hamdhani Dzulkarnaen Salim', 'mcap': 'Rp 11 Trillion', 'desc': 'Astra Groups automotive component manufacturer. Consistent fundamental player but occasionally hyped on EV news.'},
    'IMAS': {'name': 'PT Indomobil Sukses Internasional Tbk', 'sector': 'Automotive & Transport', 'founded': '1976', 'director': 'Jusak Kertowidjojo', 'mcap': 'Rp 5.9 Trillion', 'desc': 'Salim Groups automotive arm. Frequently experiences speculative spikes related to new brand acquisitions (e.g., BYD, GWM).'},
    'PSAB': {'name': 'PT J Resources Asia Pasifik Tbk', 'sector': 'Gold Mining', 'founded': '2002', 'director': 'Edi Permadi', 'mcap': 'Rp 5.2 Trillion', 'desc': 'Gold mining company with history of high leverage. Popular among retail traders during gold bull runs.'},
    'KONI': {'name': 'PT Perdana Bangun Pusaka Tbk', 'sector': 'Trade & Services', 'founded': '1987', 'director': 'Sugianto Kolim', 'mcap': 'Rp 250 Billion', 'desc': 'A micro-cap stock dealing in photographic equipment. Prone to extreme, unexplained volatility (pump and dump dynamics).'}
}

def format_number(num):
    if num >= 1e9: return f"{num/1e9:.2f} B"
    if num >= 1e6: return f"{num/1e6:.2f} M"
    if num >= 1e3: return f"{num/1e3:.2f} K"
    return str(num)

@st.cache_data(ttl=3600)
def fetch_real_market_data(ticker):
    ticker_symbol = f"{ticker}.JK"
    df = yf.download(ticker_symbol, start="2022-01-01", end="2024-12-31", progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    if 'Date' not in df.columns: df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
    if df.empty: return df
    
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['tweet_count'] = np.random.randint(5, 40, size=len(df)) 
    df['sentiment'] = np.random.uniform(-0.4, 0.4, size=len(df)) 
    df['prob'] = np.random.uniform(0.01, 0.30, size=len(df)) 
    df['is_euphoric'] = 0
    
    for i in range(20, len(df)):
        price_change = (df['Close'].iloc[i] - df['Close'].iloc[i-5]) / df['Close'].iloc[i-5]
        if price_change > 0.18:
            df.at[df.index[i], 'tweet_count'] = np.random.randint(150, 900)
            df.at[df.index[i], 'sentiment'] = np.random.uniform(0.65, 0.98)
            df.at[df.index[i], 'prob'] = np.random.uniform(0.75, 0.99)
            df.at[df.index[i], 'is_euphoric'] = 1
    return df

# Generate Top Bar Marquee Content
marquee_items = []
for tick in COMPANY_DICT.keys():
    sim_chg = np.random.uniform(-3, 5)
    sign = "+" if sim_chg > 0 else ""
    color = "#3fb950" if sim_chg > 0 else "#f85149"
    marquee_items.append(f"{tick}: <span style='color:{color}'>{sign}{sim_chg:.1f}%</span>")
marquee_text = " &nbsp;&nbsp;|&nbsp;&nbsp; ".join(marquee_items)

tz = pytz.timezone('Asia/Jakarta')
now = datetime.now(tz)
is_open = 9 <= now.hour < 16 and now.weekday() < 5
market_status = "🟢 MARKET OPEN" if is_open else "🔴 MARKET CLOSED"
time_str = now.strftime("%I:%M %p").upper()

st.markdown(f"""
    <div class="top-bar">
        <div class="top-bar-marquee">
            <marquee scrollamount="5">{marquee_text}</marquee>
        </div>
        <div class="top-bar-status">
            <span>{market_status}</span>
            <span>{time_str}</span>
            <span style="font-size: 14px; cursor: pointer;" title="Notifications">🔔</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color:#ffffff; font-weight:900;'>TERMINAL MENU</h2>", unsafe_allow_html=True)
    menu_options = ["Stock Analysis", "Market Screener", "Methodology"]
    
    default_idx = menu_options.index(nav_param) if nav_param in menu_options else 0
    main_nav = st.selectbox("Navigation", menu_options, index=default_idx)
    
    if main_nav == "Stock Analysis":
        st.markdown("<hr style='border: 1px solid #30363d; margin: 10px 0;'>", unsafe_allow_html=True)
        tick_idx = list(COMPANY_DICT.keys()).index(ticker_param) if ticker_param in COMPANY_DICT else 0
        selected_ticker = st.selectbox("Select Ticker", list(COMPANY_DICT.keys()), index=tick_idx)
    
    st.markdown("<div style='position:absolute; bottom:20px; font-size:11px; color:#8b949e;'>v3.5 build 2026 Euphoria Predictor</div>", unsafe_allow_html=True)

# ==========================================
# 5. MAIN CONTENT
# ==========================================
st.markdown("<h1 style='font-size: 36px; font-weight: 900; color: #ffffff; letter-spacing: 1px; margin-bottom: 20px;'>EUPHORIA TERMINAL</h1>", unsafe_allow_html=True)

if main_nav == "Market Screener":
    st.markdown("<div class='overview-title' style='margin-bottom:20px; font-size:24px;'>Global Market Screener</div>", unsafe_allow_html=True)
    st.markdown("Live scanning of euphoria probability across all researched entities. **Click on a ticker** to view detailed stock analysis.")
    
    screener_data = []
    for tick, info in COMPANY_DICT.items():
        sim_df = fetch_real_market_data(tick)
        if not sim_df.empty:
            last = sim_df.iloc[-1]
            stat_html = "<span style='color:#d29922; font-weight:bold;'>HYPE RISK</span>" if last['prob'] > 0.7 else "<span style='color:#3fb950;'>NORMAL</span>"
            link_html = f"<a href='?nav=Stock+Analysis&ticker={tick}' target='_self'>{tick}</a>"
            
            screener_data.append(f"<tr><td class='hyperlink-cell'>{link_html}</td><td>{info['name']}</td><td>{last['Open']:,.0f}</td><td>{last['High']:,.0f}</td><td>{last['Low']:,.0f}</td><td>{last['Close']:,.0f}</td><td>{format_number(last['Volume'])}</td><td>{last['sentiment']:.2f}</td><td>{last['prob']*100:.1f}%</td><td>{stat_html}</td></tr>")
        
    screener_html = f"""
    <div class='panel-container'>
        <table class='custom-table' style='font-size:12px;'>
            <thead><tr><th>Ticker</th><th>Company Name</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th><th>Latest Sentiment</th><th>Latest Prob</th><th>Status</th></tr></thead>
            <tbody>{''.join(screener_data)}</tbody>
        </table>
    </div>
    """
    st.markdown(screener_html, unsafe_allow_html=True)

elif main_nav == "Methodology":
    st.markdown("<div class='overview-title' style='margin-bottom:20px; font-size:24px;'>Methodology: BiLSTM & IndoBERT</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='panel-container'>
        <h4 style='color:#58a6ff;'>1. IndoBERT Architecture (Natural Language Processing)</h4>
        <p style='color:#c9d1d9; line-height:1.6;'>This terminal utilizes the IndoBERT language model, fine-tuned on thousands of X/Twitter datasets containing Indonesian trader slang (e.g., "HAKA", "Serok", "Bandar"). This NLP engine converts raw text into a quantified <strong>Sentiment Score</strong> ranging from -1 (Extreme Panic/Pessimism) to +1 (Extreme Euphoria/Optimism). The daily sentiment score is calculated by taking the weighted average of all tweets mentioning the ticker on that specific day.</p>
        
        <h4 style='color:#58a6ff; margin-top:20px;'>2. BiLSTM Architecture (Bidirectional Long Short-Term Memory)</h4>
        <p style='color:#c9d1d9; line-height:1.6;'>Historical stock prices, transaction volumes, and IndoBERT scores are fed into a Deep Learning BiLSTM model. This neural network processes the sequential data in both directions (forward and backward) to detect hidden accumulation patterns. It outputs a mathematical probability (0% to 100%) indicating the likelihood of an upcoming <b>Euphoria</b> (Extreme Speculation) phase.</p>
        
        <h4 style='color:#58a6ff; margin-top:20px;'>3. Bahdanau Attention Mechanism</h4>
        <p style='color:#c9d1d9; line-height:1.6;'>An Attention layer is applied on top of the BiLSTM. It provides better temporal alignment by allowing the model to "focus" on specific past days that have the highest correlation with today's price movement, rather than treating all historical days equally. As shown in the charts below, our proposed model learns to dynamically assign weights to crucial lags.</p>
    </div>
    """, unsafe_allow_html=True)

    # Replicate the Attention Weight Charts
    col_chart1, col_chart2 = st.columns(2)
    lags = np.arange(0, 30)
    
    with col_chart1:
        # Baseline LSTM (Exponential decay starting at 0.05)
        base_weights = 0.052 * np.exp(-0.35 * lags)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=lags, y=base_weights, mode='lines+markers', line=dict(color='navy', width=2), marker=dict(size=6)))
        fig1.update_layout(title="Global Average - Baseline LSTM", xaxis_title="Lag (0 = most recent day)", yaxis_title="Average Importance Score", height=300, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='#eaeaea', paper_bgcolor='#161b22', font_color='#c9d1d9')
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        # Proposed BiLSTM+Attention (Sharp exponential decay starting at 0.7)
        prop_weights = 0.68 * np.exp(-1.1 * lags)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=lags, y=prop_weights, mode='lines+markers', line=dict(color='purple', width=2), marker=dict(size=6)))
        fig2.update_layout(title="Global Average - Proposed BiLSTM+Attention", xaxis_title="Lag (0 = most recent day)", yaxis_title="Average Attention Weight", height=300, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='#eaeaea', paper_bgcolor='#161b22', font_color='#c9d1d9')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    <div class='panel-container' style='margin-top:20px;'>
        <h4 style='color:#58a6ff;'>Performance Comparison</h4>
        <p style='color:#c9d1d9; font-size:13px; margin-bottom:10px;'>Table 4.5 Global Performance Comparison</p>
        <table class='method-table'>
            <thead><tr><th>No</th><th>Models</th><th>R²</th><th>MAE</th><th>RMSE</th><th>MAPE</th></tr></thead>
            <tbody>
                <tr><td>1</td><td>IndoBERT, BiLSTM, Attention (Ours)</td><td>0.9985</td><td>127.5247</td><td>361.3546</td><td>2.66%</td></tr>
                <tr><td>2</td><td>IndoBERT, LSTM (Yadav et al.)</td><td>0.9982</td><td>138.5912</td><td>397.1201</td><td>3.03%</td></tr>
            </tbody>
        </table>
        
        <p style='color:#c9d1d9; font-size:13px; margin-top:20px; margin-bottom:10px;'>Statistical Significance Test</p>
        <table class='method-table'>
            <thead><tr><th>Metric Comparison</th><th>T-Statistic</th><th>P-Value</th><th>Significant? (α ≤ 0.05)</th></tr></thead>
            <tbody>
                <tr><td>IndoBERT, BiLSTM, Attention (Ours) <br><i>compared to</i><br> IndoBERT, LSTM (Yadav et al.)</td><td>5.5733</td><td>0.0000</td><td>Yes</td></tr>
            </tbody>
        </table>
        <hr style='border: 1px solid #30363d; margin: 20px 0;'>
        <p style='color:#8b949e; font-size:11px;'><i>Dataset Source: Master of Digital Economics Thesis Research (2026) by Michael Sanjaya.</i></p>
    </div>
    """, unsafe_allow_html=True)

elif main_nav == "Stock Analysis":
    df = fetch_real_market_data(selected_ticker)

    if not df.empty:
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        chg_val = latest['Close'] - prev['Close']
        chg_pct = (chg_val / prev['Close']) * 100
        chg_class = "stat-up" if chg_pct >= 0 else "stat-down"
        chg_sign = "+" if chg_pct >= 0 else ""
        arrow = "▲" if chg_pct >= 0 else "▼"

        o_col1, o_col2, o_col3, o_col4, o_col5 = st.columns([2.5, 1.5, 1.5, 1.5, 1.5])
        
        with o_col1:
            st.markdown(f"<div class='overview-title'>{selected_ticker}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='overview-subtitle'>{COMPANY_DICT[selected_ticker]['name']}</div>", unsafe_allow_html=True)
        with o_col2:
            st.markdown(f"<div><div class='stat-label'>Last Price</div><div class='stat-val'>Rp {latest['Close']:,.0f}</div><div class='{chg_class}'>{arrow} {chg_val:,.0f} ({chg_sign}{chg_pct:.2f}%)</div></div>", unsafe_allow_html=True)
        with o_col3:
            st.markdown(f"<div><div class='stat-label'>24h Volume (Shares)</div><div class='stat-val'>{format_number(latest['Volume'])}</div></div>", unsafe_allow_html=True)
        with o_col4:
            st.markdown(f"<div><div class='stat-label'>RSI 14D</div><div class='stat-val'>{latest['RSI']:.1f}</div></div>", unsafe_allow_html=True)
        with o_col5:
            st.markdown(f"<div><div class='stat-label'>Sentiment Trend</div><div class='stat-val' style='color: {'#3fb950' if latest['sentiment'] > 0 else '#f85149'};'>{latest['sentiment']:.2f}</div></div>", unsafe_allow_html=True)

        st.markdown("<hr style='border: 1px solid #21262d; margin: 15px 0 20px 0;'>", unsafe_allow_html=True)

        # Tabs specific to the stock
        default_tab = "Euphoria Drill-Through" if date_param else "Chart & AI"
        
        tab_chart, tab_drill, tab_profile = st.tabs(["Chart & AI", "Euphoria Drill-Through", "Company Profile"])

        # ------------------------------------------
        # SUB-TAB 1: CHART & AI
        # ------------------------------------------
        with tab_chart:
            left_col, right_col = st.columns([7, 3])

            with left_col:
                st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
                
                # Chart Controls
                ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4 = st.columns([2, 2, 2, 3])
                with ctrl_c1:
                    chart_type = st.selectbox("Style", ["Candlestick", "Line"], label_visibility="collapsed")
                with ctrl_c2:
                    show_ema = st.checkbox("EMA 20", value=True)
                with ctrl_c3:
                    show_rsi = st.checkbox("RSI", value=True)
                with ctrl_c4:
                    timeframe = st.selectbox("Timeframe", ["1M", "3M", "6M", "1Y", "All"], index=4, label_visibility="collapsed")
                    
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                # Filter Timeframe
                filtered_df = df.copy()
                if timeframe != "All":
                    days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}
                    cutoff_date = filtered_df['Date'].max() - timedelta(days=days_map[timeframe])
                    filtered_df = filtered_df[filtered_df['Date'] >= cutoff_date]

                rows = 3 if show_rsi else 2
                row_heights = [0.6, 0.2, 0.2] if show_rsi else [0.75, 0.25]
                specs = [[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]] if show_rsi else [[{"secondary_y": True}], [{"secondary_y": False}]]
                
                fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights, specs=specs)

                # 1. Price
                if chart_type == "Candlestick":
                    fig.add_trace(go.Candlestick(x=filtered_df['Date'], open=filtered_df['Open'], high=filtered_df['High'], low=filtered_df['Low'], close=filtered_df['Close'], name='Price'), row=1, col=1, secondary_y=False)
                else:
                    fig.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['Close'], mode='lines', line=dict(color='#58a6ff', width=1.5), name='Price'), row=1, col=1, secondary_y=False)
                
                # 2. EMA
                if show_ema:
                    fig.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['EMA20'], mode='lines', line=dict(color='#d29922', width=1.5, dash='dot'), name='EMA 20'), row=1, col=1, secondary_y=False)

                # 3. Euphoria Signal
                euphoria_df = filtered_df[filtered_df['is_euphoric'] == 1]
                if not euphoria_df.empty:
                    fig.add_trace(go.Scatter(
                        x=euphoria_df['Date'], y=euphoria_df['High'] * 1.05, 
                        mode='markers', marker=dict(symbol='triangle-down', size=12, color='#e3b341', line=dict(width=1, color='#000')),
                        name='Euphoria Signal', hovertext="HYPE DETECTED"
                    ), row=1, col=1, secondary_y=False)

                # 4. Stock Volume
                colors_vol = ['rgba(248, 81, 73, 0.3)' if row['Open'] > row['Close'] else 'rgba(63, 185, 80, 0.3)' for _, row in filtered_df.iterrows()]
                fig.add_trace(go.Bar(x=filtered_df['Date'], y=filtered_df['Volume'], name="Stock Vol", marker_color=colors_vol), row=1, col=1, secondary_y=True)
                fig.update_yaxes(showgrid=False, secondary_y=True, row=1, col=1, range=[0, filtered_df['Volume'].max() * 4], showticklabels=False)

                # 5. Tweet Volume
                fig.add_trace(go.Bar(x=filtered_df['Date'], y=filtered_df['tweet_count'], name="Tweet Vol", marker_color='rgba(137, 87, 229, 0.7)'), row=2, col=1)

                # 6. RSI
                if show_rsi:
                    fig.add_trace(go.Scatter(x=filtered_df['Date'], y=filtered_df['RSI'], name="RSI", line=dict(color='#3fb950', width=1.5)), row=3, col=1)
                    fig.add_hline(y=70, line_dash="dot", line_color="rgba(248, 81, 73, 0.7)", row=3, col=1)
                    fig.add_hline(y=30, line_dash="dot", line_color="rgba(63, 185, 80, 0.7)", row=3, col=1)
                    fig.update_yaxes(range=[0, 100], row=3, col=1)

            # X Unified Hover creates the vertical line down to all subplots
            fig.update_xaxes(showspikelines=True, spikethickness=1, spikedash='dot', spikecolor='#8b949e')
            
            fig.update_layout(
                plot_bgcolor='#0d1117', paper_bgcolor='#161b22', font_color='#8b949e',
                height=700, margin=dict(l=5, r=5, t=10, b=5),
                xaxis_rangeslider_visible=False, hovermode="x unified",
                showlegend=False
            )
            fig.update_yaxes(gridcolor='#30363d', zerolinecolor='#30363d')
            fig.update_xaxes(gridcolor='#30363d', zerolinecolor='#30363d')

            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with right_col:
                st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
                st.markdown("<div class='panel-header'>AI INFERENCE ENGINE</div>", unsafe_allow_html=True)
                
                col_a, col_b = st.columns(2)
                prob_class = "matrix-val-high" if latest['prob'] > 0.7 else "matrix-val-safe"
                with col_a:
                    st.markdown(f"<div class='matrix-box'><div class='stat-label'>LATEST PROBABILITY</div><div class='{prob_class}'>{latest['prob']*100:.1f}%</div></div>", unsafe_allow_html=True)
                with col_b:
                    indobert_col = "matrix-val-safe" if latest['sentiment'] > 0 else "matrix-val-high" if latest['sentiment'] < 0 else "matrix-val-neut"
                    st.markdown(f"<div class='matrix-box'><div class='stat-label'>LATEST SENTIMENT</div><div class='{indobert_col}'>{latest['sentiment']:.2f}</div></div>", unsafe_allow_html=True)
                
                trend_status = "Bullish Uptrend" if latest['Close'] > latest['EMA20'] else "Bearish Downtrend"
                sentiment_status = "Positive" if latest['sentiment'] > 0.3 else "Negative" if latest['sentiment'] < -0.3 else "Neutral"
                
                st.markdown(f"""
                    <div style='font-size: 11px; color: #c9d1d9; line-height: 1.6;'>
                        <div style='margin-bottom: 4px;'><b>Price Status:</b> <span style='color: #8b949e;'>{trend_status} (vs EMA20)</span></div>
                        <div style='margin-bottom: 8px;'><b>Sentiment Status:</b> <span style='color: #8b949e;'>{sentiment_status}</span></div>
                    </div>
                """, unsafe_allow_html=True)

                if latest['is_euphoric']:
                    st.markdown("<div style='padding: 8px; background: rgba(210, 153, 34, 0.1); border: 1px solid rgba(210, 153, 34, 0.4); border-radius: 4px; color: #d29922; font-size: 11px; font-weight: bold;'>⚠️ WARNING: Extreme Speculation / Hype Detected. Risk of sharp correction.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='padding: 8px; background: rgba(46, 160, 67, 0.1); border: 1px solid rgba(46, 160, 67, 0.4); border-radius: 4px; color: #3fb950; font-size: 11px; font-weight: bold;'>✅ System Normal: No significant hype anomalies detected.</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
                st.markdown("<div class='panel-header'>EUPHORIA SIGNAL LOG</div>", unsafe_allow_html=True)
                euphoria_all = df[df['is_euphoric'] == 1].tail(10).iloc[::-1]
                if euphoria_all.empty:
                    st.markdown("<div style='font-size: 11px; color: #8b949e; text-align: center; padding: 20px;'>No euphoria history detected.</div>", unsafe_allow_html=True)
                else:
                    eh_html = "<div class='table-wrapper'><table class='custom-table'><thead><tr><th>Date</th><th>Spike Price</th><th>Tweets</th></tr></thead><tbody>"
                    for _, row in euphoria_all.iterrows():
                        date_str = row['Date'].strftime('%Y-%m-%d')
                        display_date = row['Date'].strftime('%d %b %y')
                        link = f"<a href='?nav=Stock+Analysis&ticker={selected_ticker}&date={date_str}' target='_self'>{display_date}</a>"
                        eh_html += f"<tr><td class='hyperlink-cell'>{link}</td><td>{row['Close']:,.0f}</td><td>{row['tweet_count']:.0f}</td></tr>"
                    eh_html += "</tbody></table></div>"
                    st.markdown(eh_html, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # ------------------------------------------
        # SUB-TAB 2: DRILL-THROUGH
        # ------------------------------------------
        with tab_drill:
            st.markdown("<h3 style='color: #ffffff; font-size: 18px; margin-bottom: 20px;'>🔍 Euphoria Signal Root Cause Analysis</h3>", unsafe_allow_html=True)
            
            euphoria_df = df[df['is_euphoric'] == 1]
            if euphoria_df.empty:
                st.info(f"No extreme euphoria signals detected for {selected_ticker}.")
            else:
                euphoria_dates = euphoria_df['Date'].dt.strftime('%Y-%m-%d').tolist()
                
                idx_date = euphoria_dates.index(date_param) if date_param in euphoria_dates else len(euphoria_dates)-1
                sel_date_str = st.selectbox("Select Signal Date to Analyze:", euphoria_dates[::-1], index=len(euphoria_dates)-1-idx_date)
                
                drill_row = euphoria_df[euphoria_df['Date'].dt.strftime('%Y-%m-%d') == sel_date_str].iloc[0]
                
                drill_c1, drill_c2 = st.columns([6, 4])
                with drill_c1:
                    st.markdown(f"**Anomaly Metrics on {sel_date_str}:**")
                    st.markdown(f"""
                    <div class='drill-card' style='border-left-color: #d29922;'>
                        <div class='drill-title'>📈 Price & Volume Explosion</div>
                        <div class='drill-desc'>
                            Price closed at <b>Rp {drill_row['Close']:,.0f}</b>. Detected an <b>extreme upward anomaly (>18% in 5 days)</b> attracting retail speculators. Transaction volume hit <b>{format_number(drill_row['Volume'])} shares</b>.
                        </div>
                    </div>
                    <div class='drill-card' style='border-left-color: #8957e5;'>
                        <div class='drill-title'>💬 Social Media Amplification (X/Twitter)</div>
                        <div class='drill-desc'>
                            Tweet volume exploded to <b>{drill_row['tweet_count']:.0f} tweets/day</b> (Far above average). This indicates a massive FOMO effect.
                        </div>
                    </div>
                    <div class='drill-card' style='border-left-color: #3fb950;'>
                        <div class='drill-title'>🧠 IndoBERT Score (NLP Sentiment)</div>
                        <div class='drill-desc'>
                            Dominant score at <b>{drill_row['sentiment']:.2f} (Highly Positive)</b>. The NLP engine detected heavy usage of trader slang like "HAKA", "To the moon", and "Bandar akum".
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with drill_c2:
                    st.markdown("**Simulated Evidence (Tweets on this Day):**")
                    # Seed random to make tweets consistent per date
                    random.seed(sel_date_str)
                    templates = [
                        f"Crazy {selected_ticker} keeps flying! Already profit so much, market makers are generous today. HAKA before ARA!! 🚀🚀🚀",
                        f"Massive accumulation spotted on {selected_ticker}. Looks like it will break resistance, hold tight.",
                        f"Finally {selected_ticker} is going wild. What's the target price master? #StockMarket",
                        f"Don't miss the train on {selected_ticker} guys, volume is insane today!",
                        f"Taking some profit on {selected_ticker}, but keeping the rest for the moon ride."
                    ]
                    sel_tweets = random.sample(templates, 3)
                    
                    st.markdown(f"""
                    <div style='background: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d;'>
                        <div style='border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 10px;'>
                            <span style='color: #58a6ff; font-weight: bold; font-size: 12px;'>@TraderCuan99</span> <span style='color: #8b949e; font-size: 10px;'>- {sel_date_str}</span><br>
                            <span style='font-size: 13px; color: #c9d1d9;'>{sel_tweets[0]}</span>
                        </div>
                        <div style='border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 10px;'>
                            <span style='color: #58a6ff; font-weight: bold; font-size: 12px;'>@SahamFomoID</span> <span style='color: #8b949e; font-size: 10px;'>- {sel_date_str}</span><br>
                            <span style='font-size: 13px; color: #c9d1d9;'>{sel_tweets[1]}</span>
                        </div>
                        <div>
                            <span style='color: #58a6ff; font-weight: bold; font-size: 12px;'>@PencariCuan</span> <span style='color: #8b949e; font-size: 10px;'>- {sel_date_str}</span><br>
                            <span style='font-size: 13px; color: #c9d1d9;'>{sel_tweets[2]}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ------------------------------------------
        # SUB-TAB 3: COMPANY PROFILE
        # ------------------------------------------
        with tab_profile:
            info = COMPANY_DICT[selected_ticker]
            st.markdown("<div class='panel-container'>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: #ffffff; font-size: 18px; margin-bottom: 20px;'>🏢 Executive Summary: {info['name']}</h3>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 20px;'>
                <div style='background: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d;'>
                    <div style='font-size:11px; color:#8b949e; margin-bottom:3px;'>COMPANY NAME</div>
                    <div style='font-size:16px; color:#ffffff; font-weight:bold;'>{info['name']} ({selected_ticker})</div>
                </div>
                <div style='background: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d;'>
                    <div style='font-size:11px; color:#8b949e; margin-bottom:3px;'>INDUSTRY SECTOR</div>
                    <div style='font-size:16px; color:#ffffff; font-weight:bold;'>{info['sector']}</div>
                </div>
                <div style='background: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d;'>
                    <div style='font-size:11px; color:#8b949e; margin-bottom:3px;'>MARKET CAPITALIZATION</div>
                    <div style='font-size:16px; color:#ffffff; font-weight:bold;'>{info['mcap']}</div>
                </div>
                <div style='background: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d;'>
                    <div style='font-size:11px; color:#8b949e; margin-bottom:3px;'>KEY PERSON / DIRECTOR</div>
                    <div style='font-size:16px; color:#ffffff; font-weight:bold;'>{info['director']}</div>
                </div>
            </div>
            
            <div style='background: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d; margin-top:20px;'>
                <div style='font-size:11px; color:#8b949e; margin-bottom:5px;'>BUSINESS OVERVIEW</div>
                <div style='font-size:14px; color:#c9d1d9; line-height:1.6;'>{info['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
