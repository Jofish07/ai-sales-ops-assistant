"""销售看板 - 关键指标可视化"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_processor import load_data, score_customers

# Plotly中文字体配置
FONT_CN = dict(family="PingFang SC, Microsoft YaHei, Noto Sans CJK SC, Arial")

st.set_page_config(page_title="销售看板", layout="wide")
st.title("销售运营看板")

df = load_data()
df_scored = score_customers(df)

# 顶行指标
total_gmv = df_scored["年采购额(万)"].sum()
a_clients = len(df_scored[df_scored["客户等级"] == "A"])
a_gmv = df_scored[df_scored["客户等级"] == "A"]["年采购额(万)"].sum()
avg_followup = df_scored["跟进次数"].mean()

col1, col2, col3, col4 = st.columns(4)
col1.metric("客户总数", len(df_scored))
col2.metric("预计年采购额(万)", f"{total_gmv:,.0f}")
col3.metric("A级客户", a_clients, f"占总客户 {a_clients/len(df_scored)*100:.0f}%")
col4.metric("平均跟进次数", f"{avg_followup:.1f}")

st.markdown("---")

# 图表行1
col1, col2 = st.columns(2)
with col1:
    tier_gmv = df_scored.groupby("客户等级")["年采购额(万)"].sum().reset_index()
    fig = px.bar(tier_gmv, x="客户等级", y="年采购额(万)",
                 title="各等级客户采购额分布",
                 color="客户等级",
                 color_discrete_map={"A": "#1E3A8A", "B": "#3B82F6", "C": "#93C5FD"},
                 text_auto=True)
    fig.update_layout(showlegend=False, font=FONT_CN)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    industry_gmv = df_scored.groupby("行业")["年采购额(万)"].sum().reset_index()
    industry_gmv = industry_gmv.sort_values("年采购额(万)", ascending=True)
    fig2 = px.bar(industry_gmv, x="年采购额(万)", y="行业",
                  title="各行业采购额分布",
                  color="年采购额(万)", color_continuous_scale="Blues",
                  orientation="h", text_auto=True)
    fig2.update_layout(yaxis={"categoryorder": "total ascending"}, font=FONT_CN)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# 图表行2
col1, col2 = st.columns(2)
with col1:
    fig3 = px.scatter(df_scored, x="合作时长(月)", y="年采购额(万)",
                      size="跟进次数", color="客户等级",
                      hover_name="客户名称",
                      title="合作时长 vs 采购额",
                      color_discrete_map={"A": "#1E3A8A", "B": "#3B82F6", "C": "#93C5FD"})
    fig3.update_layout(font=FONT_CN)
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    intent_counts = df_scored["意向等级"].value_counts().reset_index()
    intent_counts.columns = ["意向等级", "数量"]
    fig4 = px.pie(intent_counts, values="数量", names="意向等级",
                  title="客户意向等级分布",
                  color="意向等级",
                  color_discrete_map={"高": "#1E3A8A", "中": "#3B82F6", "低": "#93C5FD"})
    fig4.update_layout(font=FONT_CN)
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# 跟进优先级列表
st.subheader("待跟进优先级列表")
df_scored["建议跟进"] = df_scored.apply(
    lambda r: "本周跟进" if r["客户等级"] == "A" and r["意向等级"] == "高"
    else ("1周内跟进" if r["客户等级"] == "B"
          else "2周内跟进"), axis=1
)
priority = df_scored.sort_values("总分", ascending=False)
st.dataframe(
    priority[["客户名称", "行业", "客户等级", "意向等级", "总分", "建议跟进"]],
    use_container_width=True, height=400
)
