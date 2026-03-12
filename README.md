# Daily Insight - AI 双语新闻聚合平台

Daily Insight 是一个全自动的 AI 驱动双语新闻聚合平台，每日自动从 30+ 个 RSS 源抓取新闻，利用 Google Gemini API 进行中英文翻译与深度分析，并生成静态网站部署到 GitHub Pages。

## 功能特性

- **多源新闻聚合** — 覆盖医疗、科技、金融、游戏四大领域，30+ 个 RSS 信息源
- **AI 翻译与摘要** — 基于 Gemini 2.5 Flash 自动翻译标题、生成中文摘要
- **AI 深度解析** — 每篇文章附带 150-250 字的 AI Insight 分析
- **全自动化流水线** — GitHub Actions 每日定时执行，零人工干预
- **双语展示** — 中英文内容同步呈现，适合不同语言背景的读者
- **响应式设计** — 基于 Tailwind CSS，支持桌面端与移动端浏览

## 新闻来源

| 分类 | 来源 |
|------|------|
| 🏥 医疗 | WHO、Mayo Clinic、Medical News Today、CDC、丁香园、Lancet、WebMD |
| 💻 科技 | Hacker News、少数派、Engadget、36氪、IT之家、TechCrunch、The Verge、Wired |
| 💰 金融 | FT中文网、华尔街见闻、Yahoo Finance、CNBC、Investing.com |
| 🎮 游戏 | Steam、Eurogamer、Nintendo Life、PC Gamer、IGN、GamesRadar |

## 技术架构

```
GitHub Actions 定时触发 (每日 UTC 22:00 / 北京时间 06:00)
    │
    ▼
┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│  Scraper    │───▶│   Translator    │───▶│  Renderer   │
│ (抓取新闻)   │    │ (AI翻译与分析)   │    │ (生成HTML)  │
└─────────────┘    └─────────────────┘    └─────────────┘
    │                     │                      │
    ▼                     ▼                      ▼
raw_news.json     processed_news.json      index.html +
                                           article pages
                                                │
                                                ▼
                                        GitHub Pages 部署
```

### 三阶段处理流水线

1. **Scraper** (`src/scraper.py`) — 抓取 RSS 订阅源，提取文章全文，过滤 24 小时内的新闻
2. **Translator** (`src/translator.py`) — 调用 Gemini API 翻译标题/摘要/正文，生成 AI 深度分析
3. **Renderer** (`src/renderer.py`) — 使用 Jinja2 模板渲染静态 HTML 页面

## 技术栈

| 层级 | 技术 |
|------|------|
| 新闻抓取 | feedparser, newspaper3k, BeautifulSoup4 |
| AI 处理 | Google Gemini 2.5 Flash (google-genai) |
| 模板渲染 | Jinja2 |
| 前端样式 | Tailwind CSS, Google Fonts (Inter, Noto Serif SC) |
| 自动化部署 | GitHub Actions, GitHub Pages |

## 项目结构

```
news/
├── .github/workflows/
│   └── daily_update.yml     # GitHub Actions 自动化流水线
├── src/
│   ├── scraper.py           # RSS 抓取与全文提取
│   ├── translator.py        # AI 翻译与深度分析
│   └── renderer.py          # 静态 HTML 渲染
├── templates/
│   ├── index.html           # 首页模板 (分类导航 + 文章卡片)
│   └── article.html         # 文章详情页模板
├── data/
│   ├── raw_news.json        # 原始抓取数据
│   └── processed_news.json  # AI 处理后的数据
├── articles/                # 生成的文章详情页
├── index.html               # 生成的首页
├── requirements.txt         # Python 依赖
└── test_env.py              # 环境验证脚本
```

## 快速开始

### 环境要求

- Python 3.12+
- Google Gemini API Key

### 本地运行

```bash
# 克隆项目
git clone https://github.com/lhwen686/news.git
cd news

# 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 设置 API Key
export GEMINI_API_KEY="your-api-key-here"

# 依次运行三阶段流水线
python src/scraper.py
python src/translator.py
python src/renderer.py
```

运行完成后，打开 `index.html` 即可浏览生成的新闻页面。

### GitHub Actions 自动部署

1. 在仓库 Settings → Secrets and variables → Actions 中添加 `GEMINI_API_KEY`
2. 流水线将在每日 UTC 22:00（北京时间 06:00）自动运行
3. 也可在 Actions 页面手动触发 `workflow_dispatch`

## 设计亮点

- **多级容错机制** — newspaper3k 解析失败时自动回退到 BeautifulSoup，全文提取失败时使用 RSS 摘要
- **API 速率保护** — 指数退避重试策略，最多 3 次重试
- **反封锁措施** — User-Agent 轮换、超时控制
- **医疗领域专项优化** — 针对医疗类文章强制使用专业术语翻译
- **内容质量过滤** — 最低字符数限制，确保文章内容有效

## 许可证

本项目仅供学习和个人使用。
