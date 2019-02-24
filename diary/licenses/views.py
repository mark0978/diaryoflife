from django.shortcuts import render
from django.views.generic import ListView, DetailView

from licenses.models import License
# Create your views here.

class Active(ListView):
    """ List licenses that are available for use """

    def get_queryset(self):
        return License.objects.active()

class Read(DetailView):
    model = License
