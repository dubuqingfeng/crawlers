#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binance Apex CMS Article Crawler
爬取 Binance 维护更新公告列表
API: https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query
"""

import requests
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

# 确保 json 和 logs 目录存在
os.makedirs("./json", exist_ok=True)
os.makedirs("./logs", exist_ok=True)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("./logs/binance_apex_cms_article.log"),
        logging.StreamHandler()
    ]
)

# 配置文件路径
ARTICLE_JSON_FILE = "./json/binance_apex_cms_articles.json"
PROGRESS_JSON_FILE = "./json/binance_apex_cms_progress.json"


def _build_card(title, articles):
    """
    构建飞书卡片消息
    
    Args:
        title: 卡片标题
        articles: 文章列表
    """
    elements = []
    
    if articles:
        # 添加概览信息
        elements.append({
            "tag": "note",
            "elements": [{
                "tag": "plain_text",
                "content": f"新增文章数: {len(articles)}"
            }]
        })
        
        # 添加每篇文章的信息
        for article in articles[:20]:  # 最多显示20条，避免消息过长
            title_text = article.get('title', 'N/A')
            release_date = article.get('release_date_readable', 'N/A')
            article_code = article.get('code', '')
            article_url = f"https://www.binance.com/zh-CN/support/announcement/{article_code}"
            
            content = f"**[{release_date}]**\n[{title_text}]({article_url})"
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": content
                }
            })
        
        if len(articles) > 20:
            elements.append({
                "tag": "note",
                "elements": [{
                    "tag": "plain_text",
                    "content": f"还有 {len(articles) - 20} 篇文章未显示..."
                }]
            })
        
        elements.append({"tag": "hr"})
    
    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "elements": elements,
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "blue"
            }
        }
    }


def send_webhook(articles):
    """
    发送 webhook 通知
    
    Args:
        articles: 新增的文章列表
    """
    if not articles:
        return
    
    # 从环境变量读取 Lark Webhook 地址
    webhook_url = os.getenv("LARK_WEBHOOK_URL")
    if not webhook_url:
        logging.warning("未配置 LARK_WEBHOOK_URL 环境变量，跳过发送 webhook")
        return
    
    try:
        payload = _build_card("Binance 维护更新公告", articles)
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"发送 webhook 成功: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"发送 webhook 失败: {str(e)}")


class BinanceArticleCrawler:
    """Binance 公告爬虫类"""
    
    def __init__(self, catalog_id: int = 157, article_type: int = 1):
        """
        初始化爬虫
        
        Args:
            catalog_id: 目录ID，默认157 (Maintenance Updates)
            article_type: 文章类型，默认1
        """
        self.base_url = "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query"
        self.catalog_id = catalog_id
        self.article_type = article_type
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 加载已保存的数据和进度
        self.all_articles = self._load_articles()
        self.progress = self._load_progress()
        
    def _load_articles(self) -> List[Dict]:
        """从文件加载已保存的文章数据"""
        try:
            if os.path.exists(ARTICLE_JSON_FILE):
                with open(ARTICLE_JSON_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logging.info(f"已加载 {len(data.get('articles', []))} 条历史文章")
                    return data.get('articles', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"加载历史文章失败: {e}")
        return []
    
    def _load_progress(self) -> Dict:
        """从文件加载爬取进度"""
        try:
            if os.path.exists(PROGRESS_JSON_FILE):
                with open(PROGRESS_JSON_FILE, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    logging.info(f"加载爬取进度: {progress}")
                    return progress
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"加载爬取进度失败: {e}")
        return {
            'last_crawl_time': None,
            'last_page': 0,
            'total_articles': 0,
            'catalog_total': 0
        }
    
    def _save_articles(self):
        """保存文章数据到文件"""
        data = {
            'catalog_id': self.catalog_id,
            'catalog_name': 'Maintenance Updates',
            'total_count': len(self.all_articles),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'articles': self.all_articles
        }
        with open(ARTICLE_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"已保存 {len(self.all_articles)} 条文章到 {ARTICLE_JSON_FILE}")
    
    def _save_progress(self, page_no: int, catalog_total: int):
        """保存爬取进度到文件"""
        self.progress.update({
            'last_crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_page': page_no,
            'total_articles': len(self.all_articles),
            'catalog_total': catalog_total
        })
        with open(PROGRESS_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
    
    def fetch_page(self, page_no: int, page_size: int = 20) -> Optional[Dict]:
        """
        获取单页数据
        
        Args:
            page_no: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            API响应数据，失败返回None
        """
        params = {
            'type': self.article_type,
            'pageNo': page_no,
            'pageSize': page_size,
            'catalogId': self.catalog_id
        }
        
        try:
            logging.info(f"正在请求第 {page_no} 页，每页 {page_size} 条...")
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查响应状态
            if data.get('code') != '000000' or not data.get('success'):
                logging.error(f"API返回错误: {data.get('message', 'Unknown error')}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logging.error(f"请求第 {page_no} 页失败: {e}")
            return None
    
    def crawl_all(self, page_size: int = 20, max_pages: Optional[int] = None, 
                  first_run_max_pages: Optional[int] = 5):
        """
        爬取所有文章（支持分页）
        
        Args:
            page_size: 每页数量
            max_pages: 最大爬取页数，None表示不限制
            first_run_max_pages: 首次运行时的最大页数限制，None表示不限制
        """
        logging.info("=" * 60)
        logging.info("开始爬取 Binance 维护更新公告")
        logging.info(f"目录ID: {self.catalog_id}, 文章类型: {self.article_type}")
        
        # 判断是否是首次运行
        is_first_run = len(self.all_articles) == 0
        if is_first_run and first_run_max_pages:
            logging.info(f"首次运行，限制最多爬取 {first_run_max_pages} 页")
            max_pages = first_run_max_pages
        elif max_pages:
            logging.info(f"最多爬取 {max_pages} 页")
        else:
            logging.info("爬取所有页面")
        
        logging.info("=" * 60)
        
        page_no = 1
        article_ids_set = {article['id'] for article in self.all_articles}
        new_articles_count = 0
        new_articles_list = []  # 收集本次新增的文章用于 webhook
        catalog_total = 0
        
        while True:
            # 检查是否达到最大页数限制
            if max_pages and page_no > max_pages:
                logging.info(f"已达到最大页数限制: {max_pages}")
                break
            
            # 获取当前页数据
            data = self.fetch_page(page_no, page_size)
            if not data:
                logging.error(f"获取第 {page_no} 页失败，停止爬取")
                break
            
            # 解析数据
            catalogs = data.get('data', {}).get('catalogs', [])
            if not catalogs:
                logging.warning("未找到目录数据")
                break
            
            catalog = catalogs[0]
            catalog_total = catalog.get('total', 0)
            articles = catalog.get('articles', [])
            
            if not articles:
                logging.info(f"第 {page_no} 页没有更多文章，爬取完成")
                break
            
            # 处理文章
            for article in articles:
                article_id = article['id']
                if article_id not in article_ids_set:
                    # 添加爬取时间
                    article['crawled_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # 转换时间戳为可读格式
                    if 'releaseDate' in article:
                        article['release_date_readable'] = datetime.fromtimestamp(
                            article['releaseDate'] / 1000
                        ).strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.all_articles.append(article)
                    new_articles_list.append(article)  # 收集新增文章
                    article_ids_set.add(article_id)
                    new_articles_count += 1
            
            logging.info(f"第 {page_no} 页: 获取 {len(articles)} 条，新增 {new_articles_count} 条，"
                        f"总计 {len(self.all_articles)}/{catalog_total} 条")
            
            # 保存进度
            self._save_progress(page_no, catalog_total)
            self._save_articles()
            
            # 检查是否已爬取完所有文章
            if len(self.all_articles) >= catalog_total:
                logging.info("已爬取所有文章")
                break
            
            # 继续下一页
            page_no += 1
            time.sleep(1)  # 避免请求过快
        
        logging.info("=" * 60)
        logging.info(f"爬取完成！共 {len(self.all_articles)} 条文章，本次新增 {new_articles_count} 条")
        logging.info(f"数据已保存到: {ARTICLE_JSON_FILE}")
        logging.info(f"进度已保存到: {PROGRESS_JSON_FILE}")
        logging.info("=" * 60)
        
        # 发送 webhook 通知（仅当有新增文章时）
        if new_articles_list:
            logging.info(f"发送 webhook 通知，新增文章数: {len(new_articles_list)}")
            # 按发布时间倒序排列，最新的在前面
            new_articles_list.sort(key=lambda x: x.get('releaseDate', 0), reverse=True)
            send_webhook(new_articles_list)
        else:
            logging.info("没有新增文章，跳过 webhook 通知")
    
    def get_latest_articles(self, limit: int = 10) -> List[Dict]:
        """获取最新的文章"""
        sorted_articles = sorted(
            self.all_articles,
            key=lambda x: x.get('releaseDate', 0),
            reverse=True
        )
        return sorted_articles[:limit]
    
    def search_articles(self, keyword: str) -> List[Dict]:
        """搜索包含关键词的文章"""
        results = []
        for article in self.all_articles:
            title = article.get('title', '').lower()
            if keyword.lower() in title:
                results.append(article)
        return results


def main():
    """主函数"""
    # 创建爬虫实例
    crawler = BinanceArticleCrawler(catalog_id=157, article_type=1)
    
    # 爬取文章
    # first_run_max_pages: 首次运行时最多爬取的页数（默认5页，即100条文章）
    # 如果需要首次爬取所有数据，设置 first_run_max_pages=None
    crawler.crawl_all(
        page_size=20,           # 每页20条
        first_run_max_pages=5   # 首次运行最多爬取5页
    )
    
    # 显示最新的5条文章
    logging.info("\n最新的5条文章:")
    for i, article in enumerate(crawler.get_latest_articles(5), 1):
        logging.info(f"{i}. [{article.get('release_date_readable', 'N/A')}] "
                    f"{article.get('title', 'N/A')}")


if __name__ == '__main__':
    main()
