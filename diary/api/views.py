from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from stories.serializers import Story, StorySerializer
from authors.serializers import Author, AuthorSerializer


class StoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows stories to be viewed or edited.
    """
    queryset = Story.objects.recent()
    serializer_class = StorySerializer


class AuthorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows authors to be viewed or edited.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
