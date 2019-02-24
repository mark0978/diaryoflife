from django import forms
from django.utils import timezone
from django.utils.translation import gettext as _

from martor.fields import MartorFormField

from licenses.models import License
from stories.models import Story
from authors.models import Author

class PublishForm(forms.ModelForm):

    license = forms.ModelChoiceField(queryset=License.objects.active(), required=True)
    private = forms.BooleanField(required=False)

    class Meta:
        model = Story
        fields = ['teaser', 'author', 'license', 'private']
        
    
class RelatedByIdField(forms.ModelChoiceField):
    widget = forms.CheckboxInput

    def to_python(self, value):
        """ This is a boolean for yes/no, we need the related object if it is True """
        if value:
            return self.queryset.first()
        return None

class StoryForm(forms.ModelForm):
    """ Used to create or edit a story.  It picks up on inspired_by via 2 mechanisms """

    text = MartorFormField(label=_('Story'), required=True)
    author = forms.ModelChoiceField(label=_('Pseudonym'), queryset=None, required=True)
    private = forms.BooleanField(required=False)
    inspired_by = RelatedByIdField(required=False, queryset=None)
    preceded_by = RelatedByIdField(label=_("This story is preceded by"), required=False, queryset=None)

    class Meta:
        model = Story
        fields = ['author', 'preceded_by', 'title', 'tagline', 'text', 'inspired_by', 'private']

    def get_from_object_or_data(self, name):
        """ We can get a value for some fields from the initial, data or the instance and it 
              might be an int or an instance.  Hide all of that here."""
        if self.instance and getattr(self.instance, name):
            return getattr(self.instance, name).id
        else:
            value = self.initial.get(name, self.data.get(name, None))
            if value:
                if isinstance(value, Story):
                    return value.id
                else:
                    return int(value)

        return None
        
    def adjust_field(self, name):
        obj_id = self.get_from_object_or_data(name)
        if obj_id:
            self.fields[name].queryset = Story.objects.published(pk=obj_id)
        else:
            # The user cannot supply a value for these fields (only check the box)
            #   Remove the field if there is no value to check the box for
            del self.fields[name]
        

    def __init__(self, *args, user, **kwargs):
        super(StoryForm, self).__init__(*args, **kwargs)

        width = Story._meta.get_field('title').max_length
        self.fields['title'].widget.attrs['size'] = width
        self.fields['tagline'].widget.attrs['size'] = width
        self.fields['text'].widget.attrs['cols'] = width

        self.fields['author'].queryset = Author.objects.for_user(user)

        # These are optional fields that may or may not be present depending on 
        #   GET params or values in the instance.  Remove/adjust them depending
        #   on the data available.
        self.adjust_field('inspired_by')
        self.adjust_field('preceded_by')


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
