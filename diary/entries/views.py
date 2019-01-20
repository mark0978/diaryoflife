from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, CreateView, ModelFormMixin
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.safestring import SafeString

from markdownx.utils import markdownify

from .models import Entry
from authors.models import Author
from .forms import EntryForm

# Create your views here.

class Recent(ListView):
    """ List recent entries that have been published """

    def get_queryset(self):
        return Entry.objects.recent()

class CommonEntryFormMixin(ModelFormMixin):
    def get_form(self, form_class=None):
        form = super(CommonEntryFormMixin, self).get_form(form_class)
        form.fields['author'].queryset = Author.objects.for_user(self.request.user)
        return form

    def get_success_url(self):
        return reverse('entries:read', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        obj = form.save(commit=False)
        if form.cleaned_data["private"]:
            obj.published_at = None
        obj.save()
        return HttpResponseRedirect(self.get_success_url())


class Create(LoginRequiredMixin, CommonEntryFormMixin, CreateView):
    """ Create a new entry in the diary of life """
    model = Entry
    form_class = EntryForm


class Edit(LoginRequiredMixin, CommonEntryFormMixin, UpdateView):
    """ Update an existing entry in the diary of life """
    model = Entry
    form_class = EntryForm


class Read(DetailView):
    model = Entry

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
        context['formatted_text'] = SafeString(markdownify(self.object.text))

        return context
