from django import forms
from django.utils.translation import gettext as _

from markdownx.fields import MarkdownxFormField

from .models import Entry

class EntryForm(forms.ModelForm):
    """ Used to create or edit a post """

    id = forms.HiddenInput()
    title = forms.CharField()
    text = MarkdownxFormField()
    author = forms.ModelChoiceField(label=_('Pseudonym'), queryset=None)
    private = forms.BooleanField(required=False)

    class Meta:
        model = Entry
        fields = ['author', 'title', 'text', 'id',]
