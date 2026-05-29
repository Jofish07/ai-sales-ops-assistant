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


def score_customers(df):
    """客户优先级评分：A/B/C三级"""
    df = df.copy()

    # 年采购额评分 (0-40分)
    pmax = df["年采购额(万)"].max()
    df["采购分"] = (df["年采购额(万)"] / pmax * 40).round(1)

    # 合作时长评分 (0-20分)
    tmax = df["合作时长(月)"].max()
    df["时长分"] = (df["合作时长(月)"] / tmax * 20).round(1)

    # 跟进频率评分 (0-20分)
    fmax = df["跟进次数"].max()
    df["跟进分"] = (df["跟进次数"] / fmax * 20).round(1)

    # 意向等级评分 (0-20分)
    intent_map = {"高": 20, "中": 10, "低": 0}
    df["意向分"] = df["意向等级"].map(intent_map)

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
