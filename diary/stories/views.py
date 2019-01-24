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
from .forms import StoryForm

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
        return Story.objects.recent().filter(author=self.kwargs['pk'])

    def get_context_data(self):
        """ Not sure why the call arguments are empty like this, it should have an
             object_list and **kwargs, but those are throwing errors......"""
        context = super(ByAuthor, self).get_context_data()
        context['author'] = Author.objects.get(pk=self.kwargs['pk'])
        return context


class CommonStoryFormMixin(ModelFormMixin):

    def get_inspired_by(self):
        """ Return the story that inspired this story, take that from the object, or if creating a
              new story, from the GET params """
        if self.object:
            return self.object.inspired_by

        pk = self.request.GET.get('inspired_by', None)
        if pk:
            # This seems hacky as hell.....
            return Story.objects.published(pk=int(pk)).first()

    def get_form(self, form_class=None):
        form = super(CommonStoryFormMixin, self).get_form(form_class)
        form.fields['author'].queryset = Author.objects.for_user(self.request.user)

        inspired_by = self.get_inspired_by()
        if inspired_by:
            form.fields['inspired_by'].label = _('Inspired by "%s"') % inspired_by.title
        else:
            del form.fields['inspired_by']
        return form

    def get_success_url(self):
        return reverse('stories:read', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        obj = form.save(commit=False)
        if form.cleaned_data["private"]:
            obj.published_at = None
        elif not obj.published_at:
            obj.published_at = timezone.now()
        obj.save()
        self.object = obj
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CommonStoryFormMixin, self).get_context_data(**kwargs)
        return context

    def get_initial(self):
        initial = super(CommonStoryFormMixin, self).get_initial()
        initial['inspired_by'] = self.request.GET.get('inspired_by', None)
        return initial


class Create(LoginRequiredMixin, CommonStoryFormMixin, CreateView):
    """ Create a new entry in the diary of life """
    model = Story
    form_class = StoryForm


class Edit(LoginRequiredMixin, CommonStoryFormMixin, UpdateView):
    """ Update an existing entry in the diary of life """
    model = Story
    form_class = StoryForm


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