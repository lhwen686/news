import json
import os
import shutil
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader

# 配置路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "processed_news.json")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_FILE = os.path.join(BASE_DIR, "index.html")
ARTICLES_DIR = os.path.join(BASE_DIR, "articles")

def render_html():
    """读取 json 并渲染 index.html 和所有的 article.html"""
    print(f"正在读取数据源: {DATA_FILE}")
    if not os.path.exists(DATA_FILE):
        print(f"【错误】找不到 {DATA_FILE}，请先运行 translator.py！")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 清理并重建 articles 文件夹
    if os.path.exists(ARTICLES_DIR):
        shutil.rmtree(ARTICLES_DIR)
    os.makedirs(ARTICLES_DIR, exist_ok=True)

    # 注入全局 ID，用于生成静态文件名
    for idx, item in enumerate(data):
        item['id'] = idx

    # 按类别对数据进行分组 (供 index.html 使用)
    grouped_news = defaultdict(list)
    for item in data:
        grouped_news[item['category']].append(item)

    print(f"加载了 {len(data)} 条新闻数据，分为 {len(grouped_news)} 个板块。")
    print("正在使用 Jinja2 渲染 HTML ...")

    # 初始化 Jinja2 环境
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    index_template = env.get_template('index.html')
    article_template = env.get_template('article.html')

    # 1. 渲染各单篇独立详情页
    print("  -> 开始渲染详情页...")
    for item in data:
        item_html = article_template.render(item=item)
        item_path = os.path.join(ARTICLES_DIR, f"news_{item['id']}.html")
        with open(item_path, 'w', encoding='utf-8') as f:
            f.write(item_html)
              
    print(f"  -> {len(data)} 篇详情 HTML 页面成功生成在 {ARTICLES_DIR}。")

    # 2. 渲染主页并传入带 ID 的数据
    index_html = index_template.render(grouped_news=grouped_news)
    
    # 写入最终的 index.html
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f"\n=========================================")
    print(f"成功！静态主页面及详情页面已全部渲染完毕！")
    print(f"主页路径: {OUTPUT_FILE}")
    print(f"详情页目录: {ARTICLES_DIR}")
    print(f"=========================================")

if __name__ == "__main__":
    render_html()
