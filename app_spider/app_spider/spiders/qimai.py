import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import random
import base64
import time
import json
from urllib.parse import urlencode
from app_spider.items import BaiDuItem


class QimaiSpider(CrawlSpider):
    name = 'qimai'
    market_rules = {
        'huawei': 6,
        'xiaomi': 4,
        'vivo': 8,
        'oppo': 9,
        'meizu': 7,
        'yingyongbao': 3,
        'baidu': 2,
        '360': 1,
        'wandoujia': 5,
        'play': 10,
    }
    market_name = 'vivo'

    def start_requests(self):
        # https://www.qimai.cn/search/android/market/8/search/%E5%AF%8C%E8%B1%AA%E9%BA%BB%E5%B0%86
        # https://api.qimai.cn/search/android?analysis=eDBWWUQESl9DUUJAFkVFWRdxbAtwEx9DVVFCAF8cVApcR1lZVHATAQIEUAULAlwIDQ4FcBMB&page=1&search=富豪麻将&market=9
        base_url = 'https://api.qimai.cn'
        url = '/search/android'
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/92.0.4515.159 Safari/537.36',
            'referer': 'https://www.qimai.cn/',
            # 'cookies': cookies,
        }
        app_list = [
            '三级人才',
            '写小说'
        ]
        market = self.market_rules[self.market_name]
        for key in range(len(app_list)):
            line = app_list[key]
            i = line.strip() #list
            params = {
                'market': market,
                'search': i,
                'page': 1
            }
            data = ''.join(sorted([str(v) for v in params.values()]))
            analysis = self.get_analysis(data, url)
            params['analysis'] = analysis
            print("appno: %d, appname: %s, market: %d" % (key, i, market))
            rurl = base_url + url + '?' +  urlencode(params)
            yield scrapy.Request(url=rurl, method="GET", callback=self.parse_search_result, meta={'keyword': i, 'key': key}, headers=headers)

    def get_analysis(self, params, url):
        # i = '00000008d78d46a'
        i = '0000000c735d856'
        f = -(random.randint(100, 10000))
        o = int(time.time() * 1000) - (f or 0) - 1515125653845
        r = base64.b64encode(params.encode()).decode()
        r = f'{r}@#{url}@#{o}@#1'
        e = len(r)
        n = len(i)
        ne = ''
        for _ in range(0, e):
            ne += chr(ord(r[_]) ^ ord(i[(_ + 10) % n]))
        ne = base64.b64encode(ne.encode()).decode()
        return ne
    
    def parse_search_result(self, response):
        keyword = response.meta.get('keyword')
        key = response.meta.get('key')
        data = json.loads(response.body)
        if data['code'] != 10000:
            self.logger.error('qimai.cn: %s' % data['msg'])
            return
        applist = data['appList']
        for app_item in applist:
            item = BaiDuItem()
            item['app_name'] = app_item['appInfo']['appName']
            item['download_num'] = app_item['appInfo']['app_download_num']
            item['size'] = 0
            item['link'] = app_item['appInfo']['appId']
            item['keyword'] = keyword
            item['image_urls'] = app_item['appInfo']['icon']
            item['introduction'] = app_item['company']['name']
            item['download_url'] = ''
            item['app_no'] = key
            item['source'] = self.market_name
            yield item
