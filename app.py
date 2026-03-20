import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 網頁基本配置
st.set_page_config(page_title="獵人專業分析站", layout="wide")

# 【核心視覺修正】強制左側與底部文字白化、加大
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    [data-testid="stHeader"] { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #0d0d0d !important; }

    /* 左側邊欄所有文字：純白、超粗、加大 */
    section[data-testid="stSidebar"] .stMarkdown h3, 
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stSlider p {
        color: #FFFFFF !important;
        font-size: 22px !important;
        font-weight: 900 !important;
        text-shadow: 1px 1px 2px #000;
    }

    /* 下拉選單文字 */
    div[data-baseweb="select"] > div {
        color: #FFFFFF !important;
        font-size: 18px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 側邊欄：更新股票清單
stock_dict = {
    "2344 華邦電": "2344.TW",
    "00981A 凱基美國優選債": "00981A.TW",
    "00982A 凱基A級公司債": "00982A.TW",
    "009816 凱基美國優選債(月)": "009816.TW",
    "1711 永光": "1711.TW"
}

st.sidebar.markdown("### 🛠️ 監控清單")
selected_label = st.sidebar.selectbox("選擇觀測標的", list(stock_dict.keys()))
target_id = stock_dict[selected_label]
view_days = st.sidebar.slider("顯示天數", 30, 250, 100)

st.title(f"📊 {selected_label} 技術觀測站")

# 3. 數據抓取與計算
@st.cache_data(ttl=60)
def fetch_stock_data(ticker, days):
    df = yf.download(ticker, period="1y", interval="1d")
    if df.empty: return None
    
    # KD 計算 (9, 3, 3)
    low_9 = df['Low'].rolling(window=9).min()
    high_9 = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_9) / (high_9 - low_9) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df.tail(days)

try:
    data = fetch_stock_data(target_id, view_days)
    
    if data is not None:
        # 4. 繪製圖表：K線(1) / 成交量(2) / KD(3)
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.04, 
            row_heights=[0.5, 0.2, 0.3]
        )

        # A. K線圖 (紅漲綠跌)
        fig.add_trace(go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            name="K線", increasing_line_color='#FF3232', decreasing_line_color='#00FF00'
        ), row=1, col=1)

        # B. 成交量圖 (對應圖二要求)
        v_colors = ['#FF3232' if c >= o else '#00FF00' for o, c in zip(data['Open'], data['Close'])]
        fig.add_trace(go.Bar(
            x=data.index, y=data['Volume'], name="成交量",
            marker_color=v_colors, opacity=0.9
        ), row=2, col=1)

        # C. KD 指標 (黃藍配色)
        fig.add_trace(go.Scatter(x=data.index, y=data['K'], name="K(黃)", line=dict(color='#FFD700', width=2.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['D'], name="D(藍)", line=dict(color='#1E90FF', width=2.5)), row=3, col=1)

        # 5. 視覺設定
        fig.update_layout(
            template="plotly_dark", paper_bgcolor='black', plot_bgcolor='black',
            height=850, xaxis_rangeslider_visible=False, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        # X軸年月份：加大變白、Arial Black
        fig.update_xaxes(
            tickfont=dict(color='#FFFFFF', size=18, family="Arial Black"),
            gridcolor='rgba(255,255,255,0.15)',
            row=3, col=1
        )
        
        # Y軸自動對焦 (解決低價債券看不到K線問題)
        fig.update_yaxes(autorange=True, fixedrange=False, tickfont=dict(color='white', size=14), row=1, col=1)
        fig.update_yaxes(showticklabels=False, row=2, col=1) 
        fig.update_yaxes(range=[0, 100], tickfont=dict(color='white', size=14), row=3, col=1)
        
        st.plotly_chart(fig, use_container_width=True)

        # 6. 狀態顯示
        k_val, d_val = data['K'].iloc[-1], data['D'].iloc[-1]
        st.markdown(f"### 💡 當前數值：K線 **{k_val:.2f}** / D線 **{d_val:.2f}**")

    else:
        st.error("目前暫無數據，請確認標的代號或 GitHub 同步狀態。")

except Exception as e:
    st.error(f"系統錯誤: {e}")