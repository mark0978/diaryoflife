from django.shortcuts import render
from django.contrib.auth import get_user_model # If used custom user model

# Create your views here.
from rest_framework import viewsets, permissions
from rest_framework.generics import CreateAPIView

from stories.serializers import Story, StorySerializer, StorySummarySerializer
from authors.serializers import Author, AuthorSerializer
from .serializers import UserSerializer


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


class StorySummaryViewSet(viewsets.mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    """
    API endpoint that allows stories to be listed in short story cards.
    """
    serializer_class = StorySummarySerializer
    queryset = Story.objects.all()

    def get_queryset(self):
        author_id = self.request.GET.get('author_id')
        if author_id:
            return Story.objects.by_author(author_id).all()
        inspired_by_id = self.request.GET.get('inspired_by_id')
        if inspired_by_id:
            return Story.objects.inspired(inspired_by_id).all()
        return Story.objects.recent().all()


class AuthorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows authors to be viewed or edited.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class CreateUserView(CreateAPIView):

    model = get_user_model()
    permission_classes = [
        permissions.AllowAny # Or anon users can't register
    ]
    serializer_class = UserSerializer

create_user = CreateUserView.as_view()
