import sys
import os
from scrapy.cmdline import execute

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))  # 当前文件的绝对路径，然后再找他的父级目录
sys.path.append(current_dir)  # 将当前路径加入到path中
execute(['scrapy', 'crawl', 'test3'])
