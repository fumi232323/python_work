# -*- coding: utf-8 -*-
import scrapy
from ..items import WeatherscrapyItem

from datetime import datetime, date
import csv

class TenkijpWeeklyWeatherSpider(scrapy.Spider):
    """
    日本気象協会 tenki.jpの週間天気予報を取得するスパイダー
    """
    name = 'tenkijp_weekly_weather'
    allowed_domains = ['tenki.jp']
    start_urls = []

    # --- 自分で追加した属性 ---
    urls_file_path = './data/urls/{}.csv'.format(name) # start_urlsを読み込むファイルのパス
    output_file_name = name # 取得した天気予報の出力先ファイル名
    area = 0
    channel = 0
    now = datetime.now()
    
    def __init__(self, area_id, channel_id, file_name_suffix, *args, **kwargs):
        super(TenkijpWeeklyWeatherSpider, self).__init__(*args, **kwargs)
        self.area = area_id
        self.channel = channel_id
        self.output_file_name += file_name_suffix
        
        with open(self.urls_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.start_urls.append(row[0])
                
    def parse(self, response):
        
        dates = response.xpath('//table[@class="forecast-point-week"]/tr[1]/td')
        weatheres = response.xpath('//table[@class="forecast-point-week"]/tr[2]/td')
        temperatures = response.xpath('//table[@class="forecast-point-week"]/tr[3]/td')
        chance_of_rains = response.xpath('//table[@class="forecast-point-week"]/tr[4]/td')

        for d, w, t, c in zip(dates[1:], weatheres[1:], temperatures[1:], chance_of_rains[1:]):
            item = WeatherscrapyItem()

            date_text = d.xpath('text()').extract_first()
            date_text_list = date_text.replace('月', ' ').replace('日', ' ').split()
            
            item['date'] = date(self.now.year, int(date_text_list[0]), int(date_text_list[1]))
            item['weather'] = w.xpath('p/text()').extract_first()
            item['highest_temperatures'] = t.xpath('p[@class="high-temp"]/text()').extract_first()
            item['lowest_temperatures'] = t.xpath('p[@class="low-temp"]/text()').extract_first()
            item['chance_of_rain'] = c.xpath('p/text()').extract_first()
            item['acquisition_date'] = self.now
            
            item['area'] = self.area
            item['channel'] = self.channel
            yield item
