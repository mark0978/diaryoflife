from rest_framework import serializers

from authors.models import Author

class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'name', 'bio_text', 'bio_html', 'avatar',)
