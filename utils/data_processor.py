"""数据处理+客户评分模块"""

import pandas as pd
import streamlit as st


@st.cache_data
def load_data(uploaded_file=None):
    """加载数据：上传文件或使用demo数据"""
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv("data/demo_clients.csv")
    return df


def score_customers(df, weights=None):
    """客户优先级评分：A/B/C三级，支持自定义权重

    Parameters
    ----------
    df : DataFrame
        客户数据
    weights : dict, optional
        自定义权重，格式：{"采购分": 40, "时长分": 20, "跟进分": 20, "意向分": 20}
        默认使用标准权重
    """
    if weights is None:
        weights = {"采购分": 40, "时长分": 20, "跟进分": 20, "意向分": 20}

    df = df.copy()

    # 处理缺失值：年采购额、合作时长、跟进次数填空
    df["年采购额(万)"] = pd.to_numeric(df["年采购额(万)"], errors="coerce").fillna(0)
    df["合作时长(月)"] = pd.to_numeric(df["合作时长(月)"], errors="coerce").fillna(0)
    df["跟进次数"] = pd.to_numeric(df["跟进次数"], errors="coerce").fillna(0)

    # 标记数据完整度
    def completeness(row):
        score = 0
        if row["年采购额(万)"] > 0:
            score += 1
        if row["合作时长(月)"] > 0:
            score += 1
        if row["跟进次数"] > 0:
            score += 1
        return score

    df["数据完整度"] = df.apply(completeness, axis=1)

    # 年采购额评分
    pmax = df["年采购额(万)"].max()
    df["采购分"] = (df["年采购额(万)"] / pmax * weights["采购分"]).round(1) if pmax > 0 else 0

    # 合作时长评分
    tmax = df["合作时长(月)"].max()
    df["时长分"] = (df["合作时长(月)"] / tmax * weights["时长分"]).round(1) if tmax > 0 else 0

    # 跟进频率评分
    fmax = df["跟进次数"].max()
    df["跟进分"] = (df["跟进次数"] / fmax * weights["跟进分"]).round(1) if fmax > 0 else 0

    # 意向等级评分
    intent_map = {"高": weights["意向分"], "中": weights["意向分"] / 2, "低": 0}
    df["意向分"] = df["意向等级"].map(intent_map).fillna(0)

    # 总分
    df["总分"] = (df["采购分"] + df["时长分"] + df["跟进分"] + df["意向分"]).round(1)

    # 等级划分
    def tier(score):
        if score >= 70:
            return "A"
        elif score >= 45:
            return "B"
        else:
            return "C"

    df["客户等级"] = df["总分"].apply(tier)

    return df


def get_summary(df):
    """生成客户概况摘要"""
    total = len(df)
    total_gmv = df["年采购额(万)"].sum()
    avg_followups = df["跟进次数"].mean()

    tier_counts = df["客户等级"].value_counts().to_dict() if "客户等级" in df.columns else {}

    return {
        "客户总数": total,
        "总采购额(万)": total_gmv,
        "平均跟进次数": round(avg_followups, 1),
        "A级客户": tier_counts.get("A", 0),
        "B级客户": tier_counts.get("B", 0),
        "C级客户": tier_counts.get("C", 0),
    }


