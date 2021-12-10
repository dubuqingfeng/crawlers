# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class AppSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class BaiDuItem(scrapy.Item):
    app_name = Field()  # 应用名称
    app_no = Field() #
    keyword = Field()  # 关键词
    link = Field()  # 链接
    download_num = Field()  # 下载量
    size = Field()  # 大小
    image_urls = Field() # 图标 url
    introduction = Field() # 介绍
    download_url = Field() # 下载 url
    source = Field() # 来源
    version = Field()
    file_urls = Field()
