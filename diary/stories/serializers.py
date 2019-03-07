from rest_framework import serializers
from rest_framework.fields import empty

from stories.models import Story

class StorySerializer(serializers.HyperlinkedModelSerializer):
    """ This contains all the info we share about the Story with the API.
          It would be used with the Story Detail view. """
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ('id', 'title', 'tagline', 'author_id', 'html',
                  'inspired_by_id', 'next_chapter_id', 'teaser',
                  'published_at', 'preceded_by_id', 'can_edit')

    def get_can_edit(self, obj):
        """ Can the person that requested this object edit it?
              (Are they the owner?) """
        return self.context['request'].user == obj.author.user


class StorySummarySerializer(serializers.ModelSerializer):
    """ The list of stories has no need of the html data which can be pulled
          later if they choose to read the story.  This contains enough info
          to display the story summary card and nothing else. """
    class Meta:
        models = Story

    class Meta:
        model = Story
        fields = ('id', 'title', 'tagline', 'author_id', 'teaser',
                  'published_at')

    def __init__(self, instance=None, data=empty, **kwargs):
        super(StorySummarySerializer, self).__init__(instance, data, read_only=True, **kwargs)
