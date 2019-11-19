from django import forms
from .models import Drawing


class DrawingForm(forms.ModelForm):

    class Meta:
        model = Drawing
        fields = ('location',)
