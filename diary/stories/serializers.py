from rest_framework import serializers

from stories.models import Story

class StorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Story
        fields = ('title', 'tagline', 'author', 'text', 'html', 'inspired_by', 'published_at',)
