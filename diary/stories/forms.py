from django import forms
from django.utils.translation import gettext as _

from martor.fields import MartorFormField

from .models import Story

class StoryForm(forms.ModelForm):
    """ Used to create or edit a post """

    text = MartorFormField(label=_('Story'), required=True)
    author = forms.ModelChoiceField(label=_('Pseudonym'), queryset=None, required=True)
    private = forms.BooleanField(required=False)

    class Meta:
        model = Story
        fields = ['author', 'title', 'tagline', 'text', 'id', 'inspired_by',]
        widgets = {
            'inspired_by': forms.CheckboxInput(check_test=bool),
        }


    def __init__(self, *args, **kwargs):
        super(StoryForm, self).__init__(*args, **kwargs)

        width = Story._meta.get_field('title').max_length
        self.fields['title'].widget.attrs['size'] = width
        self.fields['text'].widget.attrs['cols'] = width
