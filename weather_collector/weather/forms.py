from django import forms

from .models import Area


class AreaChoiceForm(forms.Form):

    queryset = Area.objects.order_by(
                            '-id'
                        )
    selected_area = forms.ModelChoiceField(label='地域', queryset=queryset)
