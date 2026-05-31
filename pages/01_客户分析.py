"""客户分析 - 上传数据 + 自动分层 + 权重可调"""

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

# 权重调节器
st.markdown("#### 评分权重配置")
st.caption("调整各维度的权重，评分和客户等级会实时更新。不同公司对客户的定义不同：有的更看重采购额，有的更看重合作时长。")
col_w1, col_w2, col_w3, col_w4 = st.columns(4)
with col_w1:
    w_purchase = st.slider("采购额权重", 0, 60, 40, 5, help="采购额越高，客户价值越大")
with col_w2:
    w_tenure = st.slider("合作时长权重", 0, 40, 20, 5, help="合作越久，客户越稳定")
with col_w3:
    w_followup = st.slider("跟进频率权重", 0, 40, 20, 5, help="跟进越勤，客户越活跃")
with col_w4:
    w_intent = st.slider("意向等级权重", 0, 40, 20, 5, help="意向越高，转化概率越大")

weights = {"采购分": w_purchase, "时长分": w_tenure, "跟进分": w_followup, "意向分": w_intent}

# 评分
df_scored = score_customers(df, weights=weights)

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

# 数据质量提示（脏数据场景）
incomplete = df_scored[df_scored["数据完整度"] < 3]
if len(incomplete) > 0:
    st.warning(f"⚠️ 发现 {len(incomplete)} 条数据不完整的客户记录（缺失采购额、合作时长或跟进次数），评分可能偏低。建议补充完整数据后重新分析。")

# 异常模式提示（面试时可展开讲）
high_value_low_intent = df_scored[(df_scored["年采购额(万)"] > 500) & (df_scored["意向等级"] == "低")]
high_intent_no_followup = df_scored[(df_scored["意向等级"] == "高") & (df_scored["跟进次数"] == 0)]
churn_risk = df_scored[(df_scored["合作时长(月)"] > 24) & (df_scored["跟进次数"] < 3) & (df_scored["意向等级"] != "低")]

if len(high_value_low_intent) > 0 or len(high_intent_no_followup) > 0 or len(churn_risk) > 0:
    with st.expander("📊 数据异常模式检测（销售运营洞察）"):
        if len(high_value_low_intent) > 0:
            st.write("**🔴 高价值低意向客户（需高层介入）**")
            for _, r in high_value_low_intent.iterrows():
                st.write(f"- {r['客户名称']}：年采购额{r['年采购额(万)']:,.0f}万，但意向等级为低。建议安排高层对接，而非常规跟进。")
        if len(high_intent_no_followup) > 0:
            st.write("**🟡 高意向未跟进客户（潜在商机遗漏）**")
            for _, r in high_intent_no_followup.iterrows():
                st.write(f"- {r['客户名称']}：意向等级为高，但跟进次数为0。系统匹配度显示存在商机，建议立即安排首次接触。")
        if len(churn_risk) > 0:
            st.write("**🟠 老客户跟进减少（流失风险）**")
            for _, r in churn_risk.iterrows():
                st.write(f"- {r['客户名称']}：已合作{r['合作时长(月)']}个月，但近期跟进频率偏低。老客户流失往往不是突然的，而是被忽视的。")

# 完整数据表
st.markdown("---")
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
