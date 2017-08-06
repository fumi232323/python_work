# -*- coding: utf-8 -*-
import scrapy
from ..items import WeatherscrapyItem

from datetime import datetime, date
import csv

class YahooWeeklyWeatherSpider(scrapy.Spider):
    """
    Yahoo!天気の週間天気予報を取得するスパイダー。
    """
    name = 'yahoo_weekly_weather'
    allowed_domains = ['weather.yahoo.co.jp']
    start_urls = []

    # --- 自分で追加した属性 ---
    urls_file_path = './data/urls/{}.csv'.format(name) # start_urlsを読み込むファイルパス
    output_file_name = name # 取得した天気予報の出力先ファイル名
    area = 0
    channel = 0
    now = datetime.now()
    
    def __init__(self, area_id, channel_id, suffix, *args, **kwargs):
        super(YahooWeeklyWeatherSpider, self).__init__(*args, **kwargs)
        self.area = area_id
        self.channel = channel_id
        self.output_file_name += suffix
        
        with open(self.urls_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.start_urls.append(row[0])
                
    def parse(self, response):
        # --- 参考 ---
        # http://scrapy-ja.readthedocs.io/ja/latest/topics/spiders.html
        # xpathはこれがわかりやすい
        #   => http://yakinikunotare.boo.jp/orebase/index.php?XML%2FXPath%2FXPath%A4%CE%BD%F1%A4%AD%CA%FD
        # 注意 : tbodyは要らない模様。

        dates = response.xpath('//div[@id="yjw_week"]/table[1]/tr[1]/td')
        weatheres = response.xpath('//div[@id="yjw_week"]/table[1]/tr[2]/td')
        temperatures = response.xpath('//div[@id="yjw_week"]/table[1]/tr[3]/td')
        chance_of_rains = response.xpath('//div[@id="yjw_week"]/table[1]/tr[4]/td')
        
        for d, w, t, c in zip(dates[1:], weatheres[1:], temperatures[1:], chance_of_rains[1:]):
            item = WeatherscrapyItem()

            date_text = d.xpath('small/text()').extract_first()
            date_text_list = date_text.replace('月', ' ').replace('日', ' ').split()
            
            item['date'] = date(self.now.year, int(date_text_list[0]), int(date_text_list[1]))
            item['weather'] = w.xpath('small/text()').extract_first()
            item['highest_temperatures'] = t.xpath('small/font[1]/text()').extract_first()
            item['lowest_temperatures'] = t.xpath('small/font[2]/text()').extract_first()
            item['chance_of_rain'] = c.xpath('small/text()').extract_first()
            item['acquisition_date'] = self.now
            
            item['area'] = self.area
            item['channel'] = self.channel
            yield item
