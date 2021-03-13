# get data and print
# scrapy crawl test2
# scrapy crawl test2 --loglevel=INFO
# scrapy crawl test3 -o zrdata.csv
# scrapy crawl test2 -s LOG_FILE=spider.log

import scrapy
import pickle
import os
import pandas as pd
import re
from zr_scrapy1.items import ZrScrapy1Item
from zr_scrapy1.items import ZrScrapy1page2
from scrapy.exceptions import CloseSpider

class ExampleSpider(scrapy.Spider):
    name = 'test3'
    print('main 333333')

    # allowed_domains = ['https://www.163.com']

    def get_master_index(self):
        doc_url = list()

        with open(self.dir_master_index + "master_index.txt", "r")as f:
            for line in f.readlines():
                line = line.strip()
                if not line.startswith(r"#"):
                    print(self.dir_master_index + line)
                    self.index_edgar.append(self.dir_master_index + line)
        print('file to handle: %s' % len(self.index_edgar))

        # read each index file, select rows with matched file type, and store matched doc_links
        for filenameTSV in self.index_edgar:
            tsv_read = pd.read_csv(filenameTSV, sep='|', header=None, encoding="utf-8")
            tsv_read.columns = ['1', '2', '3', '4', '5', '6']

            # select the rows with filetype equal to predefined type
            tsv_type = tsv_read.loc[tsv_read['3'] == self.obj_type]
            doc_link = tsv_type['6'].values.tolist()
            doc_link = ['https://www.sec.gov/Archives/' + w for w in doc_link]
            for doc in doc_link:
                doc_url.append(doc)
        self.total = len(doc_url)
        return doc_url

    def __init__(self):
        print('init 333333333')
        self.fail_urls = []  # 创建一个变量来储存404URL
        self.period_start = 2014  # included
        self.period_end = 2020  # included
        self.obj_type = '8-K'
        self.index_edgar = list()
        self.dir_master_index = ""  # pls run test at root ( dir contain scrapy.cfg)

        self.total = 0
        self.dir_master_index = os.path.abspath('.') + "\\zr_scrapy1\\master_index\\"
        self.start_urls = self.get_master_index()
        print(len(self.start_urls))
        # os.exit()

    def first(self, the_iterable, condition=lambda x: True):
        for i in the_iterable:
            if condition(i):
                return i

    def do_parse(self, response, item):
        # scrapy实战，使用内置的xpath，re和css提取值 https://www.cnblogs.com/yunlongaimeng/p/11526418.html
        accnum= response.xpath('//*[@id="secNum"]/text()').getall()
        item['accnum'] = next((x.strip() for x in accnum if x.strip()))
        item['fd'] = response.xpath('//*[@id="formDiv"]/div[2]/div[1]/div[2]/text()').get()
        item['accepted'] = response.xpath('//*[@id="formDiv"]/div[2]/div[1]/div[4]/text()').get()
        item['pdc'] = response.xpath('//*[@id="formDiv"]/div[2]/div[1]/div[6]/text()').get()
        item['rp'] = response.xpath('//*[@id="formDiv"]/div[2]/div[1]/div[2]/text()').get()
        item8k= response.xpath('//*[@id="formDiv"]/div[2]/div[3]/div[2]').get()
        item['item8k'] = re.findall(r'\d.\d\d',item8k)
        item['name'] = response.xpath('//*[@id="filerDiv"]/div[3]/span/text()[1]').get().replace(' (Filer)', '').strip()
        cik = response.xpath('//*[@id="filerDiv"]/div[3]/span/a/text()').get()
        item['cik'] = re.findall(r'\d+',cik)
        bazip = response.xpath('//*[@id="filerDiv"]/div/span/text()').getall()
        # item['bazip'] = re.findall(r'\b\d\d\d\d\d\b',self.first(bazip, lambda x: re.findall(r'\b\d\d\d\d\d\b', x)))

        item['bazip'] = re.findall(r'\b\d\d\d\d\d\b', next((x for x in bazip if re.findall(r'\b\d\d\d\d\d\b', x))))
        # item['bazip'] = next((x for x in bazip if re.findall(r'\b\d\d\d\d\d\b', x)))
        item['sic'] = response.xpath('//*[@id="filerDiv"]/div[3]/p/b/a/text()').get()
        item['fye'] = response.xpath('//*[@id="filerDiv"]/div[3]/p/strong[3]/text()').get()
        item['state'] = response.xpath('//*[@id="filerDiv"]/div[3]/p/strong[2]/text()').get()
        item['irs'] = response.xpath('//*[@id="filerDiv"]/div[3]/p/strong[1]/text()').get()
        item['film'] = response.xpath('//*[@id="filerDiv"]/div[3]/p/strong[6]/text()').get()

        tabledata = response.xpath('//*[@id="formDiv"]/div/table').get()


        item['web_url'] = r'https://www.sec.gov/'+response.xpath('//*[@id="formDiv"]/div/table/tr[2]/td[3]/a/@href').get()
        item['zr_from_url'] = response.url

    def parse2(self, response):
        item = ZrScrapy1page2()
        item['a'] = '1'
        item['b'] = '2'
        item['c'] = '3'
        item['d'] = '4'
        item['e'] = '5'
        yield item

        msg = '-----------,parse2:{}:{}'.format(response.url,len(response.body))
        print(msg)
        raise CloseSpider('测试终止')

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
            # 如果你需要带一些当前方法的局部变量到这个方法可以使用:
            # yield Request(next_page, meta={"para": "val"}, callback=self.next_parse)

            yield scrapy.Request(url=item['web_url'], callback=self.parse2)  # 爬取子页面
            self.crawler.stats.inc_value('url_crawled')
            msg = 'total:{},crawled: {}'.format(self.total, self.crawler.stats.get_value('url_crawled'))
            # print(msg)
            self.logger.warning(msg)

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
