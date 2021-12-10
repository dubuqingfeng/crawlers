import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class OppoSpider(CrawlSpider):
    name = 'oppo'
    allowed_domains = ['istore.oppomobile.com']
    # start_urls = ['https://']
    #
    # rules = (
    #     Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=True),
    # )

    def start_requests(self):
        base_url = 'https://istore.oppomobile.com/search/v1/search?keyword=%s&start=0&size=10'
        app_list = [
            '三级人才',
            '写小说'
        ]
        for i in app_list:
            print(i)
            # headers['sign'] =
            yield scrapy.Request(url=base_url % i, method="GET", callback=self.parse_search_result, meta={'keyword': i})

    def parse_search_result(self, response):
        keyword = response.meta.get('keyword')
        print(response.url)
        print(response.content)

    def parse_item(self, response):
        item = {}
        #item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
        #item['name'] = response.xpath('//div[@id="name"]').get()
        #item['description'] = response.xpath('//div[@id="description"]').get()
        return item
