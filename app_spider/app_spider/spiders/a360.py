import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from app_spider.items import BaiDuItem


class A360Spider(CrawlSpider):
    name = '360'

    # allowed_domains = ['www.xxx.com']
    # start_urls = ['http://www.xxx.com/']
    #
    # rules = (
    #     Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=True),
    # )
    #
    # def parse_item(self, response):
    #     item = {}
    #     #item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
    #     #item['name'] = response.xpath('//div[@id="name"]').get()
    #     #item['description'] = response.xpath('//div[@id="description"]').get()
    #     return item

    def start_requests(self):
        base_url = 'http://m.app.so.com/search/index?q=%s&src=srp&startup=none'
        app_list = [
            '写小说'
        ]
        for i in app_list:
            print(i)
            yield scrapy.Request(url=base_url % i, method="GET", callback=self.parse_search_result, meta={'keyword': i})

    def parse_search_result(self, response):
        keyword = response.meta.get('keyword')
        print(keyword)
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
                yield item
        print(response.url)
