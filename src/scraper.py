import json
import os
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import feedparser

# RSS 订阅源配置字典
RSS_FEEDS = {
    "医疗": {
        "NEJM": "https://www.nejm.org/action/showFeed?type=etoc&feed=rss&jc=nejm",
        "The Lancet": "http://www.thelancet.com/rssfeed/lancet_online.xml"
    },
    "科技": {
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "MIT Technology Review": "https://www.technologyreview.com/feed/"
    },
    "金融": {
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex"
    },
    "游戏": {
        "IGN": "https://feeds.feedburner.com/ign/news",
        "Polygon": "https://www.polygon.com/rss/index.xml"
    }
}

# 抓取数据保存路径
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw_news.json")

def parse_time(entry_time_struct, entry_time_str):
    """
    尝试将 RSS 解析出的时间结构或字符串转换为 datetime 对象
    """
    if entry_time_struct:
        try:
             # feedparser parsed time struct, make it UTC
             dt = datetime.fromtimestamp(time.mktime(entry_time_struct))
             return dt.replace(tzinfo=timezone.utc)
        except Exception:
             pass
             
    if entry_time_str:
        try:
             # Try parsing email formatted date
             dt = parsedate_to_datetime(entry_time_str)
             if dt.tzinfo is None:
                  dt = dt.replace(tzinfo=timezone.utc)
             return dt
        except Exception:
             pass
    
    return None

def filter_last_24_hours(entries):
    """
    过滤出过去24小时内的新闻
    """
    now = datetime.now(timezone.utc)
    twenty_four_hours_ago = now - timedelta(hours=24)
    filtered_entries = []
    
    for entry in entries:
        # 尝试获取不同的时间字段
        time_struct = entry.get('published_parsed') or entry.get('updated_parsed')
        time_str = entry.get('published') or entry.get('updated')
        
        entry_dt = parse_time(time_struct, time_str)
        
        if entry_dt and entry_dt >= twenty_four_hours_ago and entry_dt <= now:
            filtered_entries.append(entry)
            
    return filtered_entries


def fetch_and_parse_rss():
    """
    遍历 RSS 源进行抓取和解析
    """
    all_news = {category: [] for category in RSS_FEEDS.keys()}
    stats = {category: 0 for category in RSS_FEEDS.keys()}

    for category, sources in RSS_FEEDS.items():
        print(f"正在抓取分类: {category} ...")
        category_entries = []
        for source_name, source_url in sources.items():
            print(f"  -> 源: {source_name}")
            try:
                # 使用 feedparser 进行抓取解析
                feed = feedparser.parse(source_url)
                
                # 过滤出 24 小时内的内容
                recent_entries = filter_last_24_hours(feed.entries)
                
                # 提取必要字段
                for entry in recent_entries:
                     extracted_info = {
                         "title": entry.get("title", ""),
                         "link": entry.get("link", ""),
                         "summary": entry.get("summary", "") or entry.get("description", ""),
                         "source": source_name
                     }
                     category_entries.append(extracted_info)
                     
            except Exception as e:
                print(f"     [错误] 抓取 {source_name} 失败: {e}")
                
        all_news[category] = category_entries
        stats[category] = len(category_entries)
    
    return all_news, stats

def save_data(data):
    """
    保存数据为 JSON 格式
    """
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
         json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"\n抓取完成，数据已保存至 {OUTPUT_FILE}")

def main():
    print("开始执行 RSS 抓取任务...")
    news_data, category_stats = fetch_and_parse_rss()
    
    save_data(news_data)
    
    # 打印统计信息
    print("\n【抓取统计分析】")
    total_count = 0
    for category, count in category_stats.items():
         print(f"- {category}:  成功获取了 {count} 条内容")
         total_count += count
         
    print(f"总计今日新闻: {total_count} 条")


if __name__ == "__main__":
    main()
