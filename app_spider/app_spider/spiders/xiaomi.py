import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class XiaomiSpider(CrawlSpider):
    name = 'xiaomi'
    allowed_domains = ['www.xxx.com']
    start_urls = ['http://www.xxx.com/']

    # https://app.mi.com/suggestionApi?keywords=%E5%86%99%E5%B0%8F%E8%AF%B4
    rules = (
        Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        item = {}
        #item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
        #item['name'] = response.xpath('//div[@id="name"]').get()
        #item['description'] = response.xpath('//div[@id="description"]').get()
        return item
