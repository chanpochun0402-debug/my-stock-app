import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 網頁基本配置
st.set_page_config(page_title="獵人專業分析站", layout="wide")

# CSS 強制極致黑背景
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    [data-testid="stHeader"] { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #111111; }
    </style>
    """, unsafe_allow_html=True)

# 2. 側邊欄：更新後的股票清單
stock_dict = {
    "2344 華邦電": "2344.TW",
    "00981A 凱基美國優選債": "00981A.TW",
    "009816 凱基美國優選債(月)": "009816.TW",
    "00982A 凱基A級公司債": "00982A.TW",
    "1711 永光": "1711.TW"
}

st.sidebar.markdown("### 🛠️ 監控清單")
selected_label = st.sidebar.selectbox("選擇觀測標的", list(stock_dict.keys()))
target_id = stock_dict[selected_label]
view_days = st.sidebar.slider("顯示天數", 30, 250, 100)

st.title(f"📊 {selected_label} 技術觀測站")

# 3. 抓取數據與指標計算
@st.cache_data(ttl=60)
def fetch_full_analysis(ticker, days):
    # 抓取較長歷史確保指標準確
    df = yf.download(ticker, period="1y", interval="1d")
    if df.empty: return None
    
    # 計算 KD (9, 3, 3)
    low_9 = df['Low'].rolling(window=9).min()
    high_9 = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_9) / (high_9 - low_9) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    return df.tail(days)

try:
    data = fetch_full_analysis(target_id, view_days)
    
    if data is not None:
        # 4. 建立三層子圖：K線 / 成交量(圖二) / KD線
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03, 
            row_heights=[0.55, 0.15, 0.3]
        )

        # --- 第一層：K線圖 ---
        fig.add_trace(go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            name="K線", increasing_line_color='#FF3232', decreasing_line_color='#00FF00'
        ), row=1, col=1)

        # --- 第二層：成交量柱狀圖 (圖二要求的圖示) ---
        # 根據漲跌給成交量顏色
        vol_colors = ['#FF3232' if c >= o else '#00FF00' for o, c in zip(data['Open'], data['Close'])]
        fig.add_trace(go.Bar(
            x=data.index, y=data['Volume'], name="成交量",
            marker_color=vol_colors, opacity=0.8
        ), row=2, col=1)

        # --- 第三層：KD 線 ---
        fig.add_trace(go.Scatter(x=data.index, y=data['K'], name="K值 (黃)", line=dict(color='#FFD700', width=2)), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['D'], name="D值 (藍)", line=dict(color='#1E90FF', width=2)), row=3, col=1)

        # 80/20 參考線
        fig.add_hline(y=80, line_dash="dash", line_color="rgba(255,50,50,0.3)", row=3, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="rgba(0,255,0,0.3)", row=3, col=1)

        # 5. 圖表視覺與 Y 軸自動對焦設定
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='black',
            plot_bgcolor='black',
            height=900,
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False
        )
        
        # 【解決漆黑問題的關鍵】
        fig.update_yaxes(autorange=True, fixedrange=False, row=1, col=1) # K線自動縮放
        fig.update_yaxes(showticklabels=False, row=2, col=1)            # 成交量隱藏標籤
        fig.update_yaxes(range=[0, 100], row=3, col=1)                 # KD固定區間
        
        st.plotly_chart(fig, use_container_width=True)

        # 6. 即時診斷
        k_val, d_val = data['K'].iloc[-1], data['D'].iloc[-1]
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("K值", f"{k_val:.2f}", f"{(k_val-data['K'].iloc[-2]):.2f}")
        with col2:
            st.metric("D值", f"{d_val:.2f}", f"{(d_val-data['D'].iloc[-2]):.2f}")
            
    else:
        st.error("查無數據，請確認 GitHub 網路連線或代號是否正確。")

except Exception as e:
    st.error(f"系統錯誤: {e}")