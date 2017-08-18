# -*- coding: utf-8 -*-
import scrapy
from ..items import HourlyWeatherscrapyItem

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
    # start_urlsを読み込むファイルパス
    urls_file_path = './data/urls/{}.csv'.format(name)
    # 取得した天気予報の出力先ファイル名
    output_file_name = name
    channel = 0
    now = datetime.now()

    def __init__(self, channel_id, file_name_suffix, *args, **kwargs):
        super(YahooDailyWeatherSpider, self).__init__(*args, **kwargs)
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
            today_date_text: {
                # 時間
                'times': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[1]/td'),
                # 天気
                'weatheres': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[2]/td'),
                # 気温
                'temperatures': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[3]/td'),
                # 湿度
                'humidities': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[4]/td'),
                # 降水量
                'precipitations': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[5]/td'),
                # chance_of_rains 降水確率 => Yahoo!天気はなし
                # 風向
                'wind_directions': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[6]/td'),
                # 風速
                'wind_speeds': response.xpath('//div[@id="yjw_pinpoint_today"]/table[1]/tr[6]/td'),
            },
            # 明日の天気 #######
            tomorrow_date_text: {
                # 時間
                'times': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[1]/td'),
                # 天気
                'weatheres': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[2]/td'),
                # 気温
                'temperatures': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[3]/td'),
                # 湿度
                'humidities': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[4]/td'),
                # 降水量
                'precipitations': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[5]/td'),
                # chance_of_rains 降水確率 => Yahoo!天気はなし
                # 風向
                'wind_directions': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[6]/td'),
                # 風速
                'wind_speeds': response.xpath('//div[@id="yjw_pinpoint_tomorrow"]/table[1]/tr[6]/td'),
            }
        }

        for date_text, daily_weather in daily_weathers.items():

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
                    # もう過ぎた時間帯はfontスタイルが適用されているため
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
                item['time'] = time(int(time_text_list[0]), 0, 0, 0)
                item['weather'] = weather_text
                item['temperatures'] = temperatures_text
                item['humidity'] = humidity_text
                item['precipitation'] = precipitation_text
                item['wind_direction'] = wind_direction_text
                item['wind_speed'] = wind_speed_text.strip('\n')

                item['acquisition_date'] = self.now

                item['channel'] = self.channel

                yield item
