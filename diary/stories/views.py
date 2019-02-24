import urllib

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, CreateView, ModelFormMixin
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils import timezone

from .models import Story
from authors.models import Author
from .forms import StoryForm, PublishForm

# Create your views here.

class Recent(ListView):
    """ List recent entries that have been published """

    def get_queryset(self):
        return Story.objects.recent()


class ByAuthor(ListView):
    """ List recent entries that have been published """

    def get_template_names(self):
        return ['stories/story-list-by-author.html']

    def get_queryset(self):
        return Story.objects.by_author(author=self.kwargs['pk'])

    def get_context_data(self):
        """ Not sure why the call arguments are empty like this, it should have an
             object_list and **kwargs, but those are throwing errors......"""
        context = super(ByAuthor, self).get_context_data()
        context['author'] = Author.objects.get(pk=self.kwargs['pk'])
        return context


class CommonStoryFormMixin(ModelFormMixin):

    model = Story
    form_class = StoryForm

    def get_field_from_request(self, name):
        """ Return the story that inspired this story or preceded this story,
              take that from the object, 
              or if creating a new story, from the GET params """
        _name = '_' + name
        if not hasattr(self, _name):
            setattr(self, _name, None)

            if self.object:
                setattr(self, _name, getattr(self.object, name))

            pk = self.request.GET.get(name, None)
            if pk:
                # This seems hacky as hell.....
                setattr(self, _name, Story.objects.published(pk=int(pk)).first())
            else:
                setattr(self, _name, None)

        return getattr(self, _name)



    def get_form_kwargs(self):
        """ The form needs the user to get the list of possible authors """
        kwargs = super(CommonStoryFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user

        return kwargs

    def get_success_url(self):
        return reverse('stories:read', kwargs={'pk': self.object.id})

    def get_initial(self):
        initial = super(CommonStoryFormMixin, self).get_initial()
        for key in ('inspired_by', 'preceded_by', 'author'):
            value = self.get_field_from_request(key)
            if value:
                initial[key] = value
        return initial

    def get_context_data(self, **kwargs):
        context = super(CommonStoryFormMixin, self).get_context_data(**kwargs)
        for key in ('inspired_by', 'preceded_by'):
            context[key] = self.get_field_from_request(key)
        return context


class Create(LoginRequiredMixin, CommonStoryFormMixin, CreateView):
    """ Create a new entry in the diary of life """

    def get(self, request, *args, **kwargs):
        has_pseudonyms = Author.objects.for_user(self.request.user).exists()

        if not has_pseudonyms:
            return HttpResponseRedirect(reverse('authors:explain')
                                        + '?' + urllib.parse.urlencode({
                                            'next': request.get_full_path()
                                        }))
        self.object = None
        return super(Create, self).get(request, *args, **kwargs)


class Edit(LoginRequiredMixin, CommonStoryFormMixin, UpdateView):
    """ Update an existing entry in the diary of life """
    pass

class Publish(LoginRequiredMixin, CommonStoryFormMixin, UpdateView):
    """ Publish a saved but as yet unpublished entry in the diary of life """
    form_class = PublishForm



class Read(DetailView):
    model = Story

    def get_object(self, queryset=None):
        obj = super(Read, self).get_object(queryset)

        if not obj.published_at and obj.author.user != self.request.user:
            obj.title = _("This entry is private")
            obj.text = _("This entry can only be read by it's author")

        if obj.hidden_at:
            obj.title = _("This entry is hidden")
            obj.text = _("This entry is not available for viewing by anyone")

        return obj

    def get_context_data(self, **kwargs):
        context = super(Read, self).get_context_data(**kwargs)
        context['inspired'] = Story.objects.inspired(inspiration=self.object)

        return context
