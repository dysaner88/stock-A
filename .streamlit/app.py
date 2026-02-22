import streamlit as st
import akshare as ak
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd

# ---------------------- 页面基础配置 ----------------------
st.set_page_config(
    page_title="个人股票分析看板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- 标题与样式 ----------------------
st.title("📈 每日股票分析看板")
st.markdown("---")

# ---------------------- 侧边栏配置 ----------------------
with st.sidebar:
    st.header("🔧 股票配置")
    # 股票代码输入
    stock_code = st.text_input(
        "输入A股代码（如 000547 航天发展）",
        value="000547",
        placeholder="例：600343 航天动力 / 002792 通宇通讯"
    )
    # 时间周期选择
    time_range = st.slider(
        "查看最近天数",
        min_value=30,
        max_value=365,
        value=60,
        step=10
    )
    # 指标选择
    indicators = st.multiselect(
        "叠加技术指标",
        options=["成交量", "MACD"],
        default=["成交量"]
    )

# ---------------------- 数据获取 ----------------------
# 计算起止日期
end_date = datetime.now().strftime("%Y%m%d")
start_date = (datetime.now() - timedelta(days=time_range)).strftime("%Y%m%d")

# 获取股票数据
@st.cache_data(ttl=3600)  # 缓存1小时，避免频繁请求
def get_stock_data(code, start, end):
    try:
        # 获取复权日线数据
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start,
            end_date=end,
            adjust="qfq"  # 前复权
        )
        # 处理数据格式
        df["日期"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期")
        return df
    except Exception as e:
        st.error(f"数据获取失败：{str(e)}")
        st.info("💡 提示：请检查股票代码是否正确（仅支持A股），如 000547、600343 等")
        return None

# 调用函数获取数据
df = get_stock_data(stock_code, start_date, end_date)

# ---------------------- 数据展示 ----------------------
if df is not None and not df.empty:
    # 1. 最新行情卡片
    latest = df.iloc[-1]
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("最新价", f"¥{latest['收盘']:.2f}", f"{latest['涨跌幅']:.2f}%")
    with col2:
        st.metric("开盘价", f"¥{latest['开盘']:.2f}")
    with col3:
        st.metric("最高价", f"¥{latest['最高']:.2f}")
    with col4:
        st.metric("最低价", f"¥{latest['最低']:.2f}")
    with col5:
        st.metric("成交量", f"{latest['成交量']:,}")
    
    st.markdown("---")

    # 2. K线图绘制
    fig = go.Figure()

    # 添加K线主图
    fig.add_trace(go.Candlestick(
        x=df["日期"],
        open=df["开盘"],
        high=df["最高"],
        low=df["最低"],
        close=df["收盘"],
        name="K线",
        increasing_line_color="#ef5350",  # 红涨
        decreasing_line_color="#26a69a"   # 绿跌
    ))

    # 叠加成交量
    if "成交量" in indicators:
        fig.add_trace(go.Bar(
            x=df["日期"],
            y=df["成交量"],
            name="成交量",
            yaxis="y2",
            opacity=0.3,
            marker_color=df.apply(lambda row: "#ef5350" if row["收盘"] >= row["开盘"] else "#26a69a", axis=1)
        ))

    # 图表布局设置
    fig.update_layout(
        title=f"{stock_code} 日线走势（前复权）",
        xaxis_title="日期",
        yaxis_title="价格（元）",
        yaxis2=dict(title="成交量", overlaying="y", side="right"),
        xaxis_rangeslider_visible=False,  # 隐藏底部滑块
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # 显示图表
    st.plotly_chart(fig, use_container_width=True)

    # 3. 历史数据表格
    with st.expander("📋 查看详细历史数据（点击展开）"):
        st.dataframe(
            df[["日期", "开盘", "最高", "最低", "收盘", "成交量", "涨跌幅"]]
            .sort_values("日期", ascending=False)
            .reset_index(drop=True),
            use_container_width=True
        )

else:
    st.warning("暂无数据，请检查股票代码或稍后重试")

# ---------------------- 底部信息 ----------------------
st.markdown("---")
st.caption(f"数据更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 数据源：AkShare")
