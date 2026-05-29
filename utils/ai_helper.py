"""AI辅助模块：跟进建议生成"""

import json
import os

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def generate_followup(client_info, api_key=None):
    """生成客户跟进建议

    优先使用OpenAI API，无API key时使用规则生成。
    """
    if api_key and OPENAI_AVAILABLE:
        try:
            return _ai_followup(client_info, api_key)
        except Exception:
            return _rule_followup(client_info)
    else:
        return _rule_followup(client_info)


def _ai_followup(client_info, api_key):
    """使用OpenAI API生成跟进建议"""
    client = OpenAI(api_key=api_key)

    prompt = f"""你是一名销售运营专家。请分析以下客户信息，生成跟进建议。

客户信息：
- 名称：{client_info['名称']}
- 行业：{client_info['行业']}
- 规模：{client_info['规模']}人
- 年采购额：{client_info['年采购额']}万
- 合作时长：{client_info['合作时长']}个月
- 最近跟进：{client_info['最近跟进']}
- 跟进次数：{client_info['跟进次数']}
- 意向等级：{client_info['意向等级']}
- 客户等级：{client_info['客户等级']}

请输出以下内容（中文）：
1. 客户状态分析（一句话）
2. 跟进优先级（高/中/低）
3. 建议跟进时间
4. 跟进策略和建议话术要点
5. 风险提示（如果有）"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content


def _rule_followup(client_info):
    """无API key时使用规则生成建议"""
    name = client_info['名称']
    industry = client_info['行业']
    level = client_info['客户等级']
    intent = client_info['意向等级']
    purchase = client_info['年采购额']
    last_followup = client_info['最近跟进']
    followup_count = client_info['跟进次数']

    # 优先级判断
    if level == "A" and intent == "高":
        priority = "高 ⬆️"
        timing = "本周内跟进"
        strategy = "重点维护，建议安排客户拜访或高层对接，深入挖掘扩展需求"
    elif level == "B" and intent in ("高", "中"):
        priority = "中 ➡️"
        timing = "1周内跟进"
        strategy = "保持联系频率，了解近期采购计划，推送新品/优惠政策"
    else:
        priority = "低 ⬇️"
        timing = "2周内跟进"
        strategy = "发送节日问候或行业资讯，保持品牌曝光，培养合作意向"

    # 话术要点
    if intent == "高":
        talk_points = f"感谢{name}长期合作，了解近期是否有新增采购需求，介绍最新优惠政策"
    elif intent == "中":
        talk_points = f"向{name}推送行业报告或新品信息，了解业务变化，挖掘潜在需求"
    else:
        talk_points = f"初步接触{name}，介绍京东企业采购解决方案，了解客户业务模式"

    result = f"""**客户状态分析：**
{name}（{industry}）年采购额{purchase}万，当前评级{level}级，意向{intent}。
已跟进{followup_count}次，最近跟进日期为{last_followup}。

**跟进优先级：** {priority}
**建议跟进时间：** {timing}

**跟进策略：**
{strategy}

**话术要点：**
{talk_points}

**风险提示：**
{'' if followup_count >= 3 else '客户尚在培育期，建议保持定期接触，避免过度推销。'}"""

    return result
