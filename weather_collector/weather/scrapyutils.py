from datetime import datetime
import subprocess
import csv
import logging
from decimal import Decimal

from .models import Area, Channel, Weather, HourlyWeather


logger = logging.getLogger(__name__)
# scrapyのスパイダー名
SPIDER_NAMES = {
    # CHANNEL:(WEEKLY, DAILY)
    0: ('yahoo_weekly_weather', 'yahoo_daily_weather'),
    1: ('weathernews_weekly_weather', 'weathernews_daily_weather'),
    2: ('tenkijp_weekly_weather', 'tenkijp_daily_weather'),
}
# 天気予報取得対象URLのCSVファイル配置先
urls_file_path_string = '../weatherscrapy/data/urls/{}.csv'
# 天気予報サイトから取得した天気予報CSVファイル配置先
weather_file_path_string = '../weatherscrapy/data/weather/{}.csv'


def output_target_urls_to_csv(channels):
    """
    天気予報取得対象URLのCSV出力処理。
    　※scrapyスパイダーが、ここで出力されたCSVファイルのURLを使用してスクレイピングする。

    @param channels : QuerySet<Channel>。 Channelモデルのクエリセット。
    """
    logger.info('***** Started %s. *****', '__output_target_urls_to_csv')

    for channel in channels:
        file_name = SPIDER_NAMES[channel.name][channel.weather_type]
        urls_file_path = urls_file_path_string.format(file_name)
        with open(
                    urls_file_path,
                    'w', newline='',
                    encoding='utf-8'
                 ) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([channel.url])
            logger.debug('Written to csvfile: %s', channel.url)

        logger.info('Written to: "%s".', urls_file_path)

    logger.info('***** Ended %s. *****', '__output_target_urls_to_csv')


def execute_scrapy(channels):
    """
    weatherscrapy実行処理。
    指定された天気予報サイトから天気予報を取得し、CSV出力する。

    @param channels : QuerySet<Channel>。 Channelモデルのクエリセット。
    @return         : Dict{Channel.weather_type:[file_names]}。
                      KeyにChannel.weather_type、Valueに出力した天気予報CSVファイル名(拡張子は不要)のリストを持つ辞書。
                        例) {Channel.TYPE_WEEKLY:['abc', 'ddd']}
    """
    logger.info('***** Started %s. *****', '__execute_scrapy')

    cmd_string = 'scrapy crawl {spider} -a channel_id={channel_id} -a file_name_suffix={file_name_suffix}'

    weekly_file_names = []
    daily_file_names = []
    weather_file_names = {
        Channel.TYPE_WEEKLY: weekly_file_names,
        Channel.TYPE_DAILY: daily_file_names,
    }

    file_name_suffix = '_' + datetime.now().strftime('%Y%m%d%H%M%S%f')

    for channel in channels:
        spider = SPIDER_NAMES[channel.name][channel.weather_type]
        cmd = cmd_string.format(
                                spider=spider,
                                channel_id=channel.id,
                                file_name_suffix=file_name_suffix
                               ).split(' ')

        logger.info('Execute scrapy command: %s', cmd)

        try:
            proc = subprocess.Popen(cmd, cwd='../weatherscrapy')
        except OSError as e:
            logger.exception('Execute scrapy failed: %s', e)
            # TODO: 共通エラー画面へ遷移
        except ValueError:
            logger.exception('Execute scrapy failed: %s', e)
            # TODO: 共通エラー画面へ遷移
        else:
            logger.info('Execute scrapy has succeeded.')
            weather_file_names[channel.weather_type].append(
                spider + file_name_suffix
            )

        # weatherscrapy実行完了をしばし待つ。
        while proc.poll() is None:
            continue

    logger.debug('weather_file_names: %s', weather_file_names)
    logger.info('***** Ended %s. *****', '__execute_scrapy')
    return weather_file_names


def register_scrapped_weather(area_id, weather_file_names):
    """
    天気予報永続化処理。
    CSV出力された天気予報を読み込み、DBへ登録する。

    @param area_id  : int。 Areaモデルのid。選択した天気予報取得対象地域を表すモデルArea.id。
    @param weather_file_names
                    : Dict{Channel.weather_type:[file_names]}。
                       * KeyにChannel.weather_type、
                       * Valueに読み込み対象のお天気情報CSVファイル名(拡張子は不要)のリスト
                      を持つ辞書。
                      例) {Channel.TYPE_WEEKLY:['abc', 'ddd']}
    """
    logger.info('***** Started %s. *****', 'register_scrapped_weather')

    # 登録前に、既存データはdeleteしておく。
    _delete_weather(area_id)

    # まずは、週間天気予報の登録。
    _register_to_weather(weather_file_names)

    # 週間天気のURLと今日明日天気のURLは必ずセットで登録させるようにする予定だけど、
    # 今はセット登録画面を作ってないため、今日明日天気URLがない場合もあるので、なければリターン。
    if Channel.TYPE_DAILY not in weather_file_names:
        return

    # 次に、今日明日天気予報の登録。
    _register_to_hourlyweather(weather_file_names)

    logger.info('***** Ended %s. *****', 'register_scrapped_weather')


