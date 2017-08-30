from datetime import datetime
import subprocess
import csv
import os
import logging
from decimal import Decimal

from .models import Area, Channel, Weather, HourlyWeather


logger = logging.getLogger(__name__)

# scrapyのスパイダー名
SPIDER_NAMES = {
    # CHANNEL:(WEEKLY, DAILY)
    0: ('yahoo_weekly_weather', 'yahoo_daily_weather'),
    1: ('tenkijp_weekly_weather', 'tenkijp_daily_weather'),
    2: ('weathernews_weekly_weather', 'weathernews_daily_weather'),
}
# 天気予報取得対象URLのCSVファイル配置先
URLS_FILE_DIR = '../weatherscrapy/data/urls/'
# 天気予報サイトから取得したお天気情報CSVファイル配置先
WEATHER_FILE_DIR = '../weatherscrapy/data/weather/'
FILE_EXTENSION = '.csv'


def _get_urls_file_dir():
    return URLS_FILE_DIR


def _get_urls_file_path(file_name):
    """
    天気予報取得対象URLのCSVファイルのパスを返す
    """
    return os.path.join(_get_urls_file_dir(), file_name + FILE_EXTENSION)


def _get_weather_file_dir():
    return WEATHER_FILE_DIR


def _get_weather_file_path(file_name):
    """
    お天気情報のCSVファイルのパスを返す
    """
    return os.path.join(_get_weather_file_dir(), file_name + FILE_EXTENSION)


def _get_spider_name(channel):
    """
    チャンネルに応じたスパイダー名を返す
    """
    return SPIDER_NAMES[channel.name][channel.weather_type]


def output_target_urls_to_csv(channels):
    """
    天気予報取得対象URLのCSV出力処理。
    　※scrapyスパイダーが、ここで出力されたCSVファイルのURLを使用してスクレイピングする。

    @param channels : Channelモデルのリスト。
    """
    logger.info('***** Started %s. *****', 'output_target_urls_to_csv')

    for channel in channels:
        file_name = _get_spider_name(channel)
        urls_file_path = _get_urls_file_path(file_name)
        try:
            with open(
                        urls_file_path,
                        'w', newline='',
                        encoding='utf-8'
                     ) as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([channel.url])

        except OSError:
            logger.error(
                'Written to csvfile failed. urls_file_path: %s, channel_id: %s ',
                urls_file_path,
                channel.id)
            raise

        else:
            logger.debug('Written to csvfile: %s', channel.url)
            logger.info('Written to: "%s".', urls_file_path)

    logger.info('***** Ended %s. *****', 'output_target_urls_to_csv')


def execute_scrapy(channels):
    """
    weatherscrapy実行処理。
    指定された天気予報サイトから天気予報を取得し、CSV出力する。

    @param channels : Channelモデルのリスト。
    @return         : Dict{Channel.weather_type:[file_names]}。
                      * KeyにChannel.weather_type、
                      * Valueに出力したお天気情報CSVファイル名(拡張子は不要)のリスト
                      を持つ辞書。
                        (例) {Channel.TYPE_WEEKLY:['abc', 'ddd']}
    """
    logger.info('***** Started %s. *****', 'execute_scrapy')

    weekly_file_names = []
    daily_file_names = []
    weather_file_names = {
        Channel.TYPE_WEEKLY: weekly_file_names,
        Channel.TYPE_DAILY: daily_file_names,
    }

    file_name_suffix = '_' + _get_now().strftime('%Y%m%d%H%M%S%f')

    for channel in channels:

        spider = _get_spider_name(channel)
        cmd = _get_scrapy_command(spider, channel.id, file_name_suffix)
        logger.info('Execute scrapy command: %s', cmd)

        try:
            proc = subprocess.Popen(cmd, cwd='../weatherscrapy')
        except OSError as oe:
            # 実行できた分だけDB登録するため、ログ出力して処理継続
            logger.error('Execute scrapy failed: %s', oe)
            continue
        except ValueError as ve:
            # 実行できた分だけDB登録するため、ログ出力して処理継続
            logger.error('Execute scrapy failed: %s', ve)
            continue
        else:
            logger.info('Execute scrapy has succeeded.')
            weather_file_names[channel.weather_type].append(
                spider + file_name_suffix
            )

        # weatherscrapy実行完了をしばし待つ。(お天気情報ファイル出力完了後にDB登録する必要があるため。)
        # いらないかもしれない。テストの書き方がわからんし・・・。。
        while proc.poll() is None:
            continue

    logger.debug('weather_file_names: %s', weather_file_names)
    logger.info('***** Ended %s. *****', 'execute_scrapy')
    return weather_file_names


def _get_scrapy_command(spider, channel_id, file_name_suffix):
    """
    scrapy実行用のコマンドを作成する。
    """
    cmd_string = 'scrapy crawl {spider} -a channel_id={channel_id} -a file_name_suffix={file_name_suffix}'

    cmd = cmd_string.format(
                            spider=spider,
                            channel_id=channel_id,
                            file_name_suffix=file_name_suffix
                           ).split(' ')

    return cmd


