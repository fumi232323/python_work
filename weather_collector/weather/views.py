from django.template.response import TemplateResponse
from django.shortcuts import redirect  # , get_object_or_404

import logging
from datetime import datetime, date
import subprocess
import csv

from .models import Area, Channel, Weather, HourlyWeather
from .forms import AreaChoiceForm

# TODO:
#   * サイト(Channel)登録時に両方URLを登録させる機能をつくる。
#   　∟登録させる項目: AreaとChannel(サイト)名と週間天気のURL、詳細天気のURL
#   * 過去天気表示ページも作りたい
#   * テスト8/9

logger = logging.getLogger(__name__)


def weekly_weather(request, area_id):
    """
    選択したエリアの、週間天気予報を表示する。
    """
    logger.info('***** Started %s. *****', 'weekly_weather')

    # 時刻は00:00:00で取得
    today = date.today()

    channels = Channel.objects.filter(
                            area_id=area_id,
                            weather_type=Channel.TYPE_WEEKLY
                        ).order_by(
                            'id'
                        )

    all_weekly_weather = {}
    for channel in channels:
        weekly_weather_per_channel = Weather.objects.filter(
                            channel=channel.id,
                            date__gte=today
                        ).order_by(
                            'channel_id',
                            'date'
                        ).extra(
                            select={
                                'daily_weather_count':
                                'SELECT COUNT(*) FROM weather_hourlyweather WHERE weather_weather.id = weather_hourlyweather.date_id'
                            },
                        )
        all_weekly_weather[channel.get_name_display()] = weekly_weather_per_channel

    logger.info('Response template "%s".', 'weather/weekly.html')
    logger.info('***** Ended %s. *****', 'weekly_weather')

    return TemplateResponse(
                                request,
                                'weather/weekly.html',
                                {'all_weekly_weather': all_weekly_weather}
                            )


def daily_weather(request, weather_id):
    """
    選択した日付の、時間ごと天気予報を表示する。
    """
    logger.info('***** Started %s. *****', 'daily_weather')

    daily_weather = HourlyWeather.objects.filter(
                            date=weather_id
                        ).order_by(
                            'time'
                        )
    weather = Weather.objects.select_related(
                            'area',
                            'channel'
                        ).get(
                            id=weather_id
                        )

    logger.info('Response template "%s".', 'weather/daily.html')
    logger.info('***** Ended %s. *****', 'daily_weather')
    return TemplateResponse(
                                request,
                                'weather/daily.html',
                                {
                                    'daily_weather': daily_weather,
                                    'weather': weather
                                }
                            )


def __output_target_urls_to_csv(channels):
    """
    TODO: これはあとで★クラスにまとめる。
    天気予報取得対象URLのCSV出力処理。
    　※scrapyスパイダーが、ここで出力されたCSVファイルのURLを使用してスクレイピングする。

    @param channels : QuerySet<Channel>。 Channelモデルのクエリセット。
    """
    logger.info('***** Started %s. *****', '__output_target_urls_to_csv')

    SPIDER_NAMES = {
        # CHANNEL:(WEEKLY, DAILY)
        0: ('yahoo_weekly_weather', 'yahoo_daily_weather'),
        1: ('weathernews_weekly_weather', 'weathernews_daily_weather'),
        2: ('tenkijp_weekly_weather', 'tenkijp_daily_weather'),
    }

    urls_file_path_string = '../weatherscrapy/data/urls/{}.csv'

    # urls = []
    for channel in channels:
        # urls.append(channel.url)
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


def __execute_scrapy(channels):
    """
    TODO: これはあとで★クラスにまとめる。
    weatherscrapy実行処理。
    指定された天気予報サイトから天気予報を取得し、CSV出力する。

    @param channels : QuerySet<Channel>。 Channelモデルのクエリセット。
    @return         : Dict{Channel.weather_type:[file_names]}。
                      KeyにChannel.weather_type、Valueに出力した天気予報CSVファイル名(拡張子は不要)のリストを持つ辞書。
                        例) {Channel.TYPE_WEEKLY:['abc', 'ddd']}
    """
    logger.info('***** Started %s. *****', '__execute_scrapy')

    SPIDER_NAMES = {
        # CHANNEL:(WEEKLY, DAILY)
        0: ('yahoo_weekly_weather', 'yahoo_daily_weather'),
        1: ('weathernews_weekly_weather', 'weathernews_daily_weather'),
        2: ('tenkijp_weekly_weather', 'tenkijp_daily_weather'),
    }

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
            pass
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


