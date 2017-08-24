from django.test import TestCase
from django.core.urlresolvers import reverse

from weather import testing
from weather.models import Area, Channel


class TestRegisterChannel(TestCase):
    def _getTarget(self):
        return reverse('channel:register')

    def test_get(self):
        """
        【正常系】『チャンネル登録』画面
        チャンネル登録画面を初期表示する。
        """
        # 対象機能の実行
        res = self.client.get(reverse('channel:register'))

        # 実行結果の確認
        self.assertTemplateUsed(res, 'channel/register.html')
        self.assertIn('form', res.context)

    def test_post(self):
        """
        【正常系】『チャンネル登録』画面
        入力画面からのPOSTの場合、確認画面を表示する。
        """
        area = testing.factory_area()
        input_weekly_url = "https://aaa.jp/input_weekly_url=c&q=茨城県守谷市"
        input_daily_url = 'https://aaa.jp/input_daily_url=c&q=茨城県守谷市'

        data = {
            'area': area.id,
            'channel': Channel.CHANNEL_TENKIJP,
            'weather_type_weekly_url': input_weekly_url,
            'weather_type_daily_url': input_daily_url,
        }

        # 対象機能の実行
        res = self.client.post(
            reverse('channel:register'),
            data=data
        )

        # 実行結果の確認
        self.assertTemplateUsed(res, 'channel/register_confirm.html')

        self.assertEqual(res.context['form']['area'].data, str(area.id))
        self.assertEqual(res.context['form']['channel'].data, str(Channel.CHANNEL_TENKIJP))
        self.assertEqual(res.context['form']['weather_type_weekly_url'].data, input_weekly_url)
        self.assertEqual(res.context['form']['weather_type_daily_url'].data, input_daily_url)

        self.assertEqual(res.context['modified']['area'], area)
        self.assertEqual(res.context['modified']['channel'], str(Channel.CHANNEL_TENKIJP))
        self.assertEqual(res.context['modified']['weather_type_weekly_url'], input_weekly_url)
        self.assertEqual(res.context['modified']['weather_type_daily_url'], input_daily_url)
        self.assertEqual(res.context['channel_display'], '日本気象協会 tenki.jp')

    def test_post_confirmed_back(self):
        """
        【正常系】『チャンネル登録確認』画面
        戻るボタンを押下すると入力画面へ戻る。
        """
        area = testing.factory_area()
        input_weekly_url = "https://aaa.jp/input_weekly_url=c&q=茨城県守谷市"
        input_daily_url = 'https://aaa.jp/input_daily_url=c&q=茨城県守谷市'

        data = {
            'area': area.id,
            'channel': Channel.CHANNEL_TENKIJP,
            'weather_type_weekly_url': input_weekly_url,
            'weather_type_daily_url': input_daily_url,
            'confirmed': '1',
            'back': '戻る',
        }

        # 対象機能の実行
        res = self.client.post(
            reverse('channel:register'),
            data=data
        )

        # 実行結果の確認
        self.assertTemplateUsed(res, 'channel/register.html')
        self.assertEqual(Channel.objects.count(), 0)

        self.assertEqual(res.context['form']['area'].data, str(area.id))
        self.assertEqual(res.context['form']['channel'].data, str(Channel.CHANNEL_TENKIJP))
        self.assertEqual(res.context['form']['weather_type_weekly_url'].data, input_weekly_url)
        self.assertEqual(res.context['form']['weather_type_daily_url'].data, input_daily_url)

    def test_post_confirmed(self):
        """
        【正常系】『チャンネル登録確認』画面

        確認画面からのPOSTの場合、チャンネルを新規登録する。
        * 既存のチャンネルと重複しないチャンネルを登録する場合。
        """
        # データの準備
        area = testing.factory_area()
        input_weekly_url = 'https://aaa.jp/input_weekly_url=c&q=茨城県守谷市'
        input_daily_url = 'https://aaa.jp/input_daily_url=c&q=茨城県守谷市'

        # 対象機能の実行
        res = self.client.post(
            reverse('channel:register'),
            data={
                    'area': area.id,
                    'channel': Channel.CHANNEL_TENKIJP,
                    'weather_type_weekly_url': input_weekly_url,
                    'weather_type_daily_url': input_daily_url,
                    'confirmed': '1',
                    'register': '登録する',
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
        self.assertEqual(channels[0].name, Channel.CHANNEL_TENKIJP)
        self.assertEqual(channels[0].weather_type, Channel.TYPE_WEEKLY)
        self.assertEqual(channels[0].url, input_weekly_url)

        self.assertEqual(channels[1].area, area)
        self.assertEqual(channels[1].name, Channel.CHANNEL_TENKIJP)
        self.assertEqual(channels[1].weather_type, Channel.TYPE_DAILY)
        self.assertEqual(channels[1].url, input_daily_url)

        messages = list(res.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'チャンネル「草津町 * 日本気象協会 tenki.jp」を登録しました。')

    def test_post_duplicate_error(self):
        """
        【異常系】『チャンネル登録確認』画面
        既存のチャンネルと重複するチャンネルは登録できない。
        """
        # データの準備
        area = testing.factory_area()
        channel = testing.factory_channel(
            area=area,
            name=Channel.CHANNEL_TENKIJP,
            weather_type=Channel.TYPE_WEEKLY,
            url='https://weathernews.jp.test'
        )

        input_weekly_url = 'https://aaa.jp/input_weekly_url=c&q=茨城県守谷市'
        input_daily_url = 'https://aaa.jp/input_daily_url=c&q=茨城県守谷市'

        # 対象機能の実行
        res = self.client.post(
            reverse('channel:register'),
            data={
                    'area': area.id,
                    'channel': Channel.CHANNEL_TENKIJP,
                    'weather_type_weekly_url': input_weekly_url,
                    'weather_type_daily_url': input_daily_url,
                    'confirmed': '1',
                    'register': '登録する',
                 }
        )

        # 実行結果の確認
        self.assertTemplateUsed(res, 'channel/register.html')
        self.assertTrue(res.context['form'].is_valid())
        msgs = list(res.context['messages'])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(str(msgs[0]), 'チャンネル「草津町 * 日本気象協会 tenki.jp」はすでに登録されています。')
        self.assertEqual(Channel.objects.count(), 1)
        channels = Channel.objects.select_related(
                    'area'
                ).order_by(
                    'id',
                )
        self.assertEqual(channels[0].area, area)
        self.assertEqual(channels[0].name, Channel.CHANNEL_TENKIJP)
        self.assertEqual(channels[0].weather_type, Channel.TYPE_WEEKLY)
        self.assertEqual(channels[0].url, 'https://weathernews.jp.test')


class TestUpdateChannel(TestCase):
    def _getTarget(self):
        return reverse('channel:update')

    def test_get(self):
        """
        【正常系】『チャンネル変更』画面
        チャンネル変更画面を初期表示する。
        """
        # データの準備
        area = testing.factory_area()
        channel = testing.factory_channel(area=area)

        # 対象機能の実行
        res = self.client.get(reverse('channel:update', args=(channel.id,)))

        # 実行結果の確認
        self.assertTemplateUsed(res, 'channel/edit.html')
        self.assertEqual(res.context['form'].instance, channel)

    def test_get_nonexistence(self):
        """
        【異常系】『チャンネル変更』画面
        変更対象のチャンネルが存在しない場合は404エラー。
        """
        # データの準備
        area = testing.factory_area()

        # 対象機能の実行
        res = self.client.get(reverse('channel:update', args=(999,)))

        # 実行結果の確認
        self.assertEqual(res.status_code, 404)

    def test_post(self):
        """
        【正常系】『チャンネル変更』画面
        POSTの場合、チャンネルを更新する。
        """
        # データの準備
        area = testing.factory_area()
        channel = testing.factory_channel(
            area=area,
        )
        input_weekly_url = 'https://aaa.jp/input_weekly_url=c&q=茨城県守谷市'
        data = {
            'url': input_weekly_url
        }

        # 対象機能の実行
        res = self.client.post(
            reverse(
                'channel:update',
                args=(channel.id,)
            ),
            data=data
        )

        # 実行結果の確認
        self.assertRedirects(res, reverse('channel:list'))
        self.assertEqual(Channel.objects.count(), 1)

        channel.refresh_from_db()
        self.assertEqual(channel.area, area)
        self.assertEqual(channel.name, Channel.CHANNEL_YAHOO)
        self.assertEqual(channel.weather_type, Channel.TYPE_WEEKLY)
        self.assertEqual(channel.url, input_weekly_url)

    def test_post_ValidationError(self):
        """
        【異常系】『チャンネル変更』画面
        ValidationErrorの場合、チャンネルを変更せずエラーメッセージを表示する。
        """
        # データの準備
        area = testing.factory_area()
        channel = testing.factory_channel(
            area=area,
        )

        data = {
            'url': ''
        }

        # 対象機能の実行
        res = self.client.post(
            reverse(
                'channel:update',
                args=(channel.id,)
            ),
            data=data
        )

        # 実行結果の確認
        self.assertTemplateUsed(res, 'channel/edit.html')
        self.assertFalse(res.context['form'].is_valid())
        self.assertEqual(res.context['form'].instance, channel)
        self.assertEqual(res.context['form']['url'].data, '')
        self.assertEqual(
            res.context['form'].errors['url'],
            ['このフィールドは必須です。']
        )

        # DB変更されてないよね確認。
        self.assertEqual(Channel.objects.count(), 1)
        channel.refresh_from_db()
        self.assertEqual(channel.area, area)
        self.assertEqual(channel.name, Channel.CHANNEL_YAHOO)
        self.assertEqual(channel.weather_type, Channel.TYPE_WEEKLY)
        self.assertEqual(channel.url, 'https://weather.fumi.co.jp/weather/jp/11/2222/33333.html')


class TestDeleteChannel(TestCase):
    def _getTarget(self):
        return reverse('channel:delete')

    def test_get(self):
        """
        【正常系】『チャンネル一覧』画面
        チャンネルを削除する。
        """
        # データの準備
        area = testing.factory_area()
        channel_weekly = testing.factory_channel(
            area=area,
        )
        channel_daily = testing.factory_channel(
            area=area,
            weather_type=Channel.TYPE_DAILY
        )

        # 対象機能の実行
        res = self.client.get(
            reverse(
                'channel:delete',
                args=(channel_weekly.id,)
            )
        )

        # 実行結果の確認
        self.assertRedirects(res, reverse('channel:list'))
        self.assertEqual(Channel.objects.count(), 0)

    def test_get_nonexistence(self):
        """
        【異常系】『チャンネル一覧』画面
        削除対象のチャンネルが存在しない場合は404エラー。
        """
        # データの準備
        area = testing.factory_area()

        # 対象機能の実行
        res = self.client.get(reverse('channel:delete', args=(999,)))

        # 実行結果の確認
        self.assertEqual(res.status_code, 404)

    def test_post(self):
        """
        【正常系】『チャンネル一覧』画面
        POSTの場合、チャンネルを削除する。
        """
        # データの準備
        area = testing.factory_area()
        channel_weekly = testing.factory_channel(
            area=area,
        )
        channel_daily = testing.factory_channel(
            area=area,
            weather_type=Channel.TYPE_DAILY
        )

        # 対象機能の実行
        res = self.client.post(
            reverse(
                'channel:delete',
                args=(channel_weekly.id,)
            )
        )

        # 実行結果の確認
        self.assertRedirects(res, reverse('channel:list'))
        self.assertEqual(Channel.objects.count(), 0)


class TestRegisterArea(TestCase):
    def _getTarget(self):
        return reverse('channel:area')

    def test_get(self):
        """
        【正常系】『地域を登録する』画面
        地域を登録画面を初期表示する。
        """
        # 対象機能の実行
        res = self.client.get(reverse('channel:area'))

        # 実行結果の確認
        self.assertTemplateUsed(res, 'channel/register_area.html')
        self.assertIn('form', res.context)

    def test_post(self):
        """
        【正常系】『地域を登録する』画面
        POSTの場合、地域を登録する。
        """
        # 対象機能の実行
        res = self.client.post(
            reverse('channel:area'),
            data={
                    'name': '守谷市',
                 }
        )

        # 実行結果の確認
        self.assertRedirects(res, reverse('channel:register'))
        self.assertEqual(Area.objects.count(), 1)
        area = Area.objects.get()
        self.assertEqual(area.name, '守谷市')

    def test_post_ValidationError(self):
        """
        【異常系】『地域を登録する』画面
        ValidationErrorの場合、地域を登録せずエラーメッセージを表示する。
        """
        # データの準備
        data = {
            'name': ''
        }

        # 対象機能の実行
        res = self.client.post(
            reverse(
                'channel:area',
            ),
            data=data
        )

        # 実行結果の確認
        self.assertTemplateUsed(res, 'channel/register_area.html')
        self.assertFalse(res.context['form'].is_valid())
        self.assertEqual(res.context['form']['name'].data, '')
        self.assertEqual(
            res.context['form'].errors['name'],
            ['このフィールドは必須です。']
        )

        # DB変更されてないよね確認。
        self.assertEqual(Area.objects.count(), 0)
