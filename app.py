import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots

st.set_page_config(page_title="獵人技術分析站", layout="wide")
st.title("🏹 獵人：華邦電與個股技術分析")

# 1. 選擇標的 (可自行增加)
target = st.sidebar.selectbox("選擇股票", ["2344.TW", "009816.TW", "00983A.TW", "1711.TW"])

# 2. 抓取數據並計算 KD
@st.cache_data(ttl=60)
def get_analysis_data(ticker):
    df = yf.download(ticker, period="6mo", interval="1d")
    # 計算 KD 指標
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

try:
    df = get_analysis_data(target)
    
    # 3. 繪製 K線 + KD 指標子圖
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.1, row_heights=[0.7, 0.3])

    # 上圖：K線
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
    
    # 下圖：KD 指標
    fig.add_trace(go.Scatter(x=df.index, y=df['K'], name="K值", line=dict(color='yellow')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['D'], name="D值", line=dict(color='cyan')), row=2, col=1)
    
    # 加入 KD 80/20 參考線
    fig.add_hline(y=80, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"數據讀取失敗：{e}")