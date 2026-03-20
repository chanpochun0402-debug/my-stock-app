import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 網頁基本設定 (深色主題)
st.set_page_config(page_title="獵人專業分析站", layout="wide")

# 強制讓背景變成極致黑的 CSS
st.markdown("""
    <style>
    .main { background-color: #000000; }
    header { background-color: #000000 !important; }
    </style>
    """, unsafe_allow_token=True)

st.title("🎯 華邦電與個股專業技術觀測")

# 2. 側邊欄：選擇標的
target = st.sidebar.selectbox("切換觀測標的", ["2344.TW", "009816.TW", "00983A.TW", "1711.TW"])
period = st.sidebar.slider("觀察天數", 30, 180, 90)

# 3. 抓取數據與計算 KD
@st.cache_data(ttl=60)
def get_stock_analysis(ticker):
    # 抓取稍長一點的數據以便計算指標
    df = yf.download(ticker, period="1y", interval="1d")
    
    # 計算 KD (9, 3, 3)
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    return df.tail(period)

try:
    df = get_stock_analysis(target)
    
    # 4. 建立子圖：1 欄 2 列，共用 X 軸
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.7, 0.3] # K線佔 70%, KD 佔 30%
    )

    # --- 上圖：K線圖 ---
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="K線",
        increasing_line_color='#FF3232', # 上漲紅
        decreasing_line_color='#00FF00'  # 下跌綠
    ), row=1, col=1)

    # --- 下圖：KD 指標 ---
    fig.add_trace(go.Scatter(
        x=df.index, y=df['K'], 
        name="K值", line=dict(color='#FFD700', width=2) # 黃線
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['D'], 
        name="D值", line=dict(color='#1E90FF', width=2) # 藍線
    ), row=2, col=1)

    # 加入 KD 參考線 (80 高檔, 20 低檔)
    fig.add_hline(y=80, line_dash="dash", line_color="rgba(255, 50, 50, 0.5)", row=2, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="rgba(0, 255, 0, 0.5)", row=2, col=1)

    # 5. 圖表樣式調整 (全黑背景)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,1)',
        plot_bgcolor='rgba(0,0,0,1)',
        height=800,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # 調整 X 軸日期格式
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(100,100,100,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(100,100,100,0.2)')

    st.plotly_chart(fig, use_container_width=True)

    # 6. 即時診斷文字
    last_k = df['K'].iloc[-1]
    last_d = df['D'].iloc[-1]
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if last_k > last_d:
            st.success(f"🔥 目前指標：K值({last_k:.1f}) > D值({last_d:.1f}) - 短線偏多 (黃金交叉)")
        else:
            st.error(f"❄️ 目前指標：K值({last_k:.1f}) < D值({last_d:.1f}) - 短線修正 (死亡交叉)")
    with col2:
        if last_k < 20: st.warning("⚠️ 注意：KD 進入 20 以下超賣區，隨時可能反彈。")
        elif last_k > 80: st.warning("⚠️ 注意：KD 進入 80 以上超買區，謹防回檔。")

except Exception as e:
    st.error(f"讀取錯誤: {e}")
    st.error(f"數據讀取失敗：{e}")