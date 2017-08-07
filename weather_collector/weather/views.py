from django.shortcuts import render
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse

from datetime import datetime,date
import subprocess
import csv

from .models import  Area, Channel, Weather, HourlyWeather
from .forms import AreaChoiceForm

# TODO:
#   * サイト(Channel)登録時に両方URLを登録させる機能をつくる。
#   　∟登録させる項目: AreaとChannel(サイト)名と週間天気のURL、詳細天気のURL
#   * 詳細天気取得のスパイダー
#   * 過去天気表示ページも作りたい
#   * コードチェックのやつ、PEP8だったか、flask8だったかいうやつやらんと。
#   * ログ出力
#   * テスト

def weekly_weather(request, area_id):
    """
    選択したエリアの週間天気予報を表示する。
    """
    # 今日の日付(時刻は0時0分0秒で取得)
    today = date.today()
    
    # 今日以降の週間天気を全Channel分(登録されている分全部)取得。
    # Channelを登録した順 > 日付の昇順
    channels = Channel.objects.filter(
                            area_id=area_id
                        ).order_by(
                            'id'
                        )
    
    all_weekly_weather = {}
    for channel in channels:
        weekly_weather_per_channel = Weather.objects.filter(
                            area=area_id, channel=channel.id, date__gte=today
                        ).order_by(
                            'channel_id', 'date'
                        ).extra(
                            select={
                                'daily_weather_count': 'SELECT COUNT(*) FROM weather_hourlyweather WHERE weather_weather.id = weather_hourlyweather.date_id'
                            },
                        )
        all_weekly_weather[channel.get_name_display()] = weekly_weather_per_channel
    
    return TemplateResponse(request, 
                            'weather/weekly.html',
                            {'all_weekly_weather': all_weekly_weather}
                           )

def daily_weather(request, weather_id):
    """
    選択したChannel・日付の、時間ごと天気予報を表示する。
    """
    # 登録されている時間天気予報を全部取得。
    daily_weather = HourlyWeather.objects.filter(
                            date=weather_id
                        ).order_by(
                            'time'
                        )
    weather = Weather.objects.select_related('area', 'channel').get(
                            id=weather_id
                        )
        
    return TemplateResponse(request, 
                            'weather/daily.html',
                            {'daily_weather': daily_weather,
                             'weather':weather}
                           )

def __output_target_urls_to_csv(channels):
    """
    TODO: これはあとで★クラスにまとめる。
    天気予報取得対象URL、CSV出力処理。
    　※scrapyスパイダーがここで出力されたCSVファイルのURLを使用してスクレイピングする。
     
    @param channels : QuerySet<Channel>。 Channelモデルのクエリセット。
    """
    SPIDER_NAMES = {
        # CHANNEL:(WEEKLY, DAILY)
        0:('yahoo_weekly_weather', 'yahoo_daily_weather'),
        1:('weathernews_weekly_weather', 'weathernews_daily_weather'),
        2:('tenkijp_weekly_weather', 'tenkijp_daily_weather'),
    }
    
    urls_file_path_string = '../weatherscrapy/data/urls/{}.csv'
    
    # urls = []
    for channel in channels:
        # urls.append(channel.url)
        file_name = SPIDER_NAMES[channel.name][channel.weather_type]
        urls_file_path = urls_file_path_string.format(file_name) 
        with open(urls_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([channel.url])

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
    
    SPIDER_NAMES = {
        # CHANNEL:(WEEKLY, DAILY)
        0:('yahoo_weekly_weather', 'yahoo_daily_weather'),
        1:('weathernews_weekly_weather', 'weathernews_daily_weather'),
        2:('tenkijp_weekly_weather', 'tenkijp_daily_weather'),
    }
    
    cmd_string = 'scrapy crawl {spider} -a area_id={area_id} -a channel_id={channel_id} -a file_name_suffix={file_name_suffix}'
    
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
                                area_id=channel.area.id, 
                                channel_id=channel.id,
                                file_name_suffix=file_name_suffix
                               ).split(' ')
        print('★')
        print(cmd)
        # TODO: 実行したコマンドをログ出力
        try:
            proc = subprocess.Popen(cmd, cwd='../weatherscrapy')
        except OSError:
            # TODO: weatherscrapy失敗の旨をログ出力
            pass
        except ValueError:
            # TODO: weatherscrapy失敗の旨をログ出力
            pass
        else:
            # TODO: ひとまず呼び出しは正常終了の旨をログ出力
            weather_file_names[channel.weather_type].append(spider + file_name_suffix)
            
        # weatherscrapy実行完了をしばし待つ。
        while proc.poll() is None:
            continue
        
    return weather_file_names

def __register_weather(area_id, weather_file_names):
    """
    天気予報永続化処理。
    CSV出力された天気予報を読み込み、DBへ登録する。
    
    @param area_id  : int。 Areaモデルのid。選択した天気予報取得対象の地域を表すモデルArea.id。
    @param weather_file_names 
                    : Dict{Channel.weather_type:[file_names]}。
                      KeyにChannel.weather_type、Valueに読み込み対象のCSVファイル名(拡張子は不要)のリストを持つ辞書。
                        例) {Channel.TYPE_WEEKLY:['abc', 'ddd']}
    """ 
    weather_file_path_string = '../weatherscrapy/data/weather/{}.csv'
    
    # 登録前に、既存データはdeleteしておく。
    area = Area.objects.get(id=area_id)
    Weather.objects.filter(area=area).delete()

    # まずは、週間天気予報の登録。
    for file_name in weather_file_names[Channel.TYPE_WEEKLY]:
        file_path = weather_file_path_string.format(file_name)
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            for row in reader:
                # 天気予報部分が「---」の行はDB登録する必要がないので、スキップ。
                if not row[5].isdigit():
                    continue
                    
                channel = Channel.objects.get(id=row[3]) # TODO: ほんとはファイルごとに1回でいいんだけど・・・・
                Weather.objects.create(
                    area=area,
                    chance_of_rain=row[2],
                    channel=channel,
                    date=row[4],
                    highest_temperatures=row[5],
                    lowest_temperatures=row[6],
                    weather=row[7],
                    wind_speed=None,
                )
                
    # 次に、今日明日天気予報の登録。
    # TODO: HourlyWeather時、Weatherがない子はHourlyWeatherの1レコード目をWeatherとして登録しておく。
    # Yahoo天気とウェザーニューズは、今日天気=>降水量、週間天気=>降水確率、になるので注意
    # 日本気象協会 tenki.jpとgoo天気は、今日天気=>降水確率、週間天気=>降水確率、になるので注意
    
    
def select_area(request):
    """
    天気予報サイトにアクセスして、天気予報情報を取得する。
    
    POSTでアクセスされた場合  : 『お天気エリア選択』画面選択したAreaに紐づくすべてのChannel分天気予報を取得し、DBへ保存する。
    GETでアクセスされた場合   : 『お天気エリア選択』画面を表示する。
    """
    if request.method == 'POST':
        ## エリアを選択して、表示ボタンを押下時処理。
        form = AreaChoiceForm(data=request.POST)
        form.is_valid()
        area_id = form.cleaned_data['selected_area'].id
        
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

        return redirect('weather:weekly', area_id=area_id)
    else:
        ## 『お天気エリア選択画面』初期表示処理
        form = AreaChoiceForm()
        return TemplateResponse(request, 'weather/area.html',
                               {'form':form})
    