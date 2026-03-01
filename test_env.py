import sys
import requests
import feedparser
import jinja2

def main():
    print("=== 环境依赖检查通过 ===")
    print(f"Python 版本: {sys.version.split(' ')[0]}")
    print(f"Requests 版本: {requests.__version__}")
    print(f"Feedparser 版本: {feedparser.__version__}")
    print(f"Jinja2 版本: {jinja2.__version__}")
    print("=======================")
    print("所有核心依赖库均已成功安装且无版本冲突报错！可以开始项目开发。")

if __name__ == "__main__":
    main()
