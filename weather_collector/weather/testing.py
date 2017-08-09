from . import models


def factory_area(**kwargs):
    """
    テスト用の Area を作る
    """
    data = {
        'name': '草津町',
    }
    data.update(kwargs)

    return models.Area.objects.create(**data)


def factory_channel(**kwargs):
    """
    テスト用の Channel を作る
    """
    data = {
        'name': Channel.CHANNEL_YAHOO,
        'weather_type': Channel.TYPE_WEEKLY,
        'url': 'https://weather.yahoo.co.jp/weather/jp/11/4310/11222.html',
    }
    data.update(kwargs)
    if 'area' not in data:
        data['area'] = factory_area()

    return models.Channel.objects.create(**data)


def factory_weather(**kwargs):
    """
    テスト用の Weather を作る
    """
    data = {
        'name': Channel.CHANNEL_YAHOO,
        'weather_type': Channel.TYPE_WEEKLY,
        'url': 'https://weather.yahoo.co.jp/weather/jp/11/4310/11222.html',
    }
    data.update(kwargs)
    if 'area' not in data:
        data['area'] = factory_area()
    if 'channel' not in data:
        data['channel'] = factory_area()

    return models.Weather.objects.create(**data)