def register_scrapped_weather(area_id, weather_file_names):
    """
    天気予報永続化処理。
    CSV出力された天気予報を読み込み、DBへ登録する。

    @param area_id  : int。 Areaモデルのid。選択した天気予報取得対象地域を表すモデルArea.id。
    @param weather_file_names
                    : Dict{Channel.weather_type:[file_names]}。
                       * Key -> Channel.weather_type、
                       * Value -> 読み込み対象のお天気情報CSVファイル名(拡張子は不要)のリスト
                      登録対象のお天気情報CSVファイル名の辞書。
                      例) {Channel.TYPE_WEEKLY:['abc', 'ddd']}
    """
    logger.info('***** Started %s. *****', 'register_scrapped_weather')

    # 週間天気ファイル名リスト・今日明日天気ファイル名リストの両方がなければ処理終了。
    if len(weather_file_names[Channel.TYPE_WEEKLY]) == 0 and \
            len(weather_file_names[Channel.TYPE_DAILY]) == 0:
        logger.info('We did not register because weather_file_names is empty.')
        logger.info('***** Ended %s. *****', 'register_scrapped_weather')
        return

    # 登録前に、既存データはdeleteしておく。
    _delete_weather(area_id)

    # まずは、週間天気予報の登録。
    _register_to_weather(weather_file_names)

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


def _is_useless(file_path):
    """
    ファイルが以下の場合Trueを返す。
     * 存在しない
     * アクセスできない
     * 0バイト
    """
    try:
        if os.path.getsize(file_path) == 0:
            # 0バイトの場合
            return True
    except OSError:
        # 存在しない、アクセスできない場合
        return True

    return False


def _register_to_weather(weather_file_names):
    """
    週間天気予報の登録処理。
    """
    for file_name in weather_file_names[Channel.TYPE_WEEKLY]:

        file_path = _get_weather_file_path(file_name)
        if _is_useless(file_path):
            # 無用なファイルはスキップ
            logger.info('Skiped useless file: "%s".', file_path)
            continue

        created_count = 0  # <- log出力にしか使わない

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
                created_count += 1

        logger.info('Registered "%s"records to Weather: "%s".', str(created_count), file_path)


def _register_to_hourlyweather(weather_file_names):
    """
    今日明日天気予報の登録処理
    """
    # Yahoo天気、ウェザーニューズ・・・週間天気=>降水確率、今日天気=>降水量
    # 日本気象協会、goo天気・・・週間天気=>降水確率、今日天気=>降水確率

    for file_name in weather_file_names[Channel.TYPE_DAILY]:

        file_path = _get_weather_file_path(file_name)
        if _is_useless(file_path):
            # 無用なファイルはスキップ
            logger.info('Skiped useless file: "%s".', file_path)
            continue

        created_count = 0  # <- log出力にしか使わない

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            logger.debug('Opened csvfile: %s', file_path)
            reader = csv.reader(csvfile)
            next(reader)  # ヘッダーレコードはスキップ

            # 現在時刻に一番近いレコードを見つけた場合True。
            # HourlyWeather用の天気予報データでWeatherを登録時、「今日の天気」は現在時刻に一番近い時刻の天気を登録するために必要。
            found_close_time = False

            for row in reader:

                hourlyweather_channel = Channel.objects.get(id=row[2])  # row[2]=>Channel.id

                # --- Weatherの追加登録 ---
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
                created_count += 1

        logger.info('Registered "%s"records to HourlyWeather: "%s".', str(created_count), file_path)


def _add_weather_registration(hourlyweather_channel, row, found_close_time):
    """
    該当日付のWeatherが存在しない場合は、HourlyWeather用の天気予報データでWeatherを登録する
    """
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
    if created:
        logger.info('added Weather: "%s".', str(row[3]),)
    else:
        found_close_time = _update_weather_close_current_time(weather, row, found_close_time)
        _update_temperatures_at_max_and_min(weather, row)

        # Weatherの変更を保存
        weather.save()

    return weather, found_close_time


def _update_weather_close_current_time(weather, row, found_close_time):
    """
    今日の天気に限り、最高気温、最低気温以外は現在時刻に一番近いレコードで更新する。
    現在時刻に一番近いレコードを見つけた場合は、Trueを返す。
    """
    current_row_datetime = datetime.strptime(row[3] + row[7], '%Y-%m-%d%H:%M:%S')

    if (_get_now() <= current_row_datetime) and (not(found_close_time)):
        weather.weather = row[8]
        weather.wind_speed = row[10]
        weather.chance_of_rain = _get_chance_of_rain(row[1])
        return True

    return found_close_time


def _update_temperatures_at_max_and_min(weather, row):
    """
    最高気温、最低気温は1日の内で最も高い気温と最も低い気温で更新する
    """
    rounded_temperatures = _get_rounded_temperatures(row[6])
    if int(weather.highest_temperatures) < rounded_temperatures:
        weather.highest_temperatures = rounded_temperatures
    if int(weather.lowest_temperatures) > rounded_temperatures:
        weather.lowest_temperatures = rounded_temperatures


def _get_rounded_temperatures(str_temperatures):
    """
    少数第一位を四捨五入して整数を返す
    """
    return round(Decimal(str_temperatures))


def _get_chance_of_rain(row_chance_of_rain):
    """
    降水確率が空の場合、999を返す
    """
    if row_chance_of_rain == '':
        chance_of_rain = 999  # 999は画面表示時に'---'に置換
    else:
        chance_of_rain = row_chance_of_rain
    return chance_of_rain


def _get_precipitation(row_precipitation):
    """
    降水量が空の場合、999を返す
    """
    if row_precipitation == '':
        precipitation = 999  # 999は画面表示時に'---'に置換
    else:
        precipitation = row_precipitation
    return precipitation


def _get_now():
    return datetime.now()
