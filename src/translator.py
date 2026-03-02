import json
import re
import os
import time
from google import genai
from google.genai import errors

# 文件路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "data", "raw_news.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed_news.json")

def init_gemini():
    """初始化 Gemini API，依赖系统环境变量 GEMINI_API_KEY"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("【错误】未找到 GEMINI_API_KEY 环境变量！")
        return None
    return genai.Client()

def clean_llm_text(text):
    """
    清洗大模型输出，强制去除 Markdown、JSON 外骨骼和系统废话
    """
    if not text:
        return text
        
    cleaned = text
    # 1. 强行剔除 JSON 外壳，例如 {"translation": "..."} 或 {'translation': '...'}
    cleaned = re.sub(r'''^\{\s*["'][^"']*["']\s*:\s*["']?''', '', cleaned)
    cleaned = re.sub(r'''["']?\s*\}$''', '', cleaned)

    # 2. 强行剔除可能复读的系统指令和格式标签
    cleaned = re.sub(r'【系统强制约束.*?】', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'系统指令：.*?\n', '', cleaned, flags=re.DOTALL)
    cleaned = cleaned.replace('---待翻译文本开始---', '').replace('---待翻译文本结束---', '')
    cleaned = cleaned.replace('示例输入：Hello World', '').replace('示例输出：你好世界', '')

    # 3. 去除 Markdown 粗体斜体和标题
    cleaned = cleaned.replace('**', '').replace('__', '')
    cleaned = cleaned.replace('### ', '').replace('## ', '').replace('# ', '')
    
    # 返回干净字符串
    return cleaned.strip()

def call_llm_with_retry(client, prompt, max_retries=3):
    """
    带有重试机制和异常捕获的 LLM 调用函数
    """
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return clean_llm_text(response.text)
        except errors.APIError as e:
            if e.code == 429:
                wait_time = 10 * (attempt + 1)
                print(f"      -> [API 429 限流] 第 {attempt + 1} 次重试前等待 {wait_time} 秒...")
                time.sleep(wait_time)
            else:
                print(f"      -> [API 错误] {e}")
                time.sleep(5)
        except Exception as e:
            print(f"      -> [未知致命错误] {e}")
            time.sleep(5)
            
    print(f"      -> [失败] 达到最大重试次数 {max_retries}，返回空字符串。")
    return ""

def process_news():
    """
    读取 raw_news.json，处理多项翻译和摘要生成保存为 processed_news.json
    """
    client = init_gemini()
    if not client:
        return

    print(f"正在读取 {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print("【错误】找不到 raw_news.json，请先运行 scraper.py！")
        return

    processed_data = []
    total_processed = 0

    for category, items in raw_data.items():
        is_medical = (category == "医疗")
        
        for idx, item in enumerate(items):
            title_en = item.get("title", "")
            summary_en = item.get("summary", "")
            full_text_en = item.get("full_text", "")
            source = item.get("source", "")
            link = item.get("link", "")
            
            safe_title = title_en[:50]
            print(f"\n[{category}] 正在处理第 {idx+1}/{len(items)} 条: {safe_title}...")
            
            # --- 1. 翻译标题 ---
            print("  -> 翻译标题中...")
            title_req = "请将以下英文新闻标题准确地翻译成中文"
            if is_medical:
                title_req += "（注意使用标准的医学术语）"
            
            title_prompt = f"""系统指令：你是一个专业的翻译引擎。请直接输出以下英文文本的中文翻译。不要输出任何除了翻译结果以外的字符、符号、解释或原始指令。
禁止使用任何 Markdown 格式，禁止将结果包装在 JSON 中。只输出裸的中文翻译内容。
示例输入：Hello World
示例输出：你好世界

---待翻译文本开始---
【目标要求】：{title_req}
【英文原文】：{title_en}
---待翻译文本结束---"""
            title_zh = call_llm_with_retry(client, title_prompt)
            time.sleep(2)
            
            summary_zh = ""
            full_text_zh = ""
            
            if full_text_en:
                # --- 2. 基于全文生成 150 字摘要 ---
                print("  -> 生成 150 字中文摘要中...")
                summary_req = "请基于以下英文新闻全文，提炼出一段 150 字左右的高质量中文核心摘要"
                if is_medical:
                    summary_req += "（保持医学严谨性）"
                
                summary_prompt = f"""系统指令：你是一个专业的文本总结提取引擎。请直接输出符合要求的结果。不要输出任何除了摘要结果以外的字符、符号、解释或原始指令。
禁止使用任何 Markdown 格式，禁止将结果包装在 JSON 中。只输出裸的中文文本。

---待翻译文本开始---
【目标要求】：{summary_req}
【英文长文原文】：{full_text_en}
---待翻译文本结束---"""
                summary_zh = call_llm_with_retry(client, summary_prompt)
                time.sleep(2)
                
                # --- 3. 翻译完整正文及AI深度解析 ---
                print("  -> 翻译完整正文及生成 AI 深度解析中...")
                full_trans_req = "请将以下英文新闻完整正文翻译成流畅的中文，并严格保留原有的段落排版。在翻译完成后，基于文章内容生成一段 150-250 字的『AI 深度解析』，深入浅出地解释文章中的核心专业概念（如医学机制、技术原理或商业逻辑）及其行业影响。"
                if is_medical:
                    full_trans_req += "（非常重要：由于是医疗/医学新闻，请务必使用严谨、专业的医学术语和临床通用准则进行翻译和解析）"
                
                full_trans_prompt = f"""系统指令：你是一个专业的翻译及解析引擎。请先输出以下英文长文的中文流畅翻译。翻译结束后，【必须】在一个新行插入单独的分隔符 ===AI_EXPLANATION===，然后再输出一段 150-250 字的 AI 深度解析。不要输出任何除了翻译、分隔符和解析以外的字符。
绝对禁止使用 Markdown 粗体（**）和列表符号（-）。禁止将结果包装在 JSON 参数结构中。只输出原生文字。

---待翻译文本开始---
【目标要求】：{full_trans_req}
【英文原文】：{full_text_en}
---待翻译文本结束---"""
                raw_response = call_llm_with_retry(client, full_trans_prompt)
                
                # --- 解析翻译和AI深度解析 ---
                explanation_zh = ""
                full_text_zh = raw_response
                if '===AI_EXPLANATION===' in raw_response:
                    parts = raw_response.split('===AI_EXPLANATION===')
                    full_text_zh = parts[0].strip()
                    if len(parts) > 1:
                        explanation_zh = parts[1].strip()
            else:
                print("  -> [跳过] 此条目没有 full_text，无法生成摘要、全文翻译及解析。")
                explanation_zh = ""
                full_text_zh = ""

            processed_item = {
                "category": category,
                "title_en": title_en,
                "title_zh": title_zh,
                "summary_en": summary_en,
                "summary_zh": summary_zh,
                "full_text_en": full_text_en,
                "full_text_zh": full_text_zh,
                "explanation_zh": explanation_zh,
                "source": source,
                "link": link
            }
            processed_data.append(processed_item)
            total_processed += 1
            
            # 极度重要的速率限制：处理完每一篇文章后，加入延时缓解底层 API 压力
            print("  -> 当前文章处理完成，等待 3 秒进入下一篇...")
            time.sleep(3)

    # 结构化保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=4)
        
    print(f"\n=========================================")
    print(f"翻译处理完成！总共成功处理了 {total_processed} 条新闻大文本。")
    print(f"结果已结构化输出到: {OUTPUT_FILE}")
    print(f"=========================================")

if __name__ == "__main__":
    process_news()
