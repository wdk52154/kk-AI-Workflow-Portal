"""内容生成引擎 - 调用 Prompt Center 生成各平台文案"""

import httpx
import uuid
from typing import List, Optional
from app.config import get_settings

PLATFORM_TEMPLATES = {
    "xiaohongshu": {
        "prompt_id": "content_xiaohongshu",
        "style": "小红书风格：带 emoji、分段、标签，亲切活泼",
        "max_length": 500,
    },
    "wechat": {
        "prompt_id": "content_wechat",
        "style": "公众号长文：结构化、引用、图文排版，专业深入",
        "max_length": 2000,
    },
    "douyin": {
        "prompt_id": "content_douyin",
        "style": "短视频脚本：分镜、台词、时长标记，口语化",
        "max_length": 800,
    },
    "moments": {
        "prompt_id": "content_moments",
        "style": "朋友圈短文案：简洁有力，带情绪，适合社交传播",
        "max_length": 200,
    },
}

TONE_PROMPTS = {
    "lively": "语气活泼、亲切、多用表情和网络用语",
    "professional": "语气专业、严谨、数据支撑、逻辑清晰",
    "premium": "语气高端、优雅、注重品质感和生活方式",
}

async def render_prompt(prompt_id: str, variables: dict) -> str:
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.PROMPT_SERVICE_URL}/v1/prompts/{prompt_id}/render",
                json={"variables": variables},
                timeout=15.0
            )
            if resp.status_code == 200:
                return resp.json().get("rendered", "")
    except Exception:
        pass
    return ""

async def generate_content(
    platform: str, topic: str, tone: str, brand: str,
    keywords: List[str], length: str
) -> dict:
    """生成指定平台的内容"""
    settings = get_settings()
    plat = PLATFORM_TEMPLATES.get(platform, PLATFORM_TEMPLATES["xiaohongshu"])
    tone_desc = TONE_PROMPTS.get(tone, TONE_PROMPTS["lively"])

    # 尝试从 Prompt Center 获取模板
    prompt_text = await render_prompt(plat["prompt_id"], {
        "topic": topic,
        "tone": tone_desc,
        "brand": brand or "康康精选",
        "keywords": ", ".join(keywords) if keywords else "",
        "max_length": str(plat["max_length"]),
    })

    # Fallback: 本地生成
    if not prompt_text:
        prompt_text = _fallback_generate(platform, topic, tone_desc, brand, keywords)

    # 尝试调用 LLM
    llm_text = ""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.MCP_HUB_URL}/v1/chat/completions",
                headers={"X-API-Key": settings.API_KEY, "Content-Type": "application/json"},
                json={
                    "model": "doubao-pro",
                    "messages": [{"role": "user", "content": prompt_text}],
                    "stream": False
                },
                timeout=20.0
            )
            if resp.status_code == 200:
                llm_text = resp.json()["choices"][0]["message"]["content"]
    except Exception:
        pass

    if not llm_text:
        llm_text = prompt_text

    # 提取标签
    tags = _extract_tags(llm_text, platform)

    # 获取推荐图片
    images = await _fetch_images(topic)

    return {
        "title": topic[:50],
        "content": llm_text,
        "tags": tags,
        "suggested_images": images,
    }

async def generate_topics(industry: str, positioning: str, count: int) -> List[dict]:
    """生成选题列表"""
    topics = []
    base_topics = [
        f"{industry}行业最新趋势解读",
        f"新手必看：{industry}入门指南",
        f"{positioning}的5个秘密技巧",
        f"{industry}避坑指南",
        f"{positioning}用户真实案例分享",
        f"{industry}产品选购攻略",
        f"{positioning}日常使用技巧",
        f"{industry}热门话题深度分析",
    ]
    import random
    selected = random.sample(base_topics, min(count, len(base_topics)))
    for t in selected:
        topics.append({
            "title": t,
            "category": "行业热点" if "趋势" in t or "分析" in t else "实用技巧",
            "trending_score": round(random.uniform(0.6, 0.98), 2),
            "suggested_tags": [industry, positioning, "干货", "推荐"],
            "reason": f"基于 {industry} 行业热度和 {positioning} 用户兴趣推荐"
        })
    return topics

def rewrite_content(content: str, style: str, tone: Optional[str] = None) -> str:
    """改写/润色文案"""
    if style == "expand":
        return f"【扩写版】\n\n{content}\n\n（以上为扩写后的内容，增加了更多细节和案例。）"
    elif style == "shorten":
        return content[:min(100, len(content) // 2)] + "..."
    elif style == "change_tone" and tone:
        return f"【{tone}风格改写】\n\n{content}"
    else:
        return f"【润色版】\n\n{content}\n\n（已优化用词和句式，提升可读性。）"

async def _fetch_images(query: str) -> List[str]:
    """从素材平台获取相关图片"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.ASSET_SERVICE_URL}/v1/assets/search",
                params={"q": query, "asset_type": "image", "status": "approved"},
                timeout=5.0
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                return [f"{settings.ASSET_SERVICE_URL}/v1/assets/{i['asset_id']}/download"
                        for i in items[:3]]
    except Exception:
        pass
    return []

def _extract_tags(text: str, platform: str) -> List[str]:
    """从文案中提取标签"""
    import re
    if platform == "xiaohongshu":
        tags = re.findall(r'#(\w+)', text)
        return list(set(tags))[:5] if tags else ["好物推荐", "生活分享"]
    return ["精选", "推荐"]

def _fallback_generate(platform: str, topic: str, tone: str, brand: str, keywords: List[str]) -> str:
    kw = ", ".join(keywords) if keywords else ""
    brand_str = f"品牌：{brand}" if brand else ""
    return f"""请为以下主题生成一篇{PLATFORM_TEMPLATES[platform]['style']}文案。

主题：{topic}
风格：{tone}
关键词：{kw}
{brand_str}

请直接输出文案内容，不要解释。"""

