import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from app_spider.items import BaiDuItem
import datetime

class BaiduSpider(CrawlSpider):
    name = 'baidu'
    allowed_domains = ['shouji.baidu.com']
    custom_settings = {
        'LOG_LEVEL':'DEBUG',
        'LOG_FILE':'./logs/app_baidu_{}_{}_{}.log'.format(datetime.datetime.now().year,datetime.datetime.now().month,datetime.datetime.now().day)
    }

    def start_requests(self):
        base_url = 'https://shouji.baidu.com/s?wd=%s&data_type=app'
        app_list = [
            '三级人才',
            '写小说'
        ]
        data = []
        with open("names.txt","r",encoding="utf-8",errors='ignore') as f:
            data = f.readlines()
        for key in range(len(data)):
            line = data[key]
            i = line.strip() #list
            print(i)
            yield scrapy.Request(url=base_url % i, method="GET", callback=self.parse_search_result, meta={'keyword': i, 'key': key})

    def parse_search_result(self, response):
        keyword = response.meta.get('keyword')
        key = response.meta.get('keyword')
        for app_item in response.xpath(
                '//div[contains(@class, "search-res")]/ul/li'):
            if app_item.extract() != '':
                item = BaiDuItem()
                app_name = app_item.xpath('div[contains(@class, "app")]/div[contains(@class, "info")]/div[contains(@class, "top")]/a/text()').extract_first()
                if app_name is not None:
                    item['app_name'] = app_name.strip()
                else:
                    item['app_name'] = ''
                item['link'] = app_item.xpath('div[contains(@class, "app")]/div[contains(@class, "info")]/div[contains(@class, "top")]/a/@href').extract_first()
                item['keyword'] = keyword
                item['download_num'] = app_item.xpath('div[contains(@class, "app")]/div[contains(@class, "info")]/div[contains(@class, "middle")]/em/span/text()').extract_first()
                item['size'] = app_item.xpath('div[contains(@class, "app")]/div[contains(@class, "info")]/div[contains(@class, "middle")]/span[contains(@class, "size")]/text()').extract_first()
                item['image_urls'] = app_item.xpath('div[contains(@class, "app")]/div[contains(@class, "icon")]/a/img/@src').extract_first()
                item['introduction'] = app_item.xpath('div[contains(@class, "app")]/div[contains(@class, "info")]/div[contains(@class, "down")]/span/text()').extract_first()
                item['download_url'] = app_item.xpath('div[contains(@class, "app")]/div[contains(@class, "little-install")]/a/@data_url').extract_first()
                item['app_no'] = key
                item['source'] = 'baidu'
                yield item

    def parse_item(self, response):
        print(response.url)

    def parse_detail(self, response):
        item = BaiDuItem()
        app_name = response.xpath('//*[@id="doc"]/div[2]/div/div[1]/div/div[2]/h1/span/text()').extract_first()
        version = response.xpath('//*[@id="doc"]/div[2]/div/div[1]/div/div[2]/div[2]/span[2]/text()').extract_first()
        size = response.xpath('//*[@id="doc"]/div[2]/div/div[1]/div/div[2]/div[2]/span[1]/text()').extract_first()
        download_num = response.xpath(
            '//*[@id="doc"]/div[2]/div/div[1]/div/div[2]/div[2]/span[3]/text()').extract_first()
        introduction = response.xpath('//*[@id="doc"]/div[2]/div/div[2]/div[2]/div[2]/div/p/text()').extract_first()
        file_urls = response.xpath('//*[@id="doc"]/div[2]/div/div[1]/div/div[4]/a/@href').extract_first()
        image_urls = response.xpath('//*[@id="doc"]/div[2]/div/div[1]/div/div[1]/div/img/@src').extract_first()

        for key, value in item.fields.items():
            item[key] = eval(key)

        yield item
