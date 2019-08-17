# -*- coding: utf-8 -*-
import scrapy
from JD.items import JdItem
import json
import re

# ------1.导入分布式爬虫类
from scrapy_redis.spiders import RedisSpider

# ------2. 继承分布式爬虫类
class BookSpider(RedisSpider):
    name = 'book'
    # ------3. 注释掉allowed_domains及start_urls
    # allowed_domains = ['jd.com','p.3.cn']
    # start_urls = ['https://book.jd.com/booksort.html']

    # ------4. 设置redis-key
    redis_key = "jd:book"
    # ------5. 设置__init__獲取允許的域
    def __init__(self, *args, **kwargs):
        domain = kwargs.pop("domain", "")
        self.allowed_domains = list(filter(None, domain.split(',')))
        super(BookSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        # 获取图书大分类
        big_node_list = response.xpath("//div[@class='mc']/dl/dt")
        for big_node in big_node_list:
            big_category = big_node.xpath("./a/text()").get()
            big_category_link = response.urljoin(big_node.xpath("./a/@href").get())
            # 获取小分类
            small_node_list = big_node.xpath("./following-sibling::dd[1]/em")
            for small_node in small_node_list:
                temp = {}
                small_category = small_node.xpath("./a/text()").get()
                _small_category_link = small_node.xpath("./a/@href").get()
                _ids = re.search(r"(\d+)-(\d+)-(\d+)",_small_category_link)
                cat = _ids.group(1) + "," + _ids.group(2) + "," + _ids.group(3)
                small_category_link = "https://list.jd.com/list.html?cat={}&tid={}".format(cat,_ids.group(3))

                temp["big_category"] = big_category
                temp["big_category_link"] = big_category_link
                temp["small_category"] = small_category
                temp["small_category_link"] = small_category_link
                temp["page"] = 1
                yield scrapy.Request(
                    url=temp["small_category_link"],
                    callback=self.parse_booklist,
                    meta=temp
                )

    def parse_booklist(self, response):
        temp = response.meta
        page = int(temp.get("page"))
        total_page = int(response.xpath("//span[@class='p-skip']/em/b/text()").get().strip())

        book_list = response.xpath("//div[@id='plist']/ul/li/div")
        for book in book_list:
            item = JdItem()
            item["big_category"] = temp["big_category"]
            item["big_category_link"] = temp["big_category_link"]
            item["small_category"] = temp["small_category"]
            item["small_category_link"] = temp["small_category_link"]
            item["bookname"] = book.xpath(".//div[@class='p-name']/a/em/text()").get().strip()
            item["link"] = response.urljoin(book.xpath("./div[@class='p-name']/a/@href").get())
            item["author"] = book.xpath("./div[@class='p-bookdetails']/span/span/a/text()").get()

            # 获取图书编号，拼接图书价格地址
            sku_id = book.xpath(".//@data-sku").get()
            price_url = "https://p.3.cn/prices/mgets?skuIds=J_" + sku_id
            yield scrapy.Request(url=price_url, callback=self.parse_price, meta={"meta_1":item})

        if page < total_page:
            page += 1
            small_category_link = temp["small_category_link"] + "&page={}".format(page)
            temp["page"] = page
            yield scrapy.Request(small_category_link, callback=self.parse_booklist, meta=temp)


    def parse_price(self, response):
        item = response.meta.get("meta_1")
        dict_data = json.loads(response.body)
        item["price"] = dict_data[0]["p"]
        yield item