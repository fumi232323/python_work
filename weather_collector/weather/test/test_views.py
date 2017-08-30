from django.test import TestCase
from django.core.urlresolvers import reverse

import os
import tempfile
from unittest import mock
from datetime import date, datetime

from weather import testing
from weather.models import Channel, Weather, HourlyWeather
from weather import scrapyutils


class TestWeeklyWeather(TestCase):
    def _getTarget(self):
        return reverse('weather:weekly')

    @mock.patch('weather.views.get_today')
    def test_get(self, m):
        """
        【正常系】『週間天気予報』画面
        選択したエリアの、週間天気予報を表示する。
        """
        m.return_value = date(2017, 8, 11)

        area = testing.factory_area()
        channel_weekly = testing.factory_channel(area=area)
        channel_daily = testing.factory_channel(area=area, weather_type=Channel.TYPE_DAILY)
        weather1 = testing.factory_weather(channel=channel_weekly, date=date(2017, 8, 10))
        weather2 = testing.factory_weather(channel=channel_weekly, date=date(2017, 8, 11))
        weather3 = testing.factory_weather(channel=channel_weekly, date=date(2017, 8, 12))
        hourlyweather = testing.factory_hourlyweather(channel=channel_daily, date=weather2)

        res = self.client.get(reverse('weather:weekly', args=(area.id,)))

        self.assertTemplateUsed(res, 'weather/weekly.html')
        self.assertEqual(res.context['area'], area)
        self.assertContains(res, '草津町の週間天気予報')

        all_weekly_weather = res.context['all_weekly_weather']
        self.assertEqual(len(all_weekly_weather), 1)
        self.assertTrue(channel_weekly.get_name_display() in all_weekly_weather)
        self.assertContains(res, 'Yahoo!天気')

        # 今日より前の天気予報は表示しない。
        weathers = all_weekly_weather[channel_weekly.get_name_display()]
        self.assertEqual(len(weathers), 2)
        self.assertEqual(weathers[0], weather2)
        self.assertEqual(weathers[0].daily_weather_count, 1)
        self.assertEqual(weathers[1], weather3)
        self.assertEqual(weathers[1].daily_weather_count, 0)

        # hourlyweatherが存在する場合は、日付をリンク表示
        self.assertContains(res, reverse('weather:daily', args=(weather2.id,)))
        self.assertNotContains(res, reverse('weather:daily', args=(weather3.id,)))

    @mock.patch('weather.views.get_today')
    def test_post(self, m):
        """
        【正常系】『週間天気予報』画面
        選択したエリアの、週間天気予報を表示する。
        """
        m.return_value = date(2017, 8, 11)

        # 同一エリアに、'Yahoo!天気'と'日本気象協会 tenki.jp'のWeatherが存在する場合。
        area = testing.factory_area()
        channel_yahoo = testing.factory_channel(area=area)
        channel_tenkijp = testing.factory_channel(
            area=area,
            name=Channel.CHANNEL_TENKIJP
        )

        weather_yahoo = testing.factory_weather(channel=channel_yahoo, date=date(2017, 8, 11))
        weather_tenkijp = testing.factory_weather(channel=channel_tenkijp, date=date(2017, 8, 12))

        res = self.client.get(reverse('weather:weekly', args=(area.id,)))

        self.assertTemplateUsed(res, 'weather/weekly.html')
        self.assertEqual(res.context['area'], area)
        self.assertContains(res, '草津町の週間天気予報')

        all_weekly_weather = res.context['all_weekly_weather']
        self.assertEqual(len(all_weekly_weather), 2)
        self.assertTrue(channel_yahoo.get_name_display() in all_weekly_weather)
        self.assertTrue(channel_tenkijp.get_name_display() in all_weekly_weather)
        self.assertContains(res, 'Yahoo!天気')
        self.assertContains(res, '日本気象協会 tenki.jp')

        yahoo_weathers = all_weekly_weather[channel_yahoo.get_name_display()]
        self.assertEqual(len(yahoo_weathers), 1)
        self.assertEqual(yahoo_weathers[0], weather_yahoo)

        tenkijp_weathers = all_weekly_weather[channel_tenkijp.get_name_display()]
        self.assertEqual(len(tenkijp_weathers), 1)
        self.assertEqual(tenkijp_weathers[0], weather_tenkijp)

    def test_channel_does_not_exist(self):
        """
        【正常系】『週間天気予報』画面
        選択したエリアのチャンネルが存在しない場合は週間天気予報画面にチャンネル登録を促すメッセージを表示。
        """
        area = testing.factory_area()

        res = self.client.get(reverse('weather:weekly', args=(area.id,)))

        self.assertTemplateUsed(res, 'weather/weekly.html')
        self.assertEqual(res.context['area'], area)
        self.assertContains(res, '草津町の週間天気予報')

        all_weekly_weather = res.context['all_weekly_weather']
        self.assertEqual(all_weekly_weather, {})

        # チャンネルが存在しない場合は、表組を表示しない。
        self.assertNotContains(res, '日付')
        # チャンネル登録を促すメッセージとチャンネル登録ボタンを表示する。
        msg = list(res.context['messages'])
        self.assertEqual(len(msg), 1)
        self.assertContains(res, 'チャンネルが登録されていません。')
        self.assertContains(res, 'チャンネルを新規登録')

    def test_weather_does_not_exist(self):
        """
        【正常系】『週間天気予報』画面
        選択したエリアの週間天気予報(Weather)取得結果が0件の場合
        """
        area = testing.factory_area()
        channel_weekly = testing.factory_channel(area=area)
        channel_daily = testing.factory_channel(area=area, weather_type=Channel.TYPE_DAILY)

        res = self.client.get(reverse('weather:weekly', args=(area.id,)))

        self.assertTemplateUsed(res, 'weather/weekly.html')
        self.assertEqual(res.context['area'], area)
        self.assertContains(res, '草津町の週間天気予報')

        all_weekly_weather = res.context['all_weekly_weather']
        self.assertEqual(len(all_weekly_weather), 1)
        self.assertTrue(channel_weekly.get_name_display() in all_weekly_weather)
        weathers = all_weekly_weather[channel_weekly.get_name_display()]
        self.assertEqual(len(weathers), 0)
        # h2タイトルと表組は表示する。
        self.assertContains(res, 'Yahoo!天気')
        self.assertContains(res, '日付')

        # 週間天気予報(Weather)が存在しない場合は、天気予報がない旨を表示する。
        self.assertContains(res, '天気予報ないよ')


