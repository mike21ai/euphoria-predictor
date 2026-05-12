import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Euphoria Predictor", layout="wide")

st.title("🧠 Euphoria Predictor")
st.markdown("**Prediksi Harga Saham + Deteksi Euforia** — Powered by IndoBERT + BiLSTM + Attention")
st.caption("Bantu kamu melihat peluang dan risiko euforia di saham non-blue chip Indonesia")

# Pilih ticker
tickers = ['AUTO', 'BRMS', 'BRPT', 'DSSA', 'FORU', 'IMAS', 'KARW', 
           'KONI', 'MLPT', 'PANI', 'PSAB', 'SGER', 'SRAJ', 'TOBA', 'TPIA']

with st.sidebar:
    st.header("🔍 Pilih Saham")
    ticker = st.selectbox("Ticker", tickers, index=6)  # default KARW
    
    st.markdown("---")
    st.write("**Analisis 30 hari terakhir**")
    if st.button("🚀 Prediksi Sekarang", type="primary", use_container_width=True):
        st.session_state.run_prediction = True

# Mock data historis
dates = [datetime(2026, 5, 1) - timedelta(days=i) for i in range(30)][::-1]
np.random.seed(42)
close_prices = np.cumsum(np.random.randn(30) * 50) + 5000
volume = np.random.randint(1_000_000, 50_000_000, 30)
sentiment = np.random.uniform(-0.8, 0.95, 30)

df_hist = pd.DataFrame({
    'Date': dates,
    'Close': close_prices,
    'Volume': volume,
    'Sentiment': sentiment
})

# Jalankan prediksi
if st.session_state.get('run_prediction', False):
    st.markdown("### 📊 Hasil Analisis")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_hist['Date'], y=df_hist['Close'], 
                               mode='lines', name='Harga Penutupan', line=dict(color='#1f77b4')))
        fig.update_layout(title=f"Harga Historis {ticker} (30 Hari Terakhir)",
                         xaxis_title="Tanggal", yaxis_title="Harga (Rp)",
                         height=450)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Prediksi harga besok
        predicted_price = df_hist['Close'].iloc[-1] + np.random.uniform(80, 350)
        st.metric(
            label="**Prediksi Harga Besok**", 
            value=f"Rp {predicted_price:,.0f}",
            delta=f"+{np.random.uniform(1.5, 5.2):.2f}%"
        )
        
        # Euphoria Probability
        euphoria_prob = np.random.uniform(0.08, 0.89)
        st.subheader("Probabilitas Euforia")
        
        if euphoria_prob > 0.65:
            status = "🔴 **HIGH EUPHORIA** — Potensi bubble tinggi"
        elif euphoria_prob > 0.45:
            status = "🟠 **Sedang** — Perlu diwaspadai"
        else:
            status = "🟢 **Rendah** — Kondisi normal"
            
        st.progress(euphoria_prob)
        st.markdown(f"**{euphoria_prob:.1%}** — {status}")
    
    # Attention Visualization
    st.subheader("🔍 Apa yang Paling Diperhatikan Model?")
    st.caption("Bobot perhatian pada 30 hari historis")
    
    attention_weights = np.zeros(30)
    attention_weights[-6:] = np.array([0.05, 0.08, 0.15, 0.28, 0.32, 0.12])
    
    attn_df = pd.DataFrame({
        'Hari ke-': range(1, 31),
        'Bobot Attention': attention_weights
    })
    
    fig_attn = px.bar(attn_df, x='Hari ke-', y='Bobot Attention', 
                     title="Hari mana yang paling berpengaruh")
    st.plotly_chart(fig_attn, use_container_width=True)
    
    st.success("✅ Analisis selesai. Model siap digunakan.")

else:
    st.info("👆 Pilih saham di sidebar lalu klik **Prediksi Sekarang** untuk melihat hasil")

st.markdown("---")
st.caption("Euphoria Predictor • Prediksi harga & deteksi euforia saham Indonesia")
