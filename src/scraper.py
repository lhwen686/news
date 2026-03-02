import calendar
import json
import os
import requests
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import feedparser
from newspaper import Article, Config
from bs4 import BeautifulSoup

# 配置 User-Agent 以防止被反爬屏蔽
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# RSS 订阅源配置字典 - 大量补充权威大众媒体，以便顺利凑齐各类至少5篇
RSS_FEEDS = {
    "医疗": {
        "WHO News": "https://www.who.int/zh/rss-feeds/news-english.xml",
        "Medical News Today": "https://www.medicalnewstoday.com/feed",
        "Mayo Clinic": "https://newsnetwork.mayoclinic.org/feed/",
        "Health News": "https://tools.cdc.gov/api/v2/resources/media/132608.rss",
        "丁香园": "https://rsshub.app/dxy/bbs/profile/article/2115163",
        "News-Medical": "https://www.news-medical.net/tag/feed/Medical-Research.aspx",
        "The Lancet": "https://www.thelancet.com/rssfeed/lancet_online.xml",
        "WebMD": "https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
        "MedicalXpress": "https://medicalxpress.com/rss-feed/"
    },
    "科技": {
        "少数派": "https://sspai.com/feed",
        "Engadget中文": "https://cn.engadget.com/rss.xml",
        "36氪": "https://rsshub.app/36kr/newsflashes",
        "IT之家": "https://rsshub.app/ithome/it",
        "TechCrunch": "https://techcrunch.com/feed/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Wired": "https://www.wired.com/feed/rss"
    },
    "金融": {
        "FT中文网": "http://www.ftchinese.com/rss/feed",
        "华尔街见闻": "https://rsshub.app/wallstreetcn/news/global",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?id=10000664",
        "Investing.com": "https://www.investing.com/rss/news.rss"
    },
    "游戏": {
        "Steam Official": "https://store.steampowered.com/feeds/news.xml",
        "Clash of Clans News": "https://news.google.com/rss/search?q=Clash+of+Clans+update+OR+blog+site:supercell.com+OR+site:clashofclans.com&hl=en-US&gl=US&ceid=US:en",
        "Eurogamer": "https://www.eurogamer.net/feed/news",
        "Nintendo Life": "https://www.nintendolife.com/feeds/news",
        "PC Gamer": "https://www.pcgamer.com/rss/",
        "Gematsu": "https://www.gematsu.com/feed",
        "GamesRadar": "https://www.gamesradar.com/rss/",
        "IGN News": "https://feeds.feedburner.com/ign/news",
        "VG247": "https://www.vg247.com/feed/news"
    }
}

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw_news.json")