class TestDailyWeather(TestCase):
    def test_get(self):
        """
        【正常系】『今日の天気予報』画面
        選択した日付の、今日の天気予報(時間ごと)を表示する。
        """
        area = testing.factory_area()
        channel_weekly = testing.factory_channel(area=area)
        channel_daily = testing.factory_channel(area=area, weather_type=Channel.TYPE_DAILY)
        weather11 = testing.factory_weather(channel=channel_weekly, date=date(2017, 8, 11))
        hourlyweather00 = testing.factory_hourlyweather(
            channel=channel_daily,
            date=weather11,
            time='00:00:00'
        )
        hourlyweather12 = testing.factory_hourlyweather(
            channel=channel_daily,
            date=weather11,
            time='12:00:00'
        )
        hourlyweather21 = testing.factory_hourlyweather(
            channel=channel_daily,
            date=weather11,
            time='21:00:00'
        )

        weather12 = testing.factory_weather(channel=channel_weekly, date=date(2017, 8, 12))
        hourlyweather09 = testing.factory_hourlyweather(
            channel=channel_daily,
            date=weather12,
            time='09:00:00'
        )

        res = self.client.get(reverse('weather:daily', args=(weather11.id,)))

        self.assertTemplateUsed(res, 'weather/daily.html')
        self.assertEqual(res.context['weather'], weather11)
        # H1タイトル
        self.assertContains(res, '草津町*:;;;:*08/11(金)の天気予報')
        # H2タイトル
        self.assertContains(res, 'Yahoo!天気')
        daily_weather = res.context['daily_weather']
        self.assertEqual(len(daily_weather), 3)
        self.assertEqual(daily_weather[0], hourlyweather00)
        self.assertEqual(daily_weather[1], hourlyweather12)
        self.assertEqual(daily_weather[2], hourlyweather21)

    def test_post(self):
        """
        【正常系】『今日の天気予報』画面
        選択した日付の、今日の天気予報(時間ごと)を表示する。
        """
        area = testing.factory_area()
        channel_weekly = testing.factory_channel(area=area)
        channel_daily = testing.factory_channel(area=area, weather_type=Channel.TYPE_DAILY)
        weather11 = testing.factory_weather(channel=channel_weekly, date=date(2017, 8, 11))
        hourlyweather00 = testing.factory_hourlyweather(
            channel=channel_daily,
            date=weather11,
            time='00:00:00'
        )
        hourlyweather12 = testing.factory_hourlyweather(
            channel=channel_daily,
            date=weather11,
            time='12:00:00'
        )
        hourlyweather21 = testing.factory_hourlyweather(
            channel=channel_daily,
            date=weather11,
            time='21:00:00'
        )

        weather12 = testing.factory_weather(channel=channel_weekly, date=date(2017, 8, 12))
        hourlyweather09 = testing.factory_hourlyweather(
            channel=channel_daily,
            date=weather12,
            time='09:00:00'
        )

        res = self.client.post(reverse('weather:daily', args=(weather11.id,)))

        self.assertTemplateUsed(res, 'weather/daily.html')
        self.assertEqual(res.context['weather'], weather11)
        # H1タイトル
        self.assertContains(res, '草津町*:;;;:*08/11(金)の天気予報')
        # H2タイトル
        self.assertContains(res, 'Yahoo!天気')
        daily_weather = res.context['daily_weather']
        self.assertEqual(len(daily_weather), 3)
        self.assertEqual(daily_weather[0], hourlyweather00)
        self.assertEqual(daily_weather[1], hourlyweather12)
        self.assertEqual(daily_weather[2], hourlyweather21)


