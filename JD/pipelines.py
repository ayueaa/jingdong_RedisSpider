# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json

#
# class ExamplePipeline(object):
#     def open_spider(self, spider):  # 在爬虫开启的时候仅执行一次
#         if spider.name == 'book':
#             self.f = open('json.txt', 'a', encoding='utf-8')
#
#     def close_spider(self, spider):  # 在爬虫关闭的时候仅执行一次
#         if spider.name == 'book':
#             self.f.close()
#
#     def process_item(self, item, spider):
#         if spider.name == 'book':
#             self.f.write(json.dumps(dict(item), ensure_ascii=False, indent=2) + ',\n')
#         # 不return的情况下，另一个权重较低的pipeline将不会获得item
#         return item

from pymongo import MongoClient

class JdPipeline(object):
    def open_spider(self, spider):  # 在爬虫开启的时候仅执行一次
        if spider.name == 'book':
        # 也可以使用isinstanc函数来区分爬虫类:
            self.client = MongoClient(host='127.0.0.1', port=27017) # 实例化mongoclient
            self.db = self.client["jd"] # 创建数据库名为jd
            self.collection = self.db["book"] # 集合名为book的集合操作对象

    def process_item(self, item, spider):
        if spider.name == 'book':
            item = dict(item)
            self.collection.insert(item)
            # 此时item对象必须是一个字典,再插入
            # 如果此时item是BaseItem则需要先转换为字典：dict(BaseItem)
            # 不return的情况下，另一个权重较低的pipeline将不会获得item
        return item

    def close_spider(self, spider):
        self.client.close()

