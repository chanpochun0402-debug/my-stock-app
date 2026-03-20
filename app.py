import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. 網頁頁面基本設定
st.set_page_config(page_title="獵人資產戰報", layout="wide")
st.title("🛡️ 獵人：債券與高息動能觀測站")

# 2. 側邊欄：資產配置與回血試算
st.sidebar.header("💰 我的資產設定")
qty_9816 = st.sidebar.number_input("009816 持有張數", value=46)
cost_9816 = st.sidebar.number_input("009816 平均成本", value=11.0)
st.sidebar.markdown("---")
st.sidebar.info("💡 提示：永光(1711)已結案，剩餘資金可用於下週一 00400A 募集布局。")

# 3. 抓取數據函數 (自動處理台股代號)
@st.cache_data(ttl=60)
def get_stock_data(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d")
        return data
    except:
        return None

# 4. 監控標的選擇
target_map = {
    "009816 凱基美國優選債": "009816.TW",
    "00983A 凱基美國A級債": "00983A.TW",
    "00400A 凱基美國優選收益(下週募集)": "00400A.TW",
    "1711 永光 (歷史戰績)": "1711.TW"
}

selected_label = st.selectbox("🎯 選擇觀測目標：", list(target_map.keys()))
target_ticker = target_map[selected_label]

# 5. 顯示即時行情與回血進度
df = get_stock_data(target_ticker)

if df is not None and not df.empty:
    curr_price = float(df['Close'].iloc[-1])
    prev_price = float(df['Close'].iloc[-2])
    price_diff = curr_price - prev_price
    
    # 數據看板
    col1, col2, col3 = st.columns(3)
    col1.metric("當前成交價", f"{curr_price:.2f}", f"{price_diff:.2f}")
    
    # 針對主力 009816 顯示專屬進度
    if "009816" in selected_label:
        total_market_value = curr_price * qty_9816 * 1000
        total_profit = (curr_price - cost_9816) * qty_9816 * 1000
        col2.metric("預估總市值 (TWD)", f"${total_market_value:,.0f}")
        col3.metric("帳面損益 (回血金額)", f"${total_profit:,.0f}", delta_color="normal")
    
    # 6. 專業 K 線圖
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="日K"
    )])
    
    fig.update_layout(
        template="plotly_dark",
        height=550,
        title=f"{selected_label} 最近走勢圖",
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
else:
    st.warning(f"目前抓不到 {target_ticker} 的數據。如果是 00400A，請等下週募集掛牌後才會有行情喔！")

# 7. 腳註
st.markdown("---")
st.caption("🚀 獵人自動化戰情系統 | 本地設計，雲端部署")