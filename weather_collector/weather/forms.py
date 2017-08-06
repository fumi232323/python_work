from django import forms

from .models import Area

class AreaChoiceForm(forms.Form):
    
    queryset = Area.objects.order_by(
                            '-id'
                        )
    selected_area = forms.ModelChoiceField(label='地域', queryset=queryset)

# TODO: サイト(Channel)登録フォームを作ること。
# 登録させる項目: AreaとChannel(サイト)名と週間天気のURL、詳細天気のURL