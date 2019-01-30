from django import forms
from django.utils import timezone
from django.utils.translation import gettext as _

from martor.fields import MartorFormField

from stories.models import Story
from authors.models import Author

class InspiredByIdField(forms.ModelChoiceField):
    widget = forms.CheckboxInput

    def to_python(self, value):
        if value:
            return self.queryset.first()
        return None


class StoryForm(forms.ModelForm):
    """ Used to create or edit a story.  It picks up on inspired_by via 2 mechanisms """

    text = MartorFormField(label=_('Story'), required=True)
    author = forms.ModelChoiceField(label=_('Pseudonym'), queryset=None, required=True)
    private = forms.BooleanField(required=False)
    inspired_by = InspiredByIdField(required=False, queryset=None)

    class Meta:
        model = Story
        fields = ['author', 'title', 'tagline', 'text', 'inspired_by', 'private']

    def get_inspired_by_id(self):
        """ We can get a value for inspired_by from the initial or the instance and it might be an
              int or an instance.  Hide all of that here."""
        if self.instance and self.instance.inspired_by:
            return self.instance.inspired_by.id
        else:
            inspired_by = self.initial.get('inspired_by',
                                           self.data.get('inspired_by', None))
            if inspired_by:
                if isinstance(inspired_by, Story):
                    return inspired_by.id
                else:
                    return int(inspired_by)

        return None


    def __init__(self, *args, user, **kwargs):
        super(StoryForm, self).__init__(*args, **kwargs)

        width = Story._meta.get_field('title').max_length
        self.fields['title'].widget.attrs['size'] = width
        self.fields['tagline'].widget.attrs['size'] = width
        self.fields['text'].widget.attrs['cols'] = width

        self.fields['author'].queryset = Author.objects.for_user(user)

        inspired_by_id = self.get_inspired_by_id()

        if inspired_by_id:
            self.fields['inspired_by'].queryset = Story.objects.filter(pk=inspired_by_id)
        else:
            # The user cannot supply a value for inspired by (only check the box)
            #   Remove the field if there is no inspired_by value to check the box for
            del self.fields['inspired_by']


    def save(self, commit=True):

        obj = super(StoryForm, self).save(commit=False)

        if self.cleaned_data['private']:
            obj.published_at = None
        elif not obj.published_at:
            obj.published_at = timezone.now()

        if commit:
            obj.save()
            self.save_m2m()
        return obj
