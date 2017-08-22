from django.template.response import TemplateResponse
from django.shortcuts import redirect, get_object_or_404

import logging

from weather.models import Channel
from .forms import ChannelRegistrationForm, ChannelEditForm, AreaRegistrationForm

# TODO:
#   * 登録完了とかのインフォメーションメッセージを表示できるようにする。
#   * テスト書く


logger = logging.getLogger(__name__)


def channel_list(request):
    """
    登録済みのチャンネルリストを表示する。
    """
    logger.info('***** Started %s. *****', 'channel_list')

    channels = Channel.objects.select_related(
                        'area'
                    ).order_by(
                        'area_id',
                        'name',
                        'weather_type',
                    )

    logger.info('Response template "%s".', 'channel/list.html')
    logger.info('***** Ended %s. *****', 'channel_list')
    return TemplateResponse(
                                request,
                                'channel/list.html',
                                {
                                   'channels': channels,
                                }
                            )


def register_channel(request):
    """
    チャンネルを新規登録する
    """
    logger.info('***** Started %s. *****', 'register_channel')
    if request.method == 'POST':

        form = ChannelRegistrationForm(data=request.POST)

        if form.is_valid():
            # 確認画面からのPOSTの場合、チャンネルを登録する。
            if 'confirmed' in request.POST and request.POST['confirmed'] == '1':
                # 「登録する」ボタン押下時
                if 'register' in request.POST:
                    # 週間天気の登録
                    Channel.objects.create(
                        area=form.cleaned_data['area'],
                        name=form.cleaned_data['channel'],
                        weather_type=Channel.TYPE_WEEKLY,
                        url=form.cleaned_data['weather_type_weekly_url'],
                    )

                    # 今日の天気の登録
                    Channel.objects.create(
                        area=form.cleaned_data['area'],
                        name=form.cleaned_data['channel'],
                        weather_type=Channel.TYPE_DAILY,
                        url=form.cleaned_data['weather_type_daily_url'],
                    )

                    logger.info('Registered to Channel.')
                    logger.info('Redirect "%s".', 'channel:list')
                    logger.info('***** Ended %s. *****', 'register_channel')
                    return redirect('channel:list')
                else:
                    # 「戻る」ボタン押下時は入力画面へ戻る
                    logger.info('"back" was requested.')
            else:
                # 入力画面からのPOSTの場合、確認画面を表示する。
                # 表示用のチャンネル名。何か変な気がする。自信ないけどとりあえずこれで動く。
                channel_display = Channel.CHANNEL_CHOICES[int(form.cleaned_data['channel'])][1]

                logger.info('Response template "%s".', 'channel/register_confirm.html')
                logger.info('***** Ended %s. *****', 'register_channel')
                return TemplateResponse(
                                            request,
                                            'channel/register_confirm.html',
                                            {
                                                'form': form,
                                                'modified': form.cleaned_data,
                                                'channel_display': channel_display,
                                            }
                                        )

        else:
            logger.info('ValidationError "%s".', 'ChannelRegistrationForm')
    else:
        # チャンネル登録画面を初期表示する
        form = ChannelRegistrationForm()

    logger.info('Response template "%s".', 'channel/register.html')
    logger.info('***** Ended %s. *****', 'register_channel')
    return TemplateResponse(
                                request,
                                'channel/register.html',
                                {
                                    'form': form,
                                }
                            )


def update_channel(request, channel_id):
    """
    チャンネルを変更する
    """
    logger.info('***** Started %s. *****', 'update_channel')

    channel = get_object_or_404(Channel, id=channel_id)

    if request.method == 'POST':
        # チャンネルを変更する
        form = ChannelEditForm(data=request.POST, instance=channel)
        if form.is_valid():
            form.save()

            logger.info('Updated to Channel.')
            logger.info('Redirect "%s".', 'channel:list')
            logger.info('***** Ended %s. *****', 'update_channel')
            return redirect('channel:list')
        else:
            logger.info('ValidationError "%s".', 'ChannelEditForm')

    else:
        # 『チャンネル変更』画面を初期表示する
        form = ChannelEditForm(instance=channel)

    logger.info('Response template "%s".', 'channel/edit.html')
    logger.info('***** Ended %s. *****', 'update_channel')
    return TemplateResponse(
                                request,
                                'channel/edit.html',
                                {
                                    'form': form,
                                    'channel': channel,
                                }
                            )


def delete_channel(request, channel_id):
    """
    チャンネルを削除する
    """
    logger.info('***** Started %s. *****', 'delete_channel')
    channel = get_object_or_404(Channel, id=channel_id)

    # チャンネルを削除する
    # 週間天気用と今日の天気用の両方同時に削除する。
    Channel.objects.filter(
                            area=channel.area,
                            name=channel.name,
                        ).delete()

    logger.info('Deleted to Channel: "%s - %s"', channel.area, channel.get_name_display())
    logger.info('Redirect "%s".', 'channel:list')
    logger.info('***** Ended %s. *****', 'delete_channel')
    return redirect('channel:list')


def register_area(request):
    """
    地域を登録する
    """
    logger.info('***** Started %s. *****', 'register_area')

    if request.method == 'POST':
        # 地域を登録する
        form = AreaRegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()

            logger.info('Registed to Area.')
            logger.info('Redirect "%s".', 'channel:register')
            logger.info('***** Ended %s. *****', 'register_area')
            return redirect('channel:register')
        else:
            logger.info('ValidationError "%s".', 'AreaRegistrationForm')
    else:
        # 『地域を登録する』画面を初期表示する
        form = AreaRegistrationForm()

    logger.info('Response template "%s".', 'channel/register_area.html')
    logger.info('***** Ended %s. *****', 'register_area')
    return TemplateResponse(
                                request,
                                'channel/register_area.html',
                                {
                                    'form': form,
                                }
                            )
