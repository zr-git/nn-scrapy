# get data and print
# scrapy crawl test2
# scrapy crawl test2 --loglevel=INFO
# scrapy crawl test2 -s LOG_FILE=spider.log
import scrapy
import pickle
import os
from zr_scrapy1.items import ZrScrapy1Item


class ExampleSpider(scrapy.Spider):
    name = 'test2'
    print('main 2222222')
    # allowed_domains = ['https://www.163.com']
    # start_urls = ['https://www.163.com/']*100

    # print('read back doc_urls 2222...')
    # with open('edgar_indexs', 'rb')as f:
    #     start_urls = pickle.load(f)
    # total = len(start_urls)

    def __init__(self):
        print('init 22222222')
        self.fail_urls = []  # 创建一个变量来储存404URL

    def do_parse(self, response, item):
        item['accnum'] = response.xpath('//*[@id="secNum"]/text()').getall()
        item['fd'] = response.xpath('//*[@id="formDiv"]/div[2]/div[1]/div[2]/text()').get()
        item['accepted'] = response.xpath('//*[@id="formDiv"]/div[2]/div[1]/div[4]/text()').get()
        item['pdc'] = response.xpath('//*[@id="formDiv"]/div[2]/div[1]/div[6]/text()').get()
        item['rp'] = response.xpath('//*[@id="formDiv"]/div[2]/div[1]/div[2]/text()').get()
        item['item8k'] = response.xpath('//*[@id="formDiv"]/div[2]/div[3]/div[2]').get()
        item['name'] = response.xpath('//*[@id="filerDiv"]/div[3]/span/text()[1]').get()
        item['cik'] = response.xpath('//*[@id="filerDiv"]/div[3]/span/a/text()').get()
        item['bazip'] = response.xpath('//*[@id="filerDiv"]/div[2]/span[3]/text()').get()
        item['sic'] = response.xpath('//*[@id="filerDiv"]/div[3]/p/b/a/text()').get()
        item['fye'] = response.xpath('//*[@id="filerDiv"]/div[3]/p/strong[3]/text()').get()
        item['state'] = response.xpath('//*[@id="filerDiv"]/div[3]/p/strong[2]/text()').get()
        item['irs'] = response.xpath('//*[@id="filerDiv"]/div[3]/p/strong[1]/text()').get()
        item['film'] = response.xpath('//*[@id="filerDiv"]/div[3]/p/strong[6]/text()').get()
        item['web_url'] = response.xpath('//*[@id="formDiv"]/div/table/tr[2]/td[3]/a/@href').get()

    def parse(self, response):
        if response.status == 404:  # 判断返回状态码如果是404
            self.fail_urls.append(response.url)  # 将URL追加到列表
            self.crawler.stats.inc_value('failed_url')  # 设置一个数据收集，值为自增，每执行一次自增1
            print('-------------404----------')  # 打印404URL列表
            print(self.fail_urls)  # 打印404URL列表
            print(self.crawler.stats.get_value('failed_url'))  # 打印数据收集值
        elif response.status == 429:  # 判断返回状态码如果是404
            pass
        else:
            item = ZrScrapy1Item()
            self.do_parse(response, item)
            self.crawler.stats.inc_value('url_crawled')
            msg = 'total:{},crawled: {}'.format(self.total, self.crawler.stats.get_value('url_crawled'))
            print(msg)

            yield item

# {'accepted': '2014-02-04 15:16:34',
#  'accnum': ['\n         ', ' 0001193125-14-034732\n      '],
#  'bazip': '\nCLEARWATER FL 33759      ',
#  'cik': '0001000045 (see all company filings)',
#  'fd': '2014-02-04',
#  'film': '14571853',
#  'fye': '0331',
#  'irs': '593019317',
#  'item8k': '<div class="info">Item 2.02: Results of Operations and Financial '
#            'Condition<br>Item 9.01: Financial Statements and '
#            'Exhibits<br></div>',
#  'name': 'NICHOLAS FINANCIAL INC (Filer)\n ',
#  'pdc': '3',
#  'rp': '2014-02-04',
#  'sic': '6153',
#  'state': 'FL',
#  'web_url': '/Archives/edgar/data/1000045/000119312514034732/d669901d8k.htm'}
