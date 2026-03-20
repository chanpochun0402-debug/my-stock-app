import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 頁面基本配置
st.set_page_config(page_title="獵人專業分析站", layout="wide")

# CSS 強制極致黑背景
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    [data-testid="stHeader"] { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #111111; }
    </style>
    """, unsafe_allow_html=True)

# 2. 側邊欄：設定股票名稱對應代號
stock_dict = {
    "2344 華邦電": "2344.TW",
    "009816 凱基美國優選債": "009816.TW",
    "00983A 凱基美國A級債": "00983A.TW",
    "1711 永光": "1711.TW",
    "2330 台積電": "2330.TW"
}

st.sidebar.title("🛠️ 監控清單")
selected_label = st.sidebar.selectbox("選擇觀測標的", list(stock_dict.keys()))
target_id = stock_dict[selected_label]
view_days = st.sidebar.slider("顯示天數", 30, 200, 100)

st.title(f"📊 {selected_label} 技術觀測站")

# 3. 抓取數據與 KD 計算
@st.cache_data(ttl=60)
def fetch_and_calc(ticker, days):
    # 多抓一點歷史數據確保 KD 計算準確 (需要前 9 天的資料)
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
    data = fetch_and_calc(target_id, view_days)
    
    if data is not None:
        # 4. 建立子圖 (上 K 線，下 KD)
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05, 
            row_heights=[0.7, 0.3]
        )

        # 上圖：K線 (紅漲綠跌)
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'], high=data['High'], 
            low=data['Low'], close=data['Close'],
            name="K線",
            increasing_line_color='#FF3232', 
            decreasing_line_color='#00FF00'
        ), row=1, col=1)

        # 下圖：KD 線
        fig.add_trace(go.Scatter(x=data.index, y=data['K'], name="K值 (黃)", line=dict(color='#FFD700', width=2)), row=2, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['D'], name="D值 (藍)", line=dict(color='#1E90FF', width=2)), row=2, col=1)

        # 加入 80/20 參考線
        fig.add_hline(y=80, line_dash="dash", line_color="rgba(255,0,0,0.3)", row=2, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="rgba(0,255,0,0.3)", row=2, col=1)

        # 5. 圖表視覺樣式
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='black',
            plot_bgcolor='black',
            height=750,
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        # 強制 Y 軸自動縮放，確保 K 線不會消失
        fig.update_yaxes(autorange=True, fixedrange=False, row=1, col=1)
        
        st.plotly_chart(fig, use_container_width=True)

        # 6. 即時數據看板
        curr_k = data['K'].iloc[-1]
        curr_d = data['D'].iloc[-1]
        st.markdown("---")
        k1, k2, k3 = st.columns(3)
        k1.write(f"今日 K 值: **{curr_k:.2f}**")
        k2.write(f"今日 D 值: **{curr_d:.2f}**")
        k3.write("狀態: " + ("🔥 黃金交叉" if curr_k > curr_d else "❄️ 死亡交叉"))

    else:
        st.error("無法抓取數據，請檢查網路或代號。")

except Exception as e:
    st.error(f"系統錯誤: {e}")