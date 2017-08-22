from django.template.response import TemplateResponse
from django.shortcuts import redirect, get_object_or_404

import logging

from weather.models import Channel
from .forms import ChannelRegistrationForm, ChannelEditForm

# TODO:
#   * チャンネル登録機能に確認画面を足す。
#   * Areaを登録機能をつくる。


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
        # 入力されたチャンネルを登録する。
        form = ChannelRegistrationForm(data=request.POST)

        if form.is_valid():
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
        # チャンネル変更画面を初期表示する
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
    Channel.objects.filter(
        area=channel.area,
        name=channel.name,
    ).delete()

    logger.info('Deleted to Channel: "%s - %s"', channel.area, channel.get_name_display())
    logger.info('Redirect "%s".', 'channel:list')
    logger.info('***** Ended %s. *****', 'delete_channel')
    return redirect('channel:list')
