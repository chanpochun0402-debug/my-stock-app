import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 網頁基本配置 (極致黑)
st.set_page_config(page_title="獵人專業分析站", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    [data-testid="stHeader"] { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #111111; }
    </style>
    """, unsafe_allow_html=True)

# 2. 側邊欄：更新股票清單 (移除 00983A，新增 00981A、00982A)
stock_dict = {
    "2344 華邦電": "2344.TW",
    "00981A 凱基美國優選債": "00981A.TW",
    "00982A 凱基A級公司債": "00982A.TW",
    "009816 凱基美國優選債(月)": "009816.TW",
    "1711 永光": "1711.TW"
}

st.sidebar.title("🛠️ 監控清單")
selected_label = st.sidebar.selectbox("選擇觀測標的", list(stock_dict.keys()))
target_id = stock_dict[selected_label]
view_days = st.sidebar.slider("顯示天數", 30, 250, 100)

st.title(f"📊 {selected_label} 技術觀測")

# 3. 抓取數據與指標計算
@st.cache_data(ttl=60)
def get_analysis_data(ticker, days):
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
    data = get_analysis_data(target_id, view_days)
    
    if data is not None:
        # 4. 建立三層子圖 (K線 / 成交量 / KD)
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.04, 
            row_heights=[0.5, 0.2, 0.3]
        )

        # --- A. K線圖 ---
        fig.add_trace(go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            name="K線", increasing_line_color='#FF3232', decreasing_line_color='#00FF00'
        ), row=1, col=1)

        # --- B. 成交量圖 (圖二要求的圖示) ---
        v_cols = ['#FF3232' if c >= o else '#00FF00' for o, c in zip(data['Open'], data['Close'])]
        fig.add_trace(go.Bar(
            x=data.index, y=data['Volume'], name="成交量",
            marker_color=v_cols, opacity=0.9
        ), row=2, col=1)

        # --- C. KD 指標 ---
        fig.add_trace(go.Scatter(x=data.index, y=data['K'], name="K(黃)", line=dict(color='#FFD700', width=2)), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['D'], name="D(藍)", line=dict(color='#1E90FF', width=2)), row=3, col=1)

        # 5. 視覺美化：年月份字體加大、變白
        fig.update_layout(
            template="plotly_dark", paper_bgcolor='black', plot_bgcolor='black',
            height=850, xaxis_rangeslider_visible=False, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        # X軸年月份樣式 (加大變白)
        fig.update_xaxes(
            tickfont=dict(color='white', size=18, family="Arial Black"),
            gridcolor='rgba(255,255,255,0.1)',
            row=3, col=1
        )
        
        # 強制 Y 軸自動縮放 (確保 00981A 這種 15 元的價格能看清楚 K 線)
        fig.update_yaxes(autorange=True, fixedrange=False, tickfont=dict(color='white', size=14), row=1, col=1)
        fig.update_yaxes(showticklabels=False, row=2, col=1) 
        fig.update_yaxes(range=[0, 100], tickfont=dict(color='white', size=14), row=3, col=1)
        
        st.plotly_chart(fig, use_container_width=True)

        # 6. 底部數據
        k, d = data['K'].iloc[-1], data['D'].iloc[-1]
        st.markdown(f"### 💡 當前狀態：K值 **{k:.2f}** / D值 **{d:.2f}** （{'🔥黃金交叉' if k>d else '❄️空方整理'}）")

    else:
        st.error("查無數據，請確認代號或 GitHub 狀態。")

except Exception as e:
    st.error(f"錯誤: {e}")