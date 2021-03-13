# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ZrScrapy1Item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    accnum = scrapy.Field()
    fd = scrapy.Field()
    accepted = scrapy.Field()
    pdc = scrapy.Field()
    rp = scrapy.Field()
    item8k = scrapy.Field()
    name = scrapy.Field()
    cik = scrapy.Field()
    bazip = scrapy.Field()
    sic = scrapy.Field()
    fye = scrapy.Field()
    state = scrapy.Field()
    irs = scrapy.Field()
    film = scrapy.Field()
    web_url = scrapy.Field()
    zr_from_url = scrapy.Field()
    pass

class ZrScrapy1page2(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    a = scrapy.Field()
    b = scrapy.Field()
    c = scrapy.Field()
    d = scrapy.Field()
    e = scrapy.Field()
    pass
