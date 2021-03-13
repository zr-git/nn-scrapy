import scrapy


class ExampleSpider(scrapy.Spider):
    name = 'example'
    start_urls = ['http://lab.scrapyd.cn/page/1/']*100
    start_urls = ['http://lab.scrapyd.cn']*100
    start_urls = ['https://www.163.com']*1000
    start_urls = ['https://www.sec.gov/Archives/edgar/data/1000045/0001193125-14-034732-index.html'] *100

    start_urls = ['https://sports.163.com/china/']*1000

    # allowed_domains = ['https://www.163.com']
    # start_urls = ['https://www.163.com/']*100


    def parse(self, response):
        self.log(len(response.body))
        # filename = response.url.split("/")[-2]
        # with open(filename, 'wb') as f:
        #     f.write(response.body)
        # pass
