from goose3 import Goose
from scrapy.http import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

import re, os, json


class MySpider(CrawlSpider):
    max_count = 3
    count = 0
    name = 'simple-spider'
    allowed_domains = ['tvtropes.org']
    start_urls = ['https://tvtropes.org/pmwiki/pmwiki.php/Main/SayMyName']

    rules = (
        # Extract links matching 'category.php' (but not matching 'subsection.php')
        # and follow links from them (since no callback means follow=True by default).
        Rule(LinkExtractor(allow=()), callback='parse_item'),
    )

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        kwargs["crawler_settings"] = crawler.settings
        return super().from_crawler(crawler, *args, **kwargs)

    def parse_item(self, response):
        print('Page ' + str(self.count) + ' crawled')
        html = response.body
        g = Goose()
        article = g.extract(raw_html=html)
        title = article.title
        content = article.cleaned_text
        links = article.links
        current_url = article.canonical_link
        if 'Main' in current_url:
            dir_name = 'tropo'
        else:
            dir_name = 'laconic'
        tropo_dir = '{}-{}'.format(title,dir_name)
        tropo_dir = tropo_dir.replace("","-")
        json_file = {
            "title": title,
            "content": content,
            "url": article.canonical_link,
            "links": links
        }

        g.close()
        # The folder is created only in its first appearance
        if not os.path.exists('/home/jmanu/' + tropo_dir):
            os.system('mkdir -p ' + '/home/jmanu/tropos/' + tropo_dir)

        with open('/home/jmanu/tropos/' + tropo_dir + '/' + title + '.json', 'w+', encoding='utf-8') as fp:
            json.dump(json_file, fp)



