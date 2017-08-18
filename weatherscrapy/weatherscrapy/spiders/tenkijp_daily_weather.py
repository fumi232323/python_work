# -*- coding: utf-8 -*-
import scrapy
from ..items import HourlyWeatherscrapyItem

from datetime import datetime, date, time
import csv


class TenkijpDailyWeatherSpider(scrapy.Spider):
    """
    日本気象協会 tenki.jpの週間天気予報を取得するスパイダー
    """
    name = 'tenkijp_daily_weather'
    allowed_domains = ['tenki.jp']
    start_urls = []

    # --- 自分で追加した属性 ---
    # start_urlsを読み込むファイルのパス
    urls_file_path = './data/urls/{}.csv'.format(name)
    # 取得した天気予報の出力先ファイル名
    output_file_name = name
    channel = 0
    now = datetime.now()

    def __init__(self, channel_id, file_name_suffix, *args, **kwargs):
        super(TenkijpDailyWeatherSpider, self).__init__(*args, **kwargs)

        self.channel = channel_id
        self.output_file_name += file_name_suffix

        with open(self.urls_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.start_urls.append(row[0])

    def parse(self, response):
        # 今日の日付
        today_date_text = response.xpath(
                '//table[@id="forecast-point-1h-today"]/tr[1]/td/div/p/text()'
            ).extract_first()  # 今日 2017年08月16日

        # 明日の日付
        tomorrow_date_text = response.xpath(
                '//table[@id="forecast-point-1h-tomorrow"]/tr[1]/td/div/p/text()'
            ).extract_first()

        # 明後日の日付
        dayaftertomorrow_date_text = response.xpath(
                '//table[@id="forecast-point-1h-dayaftertomorrow"]/tr[1]/td/div/p/text()'
            ).extract_first()

        daily_weathers = {
            # 今日の天気 #######
            today_date_text: {
                # 時間
                'times': response.xpath('//table[@id="forecast-point-1h-today"]/tr[@class="hour"]/td'),
                # 天気
                'weatheres': response.xpath('//table[@id="forecast-point-1h-today"]/tr[@class="weather"]/td'),
                # 気温
                'temperatures': response.xpath('//table[@id="forecast-point-1h-today"]/tr[@class="temperature"]/td'),
                # 湿度
                'humidities': response.xpath('//table[@id="forecast-point-1h-today"]/tr[@class="humidity"]/td'),
                # 降水量
                'precipitations': response.xpath('//table[@id="forecast-point-1h-today"]/tr[@class="precipitation"]/td'),
                # 降水確率
                'chance_of_rains': response.xpath('//table[@id="forecast-point-1h-today"]/tr[@class="prob-precip"]/td'),
                # 風向
                'wind_directions': response.xpath('//table[@id="forecast-point-1h-today"]/tr[@class="wind-blow"]/td'),
                # 風速
                'wind_speeds': response.xpath('//table[@id="forecast-point-1h-today"]/tr[@class="wind-speed"]/td'),
            },
            # 明日の天気 #######
            tomorrow_date_text: {
                # 時間
                'times': response.xpath('//table[@id="forecast-point-1h-tomorrow"]/tr[@class="hour"]/td'),
                # 天気
                'weatheres': response.xpath('//table[@id="forecast-point-1h-tomorrow"]/tr[@class="weather"]/td'),
                # 気温
                'temperatures': response.xpath('//table[@id="forecast-point-1h-tomorrow"]/tr[@class="temperature"]/td'),
                # 湿度
                'humidities': response.xpath('//table[@id="forecast-point-1h-tomorrow"]/tr[@class="humidity"]/td'),
                # 降水量
                'precipitations': response.xpath('//table[@id="forecast-point-1h-tomorrow"]/tr[@class="precipitation"]/td'),
                # 降水確率
                'chance_of_rains': response.xpath('//table[@id="forecast-point-1h-tomorrow"]/tr[@class="prob-precip"]/td'),
                # 風向
                'wind_directions': response.xpath('//table[@id="forecast-point-1h-tomorrow"]/tr[@class="wind-blow"]/td'),
                # 風速
                'wind_speeds': response.xpath('//table[@id="forecast-point-1h-tomorrow"]/tr[@class="wind-speed"]/td'),
            },
            # 明後日の天気 #######
            dayaftertomorrow_date_text: {
                # 時間
                'times': response.xpath('//table[@id="forecast-point-1h-dayaftertomorrow"]/tr[@class="hour"]/td'),
                # 天気
                'weatheres': response.xpath('//table[@id="forecast-point-1h-dayaftertomorrow"]/tr[@class="weather"]/td'),
                # 気温
                'temperatures': response.xpath('//table[@id="forecast-point-1h-dayaftertomorrow"]/tr[@class="temperature"]/td'),
                # 湿度
                'humidities': response.xpath('//table[@id="forecast-point-1h-dayaftertomorrow"]/tr[@class="humidity"]/td'),
                # 降水量
                'precipitations': response.xpath('//table[@id="forecast-point-1h-dayaftertomorrow"]/tr[@class="precipitation"]/td'),
                # 降水確率
                'chance_of_rains': response.xpath('//table[@id="forecast-point-1h-dayaftertomorrow"]/tr[@class="prob-precip"]/td'),
                # 風向
                'wind_directions': response.xpath('//table[@id="forecast-point-1h-dayaftertomorrow"]/tr[@class="wind-blow"]/td'),
                # 風速
                'wind_speeds': response.xpath('//table[@id="forecast-point-1h-dayaftertomorrow"]/tr[@class="wind-speed"]/td'),
            }
        }

        for date_text, daily_weather in daily_weathers.items():

            date_text_list = date_text.replace('年', ' ').replace('月', ' ').replace('日', ' ').split()
            for t, w, tp, h, p, c, wd, ws in zip(
                daily_weather['times'],
                daily_weather['weatheres'],
                daily_weather['temperatures'],
                daily_weather['humidities'],
                daily_weather['precipitations'],
                daily_weather['chance_of_rains'],
                daily_weather['wind_directions'],
                daily_weather['wind_speeds'],
            ):

                item = HourlyWeatherscrapyItem()

                time_text = t.xpath('span/text()').extract_first()
                weather_text = w.xpath('p/text()').extract_first()
                temperatures_text = tp.xpath('span/text()').extract_first()
                humidity_text = h.xpath('span/text()').extract_first()
                if not humidity_text:
                    humidity_text = h.xpath('text()').extract_first()
                precipitation_text = p.xpath('span/text()').extract_first()
                chance_of_rain_text = c.xpath('span/text()').extract_first()
                wind_direction_text = wd.xpath('p/text()').extract_first()
                if not wind_direction_text:
                    wind_direction_text = wd.xpath('p/span/text()').extract_first()
                wind_speed_text = ws.xpath('span/text()').extract_first()

                item['date'] = date(
                    int(date_text_list[1]),
                    int(date_text_list[2]),
                    int(date_text_list[3])
                )
                time_t = time(23, 59, 59)
                if int(time_text) < 24:
                    time_t = time(int(time_text), 0, 0, 0)
                item['time'] = time_t
                item['weather'] = weather_text
                item['temperatures'] = temperatures_text
                item['humidity'] = humidity_text
                item['precipitation'] = precipitation_text
                item['chance_of_rain'] = chance_of_rain_text
                item['wind_direction'] = wind_direction_text
                item['wind_speed'] = wind_speed_text

                item['acquisition_date'] = self.now

                item['channel'] = self.channel

                yield item
