from django.test import TestCase
import tempfile
import os
from unittest import mock
from datetime import datetime
from decimal import Decimal

from weather import testing
from weather.models import Channel, Weather, HourlyWeather

from weather import scrapyutils


class TestRegisterScrappedWeather(TestCase):
    def test_register_weekly_weather(self):
        """
        【正常系】
        週間天気予報の登録テスト
        今日明日の天気はscrapyしなかった場合。
          * Channelに対象エリアのTYPE_DAILYレコードがなかった場合
          * 今日明日の天気のscrapyに失敗し、お天気情報CSVが出力されなかった場合
          など。
        """
        # --- 準備
        # 各テーブルの既存データ作成
        area = testing.factory_area()
        channel = testing.factory_channel(area=area, id=10)
        weather = testing.factory_weather(channel=channel)
        hourlyweather = testing.factory_hourlyweather(date=weather)

        # 一時ファイルの作成
        with tempfile.NamedTemporaryFile(
                                            mode='w',
                                            encoding='utf-8',
                                            dir='../weatherscrapy/data/weather/',
                                            suffix='.csv'
                                        ) as tfile:

            tfile.write(
"""acquisition_date,chance_of_rain,channel,date,highest_temperatures,lowest_temperatures,weather,wind_speed
2017-08-09 21:16:35.245048,50,10,2017-08-11,29,23,曇時々雨,
2017-08-09 21:16:35.245048,40,10,2017-08-12,30,24,曇り,
2017-08-09 21:16:35.245048,30,10,2017-08-13,30,24,曇時々晴,
"""
            )
            tfile.flush()

            # 引数のファイル名辞書
            test_weather_file_name = os.path.basename(tfile.name).split('.')[0]
            weather_file_names = {Channel.TYPE_WEEKLY: [test_weather_file_name]}

            # テスト対象の実行
            scrapyutils.register_scrapped_weather(area.id, weather_file_names)

            # --- DBの確認
            # 既存データがdeleteされているか
            self.assertEqual(Weather.objects.filter(id=weather.id).count(), 0)
            self.assertEqual(HourlyWeather.objects.filter(id=hourlyweather.id).count(), 0)

            # scrapyで取得したお天気は登録されているか
            self.assertEqual(Weather.objects.count(), 3)
            registered_weathers = Weather.objects.filter().order_by('id')

            self.assertEqual(registered_weathers[0].channel, channel)
            self.assertEqual(registered_weathers[0].date.isoformat(), '2017-08-11')
            self.assertEqual(registered_weathers[0].weather, '曇時々雨')
            self.assertEqual(registered_weathers[0].highest_temperatures, 29)
            self.assertEqual(registered_weathers[0].lowest_temperatures, 23)
            self.assertEqual(registered_weathers[0].chance_of_rain, 50)
            self.assertEqual(registered_weathers[0].wind_speed, None)

            self.assertEqual(registered_weathers[1].channel, channel)
            self.assertEqual(registered_weathers[1].date.isoformat(), '2017-08-12')
            self.assertEqual(registered_weathers[1].weather, '曇り')
            self.assertEqual(registered_weathers[1].highest_temperatures, 30)
            self.assertEqual(registered_weathers[1].lowest_temperatures, 24)
            self.assertEqual(registered_weathers[1].chance_of_rain, 40)
            self.assertEqual(registered_weathers[1].wind_speed, None)

            self.assertEqual(registered_weathers[2].channel, channel)
            self.assertEqual(registered_weathers[2].date.isoformat(), '2017-08-13')
            self.assertEqual(registered_weathers[2].weather, '曇時々晴')
            self.assertEqual(registered_weathers[2].highest_temperatures, 30)
            self.assertEqual(registered_weathers[2].lowest_temperatures, 24)
            self.assertEqual(registered_weathers[2].chance_of_rain, 30)
            self.assertEqual(registered_weathers[2].wind_speed, None)

    @mock.patch('weather.scrapyutils.get_now')
    def test_register_weekly_and_daily_weather(self, m):
        """
        【正常系】
        週間天気予報、今日明日の天気の登録テスト
        weeklyファイルとdailyファイルがそれぞれひとつずつの場合。
        """
        # --- 準備
        # 現在日時をモックに置き換え
        m.return_value = datetime(2017, 8, 7, 11, 00, 00, 000000)

        # 各テーブルの既存データ作成
        area = testing.factory_area()
        channel_weekly = testing.factory_channel(area=area, id=1, weather_type=Channel.TYPE_WEEKLY)
        channel_daily = testing.factory_channel(area=area, id=2, weather_type=Channel.TYPE_DAILY)
        weather = testing.factory_weather(channel=channel_weekly)
        hourlyweather = testing.factory_hourlyweather(channel=channel_daily, date=weather)

        # 一時ファイルの作成
        with tempfile.NamedTemporaryFile(
                                            mode='w',
                                            encoding='utf-8',
                                            dir='../weatherscrapy/data/weather/',
                                            suffix='.csv'
                                        ) as wfile, \
            tempfile.NamedTemporaryFile(
                                            mode='w',
                                            encoding='utf-8',
                                            dir='../weatherscrapy/data/weather/',
                                            suffix='.csv'
                                        ) as dfile:

            wfile.write(
"""acquisition_date,chance_of_rain,channel,date,highest_temperatures,lowest_temperatures,weather,wind_speed
2017-08-09 21:16:35.245048,40,1,2017-08-09,30,24,曇り,
2017-08-09 21:16:35.245048,30,1,2017-08-10,29,23,曇時々晴,
2017-08-09 21:16:35.245048,50,1,2017-08-11,30,23,曇時々雨,
"""
            )
            dfile.write(
"""acquisition_date,chance_of_rains,channel,date,humidity,precipitation,temperatures,time,weather,wind_direction,wind_speed
2017-08-09 21:16:42.516178,30,2,2017-08-07,50,0,36,00:00:00,晴れ,北西,1
2017-08-09 21:16:42.516178,40,2,2017-08-07,60,1,32,12:00:00,弱雨,西北西,2
2017-08-09 21:16:42.516178,50,2,2017-08-07,82,0,27,21:00:00,曇り,東北東,3
2017-08-09 21:16:42.516178,,2,2017-08-08,11,1,32,00:00:00,大雨,北西,1
2017-08-09 21:16:42.516178,,2,2017-08-08,22,0,24,12:00:00,晴れ,西北西,2
2017-08-09 21:16:42.516178,,2,2017-08-08,33,0,37,21:00:00,曇り,東北東,3
"""
            )

            wfile.flush()
            dfile.flush()

            # 引数のファイル名辞書
            test_weekly_file_name = os.path.basename(wfile.name).split('.')[0]
            test_daily_file_name = os.path.basename(dfile.name).split('.')[0]
            weather_file_names = {
                                    Channel.TYPE_WEEKLY: [test_weekly_file_name],
                                    Channel.TYPE_DAILY: [test_daily_file_name],
                                 }

            # テスト対象の実行
            scrapyutils.register_scrapped_weather(area.id, weather_file_names)

            # --- DBの確認
            # 既存データがdeleteされているか
            self.assertEqual(Weather.objects.filter(id=weather.id).count(), 0)
            self.assertEqual(HourlyWeather.objects.filter(id=hourlyweather.id).count(), 0)

            # scrapyで取得した週間天気は登録されているか
            self.assertEqual(Weather.objects.count(), 5)
            reg_weathers = Weather.objects.filter().order_by('id')

            self.assertEqual(reg_weathers[0].channel, channel_weekly)
            self.assertEqual(reg_weathers[0].date.isoformat(), '2017-08-09')
            self.assertEqual(reg_weathers[0].weather, '曇り')
            self.assertEqual(reg_weathers[0].highest_temperatures, 30)
            self.assertEqual(reg_weathers[0].lowest_temperatures, 24)
            self.assertEqual(reg_weathers[0].chance_of_rain, 40)
            self.assertEqual(reg_weathers[0].wind_speed, None)

            self.assertEqual(reg_weathers[1].date.isoformat(), '2017-08-10')
            self.assertEqual(reg_weathers[1].weather, '曇時々晴')

            self.assertEqual(reg_weathers[2].date.isoformat(), '2017-08-11')
            self.assertEqual(reg_weathers[2].weather, '曇時々雨')

            self.assertEqual(reg_weathers[3].channel, channel_weekly)
            self.assertEqual(reg_weathers[3].date.isoformat(), '2017-08-07')
            self.assertEqual(reg_weathers[3].weather, '弱雨')
            self.assertEqual(reg_weathers[3].highest_temperatures, 36)
            self.assertEqual(reg_weathers[3].lowest_temperatures, 27)
            self.assertEqual(reg_weathers[3].chance_of_rain, 40)
            self.assertEqual(reg_weathers[3].wind_speed, 2)

            self.assertEqual(reg_weathers[4].channel, channel_weekly)
            self.assertEqual(reg_weathers[4].date.isoformat(), '2017-08-08')
            self.assertEqual(reg_weathers[4].weather, '大雨')
            self.assertEqual(reg_weathers[4].highest_temperatures, 37)
            self.assertEqual(reg_weathers[4].lowest_temperatures, 24)
            self.assertEqual(reg_weathers[4].chance_of_rain, 999)
            self.assertEqual(reg_weathers[4].wind_speed, 1)

            # scrapyで取得した今日明日天気は登録されているか
            self.assertEqual(HourlyWeather.objects.count(), 6)
            reg_hourlyweathers = HourlyWeather.objects.filter().order_by('id')

            self.assertEqual(reg_hourlyweathers[0].channel, channel_daily)
            self.assertEqual(reg_hourlyweathers[0].date, reg_weathers[3])
            self.assertEqual(reg_hourlyweathers[0].date.date.isoformat(), '2017-08-07')
            self.assertEqual(reg_hourlyweathers[0].time.isoformat(), '00:00:00')
            self.assertEqual(reg_hourlyweathers[0].weather, '晴れ')
            self.assertEqual(reg_hourlyweathers[0].temperatures, 36)
            self.assertEqual(reg_hourlyweathers[0].humidity, 50)
            self.assertEqual(reg_hourlyweathers[0].precipitation, 0)
            self.assertEqual(reg_hourlyweathers[0].chance_of_rain, 30)
            self.assertEqual(reg_hourlyweathers[0].wind_direction, '北西')
            self.assertEqual(reg_hourlyweathers[0].wind_speed, 1)

            self.assertEqual(reg_hourlyweathers[1].date.date.isoformat(), '2017-08-07')
            self.assertEqual(reg_hourlyweathers[1].time.isoformat(), '12:00:00')
            self.assertEqual(reg_hourlyweathers[1].weather, '弱雨')

            self.assertEqual(reg_hourlyweathers[2].date.date.isoformat(), '2017-08-07')
            self.assertEqual(reg_hourlyweathers[2].time.isoformat(), '21:00:00')
            self.assertEqual(reg_hourlyweathers[2].weather, '曇り')

            self.assertEqual(reg_hourlyweathers[3].channel, channel_daily)
            self.assertEqual(reg_hourlyweathers[3].date, reg_weathers[4])
            self.assertEqual(reg_hourlyweathers[3].date.date.isoformat(), '2017-08-08')
            self.assertEqual(reg_hourlyweathers[3].time.isoformat(), '00:00:00')
            self.assertEqual(reg_hourlyweathers[3].weather, '大雨')
            self.assertEqual(reg_hourlyweathers[3].temperatures, 32)
            self.assertEqual(reg_hourlyweathers[3].humidity, 11)
            self.assertEqual(reg_hourlyweathers[3].precipitation, 1)
            self.assertEqual(reg_hourlyweathers[3].chance_of_rain, 999)
            self.assertEqual(reg_hourlyweathers[3].wind_direction, '北西')
            self.assertEqual(reg_hourlyweathers[3].wind_speed, 1)

            self.assertEqual(reg_hourlyweathers[4].date.date.isoformat(), '2017-08-08')
            self.assertEqual(reg_hourlyweathers[4].time.isoformat(), '12:00:00')
            self.assertEqual(reg_hourlyweathers[4].weather, '晴れ')

            self.assertEqual(reg_hourlyweathers[5].date.date.isoformat(), '2017-08-08')
            self.assertEqual(reg_hourlyweathers[5].time.isoformat(), '21:00:00')
            self.assertEqual(reg_hourlyweathers[5].weather, '曇り')

    @mock.patch('weather.scrapyutils.get_now')
    def test_register_multiple_weather_files(self, m):
        """
        【正常系】
        週間天気予報、今日明日の天気の登録テスト
        weeklyファイルとdailyファイルがそれぞれ複数の場合。
        """
        # --- 準備
        # 現在日時をモックに置き換え
        m.return_value = datetime(2017, 8, 7, 2, 30, 00, 000000)

        # 各テーブルの既存データ作成
        area = testing.factory_area()
        ch_weekly1 = testing.factory_channel(id=1, area=area, weather_type=Channel.TYPE_WEEKLY)
        ch_daily1 = testing.factory_channel(id=2, area=area, weather_type=Channel.TYPE_DAILY)

        ch_weekly2 = testing.factory_channel(
            id=3,
            area=area,
            name=Channel.CHANNEL_TENKIJP,
            weather_type=Channel.TYPE_WEEKLY
        )
        ch_daily2 = testing.factory_channel(
            id=4,
            area=area,
            name=Channel.CHANNEL_TENKIJP,
            weather_type=Channel.TYPE_DAILY
        )

        weather1 = testing.factory_weather(channel=ch_weekly1)
        weather2 = testing.factory_weather(channel=ch_weekly2)

        hourlyweather1 = testing.factory_hourlyweather(channel=ch_daily1, date=weather1)
        hourlyweather2 = testing.factory_hourlyweather(channel=ch_daily2, date=weather2)

        # 一時ファイルの作成
        with tempfile.NamedTemporaryFile(
                                            mode='w',
                                            encoding='utf-8',
                                            dir='../weatherscrapy/data/weather/',
                                            suffix='.csv'
                                        ) as weekly_file1, \
            tempfile.NamedTemporaryFile(
                                            mode='w',
                                            encoding='utf-8',
                                            dir='../weatherscrapy/data/weather/',
                                            suffix='.csv'
                                        ) as weekly_file2, \
            tempfile.NamedTemporaryFile(
                                            mode='w',
                                            encoding='utf-8',
                                            dir='../weatherscrapy/data/weather/',
                                            suffix='.csv'
                                        ) as daily_file1, \
            tempfile.NamedTemporaryFile(
                                            mode='w',
                                            encoding='utf-8',
                                            dir='../weatherscrapy/data/weather/',
                                            suffix='.csv'
                                        ) as daily_file2:

            weekly_file1.write(
"""acquisition_date,chance_of_rain,channel,date,highest_temperatures,lowest_temperatures,weather,wind_speed
2017-08-09 21:16:35.245048,40,1,2017-08-09,30,24,曇り,
2017-08-09 21:16:35.245048,30,1,2017-08-10,29,23,晴れ,
"""
            )
            weekly_file2.write(
"""acquisition_date,chance_of_rain,channel,date,highest_temperatures,lowest_temperatures,weather,wind_speed
2017-08-17 12:06:48.932529,60,3,2017-08-10,28,22,雨のち曇,
2017-08-17 12:06:48.932529,50,3,2017-08-11,31,22,曇,
"""
            )
            daily_file1.write(
"""acquisition_date,chance_of_rains,channel,date,humidity,precipitation,temperatures,time,weather,wind_direction,wind_speed
2017-08-09 21:16:42.516178,,2,2017-08-07,40,1,36,00:00:00,晴れ,北西,1
2017-08-09 21:16:42.516178,,2,2017-08-07,50,2,32,12:00:00,弱雨,西北西,2
2017-08-09 21:16:42.516178,,2,2017-08-07,60,3,27,21:00:00,曇り,東北東,3
2017-08-09 21:16:42.516178,,2,2017-08-08,11,4,32,00:00:00,大雨,北西,1
2017-08-09 21:16:42.516178,,2,2017-08-08,22,5,24,12:00:00,晴れ,西北西,2
2017-08-09 21:16:42.516178,,2,2017-08-08,33,6,37,21:00:00,曇り,東北東,3
"""
            )
            daily_file2.write(
"""acquisition_date,chance_of_rains,channel,date,humidity,precipitation,temperatures,time,weather,wind_direction,wind_speed
2017-08-17 12:07:11.380377,10,4,2017-08-07,96,0,20.4,01:00:00,曇り,北北西,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,96,1,20.3,02:00:00,曇り,北北西,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,96,0,20.7,03:00:00,台風,北北西,2
2017-08-17 12:07:11.380377,30,4,2017-08-07,96,0,20.3,04:00:00,小雨,北北西,1
2017-08-17 12:07:11.380377,10,4,2017-08-07,96,0,20.4,05:00:00,晴れ,北北西,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,94,0,20.7,06:00:00,曇り,北北西,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,94,0,21.7,07:00:00,曇り,北北西,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,90,0,22.7,08:00:00,曇り,北北西,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,87,0,23.8,09:00:00,曇り,北北西,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,83,0,24.0,10:00:00,曇り,北,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,82,0,24.7,11:00:00,曇り,北,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,78,0,25.4,12:00:00,曇り,北北東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,74,0,26.7,13:00:00,曇り,北東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,72,0,27.5,14:00:00,曇り,東北東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,72,0,27.3,15:00:00,曇り,東北東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,72,0,27.0,16:00:00,曇り,東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,74,0,26.1,17:00:00,曇り,東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,76,0,25.7,18:00:00,曇り,東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,78,0,25.1,19:00:00,曇り,東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,82,0,24.4,20:00:00,曇り,東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,84,0,23.5,21:00:00,曇り,東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,88,0,23.4,22:00:00,曇り,東,2
2017-08-17 12:07:11.380377,10,4,2017-08-07,90,0,23.0,23:00:00,曇り,東北東,1
2017-08-17 12:07:11.380377,10,4,2017-08-07,90,0,22.7,23:59:59,曇り,東北東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,92,0,22.7,01:00:00,曇り,東北東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,94,0,22.2,02:00:00,曇り,東北東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,94,0,21.8,03:00:00,曇り,東北東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,94,0,21.6,04:00:00,曇り,東北東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,94,0,21.8,05:00:00,曇り,東北東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,94,0,22.4,06:00:00,曇り,東北東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,92,0,23.2,07:00:00,曇り,東北東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,88,0,24.3,08:00:00,曇り,東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,84,0,25.5,09:00:00,曇り,東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,78,0,27.1,10:00:00,曇り,東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,76,0,28.2,11:00:00,曇り,東南東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,74,0,28.7,12:00:00,曇り,東南東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,74,0,29.1,13:00:00,小雨,南東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,78,0,28.1,14:00:00,小雨,南東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,82,1,27.1,15:00:00,弱雨,南東,2
2017-08-17 12:07:11.380377,20,4,2017-08-08,86,2,25.8,16:00:00,弱雨,南東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,90,3,25.2,17:00:00,弱雨,南東,2
2017-08-17 12:07:11.380377,20,4,2017-08-08,92,4,25.8,18:00:00,雨,東南東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,92,1,25.2,19:00:00,弱雨,東南東,2
2017-08-17 12:07:11.380377,20,4,2017-08-08,94,1,24.4,20:00:00,弱雨,東南東,2
2017-08-17 12:07:11.380377,20,4,2017-08-08,94,1,24.2,21:00:00,弱雨,南東,2
2017-08-17 12:07:11.380377,20,4,2017-08-08,94,1,24.3,22:00:00,弱雨,南東,2
2017-08-17 12:07:11.380377,20,4,2017-08-08,94,0,24.4,23:00:00,小雨,南東,1
2017-08-17 12:07:11.380377,20,4,2017-08-08,94,0,24.4,23:59:59,小雨,南南東,1
2017-08-17 12:07:11.380377,30,4,2017-08-09,94,0,24.4,01:00:00,曇り,南,1
2017-08-17 12:07:11.380377,30,4,2017-08-09,96,0,24.2,02:00:00,曇り,南西,1
2017-08-17 12:07:11.380377,30,4,2017-08-09,96,0,24.0,03:00:00,曇り,西南西,1
2017-08-17 12:07:11.380377,30,4,2017-08-09,96,0,23.5,04:00:00,曇り,西,1
2017-08-17 12:07:11.380377,30,4,2017-08-09,96,0,23.1,05:00:00,曇り,西,1
2017-08-17 12:07:11.380377,30,4,2017-08-09,96,0,23.1,06:00:00,曇り,北西,1
2017-08-17 12:07:11.380377,30,4,2017-08-09,92,0,23.7,07:00:00,曇り,北西,1
2017-08-17 12:07:11.380377,30,4,2017-08-09,88,0,24.5,08:00:00,曇り,北北西,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,82,0,25.3,09:00:00,曇り,北北西,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,78,0,27.0,10:00:00,曇り,北,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,74,0,27.9,11:00:00,曇り,北,3
2017-08-17 12:07:11.380377,30,4,2017-08-09,70,0,28.9,12:00:00,曇り,北北東,3
2017-08-17 12:07:11.380377,30,4,2017-08-09,66,0,30.0,13:00:00,曇り,北東,3
2017-08-17 12:07:11.380377,30,4,2017-08-09,66,0,29.3,14:00:00,曇り,北東,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,66,0,28.6,15:00:00,曇り,東北東,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,68,0,27.8,16:00:00,曇り,東北東,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,72,0,27.1,17:00:00,曇り,東北東,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,76,0,26.5,18:00:00,曇り,東北東,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,80,0,25.6,19:00:00,曇り,東北東,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,82,0,24.6,20:00:00,曇り,東北東,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,84,0,24.2,21:00:00,曇り,東北東,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,84,0,24.0,22:00:00,曇り,東北東,2
2017-08-17 12:07:11.380377,30,4,2017-08-09,86,0,23.9,23:00:00,曇り,北東,1
2017-08-17 12:07:11.380377,30,4,2017-08-09,88,0,23.5,23:59:59,曇り,北東,1
"""
            )

            weekly_file1.flush()
            weekly_file2.flush()
            daily_file1.flush()
            daily_file2.flush()

            # 引数のファイル名辞書
            test_weekly_file1_name = os.path.basename(weekly_file1.name).split('.')[0]
            test_daily_file1_name = os.path.basename(daily_file1.name).split('.')[0]
            test_weekly_file2_name = os.path.basename(weekly_file2.name).split('.')[0]
            test_daily_file2_name = os.path.basename(daily_file2.name).split('.')[0]
            weather_file_names = {
                                    Channel.TYPE_WEEKLY: [test_weekly_file1_name, test_weekly_file2_name],
                                    Channel.TYPE_DAILY: [test_daily_file1_name, test_daily_file2_name],
                                 }

            # テスト対象の実行
            scrapyutils.register_scrapped_weather(area.id, weather_file_names)

            # --- DBの確認
            # 既存データがdeleteされているか
            self.assertEqual(Weather.objects.filter(id=weather1.id).count(), 0)
            self.assertEqual(Weather.objects.filter(id=weather2.id).count(), 0)
            self.assertEqual(HourlyWeather.objects.filter(id=hourlyweather1.id).count(), 0)
            self.assertEqual(HourlyWeather.objects.filter(id=hourlyweather2.id).count(), 0)

            # scrapyで取得した週間天気は登録されているか
            self.assertEqual(Weather.objects.count(), 9)
            reg_weathers = Weather.objects.filter().order_by('id')

            # *** weekly_file1 の分
            self.assertEqual(reg_weathers[0].channel, ch_weekly1)
            self.assertEqual(reg_weathers[0].date.isoformat(), '2017-08-09')
            self.assertEqual(reg_weathers[0].weather, '曇り')
            self.assertEqual(reg_weathers[0].highest_temperatures, 30)
            self.assertEqual(reg_weathers[0].lowest_temperatures, 24)
            self.assertEqual(reg_weathers[0].chance_of_rain, 40)
            self.assertEqual(reg_weathers[0].wind_speed, None)

            self.assertEqual(reg_weathers[1].date.isoformat(), '2017-08-10')
            self.assertEqual(reg_weathers[1].weather, '晴れ')

            # *** weekly_file2 の分
            self.assertEqual(reg_weathers[2].channel, ch_weekly2)
            self.assertEqual(reg_weathers[2].date.isoformat(), '2017-08-10')
            self.assertEqual(reg_weathers[2].weather, '雨のち曇')
            self.assertEqual(reg_weathers[2].highest_temperatures, 28)
            self.assertEqual(reg_weathers[2].lowest_temperatures, 22)
            self.assertEqual(reg_weathers[2].chance_of_rain, 60)
            self.assertEqual(reg_weathers[2].wind_speed, None)

            self.assertEqual(reg_weathers[3].date.isoformat(), '2017-08-11')
            self.assertEqual(reg_weathers[3].weather, '曇')

            # *** daily_file1 の分
            self.assertEqual(reg_weathers[4].channel, ch_weekly1)
            self.assertEqual(reg_weathers[4].date.isoformat(), '2017-08-07')
            self.assertEqual(reg_weathers[4].weather, '弱雨')
            self.assertEqual(reg_weathers[4].highest_temperatures, 36)
            self.assertEqual(reg_weathers[4].lowest_temperatures, 27)
            self.assertEqual(reg_weathers[4].chance_of_rain, 999)
            self.assertEqual(reg_weathers[4].wind_speed, 2)

            self.assertEqual(reg_weathers[5].channel, ch_weekly1)
            self.assertEqual(reg_weathers[5].date.isoformat(), '2017-08-08')
            self.assertEqual(reg_weathers[5].weather, '大雨')
            self.assertEqual(reg_weathers[5].highest_temperatures, 37)
            self.assertEqual(reg_weathers[5].lowest_temperatures, 24)
            self.assertEqual(reg_weathers[5].chance_of_rain, 999)
            self.assertEqual(reg_weathers[5].wind_speed, 1)

            # *** daily_file2 の分
            self.assertEqual(reg_weathers[6].channel, ch_weekly2)
            self.assertEqual(reg_weathers[6].date.isoformat(), '2017-08-07')
            self.assertEqual(reg_weathers[6].weather, '台風')
            self.assertEqual(reg_weathers[6].highest_temperatures, 28)
            self.assertEqual(reg_weathers[6].lowest_temperatures, 20)
            self.assertEqual(reg_weathers[6].chance_of_rain, 10)
            self.assertEqual(reg_weathers[6].wind_speed, 2)

            self.assertEqual(reg_weathers[7].channel, ch_weekly2)
            self.assertEqual(reg_weathers[7].date.isoformat(), '2017-08-08')
            self.assertEqual(reg_weathers[7].weather, '曇り')
            self.assertEqual(reg_weathers[7].highest_temperatures, 29)
            self.assertEqual(reg_weathers[7].lowest_temperatures, 22)
            self.assertEqual(reg_weathers[7].chance_of_rain, 20)
            self.assertEqual(reg_weathers[7].wind_speed, 1)

            self.assertEqual(reg_weathers[8].channel, ch_weekly2)
            self.assertEqual(reg_weathers[8].date.isoformat(), '2017-08-09')
            self.assertEqual(reg_weathers[8].weather, '曇り')
            self.assertEqual(reg_weathers[8].highest_temperatures, 30)
            self.assertEqual(reg_weathers[8].lowest_temperatures, 23)
            self.assertEqual(reg_weathers[8].chance_of_rain, 30)
            self.assertEqual(reg_weathers[8].wind_speed, 1)

            # scrapyで取得した今日明日天気は登録されているか
            self.assertEqual(HourlyWeather.objects.count(), 78)
            reg_hourlyweathers = HourlyWeather.objects.filter().order_by('id')

            # *** daily_file1 の分
            self.assertEqual(reg_hourlyweathers[0].channel, ch_daily1)
            self.assertEqual(reg_hourlyweathers[0].date, reg_weathers[4])
            self.assertEqual(reg_hourlyweathers[0].date.date.isoformat(), '2017-08-07')
            self.assertEqual(reg_hourlyweathers[0].time.isoformat(), '00:00:00')
            self.assertEqual(reg_hourlyweathers[0].weather, '晴れ')
            self.assertEqual(reg_hourlyweathers[0].temperatures, 36)
            self.assertEqual(reg_hourlyweathers[0].humidity, 40)
            self.assertEqual(reg_hourlyweathers[0].precipitation, 1)
            self.assertEqual(reg_hourlyweathers[0].chance_of_rain, 999)
            self.assertEqual(reg_hourlyweathers[0].wind_direction, '北西')
            self.assertEqual(reg_hourlyweathers[0].wind_speed, 1)
            # ※以下省略

            # *** daily_file2 の分
            self.assertEqual(reg_hourlyweathers[6].channel, ch_daily2)
            self.assertEqual(reg_hourlyweathers[6].date, reg_weathers[6])
            self.assertEqual(reg_hourlyweathers[6].date.date.isoformat(), '2017-08-07')
            self.assertEqual(reg_hourlyweathers[6].time.isoformat(), '01:00:00')
            self.assertEqual(reg_hourlyweathers[6].weather, '曇り')
            self.assertEqual(reg_hourlyweathers[6].temperatures, Decimal('20.4'))
            self.assertEqual(reg_hourlyweathers[6].humidity, 96)
            self.assertEqual(reg_hourlyweathers[6].precipitation, 0)
            self.assertEqual(reg_hourlyweathers[6].chance_of_rain, 10)
            self.assertEqual(reg_hourlyweathers[6].wind_direction, '北北西')
            self.assertEqual(reg_hourlyweathers[6].wind_speed, 2)

            self.assertEqual(reg_hourlyweathers[53].channel, ch_daily2)
            self.assertEqual(reg_hourlyweathers[53].date, reg_weathers[7])
            self.assertEqual(reg_hourlyweathers[53].date.date.isoformat(), '2017-08-08')
            self.assertEqual(reg_hourlyweathers[53].time.isoformat(), '23:59:59')

            self.assertEqual(reg_hourlyweathers[54].channel, ch_daily2)
            self.assertEqual(reg_hourlyweathers[54].date, reg_weathers[8])
            self.assertEqual(reg_hourlyweathers[54].date.date.isoformat(), '2017-08-09')
            self.assertEqual(reg_hourlyweathers[54].time.isoformat(), '01:00:00')
            # ※以下省略
