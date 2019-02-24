from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from stories.serializers import Story, StorySerializer
from authors.serializers import Author, AuthorSerializer


class StoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows stories to be viewed or edited.
    """
    serializer_class = StorySerializer
    queryset = Story.objects.all()
    
    def get_queryset(self):
        author_id = self.request.GET.get('author_id')
        if author_id:
            return Story.objects.by_author(author_id).all()
        return Story.objects.recent().all()


class AuthorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows authors to be viewed or edited.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
