"""AI跟进建议 - 选择客户 → 生成跟进策略 → 记录跟进"""

import streamlit as st
import pandas as pd
from utils.data_processor import load_data, score_customers
from utils.ai_helper import generate_followup

st.set_page_config(page_title="跟进建议", layout="wide")
st.title("AI跟进建议")

# 初始化跟进记录存储
if "followup_records" not in st.session_state:
    st.session_state.followup_records = {}
if "last_suggestion" not in st.session_state:
    st.session_state.last_suggestion = ""

# 加载数据
df = load_data()
df_scored = score_customers(df)

client_list = df_scored["客户名称"].tolist()
selected = st.selectbox("选择客户", client_list, key="client_selector")

if selected:
    row = df_scored[df_scored["客户名称"] == selected].iloc[0]
    client_info = {
        "名称": row["客户名称"],
        "行业": row["行业"],
        "规模": int(row["规模(人)"]) if pd.notna(row["规模(人)"]) else 0,
        "年采购额": int(row["年采购额(万)"]) if pd.notna(row["年采购额(万)"]) else 0,
        "合作时长": int(row["合作时长(月)"]) if pd.notna(row["合作时长(月)"]) else 0,
        "最近跟进": row["最近跟进日期"],
        "跟进次数": int(row["跟进次数"]) if pd.notna(row["跟进次数"]) else 0,
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

    # 显示该客户最近的跟进记录
    last_note = st.session_state.followup_records.get(selected)
    if last_note:
        st.info(f"📋 上次跟进记录（{last_note['date']}）：{last_note['note']}")

    # AI建议
    st.markdown("#### AI跟进建议")

    api_key = st.text_input("OpenAI API Key（选填，不填则使用规则生成）",
                            type="password",
                            placeholder="sk-...")

    if st.button("生成跟进建议", type="primary"):
        with st.spinner("正在分析客户数据..."):
            result = generate_followup(client_info, api_key=api_key if api_key else None)
        st.session_state.last_suggestion = result
        st.markdown(result)

        st.markdown("---")
        st.caption("以上建议由AI生成，实际跟进时请结合客户具体情况调整。")

    # 跟进记录区域
    if st.session_state.last_suggestion:
        st.markdown("---")
        st.markdown("#### 跟进记录")
        with st.form("followup_form"):
            note = st.text_area(
                "本次跟进内容",
                placeholder="记录本次沟通要点、客户反馈、下一步计划...\n\n例如：电话沟通了30分钟，客户对新方案感兴趣，计划下周发报价。",
                height=120,
            )
            col1, col2 = st.columns([1, 5])
            submitted = col1.form_submit_button("标记为已跟进", type="primary")
            if submitted and note.strip():
                from datetime import date
                st.session_state.followup_records[selected] = {
                    "note": note,
                    "date": date.today().isoformat(),
                }
                st.success("跟进记录已保存！")
                st.rerun()

    # 全局跟进统计
    st.markdown("---")
    with st.expander("📊 本会话跟进统计"):
        if st.session_state.followup_records:
            st.write(f"已跟进客户：{len(st.session_state.followup_records)} 家")
            for name, record in st.session_state.followup_records.items():
                st.write(f"- **{name}**（{record['date']}）：{record['note'][:50]}...")
        else:
            st.write("暂无跟进记录。生成建议后记得记录跟进情况。")
