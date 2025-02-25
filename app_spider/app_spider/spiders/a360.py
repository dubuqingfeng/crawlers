import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import datetime
from app_spider.items import BaiDuItem


class A360Spider(CrawlSpider):
    name = '360'
    custom_settings = {
        'LOG_LEVEL':'DEBUG',
        'LOG_FILE':'./logs/app_360_{}_{}_{}.log'.format(datetime.datetime.now().year,datetime.datetime.now().month,datetime.datetime.now().day)
    }

    def start_requests(self):
        base_url = 'http://m.app.so.com/search/index?q=%s&src=srp&startup=none'
        app_list = [
            '写小说'
        ]
        app_list = []
        with open("names.txt", "r", encoding="utf-8", errors='ignore') as f:
            app_list = f.readlines()
        for key in range(len(app_list)):
            line = app_list[key]
            i = line.strip() #list
            print("appno: %d, appname: %s" % (key, i))
            yield scrapy.Request(url=base_url % i, method="GET", callback=self.parse_search_result, meta={'keyword': i, 'key': key})

    def parse_search_result(self, response):
        keyword = response.meta.get('keyword')
        key = response.meta.get('key')
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