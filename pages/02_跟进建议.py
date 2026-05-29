"""AI跟进建议 - 选择客户 → 生成跟进策略"""

import streamlit as st
import os
from utils.data_processor import load_data, score_customers
from utils.ai_helper import generate_followup

st.set_page_config(page_title="跟进建议", layout="wide")
st.title("AI跟进建议")

# 加载数据
df = load_data()
df_scored = score_customers(df)

client_list = df_scored["客户名称"].tolist()
selected = st.selectbox("选择客户", client_list)

if selected:
    row = df_scored[df_scored["客户名称"] == selected].iloc[0]
    client_info = {
        "名称": row["客户名称"],
        "行业": row["行业"],
        "规模": int(row["规模(人)"]),
        "年采购额": int(row["年采购额(万)"]),
        "合作时长": int(row["合作时长(月)"]),
        "最近跟进": row["最近跟进日期"],
        "跟进次数": int(row["跟进次数"]),
        "意向等级": row["意向等级"],
        "客户等级": row["客户等级"],
    }

    # 客户信息卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.info(f"{client_info['行业']}")
    col2.info(f"{client_info['年采购额']}万/年")
    col3.info(f"合作{client_info['合作时长']}个月")
    col4.info(f"{client_info['客户等级']}级客户")

    # 评分明细
    st.markdown("#### 评分明细")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("采购分(40)", row["采购分"])
    sc2.metric("时长分(20)", row["时长分"])
    sc3.metric("跟进分(20)", row["跟进分"])
    sc4.metric("意向分(20)", row["意向分"])

    # AI建议
    st.markdown("#### AI跟进建议")

    # API key输入
    api_key = st.text_input("OpenAI API Key（选填，不填则使用规则生成）",
                            type="password",
                            placeholder="sk-...")

    if st.button("生成跟进建议", type="primary"):
        with st.spinner("正在分析客户数据..."):
            result = generate_followup(client_info, api_key=api_key if api_key else None)
        st.markdown(result)

        st.markdown("---")
        st.caption("以上建议由AI生成，实际跟进时请结合客户具体情况调整。")
