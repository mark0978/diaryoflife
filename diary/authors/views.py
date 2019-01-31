from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, CreateView, ModelFormMixin
from django.urls import reverse

from authors.models import Author
from authors.forms import AuthorForm
from stories.models import Story

# Create your views here.

class MyPseudonyms(LoginRequiredMixin, ListView):

    def get_queryset(self):
        return Author.objects.for_user(self.request.user)

class CommonAuthorFormMixin(ModelFormMixin):
    model = Author
    form_class = AuthorForm

    def get_form_kwargs(self):
        """ The form needs the user to save an author object """
        kwargs = super(CommonAuthorFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user

        return kwargs

    def get_success_url(self):
        return reverse('authors:detail', kwargs={'pk': self.object.id})


class Create(LoginRequiredMixin, CommonAuthorFormMixin, CreateView):
    """ Update an new author bio/name/avatar """
    pass


class Edit(LoginRequiredMixin, CommonAuthorFormMixin, UpdateView):
    """ Update an existing author bio/name/avatar """
    pass


class Detail(DetailView):
    model = Author

    def get_context_data(self, **kwargs):
        context = super(Detail, self).get_context_data(**kwargs)
        context['stories_by_author'] = Story.objects.by_author(author=self.object)

        return context