def parse_time(entry_time_struct, entry_time_str):
    if entry_time_struct:
        try:
            dt = datetime.fromtimestamp(calendar.timegm(entry_time_struct), tz=timezone.utc)
            return dt
        except Exception:
            pass
            
    if entry_time_str:
        try:
            dt = parsedate_to_datetime(entry_time_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass
    
    return None

def filter_last_24_hours(entries):
    now = datetime.now(timezone.utc)
    twenty_four_hours_ago = now - timedelta(hours=24)
    filtered_entries = []
    
    for entry in entries:
        time_struct = entry.get('published_parsed') or entry.get('updated_parsed')
        time_str = entry.get('published') or entry.get('updated')
        
        entry_dt = parse_time(time_struct, time_str)
        # 宽容处理：如果时间无法解析，就不抛出，但为了满足要求“保留24小时过滤”，我们只能选择有明确时间的
        if entry_dt:
            if twenty_four_hours_ago <= entry_dt <= now + timedelta(hours=1):
                filtered_entries.append(entry)
            
    return filtered_entries

def fetch_full_text(url):
    try:
        config = Config()
        config.user_agent = USER_AGENT
        config.request_timeout = 10
        article = Article(url, config=config, fetch_images=True)
        article.download()
        article.parse()
        text = article.text.strip()
        image_url = article.top_image if hasattr(article, 'top_image') and article.top_image else ""
        if len(text) > 50:
            return text, image_url
    except Exception as e:
        pass
        
    # --- BeautifulSoup Fallback (针对无法解析的站点) ---
    try:
        resp = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        og_image = soup.find("meta", property="og:image")
        image_url = og_image["content"] if og_image and og_image.get("content") else ""
        if len(text) > 50:
            return text, image_url
    except Exception as e:
        pass

    return None, ""

def fetch_and_parse_rss():
    all_news = {category: [] for category in RSS_FEEDS.keys()}
    stats = {category: 0 for category in RSS_FEEDS.keys()}

    for category, sources in RSS_FEEDS.items():
        print(f"\n正在抓取分类: {category} ...")
        category_entries = []
        
        for source_name, source_url in sources.items():
            if len(category_entries) >= 5:
                break
                
            print(f"  -> 源: {source_name}")
            try:
                # 使用 requests 并带上 User-Agent，然后让 feedparser 解析 HTML，防止被屏蔽
                headers = {"User-Agent": USER_AGENT}
                try:
                    resp = requests.get(source_url, headers=headers, timeout=10)
                    feed = feedparser.parse(resp.content)
                except Exception:
                    feed = feedparser.parse(source_url)
                    
                recent_entries = filter_last_24_hours(feed.entries)
                if not recent_entries and source_name in ["Steam Official", "Clash of Clans News"]:
                    # 针对更新不频繁的官方源，若24小时内无新闻，选取最新的5条
                    recent_entries = feed.entries[:5]
                
                # 如果没有符合24h的，但是必须强求，我们也只能放宽一下（或这里保持严格不变，指望后面的源能凑够）
                
                for entry in recent_entries:
                    if len(category_entries) >= 5:
                        break
                        
                    link = entry.get("link", "")
                    if not link:
                        continue
                        
                    full_text_result = fetch_full_text(link)
                    if isinstance(full_text_result, tuple):
                        full_text, image_url = full_text_result
                    else:
                        full_text, image_url = full_text_result, ""
                    
                    if not full_text:
                        # 尝试直接从 RSS item 内容中提取正文作为最后手段 (BeautifulSoup 清洗 HTML)
                        raw_html = ""
                        if "content" in entry and len(entry.content) > 0:
                            raw_html = entry.content[0].get("value", "")
                        elif "summary" in entry:
                            raw_html = entry.summary
                        
                        if raw_html:
                            soup = BeautifulSoup(raw_html, "html.parser")
                            fallback_text = soup.get_text(separator="\n", strip=True)
                            if len(fallback_text) > 50:
                                full_text = fallback_text

                    if full_text:
                        # Steam 特定过滤逻辑：跳过少于 200 字的文章
                        if source_name == "Steam Official" and len(full_text) < 200:
                            print(f"      [跳过] Steam 新闻字数太少 ({len(full_text)} 字): {link}")
                            continue

                        extracted_info = {
                            "title": entry.get("title", ""),
                            "link": link,
                            "summary": entry.get("summary", "") or entry.get("description", ""),
                            "source": source_name,
                            "full_text": full_text,
                            "image_url": image_url
                        }
                        category_entries.append(extracted_info)
                        print(f"      [成功] 获取正文: {extracted_info['title']}")
                    else:
                        print(f"      [跳过] 无法获取正文或正文太短: {link}")
                        
            except Exception as e:
                print(f"     [错误] 抓取 {source_name} 失败: {e}")
                
        if len(category_entries) < 5:
            print(f"     [警告] 分类 {category} 仅获取到 {len(category_entries)} 条有效新闻，未达到 5 条的目标。")

        all_news[category] = category_entries
        stats[category] = len(category_entries)
    
    return all_news, stats

def save_data(data):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"\n抓取完成，数据已保存至 {OUTPUT_FILE}")

def main():
    print("开始执行 RSS 抓取任务...")
    news_data, category_stats = fetch_and_parse_rss()
    save_data(news_data)
    
    print("\n【抓取统计分析】")
    total_count = 0
    for category, count in category_stats.items():
        print(f"- {category}:  成功获取了 {count} 条内容")
        total_count += count
         
    print(f"总计今日新闻: {total_count} 条")

if __name__ == "__main__":
    main()
