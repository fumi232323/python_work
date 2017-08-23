from weather.models import Area, Channel, Weather, HourlyWeather


def factory_area(**kwargs):
    """
    テスト用の Area を作る
    """
    data = {
        'name': '草津町',
    }
    data.update(kwargs)

    return Area.objects.create(**data)


def factory_channel(**kwargs):
    """
    テスト用の Channel を作る
    """
    data = {
        'name': Channel.CHANNEL_YAHOO,
        'weather_type': Channel.TYPE_WEEKLY,
        'url': 'https://weather.fumi.co.jp/weather/jp/11/2222/33333.html',
    }
    data.update(kwargs)
    if 'area' not in data:
        data['area'] = factory_area()

    return Channel.objects.create(**data)


def factory_weather(**kwargs):
    """
    テスト用の Weather を作る
    """
    data = {
        'date': '2017-08-11',
        'weather': '晴れ',
        'highest_temperatures': 30,
        'lowest_temperatures': 23,
        'chance_of_rain': 40,
        'wind_speed': 1,
    }
    data.update(kwargs)
    if 'channel' not in data:
        data['channel'] = factory_channel()

    return Weather.objects.create(**data)


def factory_hourlyweather(**kwargs):
    """
    テスト用の Weather を作る
    """
    data = {
        'time': '12:00:00',
        'weather': '晴れ',
        'temperatures': 30,
        'humidity': 88,
        'precipitation': 5,
        'chance_of_rain': 10,
        'wind_direction': '南南西',
        'wind_speed': 1,
    }
    data.update(kwargs)
    if 'channel' not in data:
        data['channel'] = factory_channel()
    if 'date' not in data:
        data['date'] = factory_weather()

    return HourlyWeather.objects.create(**data)
