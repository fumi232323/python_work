from django.db import models
from django.utils.timezone import now


class Area(models.Model):
    """
    天気予報の対象地域
    """
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Channel(models.Model):
    """
    天気予報サイトのURL
    
    各天気予報サイトのURLは、ひとつのAreaに紐づく。
        # ちなみに、
        # ウェザーニュース
        => https://weathernews.jp/onebox/35.864499/139.806766/temp=c&q=埼玉県越谷市
        # 日本気象協会 => https://tenki.jp/forecast/3/14/4310/11222/
        # ヤフー天気 => https://weather.yahoo.co.jp/weather/jp/11/4310/11222.html
        # goo天気 => https://weather.goo.ne.jp/weather/address/11222/
    """

    TYPE_WEEKLY = 0
    TYPE_DAILY = 1

    TYPE_CHOICES = (
        (TYPE_WEEKLY, '週間天気'),
        (TYPE_DAILY, '今日の天気'),
    )

    CHANNEL_YAHOO = 0
    CHANNEL_WEATHERNEWS = 1
    CHANNEL_TENKIJP = 2

    CHANNEL_CHOICES = (
        (CHANNEL_YAHOO, 'Yahoo!天気'),
        (CHANNEL_WEATHERNEWS, 'ウェザーニュース'),
        (CHANNEL_TENKIJP, '日本気象協会 tenki.jp'),
    )

    area = models.ForeignKey(Area, on_delete=models.CASCADE)

    name = models.PositiveIntegerField(
                "チャンネル名",
                choices=CHANNEL_CHOICES,
                default=CHANNEL_YAHOO
            )
    weather_type = models.PositiveIntegerField(
                "お天気区分",
                choices=TYPE_CHOICES,
                default=TYPE_WEEKLY
            )
    url = models.CharField(max_length=1000)

    def __str__(self):
        return self.area.name + '-' + \
                self.get_name_display() + '-' + \
                self.get_weather_type_display()


class Weather(models.Model):
    """
    1日分の天気予報
    
    各1日分の天気予報はひとつのChannelに紐付く。
    """
    WEEKDAY_JA = [
        '月', '火', '水', '木', '金', '土', '日',
    ]

    # area = models.ForeignKey(Area, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)

    date = models.DateField('日付', default=now)
    weather = models.CharField('天気', max_length=200)
    highest_temperatures = models.IntegerField('最高気温（℃）', default=20)
    lowest_temperatures = models.IntegerField('最低気温（℃）', default=20)
    chance_of_rain = models.PositiveIntegerField('降水確率（％）', default=0)
    wind_speed = models.PositiveIntegerField(
            '風速（m/s）',
            default=0,
            blank=True,
            null=True
        )

    acquisition_date = models.DateTimeField('取得日時', auto_now=True)

    def __str__(self):
        return str(self.channel) + '-' + self.date.strftime('%Y/%m/%d')

    def date_display(self):
        return self.date.strftime('%m/%d')
        # return self.date.strftime('%m/%d (%a)')

    def weekday_display(self):
        return self.WEEKDAY_JA[self.date.weekday()]


class HourlyWeather(models.Model):
    """
    n時間分の天気予報

    各n時間分の天気予報はひとつのWeatherに紐付く。
    """
    date = models.ForeignKey(Weather, on_delete=models.CASCADE)

    time = models.TimeField('時', default=now)
    weather = models.CharField('天気', max_length=200)
    temperatures = models.IntegerField('気温（℃）', default=20)
    # TODO: humidityをPositiveIntegerFieldに変えないと
    humidity = models.IntegerField('湿度（％）', default=50)
    precipitation = models.PositiveIntegerField(
                '降水量（mm/h）',
                default=0,
                blank=True,
                null=True
            )
    chance_of_rain = models.PositiveIntegerField(
                '降水確率（％）',
                default=0,
                blank=True,
                null=True
            )
    wind_direction = models.CharField('風向', max_length=200)
    wind_speed = models.PositiveIntegerField(
                '風速（m/s）',
                default=0,
                blank=True,
                null=True
            )

    acquisition_date = models.DateTimeField('取得日時', auto_now=True)

    def __str__(self):
        return self.date.date.strftime('%Y/%m/%d') + \
                self.time.strftime('%H/%M/%S')
