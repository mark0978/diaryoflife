from django import forms
from django.utils import timezone
from django.utils.translation import gettext as _

from martor.fields import MartorFormField

from authors.models import Author

class AuthorForm(forms.ModelForm):
    """ Used to create or edit a story.  It picks up on inspired_by via 2 mechanisms """

    bio_text = MartorFormField(label=_('Biography'), required=False)

    class Meta:
        model = Author
        fields = ['name', 'bio_text', 'avatar']

    def __init__(self, *args, user, **kwargs):
        super(AuthorForm, self).__init__(*args, **kwargs)

        width = Author._meta.get_field('name').max_length
        self.fields['name'].widget.attrs['size'] = width
        self.fields['bio_text'].widget.attrs['cols'] = width

        self.user = user


    def save(self, commit=True):
        """ Add the user to the object before we persist it """
        obj = super(AuthorForm, self).save(commit=False)
        obj.user = self.user

        if commit:
            obj.save()
            self.save_m2m()
        return obj
