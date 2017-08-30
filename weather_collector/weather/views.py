from django.template.response import TemplateResponse
from django.shortcuts import redirect  # , get_object_or_404
from django.contrib import messages

import logging
from datetime import date

from .models import Area, Channel, Weather, HourlyWeather
from .forms import AreaChoiceForm
from .import scrapyutils


logger = logging.getLogger(__name__)


def get_today():
    return date.today()


def weekly_weather(request, area_id):
    """
    選択したエリアの、週間天気予報を表示する。
    """
    logger.info('***** Started %s. *****', 'weekly_weather')

    # 時刻は00:00:00で取得
    today = get_today()

    area = Area.objects.get(id=area_id)
    channels = Channel.objects.filter(
                            area_id=area_id,
                            weather_type=Channel.TYPE_WEEKLY
                        ).order_by(
                            'id'
                        )

    all_weekly_weather = {}
    if not channels:
        # チャンネルが存在しない場合は、週間天気予報画面にチャンネル登録を促すメッセージを表示。
        messages.warning(request, 'チャンネルが登録されていません。')
        logger.info('Channel was not registered.')
    else:
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
                                {
                                    'area': area,
                                    'all_weekly_weather': all_weekly_weather
                                }
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


def select_area(request):
    """
    『お天気エリア選択』画面

    * POSTでアクセスされた場合
     『お天気エリア選択』画面で選択した"Area"に紐づくすべての"Channel"の天気予報を取得し、DBへ登録する。
    * GETでアクセスされた場合
     『お天気エリア選択』画面を表示する。
    """
    logger.info('***** Started %s. *****', 'select_area')
    if request.method == 'POST':
        # 選択された地域を取得
        form = AreaChoiceForm(data=request.POST)
        if form.is_valid():
            area_id = form.cleaned_data['selected_area'].id
            logger.info('area_id: %d was selected.', area_id)

            if 'scrapy_weather' in request.POST:
                # 「天気予報を取得」ボタンを押下時処理。
                logger.info('"scrapy_weather" was requested.')

                channels = Channel.objects.filter(
                                area=area_id
                            ).order_by(
                                'id'
                            )
                if not channels:
                    # チャンネルが存在しない場合は、スクレイピングは行わない。
                    logger.info('Channel was not registered.')
                else:
                    # 天気予報取得対象URL、CSV出力
                    scrapyutils.output_target_urls_to_csv(channels)

                    # weatherscrapy実行
                    file_names = scrapyutils.execute_scrapy(channels)

                    # CSV出力された天気予報をDBへ登録する。
                    scrapyutils.register_scrapped_weather(area_id, file_names)

            # 「天気予報を取得」ボタン、「週間天気予報を表示」ボタンともに週間天気予表示viewにリダイレクト
            logger.info('Redirect "%s".', 'weather:weekly')
            logger.info('***** Ended %s. *****', 'select_area')

            return redirect('weather:weekly', area_id=area_id)
        else:
            # バリデーションエラー時は、『お天気エリア選択画面』に戻る
            logger.info('ValidationError "%s".', 'AreaChoiceForm')
    else:
        # 『お天気エリア選択画面』初期表示処理
        form = AreaChoiceForm()

    logger.info('Response template "%s".', 'weather/select_area.html')
    logger.info('***** Ended %s. *****', 'select_area')

    return TemplateResponse(request, 'weather/select_area.html', {'form': form})
