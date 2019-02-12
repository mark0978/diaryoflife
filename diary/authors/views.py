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


class Explain(LoginRequiredMixin, CommonAuthorFormMixin, CreateView):
    """ Explain the concept of Pseudonyms and writing a story and get the user to
          create their first pseudonym so they can write a story. """
    template_name = "authors/explain_author_form.html"

    def get_success_url(self):
        return (self.request.GET.get('next', None)
                or super(Explain, self).get_success_url())

class Create(LoginRequiredMixin, CommonAuthorFormMixin, CreateView):
    """ Create a new author bio/name/avatar """
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

