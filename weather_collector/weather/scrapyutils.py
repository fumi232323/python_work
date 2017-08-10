from datetime import datetime
import subprocess
import csv
import logging

from .models import Area, Channel, Weather, HourlyWeather


logger = logging.getLogger(__name__)
SPIDER_NAMES = {
    # CHANNEL:(WEEKLY, DAILY)
    0: ('yahoo_weekly_weather', 'yahoo_daily_weather'),
    1: ('weathernews_weekly_weather', 'weathernews_daily_weather'),
    2: ('tenkijp_weekly_weather', 'tenkijp_daily_weather'),
}


def output_target_urls_to_csv(channels):
    """
    天気予報取得対象URLのCSV出力処理。
    　※scrapyスパイダーが、ここで出力されたCSVファイルのURLを使用してスクレイピングする。

    @param channels : QuerySet<Channel>。 Channelモデルのクエリセット。
    """
    logger.info('***** Started %s. *****', '__output_target_urls_to_csv')

    urls_file_path_string = '../weatherscrapy/data/urls/{}.csv'

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

    weather_file_path_string = '../weatherscrapy/data/weather/{}.csv'

    # 登録前に、既存データはdeleteしておく。
    area = Area.objects.get(id=area_id)
    channels = Channel.objects.filter(area=area)
    Weather.objects.filter(channel__in=channels).delete()

    # まずは、週間天気予報の登録。TODO: 長たらしいので、別メソッドに切り分けたい。
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

    # 次に、今日明日天気予報の登録。TODO: 長たらしいので、別メソッドに切り分けたい。
    # TODO: HourlyWeather時、Weatherがない子はHourlyWeatherの1レコード目をWeatherとして登録しておく。
    # Yahoo天気とウェザーニューズは、    週間天気=>降水確率、今日天気=>降水量、になるので注意
    # 日本気象協会 tenki.jpとgoo天気は、週間天気=>降水確率、今日天気=>降水確率、になるので注意

    # 週間天気のURLと今日明日天気のURLは必ずセットで登録させるようにする予定だけど、
    # 今はセット登録画面を作ってないため、今日明日天気URLがない場合もあるので、なければリターン。
    if Channel.TYPE_DAILY not in weather_file_names:
        return

    # ひとまず、Yahoo版。ひとまず、HourlyWeatherを登録。
    for file_name in weather_file_names[Channel.TYPE_DAILY]:
        file_path = weather_file_path_string.format(file_name)
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            logger.debug('Opened csvfile: %s', file_path)
            reader = csv.reader(csvfile)
            next(reader)

            for row in reader:

                hourlyweather_channel=Channel.objects.get(id=row[2])
                
                # Weatherが存在しない場合は、HourlyWeather用の0時の天気で登録する
                weather_channel=Channel.objects.get(
                    area=hourlyweather_channel.area,
                    weather_type=Channel.TYPE_WEEKLY,
                    name=hourlyweather_channel.name
                )

                # TODO: 本当は、
                # * 最高気温、最低気温以外は現在時刻に一番近いレコードを登録したい
                # * chance_of_rain降水確率がある場合は、chance_of_rainを登録したい
                weather, created = Weather.objects.get_or_create(
                    channel=weather_channel,
                    date=row[3],
                    defaults={
                        'date': row[3],
                        'weather': row[8],
                        'highest_temperatures': row[6],
                        'lowest_temperatures': row[6],
                        'chance_of_rain': 999, # 999は画面表示時に'---'に置換
                        'wind_speed': row[10],
                    },
                )

                # とりあえず0時の天気を入れといて、ループしながら比較して、アップデートするのはどうだろう。
                # 性能悪くなっちゃうかな？
                if int(weather.highest_temperatures) < int(row[6]):
                    weather.highest_temperatures = row[6]
                    weather.save()
                if int(weather.lowest_temperatures) > int(row[6]):
                    weather.lowest_temperatures = row[6]
                    weather.save()

                # 降水量と降水確率はどちらか一方しかscrapyしないので、空のほうはNoneで登録する
                precipitation = row[5]
                chance_of_rain = row[1]
                if precipitation == '':
                    precipitation = None
                else:
                    chance_of_rain = None

                HourlyWeather.objects.create(
                    channel=hourlyweather_channel,
                    date=weather,
                    time=row[7],
                    weather=row[8],
                    temperatures=row[6],
                    humidity=row[4],
                    precipitation=precipitation,
                    chance_of_rain=chance_of_rain,
                    wind_direction=row[9],
                    wind_speed=row[10],
                )

        logger.info('Registered to HourlyWeather: "%s".', file_path)

    logger.info('***** Ended %s. *****', 'register_scrapped_weather')
