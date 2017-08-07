# -*- coding: utf-8 -*-
import scrapy
from ..items import WeatherscrapyItem, HourlyWeatherscrapyItem

from datetime import datetime, date, time
import csv

class YahooDailyWeatherSpider(scrapy.Spider):
    """
    Yahoo!天気の今日の天気予報を取得するスパイダー。
    """
    name = 'yahoo_daily_weather'
    allowed_domains = ['weather.yahoo.co.jp']
    start_urls = []

    # --- 自分で追加した属性 ---
    urls_file_path = './data/urls/{}.csv'.format(name) # start_urlsを読み込むファイルパス
    output_file_name = name # 取得した天気予報の出力先ファイル名
    area = 0
    channel = 0
    now = datetime.now()
    
    def __init__(self, area_id, channel_id, file_name_suffix, *args, **kwargs):
        super(YahooDailyWeatherSpider, self).__init__(*args, **kwargs)
        self.area = area_id
        self.channel = channel_id
        self.output_file_name += file_name_suffix
        
        with open(self.urls_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.start_urls.append(row[0])
                
    def parse(self, response):
                
        # 今日の日付
        today_date_text = response.xpath(
                '//div[@id="yjw_pinpoint_today"]/h3[1]/span/text()'
            ).extract_first() 
        
        # 明日の日付
        tomorrow_date_text = response.xpath(
                '//div[@id="yjw_pinpoint_tomorrow"]/h3[1]/span/text()'
            ).extract_first()
        
        daily_weathers = {
            # 今日の天気 #######
            today_date_text:{
                'times': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[1]/td'),# 時間
                'weatheres': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[2]/td'),# 天気
                'temperatures': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[3]/td'), # 気温
                'humidities': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[4]/td'), # 湿度
                'precipitations': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[5]/td'), # 降水量
                # chance_of_rains 降水確率 => Yahoo!天気はなし
                'wind_directions': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[6]/td'), # 風向
                'wind_speeds': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[6]/td'),  # 風速
            },
            # 明日の天気 #######
            tomorrow_date_text:{
                'times': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[1]/td'),# 時間
                'weatheres': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[2]/td'),# 天気
                'temperatures': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[3]/td'), # 気温
                'humidities': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[4]/td'), # 湿度
                'precipitations': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[5]/td'), # 降水量
                # chance_of_rains 降水確率 => Yahoo!天気はなし
                'wind_directions': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[6]/td'), # 風向
                'wind_speeds': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[6]/td'),  # 風速
            }
        }
                
        for date_text, daily_weather in daily_weathers.items():
            print('★')
            print(date_text)
            date_text_list = date_text.replace('月', ' ').replace('日', ' ').replace('-', ' ').split()
            for t, w, tp, h, p, wd, ws in zip(
                daily_weather['times'][1:],
                daily_weather['weatheres'][1:],
                daily_weather['temperatures'][1:],
                daily_weather['humidities'][1:],
                daily_weather['precipitations'][1:],
                daily_weather['wind_directions'][1:],
                daily_weather['wind_speeds'][1:],
            ):

                item = HourlyWeatherscrapyItem()

                time_text = t.xpath('small/text()').extract_first()
                if not time_text:
                    time_text = t.xpath('small/font/text()').extract_first()
                    weather_text = w.xpath('small/font/text()').extract_first()
                    temperatures_text = tp.xpath('small/font/text()').extract_first()
                    humidity_text = h.xpath('small/font/text()').extract_first()
                    precipitation_text = p.xpath('small/font/text()').extract_first()
                    wind_direction_text = wd.xpath('small/font[1]/text()').extract_first()
                    wind_speed_text = ws.xpath('small/font[2]/text()').extract_first()
                else:
                    weather_text = w.xpath('small/text()').extract_first()
                    temperatures_text = tp.xpath('small/text()').extract_first()
                    humidity_text = h.xpath('small/text()').extract_first()
                    precipitation_text = p.xpath('small/text()').extract_first()
                    wind_direction_text = wd.xpath('small/text()[1]').extract_first()
                    wind_speed_text = ws.xpath('small/text()[2]').extract_first()

                item['date'] = date(self.now.year, int(date_text_list[0]), int(date_text_list[1]))
                time_text_list = time_text.replace('時', ' ').split()
                item['time'] = time(int(time_text_list[0]), 0)
                item['weather'] = weather_text
                item['temperatures'] = temperatures_text
                item['humidity'] = humidity_text
                item['precipitation'] = precipitation_text
                item['wind_direction'] = wind_direction_text
                item['wind_speed'] = wind_speed_text.strip('\n')

                item['acquisition_date'] = self.now

                item['area'] = self.area
                item['channel'] = self.channel

                yield item