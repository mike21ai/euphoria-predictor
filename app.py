# ... existing code ...
                fig.update_layout(
                    plot_bgcolor='#0d1117', paper_bgcolor='#161b22', font_color='#8b949e',
                    height=chart_height, margin=dict(l=5, r=5, t=10, b=5),
                    xaxis_rangeslider_visible=False, hovermode="x unified",
                    showlegend=False
                )
                
                # Menggunakan metode update standar tanpa konfigurasi spike yang berisiko error
                fig.update_xaxes(gridcolor='#30363d', zerolinecolor='#30363d')
                fig.update_yaxes(gridcolor='#30363d', zerolinecolor='#30363d')

                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
# ... existing code ...
```

### Mengapa ini akan berhasil?
*   Kita menghapus baris `fig.update_xaxes(showspikelines=True, ...)` yang memicu `ValueError` karena ketidakcocokan argumen di server Streamlit Cloud.
*   Kita menggantinya dengan `fig.update_xaxes(gridcolor=..., zerolinecolor=...)` yang merupakan cara paling aman dan stabil untuk mengatur estetika sumbu di Plotly.
*   Karena Anda menggunakan `hovermode="x unified"` pada `fig.update_layout`, fitur garis vertikal (garis panduan saat *hover*) **akan tetap muncul secara otomatis** tanpa perlu konfigurasi `spikelines` manual yang memicu *error* tersebut.

Silakan *copy-paste* ke baris 373 di `app.py` Anda, *commit*, dan pratinjau Anda akan langsung berjalan normal!
