"""AI销售运营助手 - 主页"""

import streamlit as st

st.set_page_config(page_title="AI销售运营助手", layout="wide")

st.markdown("""
<div style="text-align:center; padding:60px 0 30px;">
    <h1 style="font-size:36px; color:#1E3A8A; margin-bottom:8px;">AI销售运营助手</h1>
    <p style="font-size:16px; color:#64748B;">帮助销售团队进行客户分析、商机识别、跟进决策支持的辅助工具</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("核心功能", "客户分层")
with col2:
    st.metric("核心功能", "AI跟进建议")
with col3:
    st.metric("核心功能", "销售看板")

st.markdown("""
<div style="background:#F8FAFC; padding:24px; border-radius:8px; margin:24px 0; border:1px solid #E2E8F0;">
    <h3 style="color:#1E3A8A; margin-bottom:8px; font-size:16px;">使用流程</h3>
    <ol style="line-height:2; color:#475569;">
        <li><strong>客户分析</strong> — 上传客户Excel/CSV，自动完成行业分布、规模分层和优先级评分</li>
        <li><strong>跟进建议</strong> — 选择客户，AI自动分析采购行为，生成跟进话术和策略</li>
        <li><strong>销售看板</strong> — 关键运营指标可视化：客户结构、跟进情况、采购趋势</li>
    </ol>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:#FFF7ED; padding:24px; border-radius:8px; margin:24px 0; border:1px solid #FFEDD5;">
    <h3 style="color:#C24100; margin-bottom:8px; font-size:16px;">项目思考</h3>
    <p style="line-height:1.8; color:#6B4421;">
    销售团队中，客户信息、跟进记录、沟通习惯往往分散在不同人员手中，客户价值判断和跟进策略常依赖个人经验。
    这个项目尝试用数据分析和AI，将客户分层、商机识别、跟进优先级等分析逻辑沉淀为可复用流程。
    AI提供分析和参考，但理解客户、建立关系，最终还是人的事。
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.info("左侧导航栏选择功能", icon=None)
with col2:
    st.info("data/demo_clients.csv 有示例数据可直接体验", icon=None)
