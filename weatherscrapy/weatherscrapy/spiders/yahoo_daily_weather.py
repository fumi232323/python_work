# -*- coding: utf-8 -*-
import scrapy
from ..items import WeatherscrapyItem

from datetime import datetime
from pytz import timezone

class YahooDailyWeatherSpider(scrapy.Spider):
    """
    YAHOO!天気の今日の天気予報を取得するスパイダー。
    TODO: 中身は書きかけ
    """
    name = 'yahoo_daily_weather'
    allowed_domains = ['weather.yahoo.co.jp']
    start_urls = ['https://weather.yahoo.co.jp/weather/jp/11/4310/11222.html']
    
    # 自分で追加した属性
    area = 0
    channel = 0
    now = datetime.now(timezone('Asia/Tokyo'))
    
    # date属性は上書き
    date = now.strftime('%Y-%m-%d')
    
    #$ scrapy crawl yahoo_weather -a area_id=1 -a channel_id=1
    def __init__(self, area_id, channel_id, *args, **kwargs):
        super(YahooDailyWeatherSpider, self).__init__(*args, **kwargs)
        self.area = area_id
        self.channel = channel_id

    def parse(self, response):
        """
        YAHOO!天気の今日の天気予報を取得する。
        """
        dates = response.xpath('//div[@id="yjw_week"]/table[1]/tr[1]/td')
        weatheres = response.xpath('//div[@id="yjw_week"]/table[1]/tr[2]/td')
        temperatures = response.xpath('//div[@id="yjw_week"]/table[1]/tr[3]/td')
        chance_of_rains = response.xpath('//div[@id="yjw_week"]/table[1]/tr[4]/td')
        
        for d, w, t, c in zip(dates[1:], weatheres[1:], temperatures[1:], chance_of_rains[1:]):
            item = WeatherscrapyItem()

            date = datetime.strptime(d.xpath('small/text()').extract_first(), '%m月%d日')
            item['date'] = datetime(self.now.year, date.month, date.day)
            item['weather'] = w.xpath('small/text()').extract_first()
            item['highest_temperatures'] = t.xpath('small/font[1]/text()').extract_first()
            item['lowest_temperatures'] = t.xpath('small/font[2]/text()').extract_first()
            item['chance_of_rain'] = c.xpath('small/text()').extract_first()
            item['acquisition_date'] = self.now
            
            item['area'] = self.area
            item['channel'] = self.channel
            yield item
