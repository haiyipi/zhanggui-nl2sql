"""
UCL Honours Degree System 网页解析脚本
使用 curl_cffi 模拟 Chrome 120 指纹，绕过 Cloudflare 防护
"""

import json
import re
import yaml
import time
from pathlib import Path
from curl_cffi import requests
from openai import OpenAI


# ============================================================
# 0. 加载配置文件
# ============================================================
def load_config():
    config_path = Path(__file__).parent.parent / "conf" / "app_config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件未找到: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG = load_config()
LLM_CONFIG = CONFIG.get("llm", {})


# ============================================================
# 1. 数据格式定义 (Schema)
# ============================================================
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "degree_classes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "class_name": {"type": "string"},
                    "class_name_zh": {"type": "string"},
                    "mark_range": {"type": "string"},
                    "description": {"type": "string"},
                    "abbreviation": {"type": "string"}
                }
            }
        },
        "uk_award_statistics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "year": {"type": "string"},
                    "1st": {"type": "string"},
                    "2_1": {"type": "string"},
                    "2_2": {"type": "string"},
                    "3rd": {"type": "string"}
                }
            }
        },
        "international_equivalencies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "degree_class": {"type": "string"},
                    "ucl_mark_range": {"type": "string"},
                    "us": {"type": "string"},
                    "ects": {"type": "string"},
                    "china_gpa": {"type": "string"},
                    "germany": {"type": "string"},
                    "italy": {"type": "string"},
                    "india": {"type": "string"},
                    "netherlands_spain": {"type": "string"}
                }
            }
        },
        "ordinary_degree": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "condition": {"type": "string"}
            }
        }
    }
}


# ============================================================
# 2. Prompt
# ============================================================
SYSTEM_PROMPT = """你是一个数据提取助手。请从提供的网页内容中提取关于英国UCL荣誉学位体系的核心信息，并严格按照指定的JSON Schema格式输出。

注意：
1. 只提取页面中明确提到的信息，不要编造任何数据。
2. degree_classes 中的 class_name_zh 请使用标准中文翻译。
3. 返回的JSON必须是一个有效的对象，不要包含任何额外的文字说明。
"""

USER_PROMPT_TEMPLATE = """请从以下网页内容中提取关于UCL荣誉学位体系的核心信息。

网页内容：
{content}

请按照以下JSON Schema格式输出：
{output_schema}

要求：
1. 只提取页面中明确存在的信息
2. 表格数据请完整提取
3. 翻译要准确
4. 输出必须是合法的JSON
"""


# ============================================================
# 3. 抓取网页内容（curl_cffi 版本）
# ============================================================
def fetch_webpage_content(url: str) -> str:
    """
    使用 curl_cffi 抓取网页内容
    通过 impersonate 参数模拟 Chrome 120 的 TLS 指纹
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }

    try:
        # 模拟 Chrome 120 的 TLS 指纹
        response = requests.get(
            url,
            headers=headers,
            impersonate="chrome120",
            timeout=30
        )
        response.raise_for_status()

        html = response.text

        # 清理 HTML 标签，提取文本内容
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL | re.IGNORECASE)

        html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</p>', '\n\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</h[1-6]>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</li>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</tr>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</td>', ' ', html, flags=re.IGNORECASE)

        html = re.sub(r'<[^>]+>', ' ', html)

        lines = [line.strip() for line in html.split('\n') if line.strip()]
        content = '\n'.join(lines)

        if len(content) < 100:
            print("⚠️ 警告：提取的内容较少，页面结构可能有变化")

        return content

    except Exception as e:
        raise RuntimeError(f"网页抓取失败: {str(e)}")


# ============================================================
# 4. 备用方案：使用真实内容（当抓取失败时）
# ============================================================
def get_fallback_content() -> str:
    return """The UK Honours Degree System for Undergraduates

If you study for an undergraduate degree at UCL, you are aiming to graduate with a degree with honours. With this type of degree, the level of your academic performance on your programme is indicated by the 'class' of degree - or honours - you are awarded. Most universities award a class of degree based on the marks from the assessed work you have completed. To distinguish between students on the basis of their academic achievement, undergraduate degree awards are classified as follows:

