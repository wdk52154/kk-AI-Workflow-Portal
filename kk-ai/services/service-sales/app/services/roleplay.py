import uuid
from typing import Optional, List
from datetime import datetime, timezone
from app.services.script_store import get_script_store


CUSTOMER_PROFILES = {
    "hesitant": {
        "name": "犹豫型客户",
        "traits": ["反复比较", "担心售后", "需要多次确认"],
        "opening": "我再想想……你们这个产品和其他家的有什么区别？",
        "hints": ["不要急于推销，先建立信任", "多给客观对比数据", "强调售后保障"]
    },
    "price_sensitive": {
        "name": "价格敏感型客户",
        "traits": ["关注折扣", "喜欢比价", "对优惠敏感"],
        "opening": "你们这个能不能再便宜点？我看别家比你这便宜不少。",
        "hints": ["强调性价比而非单纯低价", "提及限时优惠", "展示增值服务"]
    },
    "clear_need": {
        "name": "需求明确型客户",
        "traits": ["目标清晰", "决策果断", "关注产品细节"],
        "opening": "我已经了解过你们的产品了，想确认一下具体的功能细节。",
        "hints": ["直接回答技术/功能问题", "提供精确数据", "引导快速下单"]
    }
}

def create_session(customer_type: str, scenario: Optional[str], product: Optional[str]) -> dict:
    session_id = str(uuid.uuid4())
    profile = CUSTOMER_PROFILES.get(customer_type, CUSTOMER_PROFILES["hesitant"])
    store = get_script_store()
    store.create_session(session_id, customer_type, scenario, product)
    store.append_message(session_id, "customer", profile["opening"])

    return {
        "session_id": session_id,
        "customer_profile": {
            "type": customer_type,
            "name": profile["name"],
            "traits": profile["traits"],
            "scenario": scenario,
            "product": product
        },
        "opening_message": profile["opening"],
        "hints": profile["hints"]
    }

def chat(session_id: str, message: str) -> dict:
    store = get_script_store()
    store.append_message(session_id, "sales", message)

    session = store.get_session(session_id)
    customer_type = session["customer_type"] if session else "hesitant"
    profile = CUSTOMER_PROFILES.get(customer_type, CUSTOMER_PROFILES["hesitant"])

    # 模拟 AI 客户回复（实际应调用 LLM）
    reply = _generate_customer_reply(customer_type, message)
    store.append_message(session_id, "customer", reply)

    # 实时评分（模拟）
    score = _evaluate_turn(message, customer_type)

    return {
        "customer_reply": reply,
        "real_time_score": score,
        "hints": profile["hints"]
    }

def _generate_customer_reply(customer_type: str, sales_message: str) -> str:
    replies = {
        "hesitant": [
            "嗯……我再考虑一下吧。",
            "你们的售后政策是怎样的？",
            "能不能给我发一些资料，我回去和家里商量一下。",
        ],
        "price_sensitive": [
            "还是有点贵，能不能申请个内部价？",
            "你们有没有老客户优惠？",
            "隔壁那家便宜 20%，你们凭什么更贵？",
        ],
        "clear_need": [
            "好的，这个功能我了解了。",
            "支持 API 对接吗？文档在哪里？",
            "如果没问题的话，我下周可以下单。",
        ]
    }
    import random
    return random.choice(replies.get(customer_type, ["好的，我知道了。"]))

def _evaluate_turn(sales_message: str, customer_type: str) -> dict:
    import random
    base = random.uniform(60, 95)
    return {
        "standardization": round(base + random.uniform(-5, 5), 1),
        "empathy": round(base + random.uniform(-10, 10), 1),
        "information_coverage": round(base + random.uniform(-8, 8), 1),
        "conversion_guidance": round(base + random.uniform(-12, 12), 1),
    }

def evaluate(session_id: str) -> dict:
    store = get_script_store()
    session = store.get_session(session_id)
    if not session:
        return {"error": "Session not found"}

    transcript = session["transcript"]
    total_messages = len([m for m in transcript if m["role"] == "sales"])

    import random
    scores = {
        "standardization": round(random.uniform(70, 98), 1),
        "empathy": round(random.uniform(65, 95), 1),
        "information_coverage": round(random.uniform(60, 96), 1),
        "conversion_guidance": round(random.uniform(55, 92), 1),
    }
    avg = sum(scores.values()) / len(scores)

    suggestions = []
    if scores["standardization"] < 75:
        suggestions.append("话术规范度有待提升，建议使用标准开场白和结束语。")
    if scores["empathy"] < 75:
        suggestions.append('共情能力需加强，多使用"我理解您的顾虑"等表达。')
    if scores["information_coverage"] < 75:
        suggestions.append("关键信息覆盖不足，注意补充产品核心卖点。")
    if scores["conversion_guidance"] < 75:
        suggestions.append("转化引导较弱，建议在适当时机提出明确的行动号召。")
    if not suggestions:
        suggestions.append("表现优秀！继续保持，建议尝试更高难度的客户类型。")

    store.end_session(session_id, scores)

    return {
        "total_score": round(avg, 1),
        "dimensions": scores,
        "suggestions": suggestions,
        "transcript": transcript,
        "total_messages": total_messages
    }
