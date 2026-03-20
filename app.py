import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 網頁基本配置
st.set_page_config(page_title="獵人專業分析站", layout="wide")

# 強制極致黑背景 CSS
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    [data-testid="stHeader"] { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #111111; }
    </style>
    """, unsafe_allow_html=True)

# 2. 側邊欄：設定股票名稱與代號
stock_dict = {
    "2344 華邦電": "2344.TW",
    "00983A 凱基美國A級債": "00983A.TW",
    "009816 凱基美國優選債": "009816.TW",
    "1711 永光": "1711.TW"
}

st.sidebar.markdown("### 🛠️ 監控清單")
selected_label = st.sidebar.selectbox("選擇觀測標的", list(stock_dict.keys()))
target_id = stock_dict[selected_label]
view_days = st.sidebar.slider("顯示天數", 30, 250, 100)

st.title(f"📊 {selected_label} 技術觀測站")

# 3. 抓取數據與計算指標
@st.cache_data(ttl=60)
def fetch_analysis_data(ticker, days):
    # 抓取較長數據以計算指標
    raw = yf.download(ticker, period="1y", interval="1d")
    if raw.empty: return None
    
    # 計算 KD (9, 3, 3)
    low_9 = raw['Low'].rolling(window=9).min()
    high_9 = raw['High'].rolling(window=9).max()
    rsv = (raw['Close'] - low_9) / (high_9 - low_9) * 100
    raw['K'] = rsv.ewm(com=2).mean()
    raw['D'] = raw['K'].ewm(com=2).mean()
    
    return raw.tail(days)

try:
    data = fetch_analysis_data(target_id, view_days)
    
    if data is not None:
        # 4. 建立子圖 (K線/成交量/KD線)
        # 增加一列來放圖二要求的成交量走勢
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03, 
            row_heights=[0.6, 0.15, 0.25]
        )

        # --- A. K線圖 (上) ---
        fig.add_trace(go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            name="K線", increasing_line_color='#FF3232', decreasing_line_color='#00FF00'
        ), row=1, col=1)

        # --- B. 即時成交量 (中) - 參考圖二圖示 ---
        fig.add_trace(go.Bar(
            x=data.index, y=data['Volume'], name="成交量",
            marker_color='rgba(0, 255, 0, 0.5)', showlegend=False
        ), row=2, col=1)

        # --- C. KD 指標 (下) ---
        fig.add_trace(go.Scatter(x=data.index, y=data['K'], name="K值 (黃)", line=dict(color='#FFD700', width=2)), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['D'], name="D值 (藍)", line=dict(color='#1E90FF', width=2)), row=3, col=1)

        # KD 參考線
        fig.add_hline(y=80, line_dash="dash", line_color="rgba(255,0,0,0.3)", row=3, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="rgba(0,255,0,0.3)", row=3, col=1)

        # 5. 視覺化樣式設定
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='black',
            plot_bgcolor='black',
            height=850,
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        # 【關鍵修復】自動調整 Y 軸，不讓 K 線消失
        fig.update_yaxes(autorange=True, fixedrange=False, row=1, col=1)
        fig.update_yaxes(showticklabels=False, row=2, col=1) # 隱藏成交量數值
        fig.update_yaxes(range=[0, 100], row=3, col=1)       # KD 固定 0-100
        
        st.plotly_chart(fig, use_container_width=True)

        # 6. 即時診斷
        curr_k = data['K'].iloc[-1]
        curr_d = data['D'].iloc[-1]
        st.markdown("---")
        k1, k2, k3 = st.columns(3)
        k1.metric("今日 K 值", f"{curr_k:.2f}")
        k2.metric("今日 D 值", f"{curr_d:.2f}")
        k3.info("趨勢：" + ("🔥 多方強勢" if curr_k > curr_d else "❄️ 整理修正"))

    else:
        st.error("目前無法獲取數據，請確認網路連線或稍後再試。")

except Exception as e:
    st.error(f"系統錯誤: {e}")