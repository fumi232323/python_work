from django import forms
from django.utils.translation import ugettext_lazy as _

from weather.models import Area, Channel


class ChannelRegistrationForm(forms.Form):
    """
    チャンネル登録用のフォーム
    """
    area_queryset = Area.objects.order_by('id')
    list_channel_choices = list(Channel.CHANNEL_CHOICES)
    list_channel_choices.insert(0, ('', '---------'))

    area = forms.ModelChoiceField(label='地域', queryset=area_queryset)
    channel = forms.ChoiceField(label='チャンネル', choices=list_channel_choices)

    weather_type_weekly_url = forms.URLField(max_length=255, label='週間天気予報のURL')
    weather_type_daily_url = forms.URLField(max_length=255, label='今日の天気予報のURL')


class ChannelEditForm(forms.ModelForm):
    """
    チャンネル変更用のフォーム
    """
    class Meta:
        model = Channel
        fields = [
            'url',
        ]
        labels = {
            'url': _('URL'),
        }


class AreaRegistrationForm(forms.ModelForm):
    """
    地域登録用のフォーム
    """
    class Meta:
        model = Area
        fields = [
            'name',
        ]