First-Class Honours (70% and above): a first class degree, usually referred to as a 'first' or 1st, is the highest honours degree you can achieve
Upper Second-Class Honours (60-70%): there are two levels of second class degree. An upper second class, known as a 2:1 or two-one, is the higher of the two levels
Lower Second-Class Honours (50-60%): a 2.2 or two-two is the lower level of the second class degree
Third-Class Honours (40-50%): known as a 'third' or 3rd, this degree is the lowest honours degree achievable
Ordinary Degree: If an honours student fails to achieve a third class by a small margin, they may be awarded an ordinary degree i.e. without honours.

UK-wide award of different classes of honours degrees
The table below shows the percentage of each class of honours degree awarded across the UK, by year.
UK Honours degrees awarded: 1st, 2:1, 2:2, 3rd
2014/15: 22.0%, 49.5%, 23.0%, 5.5%
2015/16: 23.6%, 49.6%, 21.7%, 5.1%
2016/17: 25.8%, 49.1%, 20.3%, 4.9%
2017/18: 27.8%, 48.5%, 19.2%, 4.5%
2018/19: 28.4%, 48.3%, 19.0%, 4.3%

How does UK marking compare to other countries?
Type of degree, UCL mark, US, ECTS scale, China (GPA 4.0 scale), Germany, Italy, India, Netherlands & Spain
1st: 70-100%, A, A, 90% (3.7), Sehr gut, 108, 75%, 9
2:1: 65-69%, A-, B, 80% (3.3), Gut, Gut, 94, 60%, 7
     60-64%, B+
2:2: 55-59%, B, C, 75% (2.9), Gut -, 84, 50%, 6
     50-54%, B-, Befriedigend +
3rd: 46-49%, C+, D, Befriedigend
     43-45%, C, D, Befriedigend -
     40-42%, C-, D, Ausreichend
Fail: 0-39%, F, F, Ungenügend"""


# ============================================================
# 5. LLM 调用
# ============================================================
def extract_with_llm(content: str) -> dict:
    api_key = LLM_CONFIG.get('api_key')
    base_url = LLM_CONFIG.get('base_url')
    model_name = LLM_CONFIG.get('model_name', 'qwen-max')

    if not api_key:
        raise ValueError("app_config.yaml 中未配置 llm.api_key")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url or "https://api.openai.com/v1"
    )

    if len(content) > 8000:
        content = content[:8000]

    user_prompt = USER_PROMPT_TEMPLATE.format(
        content=content,
        output_schema=json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=2)
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


# ============================================================
# 6. 主程序入口
# ============================================================
def main():
    print("=" * 60)
    print("UCL Honours Degree System 网页解析工具 (curl_cffi 版本)")
    print("=" * 60)
    print(f"📋 使用模型: {LLM_CONFIG.get('model_name', 'qwen-max')}")

    target_url = "https://www.ucl.ac.uk/study/current-students/certificates-and-results/uk-honours-degree-system-undergraduates"

    try:
        print("\n📡 正在使用 curl_cffi 抓取真实网页内容...")
        print(f"🔗 URL: {target_url}")

        try:
            content = fetch_webpage_content(target_url)
            print(f"✅ 抓取成功，共 {len(content)} 个字符")

            if len(content) < 200:
                print("   ⚠️ 抓取内容不足，切换至备用方案...")
                content = get_fallback_content()
                print(f"   ✅ 备用方案加载完成，共 {len(content)} 个字符")
        except Exception as e:
            print(f"   ⚠️ 抓取失败: {e}")
            print("   🔄 切换至备用方案...")
            content = get_fallback_content()
            print(f"   ✅ 备用方案加载完成，共 {len(content)} 个字符")

        print("\n🤖 正在调用 LLM 进行信息提取...")
        result = extract_with_llm(content)
        print("✅ 提取完成")

        print("\n" + "=" * 60)
        print("📊 解析结果 (JSON):")
        print("=" * 60)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        with open("ucl_honours_degree_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n💾 结果已保存到 ucl_honours_degree_result.json")

    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())