def _delete_weather(area_id):
    """
    既存データの削除処理。
    """
    area = Area.objects.get(id=area_id)
    channels = Channel.objects.filter(area=area)
    Weather.objects.filter(channel__in=channels).delete()


def _register_to_weather(weather_file_names):
    """
    週間天気予報の登録処理。
    """
    for file_name in weather_file_names[Channel.TYPE_WEEKLY]:
        file_path = weather_file_path_string.format(file_name)
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            logger.debug('Opened csvfile: %s', file_path)
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                # 天気予報部分が「---」の行はDB登録する必要がないので、スキップ。
                if not row[1].isdigit():
                    continue

                Weather.objects.create(
                    channel=Channel.objects.get(id=row[2]),
                    date=row[3],
                    weather=row[6],
                    highest_temperatures=row[4],
                    lowest_temperatures=row[5],
                    chance_of_rain=row[1],
                    wind_speed=None,
                )

        logger.info('Registered to Weather: "%s".', file_path)


def _register_to_hourlyweather(weather_file_names):
    """
    今日明日天気予報の登録処理
    """
    # Yahoo天気、ウェザーニューズ・・・週間天気=>降水確率、今日天気=>降水量
    # 日本気象協会、goo天気・・・週間天気=>降水確率、今日天気=>降水確率

    for file_name in weather_file_names[Channel.TYPE_DAILY]:
        file_path = weather_file_path_string.format(file_name)
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            logger.debug('Opened csvfile: %s', file_path)
            reader = csv.reader(csvfile)
            next(reader)  # ヘッダーレコードはスキップ

            # 現在時刻に一番近いレコードを見つけた場合True。
            # HourlyWeather用の天気予報データでWeatherを登録時、「今日の天気」は現在時刻に一番近い時刻の天気を登録するために必要。
            found_close_time = False

            for row in reader:

                hourlyweather_channel = Channel.objects.get(id=row[2])  # row[2]=>Channel.id

                # --- Weatherの登録 ---
                weather, found_close_time = _add_weather_registration(
                    hourlyweather_channel,
                    row,
                    found_close_time
                )

                # --- HourlyWeatherの登録 ---
                HourlyWeather.objects.create(
                    channel=hourlyweather_channel,
                    date=weather,
                    time=row[7],
                    weather=row[8],
                    temperatures=row[6],
                    humidity=row[4],
                    precipitation=_get_precipitation(row[5]),
                    chance_of_rain=_get_chance_of_rain(row[1]),
                    wind_direction=row[9],
                    wind_speed=row[10],
                )

        logger.info('Registered to HourlyWeather: "%s".', file_path)


def _add_weather_registration(hourlyweather_channel, row, found_close_time):
    # 該当日付のWeatherが存在しない場合は、HourlyWeather用の天気予報データでWeatherを登録する
    weather_channel = Channel.objects.get(
        area=hourlyweather_channel.area,
        weather_type=Channel.TYPE_WEEKLY,
        name=hourlyweather_channel.name
    )

    # 一旦、0時(1件目)の天気予報をWeatherに登録する。
    weather, created = Weather.objects.get_or_create(
        channel=weather_channel,
        date=row[3],
        defaults={
            'date': row[3],
            'weather': row[8],
            'highest_temperatures': _get_rounded_temperatures(row[6]),
            'lowest_temperatures': _get_rounded_temperatures(row[6]),
            'chance_of_rain': _get_chance_of_rain(row[1]),
            'wind_speed': row[10],
        },
    )

    # 必要に応じて、weatherを更新する。
    if not created:
        found_close_time = _update_weather_close_current_time(weather, row, found_close_time)
        _update_temperatures_as_necessary(weather, row)

    # Weatherの変更を保存
    weather.save()

    return weather, found_close_time


def _update_weather_close_current_time(weather, row, found_close_time):
    # 最高気温、最低気温以外は現在時刻に一番近いレコードでアップデートする。
    current_row_datetime = datetime.strptime(row[3] + row[7], '%Y-%m-%d%H:%M:%S')

    if (get_now() <= current_row_datetime) and (not(found_close_time)):
        weather.weather = row[8]
        weather.wind_speed = row[10]
        weather.chance_of_rain = _get_chance_of_rain(row[1])
        return True

    return found_close_time


def _update_temperatures_as_necessary(weather, row):
    # 最高気温、最低気温は1日の内で最も高い気温と最も低い気温でアップデートする。
    rounded_temperatures = _get_rounded_temperatures(row[6])
    if int(weather.highest_temperatures) < rounded_temperatures:
        weather.highest_temperatures = rounded_temperatures
    if int(weather.lowest_temperatures) > rounded_temperatures:
        weather.lowest_temperatures = rounded_temperatures


def _get_rounded_temperatures(str_temperatures):
    return round(Decimal(str_temperatures))


def _get_chance_of_rain(row_value):
    if row_value == '':
        chance_of_rain = 999  # 999は画面表示時に'---'に置換
    else:
        chance_of_rain = row_value
    return chance_of_rain


def _get_precipitation(row_value):
    if row_value == '':
        precipitation = 999  # 999は画面表示時に'---'に置換
    else:
        precipitation = row_value
    return precipitation


def get_now():
    return datetime.now()
