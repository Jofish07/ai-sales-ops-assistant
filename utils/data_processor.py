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