def generate_insights(df):
    """生成销售运营洞察（规则引擎，不调用大模型）

    输出：
    - 客户结构分析
    - 行业分布分析
    - 商机遗漏分析
    - 客户流失风险分析
    - 本周优先行动建议
    """
    insights = {}

    # ── 1. 客户结构分析 ──
    total = len(df)
    tier_counts = df["客户等级"].value_counts()
    tier_gmv = df.groupby("客户等级")["年采购额(万)"].sum()
    total_gmv = df["年采购额(万)"].sum()

    structure = {
        "total": total,
        "tier": {},
        "gmv_concentration": "",
    }
    for t in ["A", "B", "C"]:
        count = int(tier_counts.get(t, 0))
        gmv = float(tier_gmv.get(t, 0))
        structure["tier"][t] = {
            "count": count,
            "pct": round(count / total * 100, 1) if total > 0 else 0,
            "gmv": gmv,
            "gmv_pct": round(gmv / total_gmv * 100, 1) if total_gmv > 0 else 0,
        }

    a_gmv_pct = structure["tier"]["A"]["gmv_pct"]
    structure["gmv_concentration"] = f"A级客户以{structure['tier']['A']['pct']}%的数量贡献了{a_gmv_pct}%的采购额"
    insights["structure"] = structure

    # ── 2. 行业分布分析 ──
    industry_gmv = df.groupby("行业")["年采购额(万)"].sum().sort_values(ascending=False)
    top_industries = industry_gmv.head(3)
    other_gmv = industry_gmv.iloc[3:].sum() if len(industry_gmv) > 3 else 0
    industry_analysis = {
        "top": [],
        "concentration": "",
    }
    for ind, gmv in top_industries.items():
        industry_analysis["top"].append({"industry": ind, "gmv": round(gmv, 0)})
    top3_gmv = top_industries.sum()
    industry_analysis["concentration"] = (
        f"top3行业（{'/'.join(top_industries.index.tolist())}）"
        f"合计采购额{top3_gmv:,.0f}万，占总盘{round(top3_gmv/total_gmv*100,1) if total_gmv > 0 else 0}%"
    )
    if other_gmv > 0:
        industry_analysis["concentration"] += f"，其余{len(industry_gmv)-3}个行业合计{other_gmv:,.0f}万"
    insights["industry"] = industry_analysis

    # ── 3. 商机遗漏分析 ──
    opportunities = []
    # 高意向未跟进
    no_followup = df[(df["意向等级"] == "高") & (df["跟进次数"] == 0)]
    for _, r in no_followup.iterrows():
        opportunities.append({
            "type": "high_intent_no_followup",
            "client": r["客户名称"],
            "detail": f"意向等级为高，但跟进次数为0，建议本周内安排首次接触",
            "action": "首次接触",
            "priority": "高",
        })
    # 高采购低意向（需高层介入）
    high_value = df[(df["年采购额(万)"] > 500) & (df["意向等级"] == "低")]
    for _, r in high_value.iterrows():
        opportunities.append({
            "type": "high_value_low_intent",
            "client": r["客户名称"],
            "detail": f"年采购额{r['年采购额(万)']:,.0f}万但意向等级为低，常规定期跟进难以突破，建议安排销售总监级别对接",
            "action": "高层拜访",
            "priority": "高",
        })
    # 意向高但跟进频率偏低
    low_freq = df[(df["意向等级"] == "高") & (df["跟进次数"] > 0) & (df["跟进次数"] <= 2)]
    for _, r in low_freq.iterrows():
        opportunities.append({
            "type": "low_frequency_high_intent",
            "client": r["客户名称"],
            "detail": f"意向等级为高但仅跟进{r['跟进次数']}次，建议加大跟进频率，把握商机窗口",
            "action": "增加跟进",
            "priority": "中",
        })
    insights["opportunities"] = opportunities

    # ── 4. 客户流失风险分析 ──
    churn_risks = []
    # 合作超24个月但近期跟进不足3次
    long_term_low_freq = df[(df["合作时长(月)"] > 24) & (df["跟进次数"] < 3) & (df["意向等级"] != "低")]
    for _, r in long_term_low_freq.iterrows():
        churn_risks.append({
            "client": r["客户名称"],
            "reason": f"已合作{r['合作时长(月)']}个月，属老客户，但累计跟进仅{r['跟进次数']}次",
            "risk_level": "中",
            "action": "安排一次高层回访，了解近期需求和满意度",
        })
    # 超1个月未跟进
    import datetime
    try:
        df_temp = df.copy()
        df_temp["最近跟进日期"] = pd.to_datetime(df_temp["最近跟进日期"], errors="coerce")
        today = datetime.date.today()
        overdue = df_temp[
            (df_temp["最近跟进日期"].notna()) &
            (df_temp["最近跟进日期"].dt.date < pd.Timestamp(today - datetime.timedelta(days=30)).date()) &
            (df_temp["意向等级"] != "低")
        ]
        for _, r in overdue.iterrows():
            last_date = r["最近跟进日期"].strftime("%Y-%m-%d") if pd.notna(r["最近跟进日期"]) else "未知"
            churn_risks.append({
                "client": r["客户名称"],
                "reason": f"最近跟进日期为{last_date}，已超过30天未联系",
                "risk_level": "中",
                "action": "本周内主动联系，了解近况",
            })
    except Exception:
        pass
    insights["churn_risks"] = churn_risks

    # ── 5. 本周优先行动建议 ──
    actions = []

    # 汇总所有高优先级商机
    high_opportunities = [o for o in opportunities if o["priority"] == "高"]
    if high_opportunities:
        actions.append({
            "priority": "P0",
            "title": f"跟进{len(high_opportunities)}个高优先级商机",
            "detail": " | ".join([f"{o['client']}（{o['action']}）" for o in high_opportunities[:3]]),
        })

    # A级客户跟进提醒
    a_clients = df[df["客户等级"] == "A"]
    a_due = len(a_clients[a_clients["跟进次数"] < 6])
    if a_due > 0:
        actions.append({
            "priority": "P0",
            "title": f"{a_due}个A级客户跟进不足，需加强维护",
            "detail": f"A级客户是收入核心，建议至少保持每月1次有效接触",
        })

    # 数据完整性提醒
    incomplete = df[df["数据完整度"] < 3]
    if len(incomplete) > 0:
        actions.append({
            "priority": "P1",
            "title": f"完善{len(incomplete)}条客户数据的缺失字段",
            "detail": "缺失年采购额或跟进次数的客户无法准确评分，影响分层决策",
        })

    # 行业拓展建议
    if len(top_industries) >= 1:
        actions.append({
            "priority": "P1",
            "title": f"关注{top_industries.index[0]}行业的增量机会",
            "detail": f"该行业贡献{round(top_industries.iloc[0]/total_gmv*100,1) if total_gmv > 0 else 0}%采购额，是当前最大收入来源",
        })

    # 流失风险
    if churn_risks:
        actions.append({
            "priority": "P1",
            "title": f"安排{len(churn_risks)}个流失风险客户的回访",
            "detail": "老客户流失往往不是突然的，而是被忽视的。建议本周内优先联系",
        })

    insights["actions"] = actions

    return insights
