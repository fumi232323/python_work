from django.test import TestCase
from django.core.urlresolvers import reverse
from django.http import Http404

from datetime import datetime

from weather import testing
from weather.models import Channel


class TestRegisterChannel(TestCase):
    def _getTarget(self):
        return reverse('channel:register')

    def test_get(self):
        """
        チャンネル登録画面を初期表示するテスト
        """
        # データの準備
        area = testing.factory_area()

        # 対象機能の実行
        res = self.client.get(reverse('channel:register'))

        # 実行結果の確認
        self.assertTemplateUsed(res, 'channel/register.html')
        self.assertIn('form', res.context)


    def test_post(self):
        """
        【正常系】
        入力されたチャンネルを登録するテスト
        既存のチャンネルと重複しないチャンネルを登録する場合。
        """
        # データの準備
        area = testing.factory_area()
        input_weekly_url = 'https://weathernews.jp/onebox/35.864499/139.806766/temp=c&q=埼玉県越谷市'
        input_daily_url ='https://weathernews.jp/onebox/35.864499/139.806766/'

        # 対象機能の実行
        res = self.client.post(
            reverse('channel:register'),
            data={'area': area.id,
                  'channel': Channel.CHANNEL_WEATHERNEWS,
                  'weather_type_weekly_url': input_weekly_url,
                  'weather_type_daily_url': input_daily_url,
                 }
        )

        # 実行結果の確認
        self.assertRedirects(res, reverse('channel:list'))
        self.assertEqual(Channel.objects.count(), 2)
        channels = Channel.objects.select_related(
                    'area'
                ).order_by(
                    'id',
                )
        self.assertEqual(channels[0].area, area)
        self.assertEqual(channels[0].name, Channel.CHANNEL_WEATHERNEWS)
        self.assertEqual(channels[0].weather_type, Channel.TYPE_WEEKLY)
        self.assertEqual(channels[0].url, input_weekly_url)
        
        self.assertEqual(channels[1].area, area)
        self.assertEqual(channels[1].name, Channel.CHANNEL_WEATHERNEWS)
        self.assertEqual(channels[1].weather_type, Channel.TYPE_DAILY)
        self.assertEqual(channels[1].url, input_daily_url)


    def test_post_duplicate_error(self):
        """
        【正常系】
        入力されたチャンネルを登録するテスト
        既存のチャンネルと重複するチャンネルを登録する場合。
        """
        # データの準備
        area = testing.factory_area()
        channel = testing.factory_channel(
            area=area,
            name=Channel.CHANNEL_WEATHERNEWS,
            weather_type=Channel.TYPE_WEEKLY,
            url='https://weathernews.jp.test'
        )

        input_weekly_url = 'https://weathernews.jp/onebox/35.864499/139.806766/temp=c&q=埼玉県越谷市'
        input_daily_url ='https://weathernews.jp/onebox/35.864499/139.806766/'

        # 対象機能の実行
        res = self.client.post(
            reverse('channel:register'),
            data={'area': area.id,
                  'channel': Channel.CHANNEL_WEATHERNEWS,
                  'weather_type_weekly_url': input_weekly_url,
                  'weather_type_daily_url': input_daily_url,
                 }
        )

        # 実行結果の確認
        self.assertTemplateUsed(res, 'channel/register.html')
        self.assertFalse(res.context['form'].is_valid())
        self.assertContains(res, '[草津町 - ウェザーニュース] チャンネルはすでに登録されています。')
        self.assertEqual(Channel.objects.count(), 1)
        channels = Channel.objects.select_related(
                    'area'
                ).order_by(
                    'id',
                )
        self.assertEqual(channels[0].area, area)
        self.assertEqual(channels[0].name, Channel.CHANNEL_WEATHERNEWS)
        self.assertEqual(channels[0].weather_type, Channel.TYPE_WEEKLY)
        self.assertEqual(channels[0].url, 'https://weathernews.jp.test')