def __register_weather(area_id, weather_file_names):
    """
    天気予報永続化処理。
    CSV出力された天気予報を読み込み、DBへ登録する。

    @param area_id  : int。 Areaモデルのid。選択した天気予報取得対象地域を表すモデルArea.id。
    @param weather_file_names
                    : Dict{Channel.weather_type:[file_names]}。
                      KeyにChannel.weather_type、Valueに読み込み対象のCSVファイル名(拡張子は不要)のリストを持つ辞書。
                        例) {Channel.TYPE_WEEKLY:['abc', 'ddd']}
    """
    logger.info('***** Started %s. *****', '__register_weather')

    weather_file_path_string = '../weatherscrapy/data/weather/{}.csv'

    # 登録前に、既存データはdeleteしておく。
    area = Area.objects.get(id=area_id)
    channels = Channel.objects.filter(area=area)
    Weather.objects.filter(channel__in=channels).delete()
    # HourlyWeather.objects.filter(area=area).delete()
    # ↑TODO:Weatherをdeleteするとたぶん全部消えるに違いない => ちと確認

    # まずは、週間天気予報の登録。
    for file_name in weather_file_names[Channel.TYPE_WEEKLY]:
        file_path = weather_file_path_string.format(file_name)
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            logger.debug('Opened csvfile: %s', file_path)
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                # 天気予報部分が「---」の行はDB登録する必要がないので、スキップ。
                if not row[6].isdigit():
                    continue
                # TODO: ほんとはファイルごとに1回でいいんだけど・・・
                channel = Channel.objects.get(id=row[2])
                Weather.objects.create(
                    channel=channel,
                    date=row[3],
                    weather=row[6],
                    highest_temperatures=row[4],
                    lowest_temperatures=row[5],
                    chance_of_rain=row[1],
                    wind_speed=None,
                )

        logger.info('Registered to Weather: "%s".', file_path)

    # 次に、今日明日天気予報の登録。
    # TODO: HourlyWeather時、Weatherがない子はHourlyWeatherの1レコード目をWeatherとして登録しておく。
    # Yahoo天気とウェザーニューズは、    週間天気=>降水確率、今日天気=>降水量、になるので注意
    # 日本気象協会 tenki.jpとgoo天気は、週間天気=>降水確率、今日天気=>降水確率、になるので注意

    # ひとまず、Yahoo版で書いてみる TODO: 明日8/9テストを書いてデバッグ
    for file_name in weather_file_names[Channel.TYPE_DAILY]:
        file_path = weather_file_path_string.format(file_name)
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            logger.debug('Opened csvfile: %s', file_path)
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                # TODO: ほんとはファイルごとに1回でいいんだけど・・・
                weather = Weather.objects.get(date=row[3])
                HourlyWeather.objects.create(
                    date=weather,
                    time=row[7],
                    weather=row[8],
                    temperatures=row[6],
                    humidity=row[4],
                    precipitation=row[5],
                    chance_of_rain=row[1],
                    wind_direction=row[9],
                    wind_speed=row[10],
                )

        logger.info('Registered to Weather: "%s".', file_path)
    logger.info('***** Ended %s. *****', '__register_weather')


def select_area(request):
    """
    『お天気エリア選択』画面

    POSTでアクセスされた場合  : 『お天気エリア選択』画面で選択した"Area"に紐づくすべての"Channel"の天気予報を取得し、
                              DBへ登録する。
    GETでアクセスされた場合   : 『お天気エリア選択』画面を表示する。
    """
    logger.info('***** Started %s. *****', 'select_area')
    if request.method == 'POST':
        # 選択された地域を取得
        form = AreaChoiceForm(data=request.POST)
        form.is_valid()
        area_id = form.cleaned_data['selected_area'].id

        if 'scrapy_weather' in request.POST:
            # 「天気予報を取得」ボタンを押下時処理。
            logger.info('"scrapy_weather" was requested.')

            channels = Channel.objects.filter(
                            area=area_id
                        ).order_by(
                            'id'
                        )
            # 天気予報取得対象URL、CSV出力
            __output_target_urls_to_csv(channels)

            # weatherscrapy実行
            file_names = __execute_scrapy(channels)

            # CSV出力された天気予報をDBへ登録する。
            __register_weather(area_id, file_names)

        logger.info('Redirect "%s".', 'weather:weekly')
        logger.info('***** Ended %s. *****', 'select_area')

        return redirect('weather:weekly', area_id=area_id)
    else:
        # 『お天気エリア選択画面』初期表示処理
        form = AreaChoiceForm()

        logger.info('Response template "%s".', 'weather/area.html')
        logger.info('***** Ended %s. *****', 'select_area')

        return TemplateResponse(request, 'weather/area.html', {'form': form})
