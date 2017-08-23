from django.db import models
from django.utils.timezone import now


class Area(models.Model):
    """
    天気予報の対象地域
    """
    name = models.CharField("地域", max_length=200)

    def __str__(self):
        return self.name


class Channel(models.Model):
    """
    天気予報サイトのURL

    各天気予報サイトのURLは、ひとつのAreaに紐づく。
        # ちなみに、
        # weathernews
        # => https://weathernews.jp/onebox/35.864499/139.806766/temp=c&q=埼玉県越谷市
        # 日本気象協会
        # => https://tenki.jp/forecast/3/14/4310/11222/
        # => https://tenki.jp/forecast/3/14/4310/11222/1hour.html
        # Yahoo天気 => https://weather.yahoo.co.jp/weather/jp/11/4310/11222.html
        # goo天気 => https://weather.goo.ne.jp/weather/address/11222/
    """

    TYPE_WEEKLY = 0
    TYPE_DAILY = 1

    TYPE_CHOICES = (
        (TYPE_WEEKLY, '週間天気'),
        (TYPE_DAILY, '今日の天気'),
    )

    CHANNEL_YAHOO = 0
    CHANNEL_TENKIJP = 1
    # CHANNEL_WEATHERNEWS = 2
    

    CHANNEL_CHOICES = (
        (CHANNEL_YAHOO, 'Yahoo!天気'),
        (CHANNEL_TENKIJP, '日本気象協会 tenki.jp'),
        # (CHANNEL_WEATHERNEWS, 'ウェザーニュース'),
    )

    area = models.ForeignKey(Area, on_delete=models.CASCADE, )

    name = models.PositiveIntegerField(
                "チャンネル",
                choices=CHANNEL_CHOICES,
            )
    weather_type = models.PositiveIntegerField(
                "予報タイプ",
                choices=TYPE_CHOICES,
            )
    url = models.URLField(max_length=1000)

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

    def chance_of_rain_display(self):
        if self.chance_of_rain == 999:
            return '---'
        else:
            return self.chance_of_rain


class HourlyWeather(models.Model):
    """
    n時間分の天気予報

    各n時間分の天気予報はひとつのWeatherに紐付く。
    """
    # やっぱりchannelは必要なので、足す
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    date = models.ForeignKey(Weather, on_delete=models.CASCADE)

    time = models.TimeField('時', default=now)
    weather = models.CharField('天気', max_length=200)
    temperatures = models.DecimalField('気温（℃）', max_digits=4, decimal_places=1, default=20)
    humidity = models.PositiveIntegerField('湿度（％）', default=50)
    precipitation = models.PositiveIntegerField(
                '降水量（mm/h）',
                blank=True,
                null=True
            )
    chance_of_rain = models.PositiveIntegerField(
                '降水確率（％）',
                blank=True,
                null=True
            )
    wind_direction = models.CharField('風向', max_length=200)
    wind_speed = models.PositiveIntegerField(
                '風速（m/s）',
                blank=True,
                null=True
            )

    acquisition_date = models.DateTimeField('取得日時', auto_now=True)

    def __str__(self):
        return self.date.date.strftime('%Y/%m/%d') + \
                self.time.strftime('%H/%M/%S')

    def chance_of_rain_display(self):
        worthless_values = [999, '', None]
        if self.chance_of_rain in worthless_values:
            return('---')
        else:
            return self.chance_of_rain
