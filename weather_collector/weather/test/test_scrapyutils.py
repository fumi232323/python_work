from django.test import TestCase
import tempfile
import os

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


    def test_register_weekly_and_daily_weather(self):
        """
        【正常系】
        週間天気予報、今日明日の天気の登録テスト
        """
        # --- 準備
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
2017-08-09 21:16:42.516178,,2,2017-08-07,50,0,36,00:00:00,晴れ,北西,1
2017-08-09 21:16:42.516178,,2,2017-08-07,60,1,32,12:00:00,弱雨,西北西,1
2017-08-09 21:16:42.516178,,2,2017-08-07,82,0,27,21:00:00,曇り,東北東,1
2017-08-09 21:16:42.516178,,2,2017-08-08,50,1,32,00:00:00,弱雨,北西,1
2017-08-09 21:16:42.516178,,2,2017-08-08,60,0,24,12:00:00,晴れ,西北西,1
2017-08-09 21:16:42.516178,,2,2017-08-08,82,0,37,21:00:00,曇り,東北東,1
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
            self.assertEqual(reg_weathers[2].date.isoformat(), '2017-08-11')
            
            self.assertEqual(reg_weathers[3].channel, channel_weekly)
            self.assertEqual(reg_weathers[3].date.isoformat(), '2017-08-07')
            self.assertEqual(reg_weathers[3].weather, '晴れ')
            self.assertEqual(reg_weathers[3].highest_temperatures, 36)
            self.assertEqual(reg_weathers[3].lowest_temperatures, 27)
            self.assertEqual(reg_weathers[3].chance_of_rain, 999)
            self.assertEqual(reg_weathers[3].wind_speed, 1)
            
            self.assertEqual(reg_weathers[4].channel, channel_weekly)
            self.assertEqual(reg_weathers[4].date.isoformat(), '2017-08-08')
            self.assertEqual(reg_weathers[4].weather, '弱雨')
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
            self.assertEqual(reg_hourlyweathers[0].chance_of_rain, None)
            self.assertEqual(reg_hourlyweathers[0].wind_direction, '北西')
            self.assertEqual(reg_hourlyweathers[0].wind_speed, 1)

            self.assertEqual(reg_hourlyweathers[3].channel, channel_daily)
            self.assertEqual(reg_hourlyweathers[3].date, reg_weathers[4])
            self.assertEqual(reg_hourlyweathers[3].date.date.isoformat(), '2017-08-08')