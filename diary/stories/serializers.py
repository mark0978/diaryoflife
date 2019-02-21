from rest_framework import serializers

from stories.models import Story

class StorySerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(view_name="story-detail")
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ('url', 'title', 'tagline', 'author', 'html', 'inspired_by', 
                  'published_at', 'preceeded_by', 'next_chapter', 'can_edit')

    def get_can_edit(self, obj):
        """ Can the person that requested this object edit it?
              (Are they the owner?) """
        return self.context['request'].user == obj.author.user