import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 網頁基本設定 (極簡黑風格)
st.set_page_config(page_title="獵人專業分析站", layout="wide")

# 修正報錯：使用正確的參數 unsafe_allow_html
st.markdown("""
    <style>
    .main { background-color: #000000; }
    header { background-color: #000000 !important; }
    div[data-testid="stToolbar"] { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 華邦電與個股技術分析")

# 2. 側邊欄設定
target = st.sidebar.selectbox("選擇觀測標的", ["2344.TW", "009816.TW", "00983A.TW", "1711.TW"])
period = st.sidebar.slider("觀察天數", 30, 180, 100)

# 3. 抓取數據與計算 KD
@st.cache_data(ttl=60)
def get_analysis_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d")
    # 計算 KD (9, 3, 3)
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df.tail(period)

try:
    df = get_analysis_data(target)
    
    # 4. 建立子圖：1 欄 2 列，共用 X 軸
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.7, 0.3]
    )

    # 上圖：K線圖 (紅漲綠跌)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="K線",
        increasing_line_color='#FF3232', # 上漲紅
        decreasing_line_color='#00FF00'  # 下跌綠
    ), row=1, col=1)

    # 下圖：KD 指標 (黃藍配色)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['K'], name="K值 (黃)", 
        line=dict(color='#FFD700', width=2) 
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['D'], name="D值 (藍)", 
        line=dict(color='#1E90FF', width=2)
    ), row=2, col=1)

    # 參考線
    fig.add_hline(y=80, line_dash="dash", line_color="rgba(255, 50, 50, 0.5)", row=2, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="rgba(0, 255, 0, 0.5)", row=2, col=1)

    # 圖表美化
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='black',
        plot_bgcolor='black',
        height=800,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # 5. 底部快速診斷
    last_k = df['K'].iloc[-1]
    last_d = df['D'].iloc[-1]
    st.markdown("---")
    if last_k > last_d:
        st.write(f"🚀 **當前趨勢**：K值({last_k:.1f}) > D值({last_d:.1f}) —— **短線多方佔優**")
    else:
        st.write(f"📉 **當前趨勢**：K值({last_k:.1f}) < D值({last_d:.1f}) —— **短線整理中**")

except Exception as e:
    st.error(f"發生錯誤：{e}")