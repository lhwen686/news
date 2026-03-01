import json
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
        print("请运行以下命令设置你的真实 API Key (例如):")
        print("  $env:GEMINI_API_KEY=\"AIza...你的真实密钥\"")
        print("然后再次运行此脚本。")
        return None
    
    # 自动读取 GEMINI_API_KEY 环境变量
    return genai.Client()

def translate_content(client, text, is_medical=False):
    """
    调用 Gemini 大模型进行翻译
    """
    if not text or text.strip() == "":
        return ""
        
    prompt = f"请将以下英文段落准确地翻译成中文。"
    if is_medical:
        prompt += "注意：此段落属于医疗/医学新闻，请务必使用严谨、专业的医学医学术语和临床通用准则进行翻译。"
    else:
        prompt += "请保持语言流畅、符合中文阅读习惯。"
        
    prompt += f"\n\n待翻译文本：\n{text}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except errors.APIError as e:
        if e.code == 429:
             print("  -> API 达到速率限制，等待 5 秒后重试...")
             time.sleep(5)
             return translate_content(client, text, is_medical)
        else:
             print(f"  -> 翻译发生错误: {e}")
             return text
    except Exception as e:
        print(f"  -> 翻译发生致命错误: {e}")
        return text # 降级：返回原文

def process_news():
    """
    读取 raw_news.json，处理翻译后保存为 processed_news.json
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
        
        # 为了演示，每个分类只翻译前 2 条，避免长时间等待和触发免费 API 严格限流
        for idx, item in enumerate(items[:2]):
            title_en = item.get("title", "")
            summary_en = item.get("summary", "")
            source = item.get("source", "")
            link = item.get("link", "")
            
            print(f"[{category}] 正在翻译第 {idx+1}/{min(2, len(items))} 条: {title_en[:30]}...")
            
            # 分别翻译标题和摘要
            title_zh = translate_content(client, title_en, is_medical)
            time.sleep(4) # 严格控制速率，避免 429
            
            print(f"  -> 摘要翻译中...")
            summary_zh = translate_content(client, summary_en, is_medical)
            time.sleep(4) # 严格控制速率，避免 429
            
            processed_item = {
                "category": category,
                "title_en": title_en,
                "title_zh": title_zh,
                "summary_en": summary_en,
                "summary_zh": summary_zh,
                "source": source,
                "link": link
            }
            processed_data.append(processed_item)
            total_processed += 1
            
            # 为避免触发免费 API 的限流，稍微增加延迟
            time.sleep(1)

    # 结构化保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=4)
        
    print(f"\n=========================================")
    print(f"翻译处理完成！总共处理了 {total_processed} 条新闻。")
    print(f"结果已结构化输出到: {OUTPUT_FILE}")
    print(f"=========================================")

if __name__ == "__main__":
    process_news()
