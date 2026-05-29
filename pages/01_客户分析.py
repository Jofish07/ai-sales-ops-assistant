"""客户分析 - 上传数据 + 自动分层"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_processor import load_data, score_customers, get_summary

# Plotly中文字体配置（防止图表显示方块）
FONT_CN = dict(family="PingFang SC, Microsoft YaHei, Noto Sans CJK SC, Arial")

st.set_page_config(page_title="客户分析", layout="wide")
st.title("客户数据分析")

# 数据上传
uploaded = st.file_uploader("上传客户数据（CSV/Excel）", type=["csv", "xlsx"])

# 加载数据
df = load_data(uploaded)
df_scored = score_customers(df)

# 概览指标
summary = get_summary(df_scored)
cols = st.columns(5)
cols[0].metric("客户总数", summary["客户总数"])
cols[1].metric("总采购额(万)", summary["总采购额(万)"])
cols[2].metric("A级客户", summary["A级客户"])
cols[3].metric("B级客户", summary["B级客户"])
cols[4].metric("C级客户", summary["C级客户"])

st.markdown("---")

# 客户等级分布
col1, col2 = st.columns(2)
with col1:
    tier_counts = df_scored["客户等级"].value_counts().reset_index()
    tier_counts.columns = ["客户等级", "数量"]
    fig = px.pie(tier_counts, values="数量", names="客户等级",
                 title="客户等级分布", color="客户等级",
                 color_discrete_map={"A": "#1E3A8A", "B": "#3B82F6", "C": "#93C5FD"})
    fig.update_layout(font=FONT_CN)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    industry_counts = df_scored["行业"].value_counts().reset_index()
    industry_counts.columns = ["行业", "数量"]
    fig2 = px.bar(industry_counts, x="行业", y="数量", title="行业分布",
                  color="数量", color_continuous_scale="Blues")
    fig2.update_layout(xaxis_tickangle=-30, font=FONT_CN)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# 完整数据表
st.subheader("客户明细（含评分）")
show_cols = ["客户ID", "客户名称", "行业", "规模(人)", "年采购额(万)",
             "合作时长(月)", "跟进次数", "意向等级", "客户等级", "总分"]
display_df = df_scored[show_cols].sort_values("总分", ascending=False)

# 条件染色
def color_tier(val):
    if val == "A":
        return "background: #DCFCE7; color: #166534"
    elif val == "B":
        return "background: #FEF9C3; color: #854D0E"
    elif val == "C":
        return "background: #FEE2E2; color: #991B1B"
    return ""

st.dataframe(display_df.style.applymap(color_tier, subset=["客户等级"]),
             use_container_width=True, height=500)
