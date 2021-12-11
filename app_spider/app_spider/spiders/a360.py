import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from app_spider.items import BaiDuItem


class A360Spider(CrawlSpider):
    name = '360'

    def start_requests(self):
        base_url = 'http://m.app.so.com/search/index?q=%s&src=srp&startup=none'
        app_list = [
            '写小说'
        ]
        data = []
        with open("names.txt", "r", encoding="utf-8", errors='ignore') as f:
            data = f.readlines()
        for key in range(len(data)):
            line = data[key]
            i = line.strip() #list
            print("appno: %d, appname: %s" % (key, i))
            yield scrapy.Request(url=base_url % i, method="GET", callback=self.parse_search_result, meta={'keyword': i, 'key': key})

    def parse_search_result(self, response):
        keyword = response.meta.get('keyword')
        for app_item in response.xpath(
                '//div/div[contains(@class, "main")]/div[contains(@class, "list")]/ul/li'):
            if app_item.extract() != '':
                item = BaiDuItem()
                item['app_name'] = app_item.xpath(
                    'div[contains(@class, "list-cont")]/div[contains(@class, "lt-c-tit")]/h2/a/text()').extract_first()
                item['download_num'] = app_item.xpath(
                    'div[contains(@class, "list-cont")]/div[contains(@class, "lt-c-s-n")]/span/text()').extract_first()
                item['size'] = app_item.xpath(
                    'div[contains(@class, "list-cont")]/div[contains(@class, "lt-c-tit")]/span/text()').extract_first()
                item['link'] = app_item.xpath(
                    '@data-href').extract_first()
                item['keyword'] = keyword
                item['image_urls'] = app_item.xpath(
                    'div[contains(@class, "list-img")]/img/@src').extract_first()
                item['introduction'] = ''
                item['download_url'] = app_item.xpath(
                    'div[contains(@class, "btns")]/a/@href').extract_first()
                item['app_no'] = key
                item['source'] = 'a360'
                yield item