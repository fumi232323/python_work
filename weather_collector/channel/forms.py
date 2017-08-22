from django import forms
from django.utils.translation import ugettext_lazy as _

from weather.models import Area, Channel


class ChannelRegistrationForm(forms.Form):
    """
    チャンネル登録用のフォーム
    """
    queryset = Area.objects.order_by('id')

    area = forms.ModelChoiceField(label='地域', queryset=queryset)
    channel = forms.ChoiceField(label='チャンネル', choices=Channel.CHANNEL_CHOICES)

    weather_type_weekly_url = forms.URLField(max_length=255, label='週間天気予報のURL')
    weather_type_daily_url = forms.URLField(max_length=255, label='今日の天気予報のURL')

    def clean(self):
        cleaned_data = super(ChannelRegistrationForm, self).clean()
        area = cleaned_data.get("area")
        channel = cleaned_data.get("channel")

        channels = Channel.objects.select_related(
                'area'
            ).filter(
                area=area,
                name=channel,
            )
        if channels:
            raise forms.ValidationError(
                "[{} - {}] チャンネルはすでに登録されています。".format(
                    channels[0].area.name,
                    channels[0].get_name_display(),
                )
            )


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