# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo

from twisted.internet import defer, reactor
import time


class AppSpiderPipeline:
    def process_item(self, item, spider):
        return item


class MongoPipeline(object):
    def __init__(self, mongo_uri, mongo_db, mongo_col):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_col = mongo_col

    # MONGO_URI,MONGO_DB 在settings.py中配置
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB'),
            mongo_col=crawler.settings.get('MONGO_COL'),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.mongodb = self.client[self.mongo_db]

    def spider_closed(self, spider, reason):
        self.client.close()

    # 下面的操作是重点
    @defer.inlineCallbacks
    def process_item(self, item, spider):
        out = defer.Deferred()
        reactor.callInThread(self._insert, item, out)
        yield out
        defer.returnValue(item)

    def _insert(self, item, out):
        collections = ''
        if 'source' in item.keys():
            collections = item['source']
        if len(self.mongo_col) != 0:
            collections = self.mongo_col
        self.mongodb[collections].insert(dict(item))
        reactor.callFromThread(out.callback, item)