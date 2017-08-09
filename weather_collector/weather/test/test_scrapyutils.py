from django.test import TestCase
import tempfile
import os

from weather import testing
from weather.models import Channel, Weather, HourlyWeather

from weather import scrapyutils


class TestRegisterScrappedWeather(TestCase):
    def test__register_weekly_weather(self):
        """
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
2017-08-09 21:16:35.245048,30,10,2017-08-14,29,23,曇時々晴,
2017-08-09 21:16:35.245048,50,10,2017-08-15,28,23,曇時々雨,
2017-08-09 21:16:35.245048,50,10,2017-08-16,30,23,曇時々雨,
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
            self.assertEqual(Weather.objects.count(), 6)
            registered_weathers = Weather.objects.filter().order_by('id')

            self.assertEqual(registered_weathers[0].channel, channel)
            self.assertEqual(registered_weathers[0].date.isoformat(), '2017-08-11')
            self.assertEqual(registered_weathers[0].weather, '曇時々雨')
            self.assertEqual(registered_weathers[0].highest_temperatures, 29)
            self.assertEqual(registered_weathers[0].lowest_temperatures, 23)
            self.assertEqual(registered_weathers[0].chance_of_rain, 50)
            self.assertEqual(registered_weathers[0].wind_speed, None)

            # TODO: あとのレコードの確認はあとで書きます。


    def test__register_weekly_daily_weather(self):
        """
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
2017-08-09 21:16:35.245048,30,10,2017-08-14,29,23,曇時々晴,
2017-08-09 21:16:35.245048,50,10,2017-08-15,28,23,曇時々雨,
2017-08-09 21:16:35.245048,50,10,2017-08-16,30,23,曇時々雨,
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
            self.assertEqual(Weather.objects.count(), 6)
            registered_weathers = Weather.objects.filter().order_by('id')

            self.assertEqual(registered_weathers[0].channel, channel)
            self.assertEqual(registered_weathers[0].date.isoformat(), '2017-08-11')
            self.assertEqual(registered_weathers[0].weather, '曇時々雨')
            self.assertEqual(registered_weathers[0].highest_temperatures, 29)
            self.assertEqual(registered_weathers[0].lowest_temperatures, 23)
            self.assertEqual(registered_weathers[0].chance_of_rain, 50)
            self.assertEqual(registered_weathers[0].wind_speed, None)