class TestSelectArea(TestCase):
    def test_get(self):
        """
        【正常系】『お天気エリア選択』画面
        お天気エリア選択画面を初期表示する。
        """
        area = testing.factory_area()

        res = self.client.get(reverse('weather:select_area'))

        self.assertTemplateUsed(res, 'weather/select_area.html')
        self.assertIn('form', res.context)

    @mock.patch('weather.scrapyutils.output_target_urls_to_csv')
    @mock.patch('weather.scrapyutils.execute_scrapy')
    @mock.patch('weather.scrapyutils.register_scrapped_weather')
    def test_post(self, mock_register, mock_scrapy, mock_url):
        """
        【正常系】『お天気エリア選択』画面
        「天気予報を取得」ボタンを押下時処理。
        選択した地域の天気予報をスクレイピング&DB登録し、週間天気予報を表示する。
        """
        area = testing.factory_area()
        channel_weekly = testing.factory_channel(area=area)
        channel_daily = testing.factory_channel(area=area, weather_type=Channel.TYPE_DAILY)

        res = self.client.post(
            reverse('weather:select_area'),
            data={
                    'selected_area': area.id,
                    'scrapy_weather': '天気予報を取得',
                }
        )

        self.assertRedirects(res, reverse('weather:weekly', kwargs={'area_id': area.id}))

    @mock.patch('weather.scrapyutils._get_now')
    @mock.patch('weather.scrapyutils._get_urls_file_dir')
    @mock.patch('weather.scrapyutils._get_weather_file_dir')
    def test_post_channel_does_not_exist(
        self,
        mock_weather_file_dir,
        mock_urls_file_dir,
        mock_now
    ):
        """
        【正常系】『お天気エリア選択』画面
        「天気予報を取得」ボタンを押下時処理。
        選択したエリアのチャンネルが存在しない場合は、スクレイピングは行わず、週間天気予報画面を表示する。
        """
        mock_now.return_value = datetime(2017, 8, 7, 11, 00, 00, 000000)
        area1 = testing.factory_area(name='エリア１')
        area2 = testing.factory_area(name='エリア２')
        channel_weekly = testing.factory_channel(area=area2)
        channel_daily = testing.factory_channel(area=area2, weather_type=Channel.TYPE_DAILY)

        # URLファイルとお天気情報ファイル出力先を、一時ディレクトリにモックする
        with tempfile.TemporaryDirectory() as urls_dirpath, \
                tempfile.TemporaryDirectory() as weather_dirpath:

            mock_urls_file_dir.return_value = urls_dirpath
            mock_weather_file_dir.return_value = weather_dirpath

            res = self.client.post(
                reverse('weather:select_area'),
                data={
                        'selected_area': area1.id,
                        'scrapy_weather': '天気予報を取得',
                    }
            )

            self.assertRedirects(res, reverse('weather:weekly', kwargs={'area_id': area1.id}))

            # URLファイルが出力されていないことを確認
            w_urls_file_path = scrapyutils._get_urls_file_path('yahoo_weekly_weather')
            d_urls_file_path = scrapyutils._get_urls_file_path('yahoo_daily_weather')
            self.assertFalse(os.path.isfile(w_urls_file_path))
            self.assertFalse(os.path.isfile(d_urls_file_path))

            # お天気情報ファイルが出力されていないことを確認
            w_weather_file_path = scrapyutils._get_weather_file_path(
                'yahoo_weekly_weather_20170807110000000000'
            )
            d_weather_file_path = scrapyutils._get_weather_file_path(
                'yahoo_daily_weather_20170807110000000000'
            )
            self.assertFalse(os.path.isfile(w_weather_file_path))
            self.assertFalse(os.path.isfile(d_weather_file_path))

        # DB登録されないことを確認
        self.assertEqual(Weather.objects.count(), 0)
        self.assertEqual(HourlyWeather.objects.count(), 0)

        self.assertRedirects(res, reverse('weather:weekly', kwargs={'area_id': area1.id}))

    def test_post_weekly_weather(self):
        """
        【正常系】『お天気エリア選択』画面
        「週間天気予報を表示」ボタンを押下時処理。
        選択したエリアの週間天気予報画面を表示する。
        """
        area = testing.factory_area(name='エリア１')
        channel_weekly = testing.factory_channel(area=area)
        channel_daily = testing.factory_channel(area=area, weather_type=Channel.TYPE_DAILY)

        res = self.client.post(
            reverse('weather:select_area'),
            data={
                    'selected_area': area.id,
                    'display_weekly': '週間天気予報を表示',
                }
        )

        self.assertRedirects(res, reverse('weather:weekly', kwargs={'area_id': area.id}))

    def test_post_validationError(self):
        """
        【正常系】『お天気エリア選択』画面
        バリデーションエラー時は、お天気エリア選択画面に戻る。
        """
        area1 = testing.factory_area(name='エリア１')
        channel_weekly = testing.factory_channel(area=area1)
        channel_daily = testing.factory_channel(area=area1, weather_type=Channel.TYPE_DAILY)

        res = self.client.post(
            reverse('weather:select_area'),
            data={
                    'selected_area': '',
                    'display_weekly': '週間天気予報を表示',
                }
        )

        self.assertTemplateUsed(res, 'weather/select_area.html')
        self.assertFalse(res.context['form'].is_valid())
        self.assertEqual(res.context['form']['selected_area'].data, '')
        self.assertEqual(
            res.context['form'].errors['selected_area'],
            ['このフィールドは必須です。']
        )

    @mock.patch('weather.scrapyutils._get_urls_file_dir')
    @mock.patch('weather.scrapyutils.execute_scrapy')
    @mock.patch('weather.scrapyutils.register_scrapped_weather')
    def test_post_output_target_urls_to_csv_OSError(self, mock_register, mock_scrapy, mock_urls_file_dir):
        """
        【異常系】『お天気エリア選択』画面
        天気予報取得対象URLのCSV出力処理呼び出しでOSError発生時は、500エラー。
        """
        area = testing.factory_area()
        channel_weekly = testing.factory_channel(area=area)
        channel_daily = testing.factory_channel(area=area, weather_type=Channel.TYPE_DAILY)

        # URLファイル出力先を、一時ディレクトリにモックする
        with tempfile.TemporaryDirectory() as dirpath:
            mock_urls_file_dir.return_value = dirpath

        with self.assertRaises(OSError):
            res = self.client.post(
                reverse('weather:select_area'),
                data={
                        'selected_area': area.id,
                        'scrapy_weather': '天気予報を取得',
                    }
            )
            self.assertTemplateUsed(res, '500.html')
