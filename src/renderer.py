import json
import os
from jinja2 import Environment, FileSystemLoader

# 配置路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "processed_news.json")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_FILE = os.path.join(BASE_DIR, "index.html")

def render_html():
    """读取 json 并渲染 index.html"""
    print(f"正在读取数据源: {DATA_FILE}")
    if not os.path.exists(DATA_FILE):
        print(f"【错误】找不到 {DATA_FILE}，请先运行 translator.py！")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 按类别对数据进行分组
    grouped_news = {}
    for item in data:
        cat = item['category']
        if cat not in grouped_news:
            grouped_news[cat] = []
        grouped_news[cat].append(item)

    print(f"加载了 {len(data)} 条新闻数据，分为 {len(grouped_news)} 个板块。")
    print("正在使用 Jinja2 渲染 HTML ...")

    # 初始化 Jinja2 环境
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('index.html')

    # 将分组数据传入模板
    html_out = template.render(grouped_news=grouped_news)
    
    # 写入最终的 index.html
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_out)

    print(f"\n=========================================")
    print(f"成功！静态网页已生成完毕，请打开查看: \n【文件路径: {OUTPUT_FILE}】")
    print(f"=========================================")

if __name__ == "__main__":
    render_html()
